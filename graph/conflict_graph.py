# graph/conflict_graph.py — Enhanced Graph Analytics
"""
V2 Improvement: Adds betweenness centrality, community detection,
PageRank, and a composite litigation risk score.
"""
import networkx as nx
import sqlite3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DB_PATH


def build_graph(db_path: str = None) -> nx.MultiDiGraph:
    """Build a NetworkX MultiDiGraph from entities and case_edges tables."""
    if db_path is None:
        db_path = DB_PATH

    G = nx.MultiDiGraph()
    conn = sqlite3.connect(db_path)

    for row in conn.execute("SELECT id, name, type FROM entities"):
        G.add_node(row[0], label=row[1], entity_type=row[2], case_count=0)

    for row in conn.execute("SELECT case_id, entity_a, entity_b, edge_type FROM case_edges"):
        case_id, entity_a, entity_b, edge_type = row
        if entity_a not in G:
            G.add_node(entity_a, label=entity_a, entity_type="unknown", case_count=0)
        if entity_b not in G:
            G.add_node(entity_b, label=entity_b, entity_type="unknown", case_count=0)
        G.add_edge(entity_a, entity_b, case_id=case_id, edge_type=edge_type)
        G.nodes[entity_a]["case_count"] = G.nodes[entity_a].get("case_count", 0) + 1
        G.nodes[entity_b]["case_count"] = G.nodes[entity_b].get("case_count", 0) + 1

    conn.close()
    return G


def compute_centrality_metrics(G: nx.MultiDiGraph) -> dict:
    """Compute centrality metrics for all nodes."""
    if len(G.nodes) == 0:
        return {}

    # Convert to simple graph for some metrics
    G_simple = nx.Graph(G)

    # Betweenness centrality
    betweenness = nx.betweenness_centrality(G_simple)

    # PageRank (on directed graph)
    try:
        pagerank = nx.pagerank(G, alpha=0.85)
    except (nx.PowerIterationFailedConvergence, ZeroDivisionError):
        pagerank = {n: 1.0 / len(G.nodes) for n in G.nodes}

    # Degree centrality
    degree = nx.degree_centrality(G_simple)

    metrics = {}
    for node in G.nodes:
        case_count = G.nodes[node].get("case_count", 0)
        bc = betweenness.get(node, 0)
        pr = pagerank.get(node, 0)
        dc = degree.get(node, 0)

        # Composite litigation risk score (0-100)
        risk = min(100, int(
            (case_count / max(1, max(G.nodes[n].get("case_count", 0) for n in G.nodes))) * 40 +
            bc * 30 +
            pr * 100 * 20 +
            dc * 10
        ))

        metrics[node] = {
            "betweenness": round(bc, 4),
            "pagerank": round(pr, 4),
            "degree_centrality": round(dc, 4),
            "litigation_risk": risk,
        }

    return metrics


def detect_communities(G: nx.MultiDiGraph) -> dict:
    """Detect communities using greedy modularity (no extra dependency)."""
    if len(G.nodes) < 2:
        return {n: 0 for n in G.nodes}

    G_simple = nx.Graph(G)

    try:
        # Try python-louvain if available
        import community as community_louvain
        partition = community_louvain.best_partition(G_simple)
        return partition
    except ImportError:
        pass

    # Fallback: greedy modularity
    try:
        communities = nx.community.greedy_modularity_communities(G_simple)
        partition = {}
        for i, comm in enumerate(communities):
            for node in comm:
                partition[node] = i
        return partition
    except Exception:
        return {n: 0 for n in G.nodes}


def detect_repeat_offenders(G: nx.MultiDiGraph, threshold: int = 3) -> list[dict]:
    """Find entities involved in more cases than the threshold."""
    metrics = compute_centrality_metrics(G)
    offenders = []
    for n in G.nodes:
        cc = G.nodes[n].get("case_count", 0)
        if cc >= threshold:
            m = metrics.get(n, {})
            offenders.append({
                "entity": n,
                "label": G.nodes[n].get("label", n),
                "case_count": cc,
                "entity_type": G.nodes[n].get("entity_type", "unknown"),
                "litigation_risk": m.get("litigation_risk", 0),
                "pagerank": m.get("pagerank", 0),
                "betweenness": m.get("betweenness", 0),
            })
    return sorted(offenders, key=lambda x: x["litigation_risk"], reverse=True)


def detect_systematic_patterns(G: nx.MultiDiGraph) -> list[dict]:
    """Detect entities with same edge_type against different parties."""
    alerts = []
    for node in G.nodes:
        edge_types = {}
        for _, target, data in G.edges(node, data=True):
            etype = data.get("edge_type", "")
            if etype not in edge_types:
                edge_types[etype] = set()
            edge_types[etype].add(target)

        for etype, targets in edge_types.items():
            if len(targets) >= 3:
                alerts.append({
                    "entity": node,
                    "label": G.nodes[node].get("label", node),
                    "pattern": etype,
                    "target_count": len(targets),
                    "severity": "high" if len(targets) >= 5 else "medium",
                })

    return alerts


def get_entity_history(G: nx.MultiDiGraph, entity_id: str) -> dict:
    """Get the full dispute history for an entity."""
    if entity_id not in G:
        return {"node_count": 0, "edge_count": 0, "edges": [], "metrics": {}}

    neighbors = list(set(list(G.neighbors(entity_id)) + list(G.predecessors(entity_id))))
    subgraph = G.subgraph([entity_id] + neighbors)

    edges = []
    for u, v, data in subgraph.edges(data=True):
        edges.append({
            "from": G.nodes[u].get("label", u),
            "to": G.nodes[v].get("label", v),
            "from_id": u,
            "to_id": v,
            "case_id": data.get("case_id", ""),
            "edge_type": data.get("edge_type", ""),
        })

    metrics = compute_centrality_metrics(G).get(entity_id, {})

    return {
        "node_count": subgraph.number_of_nodes(),
        "edge_count": subgraph.number_of_edges(),
        "edges": edges,
        "metrics": metrics,
    }


def get_graph_summary(G: nx.MultiDiGraph) -> dict:
    """Get high-level graph statistics."""
    if len(G.nodes) == 0:
        return {"nodes": 0, "edges": 0, "density": 0, "components": 0}

    G_simple = nx.Graph(G)
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G_simple), 4),
        "components": nx.number_connected_components(G_simple),
        "avg_degree": round(sum(dict(G_simple.degree()).values()) / max(1, len(G_simple.nodes)), 2),
    }
