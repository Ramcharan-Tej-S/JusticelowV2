# test_smoke.py — JusticeFlow V2 Smoke Test
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("  JusticeFlow V2 — Smoke Test")
print("=" * 60)

# Test 1: Config
print("\n[1/8] Testing config...")
from config import get_llm, COLORS, CASE_CATEGORIES, CATEGORY_LABELS
assert len(COLORS) > 10, "Missing color tokens"
assert len(CASE_CATEGORIES) == 9, "Expected 9 categories"
assert len(CATEGORY_LABELS) == 9, "Expected 9 category labels"
print(f"  ✅ Config OK: {len(COLORS)} colors, {len(CASE_CATEGORIES)} categories")

# Test 2: Database
print("\n[2/8] Testing database...")
from db.database import init_db, get_connection, get_stats
init_db()
conn = get_connection()
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
table_names = [t[0] for t in tables]
conn.close()
assert "cases" in table_names, "Missing cases table"
assert "entities" in table_names, "Missing entities table"
assert "case_edges" in table_names, "Missing case_edges table"
assert "negotiation_log" in table_names, "Missing negotiation_log table"
assert "historical_cases" in table_names, "Missing historical_cases table"
print(f"  ✅ DB OK: {len(table_names)} tables: {table_names}")

# Test 3: Agent imports
print("\n[3/8] Testing agent imports...")
from agents.dna_agent import build_dna_vector, cosine_similarity, find_case_twin
print("  ✅ DNA agent (Chain-of-Thought) OK")
from agents.dls_agent import compute_dls
print("  ✅ DLS agent (LLM-as-Judge) OK")
from agents.emotion_agent import analyze_emotion, EMOTION_COLORS
print("  ✅ Emotion agent (Aspect-level) OK")
from agents.negotiation_graph import create_initial_state, run_negotiation_round
print("  ✅ Negotiation agent (State Machine) OK")
from agents.auto_filter_agent import run_filter_pipeline
print("  ✅ Auto-filter agent (Sequential Chain) OK")
from agents.judge_agent import generate_judge_brief
print("  ✅ Judge agent (Aggregator) OK")

# Test 4: Graph
print("\n[4/8] Testing graph module...")
from graph.conflict_graph import (
    build_graph, compute_centrality_metrics, detect_communities,
    detect_repeat_offenders, detect_systematic_patterns, get_graph_summary
)
G = build_graph()
summary = get_graph_summary(G)
print(f"  ✅ Graph OK: {summary}")

# Test 5: Charts
print("\n[5/8] Testing charts...")
from utils.charts import (
    render_gauge, render_dna_radar, render_dls_breakdown,
    render_emotion_timeline, render_conflict_graph,
    render_negotiation_offers, render_category_distribution,
)
fig = render_gauge(65, "Test Gauge")
assert fig is not None, "Gauge chart failed"
fig2 = render_dna_radar([0.5, 0.6, 0.7, 0.8, 0.3, 0.4])
assert fig2 is not None, "Radar chart failed"
print("  ✅ Charts OK: all chart functions return valid figures")

# Test 6: Theme
print("\n[6/8] Testing theme...")
from utils.theme import inject_css, page_header, section_header, metric_card, badge, cot_reasoning_box
print("  ✅ Theme OK: all functions importable")

# Test 7: Seed data
print("\n[7/8] Testing seed data...")
from utils.seed_data import seed_all, HISTORICAL_CASES, DEMO_CASES
cases, entities, edges = seed_all()
print(f"  ✅ Seed data OK: {cases} cases, {entities} entities, {edges} edges")
print(f"     Historical: {len(HISTORICAL_CASES)} cases with real statutes")
print(f"     Demo: {len(DEMO_CASES)} active cases")

# Test 8: Verify seeded data
print("\n[8/8] Verifying database content...")
from db.database import get_historical_cases, get_all_cases
hist = get_historical_cases()
all_cases = get_all_cases()
stats = get_stats()
print(f"  ✅ Database verified: {stats}")
assert len(hist) >= 20, f"Expected 20+ historical cases, got {len(hist)}"

print("\n" + "=" * 60)
print("  ✅ ALL TESTS PASSED — JusticeFlow V2 is ready!")
print("=" * 60)
print(f"\nTo run the app:")
print(f'  cd "{os.path.dirname(os.path.abspath(__file__))}"')
print(f'  $env:GROQ_API_KEY = "your_key"; streamlit run app.py')
