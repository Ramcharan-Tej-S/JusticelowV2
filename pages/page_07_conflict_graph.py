# pages/page_07_conflict_graph.py — Enhanced Graph Analytics
import streamlit as st
from utils.theme import page_header, section_header, metric_card, badge
from utils.charts import render_conflict_graph
from graph.conflict_graph import (
    build_graph, compute_centrality_metrics, detect_communities,
    detect_repeat_offenders, detect_systematic_patterns, get_graph_summary,
)


def render():
    page_header("🕸️ Conflict Graph", "Network analysis with PageRank, centrality, and community detection")

    # Build graph
    G = build_graph()
    summary = get_graph_summary(G)

    if summary["nodes"] == 0:
        st.info("No entities in the graph yet. File some cases or seed demo data first.")
        return

    # Graph stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Nodes", str(summary["nodes"]), "Entities")
    with c2:
        metric_card("Edges", str(summary["edges"]), "Dispute links")
    with c3:
        metric_card("Components", str(summary["components"]), "Isolated clusters")
    with c4:
        metric_card("Avg Degree", str(summary["avg_degree"]), "Connections per entity")

    # Visualization
    section_header("🕸️ Dispute Network")

    communities = detect_communities(G)

    # Prepare data for chart
    nodes_data = []
    for n in G.nodes:
        nodes_data.append({
            "id": n,
            "label": G.nodes[n].get("label", n),
            "entity_type": G.nodes[n].get("entity_type", "unknown"),
            "case_count": G.nodes[n].get("case_count", 0),
        })

    edges_data = []
    for u, v, data in G.edges(data=True):
        edges_data.append({
            "from_id": u,
            "to_id": v,
            "case_id": data.get("case_id", ""),
            "edge_type": data.get("edge_type", ""),
        })

    fig = render_conflict_graph(nodes_data, edges_data, communities)
    st.plotly_chart(fig, use_container_width=True)

    # Analytics tabs
    tab1, tab2, tab3 = st.tabs(["🔴 Repeat Offenders", "📊 Centrality Metrics", "⚠️ Systematic Patterns"])

    with tab1:
        offenders = detect_repeat_offenders(G, threshold=2)
        if offenders:
            for off in offenders:
                risk_color = "#FF5252" if off["litigation_risk"] > 60 else "#FFB740" if off["litigation_risk"] > 30 else "#00E676"
                st.markdown(f"""
                <div class="glass-panel" style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #E8EAED; font-weight: 600;">{off['label']}</span>
                        <span style="margin-left: 0.5rem;">{badge(off['entity_type'], 'info')}</span>
                        <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.3rem;">
                            {off['case_count']} cases · PageRank: {off.get('pagerank', 0):.4f} · Betweenness: {off.get('betweenness', 0):.4f}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: {risk_color}; font-weight: 700; font-size: 1.3rem;">
                            {off['litigation_risk']}
                        </div>
                        <div style="color: #9AA0A6; font-size: 0.75rem;">Risk Score</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No repeat offenders detected (threshold: 2+ cases).")

    with tab2:
        metrics = compute_centrality_metrics(G)
        if metrics:
            # Sort by risk
            sorted_nodes = sorted(metrics.items(), key=lambda x: x[1]["litigation_risk"], reverse=True)

            st.markdown("""
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; padding: 0.75rem 1rem;
                        background: #242736; border-radius: 10px; margin-bottom: 0.5rem;">
                <span style="color: #9AA0A6; font-weight: 600; font-size: 0.8rem;">Entity</span>
                <span style="color: #9AA0A6; font-weight: 600; font-size: 0.8rem;">PageRank</span>
                <span style="color: #9AA0A6; font-weight: 600; font-size: 0.8rem;">Betweenness</span>
                <span style="color: #9AA0A6; font-weight: 600; font-size: 0.8rem;">Risk Score</span>
            </div>
            """, unsafe_allow_html=True)

            for node_id, m in sorted_nodes[:15]:
                label = G.nodes[node_id].get("label", node_id)
                risk_color = "#FF5252" if m["litigation_risk"] > 60 else "#FFB740" if m["litigation_risk"] > 30 else "#00E676"
                st.markdown(f"""
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; padding: 0.5rem 1rem;
                            border-bottom: 1px solid #2D3143;">
                    <span style="color: #E8EAED; font-size: 0.85rem;">{label[:25]}</span>
                    <span style="color: #6C63FF; font-size: 0.85rem;">{m['pagerank']:.4f}</span>
                    <span style="color: #00D9FF; font-size: 0.85rem;">{m['betweenness']:.4f}</span>
                    <span style="color: {risk_color}; font-weight: 600; font-size: 0.85rem;">{m['litigation_risk']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Not enough data for centrality metrics.")

    with tab3:
        patterns = detect_systematic_patterns(G)
        if patterns:
            for p in patterns:
                severity_color = "#FF5252" if p.get("severity") == "high" else "#FFB740"
                st.markdown(f"""
                <div class="glass-panel" style="border-left: 3px solid {severity_color};">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #E8EAED; font-weight: 600;">{p['label']}</span>
                        {badge(p.get('severity', 'medium').upper(), 'danger' if p.get('severity') == 'high' else 'warning')}
                    </div>
                    <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.3rem;">
                        Pattern: <strong>{p['pattern']}</strong> against {p['target_count']} different parties
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No systematic filing patterns detected.")

    # Community breakdown
    section_header("🏘️ Community Detection")
    if communities:
        comm_counts = {}
        for node, comm_id in communities.items():
            if comm_id not in comm_counts:
                comm_counts[comm_id] = []
            comm_counts[comm_id].append(G.nodes[node].get("label", node))

        for comm_id, members in sorted(comm_counts.items()):
            st.markdown(f"""
            <div class="glass-panel" style="padding: 1rem;">
                <span style="color: #6C63FF; font-weight: 600;">Community {comm_id + 1}</span>
                <span style="color: #9AA0A6; margin-left: 0.5rem;">{len(members)} members</span>
                <div style="color: #E8EAED; font-size: 0.85rem; margin-top: 0.3rem;">
                    {', '.join(members[:10])}{'...' if len(members) > 10 else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
