# pages/page_02_dls_engine.py — LLM-as-Judge Dismissal Likelihood Score
import streamlit as st
import json
from utils.theme import page_header, section_header, cot_reasoning_box, metric_card, badge, confidence_bar
from utils.charts import render_gauge, render_dls_breakdown
from config import get_llm
from db.database import get_all_cases, update_case


def render():
    page_header("📊 DLS Engine", "LLM-as-Judge: Three-step dismissal risk analysis with self-critique")

    # Case selector
    cases = get_all_cases()
    if not cases:
        st.info("No cases filed yet. Go to **📝 File Case** first.")
        return

    case_options = {f"{c['id']} — {c['title']}": c for c in cases}
    selected = st.selectbox("Select a case to analyze", list(case_options.keys()))
    case = case_options[selected]

    st.markdown(f"""
    <div class="glass-panel">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="color: #E8EAED; font-weight: 600;">{case['title']}</div>
                <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.3rem;">
                    {case['category']} · {case['jurisdiction']} · ${case.get('claim_amount', 0):,.0f}
                </div>
            </div>
            <div>{badge(case.get('status', 'intake').upper(), 'info')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show AI pattern explanation
    st.markdown("""
    <div class="glass-panel">
        <span style="color: #6C63FF; font-weight: 600;">Three-Step LLM-as-Judge Pattern</span>
        <div style="display: flex; gap: 1.5rem; margin-top: 0.75rem;">
            <div style="flex: 1;">
                <div style="color: #6C63FF; font-size: 0.8rem; font-weight: 600;">Step 1: Initial Assessment</div>
                <div style="color: #9AA0A6; font-size: 0.8rem;">Court clerk analyzes case</div>
            </div>
            <div style="color: #2D3143;">→</div>
            <div style="flex: 1;">
                <div style="color: #00D9FF; font-size: 0.8rem; font-weight: 600;">Step 2: Judicial Critique</div>
                <div style="color: #9AA0A6; font-size: 0.8rem;">Senior judge reviews for flaws</div>
            </div>
            <div style="color: #2D3143;">→</div>
            <div style="flex: 1;">
                <div style="color: #00E676; font-size: 0.8rem; font-weight: 600;">Step 3: Final Synthesis</div>
                <div style="color: #9AA0A6; font-size: 0.8rem;">Balanced score with confidence</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⚡ Run DLS Analysis", use_container_width=True):
        try:
            llm = get_llm()
            from agents.dls_agent import compute_dls

            # Step indicators
            step1_ph = st.empty()
            step2_ph = st.empty()
            step3_ph = st.empty()

            step1_ph.markdown('<div class="step-indicator step-active">⏳ Step 1: Initial Assessment in progress...</div>', unsafe_allow_html=True)

            with st.spinner("Running 3-step analysis..."):
                result = compute_dls(case, llm)

            step1_ph.markdown('<div class="step-indicator step-passed">✅ Step 1: Initial Assessment complete</div>', unsafe_allow_html=True)
            step2_ph.markdown('<div class="step-indicator step-passed">✅ Step 2: Judicial Critique complete</div>', unsafe_allow_html=True)
            step3_ph.markdown('<div class="step-indicator step-passed">✅ Step 3: Final Synthesis complete</div>', unsafe_allow_html=True)

            # Store results
            update_case(case["id"],
                        dls_score=result["dls"],
                        dls_reasons=json.dumps(result["reasons"]),
                        dls_critique=result["critique"],
                        dls_confidence=result["confidence"],
                        status="scored")

            st.markdown("<br>", unsafe_allow_html=True)

            # Display results
            col_gauge, col_meta = st.columns([2, 1])

            with col_gauge:
                fig = render_gauge(result["dls"], "Dismissal Likelihood Score")
                st.plotly_chart(fig, use_container_width=True)

                # Warning banner
                if result["dls"] > 75:
                    st.markdown(f"""
                    <div style="background: rgba(255,82,82,0.1); border: 1px solid rgba(255,82,82,0.3);
                                border-radius: 10px; padding: 1rem; text-align: center;">
                        <span style="font-size: 1.1rem;">⚠️</span>
                        <span style="color: #FF5252; font-weight: 600;">HIGH DISMISSAL RISK</span>
                        <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.3rem;">
                            Score exceeds 75%. Judicial override required to proceed.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with col_meta:
                metric_card("Final Score", f"{result['dls']}%")
                metric_card("Initial Score", f"{result['initial_dls']}%",
                           f"{'↓' if result['dls'] < result['initial_dls'] else '↑'} After critique")
                metric_card("Confidence", f"{result['confidence']:.0%}")
                if result.get("key_risk"):
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Key Risk</h3>
                        <div style="color: #FF5252; font-size: 0.9rem;">{result['key_risk']}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Reason breakdown
            section_header("📊 Risk Factor Breakdown")
            fig2 = render_dls_breakdown(result["reasons"])
            st.plotly_chart(fig2, use_container_width=True)

            # Explanation
            section_header("📝 Final Analysis")
            st.markdown(f"""
            <div class="glass-panel">
                <div style="color: #E8EAED; line-height: 1.6;">{result['explanation']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Critique display
            section_header("🔍 Judicial Critique")
            cot_reasoning_box(result["critique"].replace("\n", "<br>"))

        except Exception as e:
            st.error(f"⚠️ DLS analysis failed: {str(e)}")
            st.info("Make sure your GROQ_API_KEY environment variable is set.")

    # Show existing DLS if available
    elif case.get("dls_score") is not None:
        section_header("📊 Previous DLS Analysis")
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_card("DLS Score", f"{case['dls_score']:.0f}%")
        with col2:
            metric_card("Confidence", f"{case.get('dls_confidence', 0):.0%}" if case.get('dls_confidence') else "N/A")
        with col3:
            metric_card("Status", case.get("status", "intake").upper())

        if case.get("dls_critique"):
            section_header("🔍 Previous Critique")
            cot_reasoning_box(case["dls_critique"].replace("\n", "<br>"))
