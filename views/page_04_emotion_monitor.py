# pages/page_04_emotion_monitor.py — Aspect-Level Emotional Intelligence
import streamlit as st
import json
from utils.theme import page_header, section_header, cot_reasoning_box, metric_card, badge, confidence_bar
from config import get_llm
from db.database import get_all_cases, update_case
from agents.emotion_agent import EMOTION_COLORS, EMOTION_ICONS


def render():
    page_header("💭 Emotion Monitor", "Aspect-level emotional analysis with per-party breakdown")

    cases = get_all_cases()
    if not cases:
        st.info("No cases filed yet. Go to **📝 File Case** first.")
        return

    case_options = {f"{c['id']} — {c['title']}": c for c in cases}
    selected = st.selectbox("Select a case", list(case_options.keys()))
    case = case_options[selected]

    # Tabs for different analysis modes
    tab1, tab2 = st.tabs(["📄 Case Filing Analysis", "✍️ Custom Text Analysis"])

    with tab1:
        if st.button("⚡ Analyze Case Emotions", use_container_width=True, key="case_emotion"):
            _run_analysis(case["description"], case)

    with tab2:
        custom_text = st.text_area(
            "Paste negotiation transcript or legal filing",
            placeholder="Enter text to analyze for emotional content...",
            height=200, key="custom_text"
        )
        if st.button("⚡ Analyze Text", use_container_width=True, key="text_emotion"):
            if custom_text:
                _run_analysis(custom_text, case)
            else:
                st.warning("Please enter text to analyze.")

    # Show existing analysis if available
    if case.get("emotion_detail") and not st.session_state.get("_emotion_just_ran"):
        section_header("📊 Previous Analysis")
        try:
            detail = json.loads(case["emotion_detail"])
            _display_results(detail)
        except:
            pass


def _run_analysis(text: str, case: dict):
    try:
        llm = get_llm()
        from agents.emotion_agent import analyze_emotion

        with st.spinner("🧠 Analyzing emotional dimensions..."):
            result = analyze_emotion(text, llm)

        # Store
        update_case(case["id"],
                    emotional_temp=result["temperature"],
                    emotion_detail=json.dumps(result))

        _display_results(result)
        st.session_state["_emotion_just_ran"] = True

    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")


def _display_results(result: dict):
    temp = result.get("temperature", 50)
    emotion = result.get("dominant_emotion", "neutral")
    icon = EMOTION_ICONS.get(emotion, "😐")
    color = EMOTION_COLORS.get(emotion, "#9AA0A6")

    # Temperature display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <h3>Temperature</h3>
            <div style="font-size: 3rem; margin: 0.5rem 0;">{icon}</div>
            <div class="value" style="background: linear-gradient(135deg, {'#00E676' if temp < 40 else '#FFB740' if temp < 70 else '#FF5252'}, #E8EAED);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{temp}/100</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        metric_card("Dominant Emotion", f"{icon} {emotion.title()}")
    with col3:
        risk = result.get("escalation_risk", 0.5)
        risk_label = "High" if risk > 0.7 else "Medium" if risk > 0.4 else "Low"
        risk_badge = "danger" if risk > 0.7 else "warning" if risk > 0.4 else "success"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Escalation Risk</h3>
            <div style="margin: 0.5rem 0;">{badge(risk_label, risk_badge)}</div>
            <div class="subtitle">Confidence: {result.get('confidence', 0):.0%}</div>
        </div>
        """, unsafe_allow_html=True)

    # Cooling-off alert
    if temp > 70:
        st.markdown(f"""
        <div style="background: rgba(255,82,82,0.1); border: 1px solid rgba(255,82,82,0.3);
                    border-radius: 12px; padding: 1.25rem; margin: 1rem 0; text-align: center;">
            <span style="font-size: 1.3rem;">🚨</span>
            <span style="color: #FF5252; font-weight: 700; font-size: 1.1rem;"> COOLING-OFF PERIOD RECOMMENDED</span>
            <div style="color: #9AA0A6; font-size: 0.9rem; margin-top: 0.5rem;">
                Emotional temperature exceeds 70. Consider a cooling-off period before proceeding.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Party-level breakdown
    party_emotions = result.get("party_emotions", [])
    if party_emotions:
        section_header("👥 Party-Level Emotion Breakdown")
        for pe in party_emotions:
            party_color = EMOTION_COLORS.get(pe.get("emotion", "neutral"), "#9AA0A6")
            party_icon = EMOTION_ICONS.get(pe.get("emotion", "neutral"), "😐")
            intensity = pe.get("intensity", 50)
            st.markdown(f"""
            <div class="glass-panel" style="display: flex; align-items: center; gap: 1rem;">
                <div style="font-size: 1.5rem;">{party_icon}</div>
                <div style="flex: 1;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #E8EAED; font-weight: 600;">{pe.get('party', 'Unknown')}</span>
                        <span style="color: {party_color}; font-weight: 600;">{pe.get('emotion', 'neutral').title()} ({intensity}%)</span>
                    </div>
                    <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.3rem;">
                        {pe.get('reasoning', '')}
                    </div>
                    <div class="confidence-bar" style="margin-top: 0.5rem;">
                        <div class="confidence-fill" style="width: {intensity}%; background: {party_color};"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Trigger phrases
    triggers = result.get("trigger_phrases", [])
    if triggers:
        section_header("🎯 Emotional Trigger Phrases")
        for phrase in triggers:
            st.markdown(f"""
            <div style="background: rgba(255,82,82,0.08); border-left: 3px solid #FF5252;
                        padding: 0.75rem 1rem; margin-bottom: 0.5rem; border-radius: 0 8px 8px 0;">
                <span style="color: #FF5252;">⚡</span>
                <span style="color: #E8EAED; font-style: italic;">"{phrase}"</span>
            </div>
            """, unsafe_allow_html=True)

    # Recommendation
    section_header("💡 Recommended Action")
    st.markdown(f"""
    <div class="cot-box">
        <div class="cot-label">🧠 AI Recommendation</div>
        <div>{result.get('recommendation', 'No recommendation available.')}</div>
    </div>
    """, unsafe_allow_html=True)
