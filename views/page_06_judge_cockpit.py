# pages/page_06_judge_cockpit.py — Multi-Signal Aggregation Dashboard
import streamlit as st
import json
from utils.theme import page_header, section_header, metric_card, badge, cot_reasoning_box, confidence_bar
from utils.charts import render_gauge
from config import get_llm
from db.database import get_all_cases, get_historical_cases, update_case


def render():
    page_header("👨‍⚖️ Judge Cockpit", "AI-aggregated judicial brief synthesizing all case signals")

    cases = get_all_cases()
    if not cases:
        st.info("No cases filed yet. Go to **📝 File Case** first.")
        return

    case_options = {f"{c['id']} — {c['title']}": c for c in cases}
    selected = st.selectbox("Select a case for judicial review", list(case_options.keys()))
    case = case_options[selected]

    # Case overview
    st.markdown(f"""
    <div class="glass-panel">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 1;">
                <div style="color: #E8EAED; font-weight: 600; font-size: 1.1rem;">{case['title']}</div>
                <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.5rem; line-height: 1.6;">
                    {case['description'][:300]}{'...' if len(case.get('description', '')) > 300 else ''}
                </div>
            </div>
            <div style="text-align: right; min-width: 150px;">
                <div>{badge(case.get('status', 'intake').upper(), 'info')}</div>
                <div style="color: #9AA0A6; font-size: 0.8rem; margin-top: 0.5rem;">
                    {case.get('category', '')} · ${case.get('claim_amount', 0):,.0f}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Current signals summary
    section_header("📊 AI Signal Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        dls = case.get("dls_score")
        metric_card("DLS Score", f"{dls:.0f}%" if dls else "—", "Dismissal risk")
    with c2:
        temp = case.get("emotional_temp")
        metric_card("Emotion Temp", f"{temp:.0f}" if temp else "—", "0-100 scale")
    with c3:
        status = case.get("status", "intake")
        metric_card("Status", status.upper())
    with c4:
        conf = case.get("dls_confidence")
        metric_card("AI Confidence", f"{conf:.0%}" if conf else "—")

    # Generate judicial brief
    if st.button("⚡ Generate Judicial Brief", use_container_width=True):
        try:
            llm = get_llm()
            from agents.judge_agent import generate_judge_brief
            from agents.dna_agent import find_case_twin

            # Gather all signals
            dls_result = {
                "dls": case.get("dls_score", 50),
                "confidence": case.get("dls_confidence", 0.5),
                "key_risk": "",
                "critique": case.get("dls_critique", ""),
            }

            # Get twin info
            twin_info = {"similarity": 0, "summary": "No analysis run", "outcome": "N/A"}
            if case.get("dna_vector"):
                try:
                    vector = json.loads(case["dna_vector"])
                    historical = get_historical_cases()
                    twin, sim = find_case_twin(vector, historical)
                    if twin:
                        twin_info = {
                            "similarity": sim,
                            "summary": twin.get("summary", ""),
                            "outcome": twin.get("outcome", "N/A"),
                        }
                except:
                    pass

            emotion_result = {
                "temperature": case.get("emotional_temp", 50),
                "dominant_emotion": "neutral",
                "escalation_risk": 0.5,
            }
            if case.get("emotion_detail"):
                try:
                    emotion_result = json.loads(case["emotion_detail"])
                except:
                    pass

            neg_state = {"status": "not_started", "turn": 0, "current_offer": 0}
            filter_result = {"final_action": "not_run"}
            if case.get("filter_result"):
                try:
                    filter_result = json.loads(case["filter_result"])
                except:
                    pass

            with st.spinner("🧠 Synthesizing all AI signals into judicial brief..."):
                brief = generate_judge_brief(
                    case, dls_result, twin_info, emotion_result,
                    neg_state, filter_result, llm
                )

            # Store
            update_case(case["id"],
                        ai_recommendation=json.dumps(brief),
                        ai_confidence=brief.get("confidence", 0))

            # Display brief
            _display_brief(brief, twin_info)

        except Exception as e:
            st.error(f"Brief generation failed: {str(e)}")

    # Show existing brief
    elif case.get("ai_recommendation"):
        try:
            brief = json.loads(case["ai_recommendation"])
            twin_info = {"similarity": 0, "summary": "", "outcome": "N/A"}
            if case.get("dna_vector"):
                try:
                    vector = json.loads(case["dna_vector"])
                    historical = get_historical_cases()
                    twin, sim = find_case_twin(vector, historical)
                    if twin:
                        twin_info = {"similarity": sim, "summary": twin.get("summary", ""), "outcome": twin.get("outcome", "")}
                except:
                    pass
            _display_brief(brief, twin_info)
        except:
            pass

    # Quick actions
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("⚡ Judicial Actions")
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        if st.button("✅ Proceed to Trial", use_container_width=True):
            update_case(case["id"], status="escalated")
            st.success("Case escalated to trial.")
            st.rerun()
    with col_a2:
        if st.button("🤝 Send to Mediation", use_container_width=True):
            update_case(case["id"], status="negotiating")
            st.info("Case sent to negotiation sandbox.")
            st.rerun()
    with col_a3:
        if st.button("❌ Dismiss Case", use_container_width=True):
            update_case(case["id"], status="dismissed")
            st.warning("Case dismissed.")
            st.rerun()


def _display_brief(brief: dict, twin_info: dict):
    section_header("📋 AI Judicial Brief")

    # Recommendation
    rec = brief.get("recommendation", "proceed_to_trial")
    rec_colors = {
        "dismiss": ("#FF5252", "danger"),
        "proceed_to_trial": ("#FFB740", "warning"),
        "mediate": ("#00D9FF", "info"),
        "settle": ("#00E676", "success"),
    }
    rec_color, rec_badge = rec_colors.get(rec, ("#9AA0A6", "info"))

    st.markdown(f"""
    <div class="glass-panel" style="border-left: 4px solid {rec_color};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <div>
                <span style="font-weight: 700; color: {rec_color}; font-size: 1rem; text-transform: uppercase;">
                    {rec.replace('_', ' ')}
                </span>
                {badge(brief.get('priority', 'normal').upper(), rec_badge)}
            </div>
            <span style="color: #9AA0A6;">Confidence: {brief.get('confidence', 0):.0%}</span>
        </div>
        <div style="color: #E8EAED; line-height: 1.6;">
            {brief.get('recommendation_reasoning', '')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Risk factors
    with col1:
        section_header("⚠️ Key Risk Factors")
        for rf in brief.get("risk_factors", []):
            severity = rf.get("severity", "medium")
            sv_color = "#FF5252" if severity == "high" else "#FFB740" if severity == "medium" else "#00E676"
            st.markdown(f"""
            <div class="glass-panel" style="padding: 1rem;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #E8EAED; font-weight: 600;">{rf.get('factor', '')}</span>
                    <span style="color: {sv_color}; font-size: 0.8rem; font-weight: 600;">{severity.upper()}</span>
                </div>
                <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.3rem;">
                    💡 {rf.get('mitigation', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Relevant statutes
    with col2:
        section_header("📜 Relevant Statutes")
        for statute in brief.get("relevant_statutes", []):
            st.markdown(f"""
            <div class="glass-panel" style="padding: 1rem;">
                <div style="color: #6C63FF; font-weight: 600; font-size: 0.9rem;">
                    {statute.get('statute', '')}
                </div>
                <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.3rem;">
                    {statute.get('relevance', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Action items and timeline
    col3, col4 = st.columns(2)
    with col3:
        section_header("📝 Action Items")
        for i, item in enumerate(brief.get("action_items", []), 1):
            st.markdown(f"""
            <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span style="color: #6C63FF; font-weight: 600;">{i}.</span>
                <span style="color: #E8EAED;">{item}</span>
            </div>
            """, unsafe_allow_html=True)
    with col4:
        metric_card("Est. Resolution Time", f"{brief.get('estimated_days', 180)} days")
