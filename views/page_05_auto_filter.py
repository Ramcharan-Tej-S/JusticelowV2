# pages/page_05_auto_filter.py — Sequential Reasoning Chain Pipeline
import streamlit as st
import json
import time
from utils.theme import page_header, section_header, badge, metric_card, cot_reasoning_box
from config import get_llm
from db.database import get_all_cases, update_case


def render():
    page_header("🔍 Auto Filter Pipeline", "6-step sequential screening — each step builds on previous context")

    cases = get_all_cases()
    if not cases:
        st.info("No cases filed yet. Go to **📝 File Case** first.")
        return

    # Filter to cases that haven't been filtered yet
    case_options = {f"{c['id']} — {c['title']}": c for c in cases}
    selected = st.selectbox("Select a case to screen", list(case_options.keys()))
    case = case_options[selected]

    # Pipeline architecture display
    st.markdown("""
    <div class="glass-panel">
        <span style="color: #6C63FF; font-weight: 600;">Sequential Chain Architecture</span>
        <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.5rem; line-height: 1.6;">
            Each step receives the accumulated context from ALL previous steps.
            Rule-based steps (1-3) execute instantly. LLM steps (4-6) use previous results for smarter decisions.
        </div>
        <div style="display: flex; gap: 0.5rem; margin-top: 0.75rem; flex-wrap: wrap;">
            <span class="badge badge-success">Rule-Based</span>
            <span class="badge badge-success">Rule-Based</span>
            <span class="badge badge-info">DB Query</span>
            <span class="badge badge-warning">LLM + Context</span>
            <span class="badge badge-warning">LLM + Context</span>
            <span class="badge badge-danger">LLM Synthesis</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⚡ Run Filter Pipeline", use_container_width=True):
        try:
            llm = get_llm()
            from agents.auto_filter_agent import run_filter_pipeline

            # Create step placeholders
            step_phs = []
            for i in range(6):
                step_phs.append(st.empty())

            step_names = [
                "💰 Minimum Claim Threshold",
                "🏛️ Government Party Detection",
                "🔍 Duplicate Case Check",
                "⚖️ AI Jurisdiction Validation",
                "🧪 AI Triviality Assessment",
                "📋 AI Final Recommendation",
            ]

            # Show initial state
            for i, name in enumerate(step_names):
                step_phs[i].markdown(f"""
                <div class="step-indicator" style="opacity: 0.4;">
                    ⏸️ {name} — Waiting...
                </div>
                """, unsafe_allow_html=True)

            # Run pipeline with progress
            with st.spinner("Running 6-step pipeline..."):
                result = run_filter_pipeline(case, llm)

            # Animate results
            for i, step in enumerate(result["steps"]):
                time.sleep(0.3)  # Brief animation delay
                icon = "✅" if step["passed"] else "❌"
                css = "step-passed" if step["passed"] else "step-failed"

                conf_html = ""
                if step.get("confidence"):
                    conf_html = f'<span style="color: #9AA0A6; font-size: 0.75rem; margin-left: 0.5rem;">Confidence: {step["confidence"]:.0%}</span>'

                routing_html = ""
                if step.get("routing"):
                    routing_html = f'<div style="color: #FFB740; font-size: 0.8rem; margin-top: 0.3rem;">📍 Route to: {step["routing"]}</div>'

                type_badge = badge("Rule", "success") if step["type"] == "rule" else badge("DB", "info") if step["type"] == "db_query" else badge("LLM", "warning")

                step_phs[i].markdown(f"""
                <div class="step-indicator {css}">
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            {icon} <strong>{step['name']}</strong> {type_badge}{conf_html}
                        </div>
                        <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.3rem; margin-left: 1.5rem;">
                            {step['detail']}
                        </div>
                        {routing_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Store result
            update_case(case["id"],
                        filter_result=json.dumps(result),
                        status="filtered" if result["passed"] else case.get("status", "intake"))

            # Final verdict
            st.markdown("<br>", unsafe_allow_html=True)
            if result["passed"]:
                st.markdown(f"""
                <div class="glass-panel" style="border-color: rgba(0,230,118,0.4); text-align: center;">
                    <div style="font-size: 2rem;">✅</div>
                    <div style="color: #00E676; font-weight: 700; font-size: 1.2rem;">
                        CASE PASSED ALL FILTERS
                    </div>
                    <div style="color: #9AA0A6; font-size: 0.9rem; margin-top: 0.5rem;">
                        Action: {result.get('final_action', 'proceed').upper()} · {result.get('routing', 'Standard processing')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                failed_steps = [s for s in result["steps"] if not s["passed"]]
                st.markdown(f"""
                <div class="glass-panel" style="border-color: rgba(255,82,82,0.4); text-align: center;">
                    <div style="font-size: 2rem;">⚠️</div>
                    <div style="color: #FF5252; font-weight: 700; font-size: 1.2rem;">
                        CASE FLAGGED — {len(failed_steps)} step(s) failed
                    </div>
                    <div style="color: #9AA0A6; font-size: 0.9rem; margin-top: 0.5rem;">
                        Action: {result.get('final_action', 'flag').upper()} · {result.get('routing', 'Manual review required')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Pipeline error: {str(e)}")

    # Show previous filter results
    elif case.get("filter_result"):
        section_header("📋 Previous Filter Results")
        try:
            prev = json.loads(case["filter_result"])
            for step in prev.get("steps", []):
                icon = "✅" if step["passed"] else "❌"
                css = "step-passed" if step["passed"] else "step-failed"
                st.markdown(f"""
                <div class="step-indicator {css}">
                    {icon} <strong>{step['name']}</strong>
                    <span style="color: #9AA0A6; font-size: 0.85rem; margin-left: 0.5rem;">{step['detail'][:100]}</span>
                </div>
                """, unsafe_allow_html=True)
        except:
            pass
