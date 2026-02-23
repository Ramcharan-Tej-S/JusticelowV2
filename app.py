# app.py — JusticeFlow V2 Streamlit entry point
import streamlit as st
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.theme import inject_css, page_header, metric_card
from db.database import init_db, get_all_cases, get_stats

# ─── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="⚖️ JusticeFlow V2",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Initialize ──────────────────────────────────────────────────────
init_db()
inject_css()

# ─── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1.5rem 0;">
        <div style="font-size: 2.5rem; margin-bottom: 0.3rem;">⚖️</div>
        <h1 style="font-size: 1.5rem; margin:0; letter-spacing: -0.02em;
                    background: linear-gradient(135deg, #6C63FF, #00D9FF);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            JusticeFlow
        </h1>
        <p style="font-size: 0.75rem; margin: 0.3rem 0 0 0; color: #9AA0A6;">
            AI-Powered Dispute Resolution v2.0
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigate",
        [
            "🏠 Home",
            "📝 File Case",
            "📊 DLS Engine",
            "🤝 Negotiation Sandbox",
            "💭 Emotion Monitor",
            "🔍 Auto Filter",
            "👨‍⚖️ Judge Cockpit",
            "🕸️ Conflict Graph",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Seed data button
    if st.button("🌱 Seed Demo Data", use_container_width=True):
        from utils.seed_data import seed_all
        cases, entities, edges = seed_all()
        if cases > 0:
            st.success(f"✅ Seeded {cases} cases, {entities} entities, {edges} edges")
        else:
            st.info("Data already seeded.")

    # Stats
    stats = get_stats()
    st.markdown(f"""
    <div style="text-align:center; padding: 1rem 0; opacity: 0.6; font-size: 0.75rem; color: #9AA0A6;">
        📁 {stats['cases']} cases · 👥 {stats['entities']} entities · 📚 {stats['historical']} historical
    </div>
    """, unsafe_allow_html=True)

# ─── Page Routing ─────────────────────────────────────────────────────
if page == "🏠 Home":
    page_header("⚖️ JusticeFlow", "AI-Powered Dispute Resolution Platform")

    st.markdown("""
    <div style="max-width: 700px; margin-bottom: 2rem;">
        <p style="font-size: 1.05rem; color: #9AA0A6; line-height: 1.7;">
            Transform dispute resolution from a slow, paper-bound process into an intelligent
            system that saves courts time, guides parties toward fair settlements,
            and exposes bad actors through relational graph intelligence.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    col1, col2, col3 = st.columns(3)
    features = [
        ("🧬 Case DNA", "Chain-of-Thought fingerprinting matches cases to historical twins with explainable reasoning.", col1),
        ("📊 DLS Engine", "LLM-as-Judge pattern: initial assessment → critique → refined score with confidence.", col1),
        ("🤝 Negotiation AI", "State machine with plaintiff, defendant, and mediator agents. You preside as judge.", col2),
        ("💭 Emotion Layer", "Aspect-level analysis: per-party emotions, trigger phrases, escalation risk.", col2),
        ("🔍 Auto Filter", "6-step sequential pipeline where each step builds on previous context.", col3),
        ("🕸️ Conflict Graph", "PageRank, betweenness centrality, community detection for dispute networks.", col3),
    ]
    for title, desc, col in features:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{title}</h3>
                <div style="color: #9AA0A6; font-size: 0.85rem; line-height: 1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Active Cases", str(stats["cases"]))
    with c2:
        metric_card("Entities", str(stats["entities"]))
    with c3:
        metric_card("Historical Cases", str(stats["historical"]))
    with c4:
        metric_card("AI Model", "LLaMA 3.3 70B", "via Groq")

    # AI Architecture section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-panel">
        <h3 style="color: #E8EAED; margin-top: 0;">🧠 Smart AI Patterns Used</h3>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;">
            <div>
                <div style="color: #6C63FF; font-weight: 600; font-size: 0.85rem;">Chain-of-Thought</div>
                <div style="color: #9AA0A6; font-size: 0.8rem;">AI reasons step-by-step, citing evidence before scoring</div>
            </div>
            <div>
                <div style="color: #00D9FF; font-weight: 600; font-size: 0.85rem;">LLM-as-Judge</div>
                <div style="color: #9AA0A6; font-size: 0.8rem;">Second LLM critiques the first, then a third synthesizes both</div>
            </div>
            <div>
                <div style="color: #00E676; font-weight: 600; font-size: 0.85rem;">Sequential Chain</div>
                <div style="color: #9AA0A6; font-size: 0.8rem;">Each filter step receives all prior context for smarter decisions</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

elif page == "📝 File Case":
    from views.page_01_file_case import render
    render()
elif page == "📊 DLS Engine":
    from views.page_02_dls_engine import render
    render()
elif page == "🤝 Negotiation Sandbox":
    from views.page_03_negotiation import render
    render()
elif page == "💭 Emotion Monitor":
    from views.page_04_emotion_monitor import render
    render()
elif page == "🔍 Auto Filter":
    from views.page_05_auto_filter import render
    render()
elif page == "👨‍⚖️ Judge Cockpit":
    from views.page_06_judge_cockpit import render
    render()
elif page == "🕸️ Conflict Graph":
    from views.page_07_conflict_graph import render
    render()
