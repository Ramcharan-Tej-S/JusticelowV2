# pages/page_03_negotiation.py — Interactive Negotiation Sandbox
import streamlit as st
import json
from utils.theme import page_header, section_header, badge, metric_card
from utils.charts import render_negotiation_offers, render_emotion_timeline
from config import get_llm
from db.database import get_all_cases, insert_negotiation_turn


def render():
    page_header("🤝 Negotiation Sandbox", "AI agents debate while you preside as judge")

    cases = get_all_cases()
    if not cases:
        st.info("No cases filed yet. Go to **📝 File Case** first.")
        return

    case_options = {f"{c['id']} — {c['title']}": c for c in cases}
    selected = st.selectbox("Select a case", list(case_options.keys()))
    case = case_options[selected]

    # Show AI pattern
    st.markdown("""
    <div class="glass-panel">
        <span style="color: #6C63FF; font-weight: 600;">State Machine Negotiation</span>
        <div style="display: flex; gap: 0.75rem; margin-top: 0.75rem; flex-wrap: wrap;">
            <div class="badge badge-info">Plaintiff Argues</div>
            <span style="color: #2D3143;">→</span>
            <div class="badge badge-warning">Defendant Responds</div>
            <span style="color: #2D3143;">→</span>
            <span class="badge" style="background: rgba(0,217,255,0.15); color: #00D9FF; border: 1px solid rgba(0,217,255,0.3);">Mediator Assesses</span>
            <span style="color: #2D3143;">→</span>
            <div class="badge badge-success">You Intervene as Judge</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Session state
    if "neg_state" not in st.session_state:
        st.session_state.neg_state = None
    if "neg_case_id" not in st.session_state:
        st.session_state.neg_case_id = None

    # Setup form
    if st.session_state.neg_state is None or st.session_state.neg_case_id != case["id"]:
        with st.form("neg_setup"):
            col1, col2 = st.columns(2)
            with col1:
                plaintiff_interests = st.text_area("Plaintiff's Key Interests",
                    value=f"Seeking full compensation of ${case.get('claim_amount', 0):,.0f} for damages and losses described in the case.",
                    height=100)
            with col2:
                defendant_interests = st.text_area("Defendant's Key Interests",
                    value="Minimize liability while maintaining reputation. Willing to negotiate if claim has merit.",
                    height=100)

            max_turns = st.slider("Maximum Rounds", 3, 15, 8)

            if st.form_submit_button("🚀 Start Negotiation", use_container_width=True):
                from agents.negotiation_graph import create_initial_state
                st.session_state.neg_state = create_initial_state(
                    case["id"], case["description"],
                    plaintiff_interests, defendant_interests,
                    case.get("claim_amount", 10000), max_turns
                )
                st.session_state.neg_case_id = case["id"]
                st.rerun()
        return

    # ── Active Negotiation ──
    state = st.session_state.neg_state

    # Status bar
    status_color = "#00E676" if state["status"] == "settled" else "#FF5252" if state["status"] == "failed" else "#6C63FF"
    st.markdown(f"""
    <div class="glass-panel" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="color: {status_color}; font-weight: 700; text-transform: uppercase;">
                {state['status']}
            </span>
            <span style="color: #9AA0A6; margin-left: 1rem;">
                Round {state['turn']} / {state['max_turns']}
            </span>
        </div>
        <div style="color: #E8EAED; font-weight: 600;">
            Current Offer: ${state['current_offer']:,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chat history
    section_header("💬 Negotiation Transcript")
    for entry in state.get("history", []):
        speaker = entry.get("speaker", "")
        if "Plaintiff" in speaker:
            css_class = "chat-plaintiff"
            color = "#6C63FF"
        elif "Defendant" in speaker:
            css_class = "chat-defendant"
            color = "#FFB740"
        elif "Mediator" in speaker:
            css_class = "chat-mediator"
            color = "#00D9FF"
        elif "Judge" in speaker:
            css_class = "chat-judge"
            color = "#00E676"
        else:
            css_class = "chat-mediator"
            color = "#9AA0A6"

        offer_text = f" · Offer: ${entry.get('offer_amount', 0):,.2f}" if entry.get("offer_amount") else ""
        legal_text = f"<div style='color: #9AA0A6; font-size: 0.8rem; margin-top: 0.3rem; font-style: italic;'>📜 {entry.get('legal_basis', '')}</div>" if entry.get("legal_basis") else ""

        st.markdown(f"""
        <div class="chat-message {css_class}">
            <div class="chat-speaker" style="color: {color};">
                {speaker}{offer_text}
            </div>
            <div style="color: #E8EAED; font-size: 0.9rem; line-height: 1.5;">
                {entry.get('message', '')}
            </div>
            {legal_text}
        </div>
        """, unsafe_allow_html=True)

    # Continue negotiation or show results
    if state["status"] == "negotiating":
        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])
        with col1:
            judge_input = st.text_input(
                "⚖️ Judge's Direction (optional)",
                placeholder="Enter guidance for both parties, e.g., 'Consider the strength of the evidence before making your next offer'",
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            run_round = st.button("▶️ Run Next Round", use_container_width=True)

        if run_round:
            try:
                llm = get_llm()
                from agents.negotiation_graph import run_negotiation_round

                with st.spinner(f"⏳ Running Round {state['turn']}..."):
                    state = run_negotiation_round(state, llm, judge_input)

                st.session_state.neg_state = state

                # Log turns
                for entry in state.get("history", [])[-3:]:
                    insert_negotiation_turn(
                        case["id"], state["turn"],
                        entry.get("speaker", ""),
                        entry.get("message", ""),
                        entry.get("offer_amount"),
                        None,
                    )

                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

        # Reset button
        if st.button("🔄 Reset Negotiation"):
            st.session_state.neg_state = None
            st.session_state.neg_case_id = None
            st.rerun()

    else:
        # Show settlement result
        section_header("📋 Negotiation Result")
        if state["status"] == "settled":
            st.markdown(f"""
            <div class="glass-panel" style="border-color: rgba(0,230,118,0.4);">
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">🎉</div>
                    <div style="color: #00E676; font-weight: 700; font-size: 1.3rem; margin: 0.5rem 0;">
                        SETTLEMENT REACHED
                    </div>
                    <div style="color: #E8EAED; font-size: 1.1rem;">
                        {state.get('settlement_text', f"${state['current_offer']:,.2f}")}
                    </div>
                    <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.5rem;">
                        Resolved in {state['turn']} rounds
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="glass-panel" style="border-color: rgba(255,82,82,0.4);">
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">⚠️</div>
                    <div style="color: #FF5252; font-weight: 700; font-size: 1.3rem;">
                        NEGOTIATION FAILED — Escalated to Trial
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🔄 Start New Negotiation"):
            st.session_state.neg_state = None
            st.session_state.neg_case_id = None
            st.rerun()

    # Charts
    if state.get("history"):
        st.markdown("<br>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            section_header("📈 Offer Convergence")
            fig = render_negotiation_offers(state["history"])
            st.plotly_chart(fig, use_container_width=True)
        with col_c2:
            section_header("📊 Round Stats")
            metric_card("Rounds Played", str(state["turn"]))
            metric_card("Current Offer", f"${state['current_offer']:,.2f}")
            metric_card("Original Claim", f"${state['claim_amount']:,.2f}")
            if state["claim_amount"] > 0:
                reduction = (1 - state["current_offer"] / state["claim_amount"]) * 100
                metric_card("Negotiated Reduction", f"{reduction:.1f}%")
