# pages/page_01_file_case.py — Case Filing + Chain-of-Thought DNA Visualization
import streamlit as st
import json
from utils.theme import page_header, section_header, cot_reasoning_box, metric_card, badge, confidence_bar
from utils.charts import render_dna_radar
from config import CASE_CATEGORIES, CATEGORY_LABELS, get_llm
from db.database import insert_case, update_case, get_historical_cases


def render():
    page_header("📝 File New Case", "Submit a dispute and get instant AI Case DNA fingerprinting")

    with st.form("case_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Case Title", placeholder="e.g., Smith v. Acme Corp - Wrongful Termination")
            category = st.selectbox("Category", CASE_CATEGORIES,
                                    format_func=lambda x: CATEGORY_LABELS.get(x, x))
            plaintiff = st.text_input("Plaintiff Name", placeholder="Full name of the filing party")
        with col2:
            jurisdiction = st.text_input("Jurisdiction", placeholder="e.g., Labour Court Bangalore")
            claim_amount = st.number_input("Claim Amount ($)", min_value=0.0, step=100.0, value=10000.0)
            defendant = st.text_input("Defendant Name", placeholder="Full name of the opposing party")

        description = st.text_area("Case Description",
            placeholder="Describe the dispute in detail. Include relevant dates, evidence, and specific grievances...",
            height=200)

        submitted = st.form_submit_button("⚡ File Case & Generate DNA", use_container_width=True)

    if submitted:
        if not title or not description:
            st.error("Please fill in the case title and description.")
            return

        # Insert case
        with st.spinner("Filing case..."):
            case_id = insert_case(title, description, category, jurisdiction,
                                  claim_amount, plaintiff, defendant)

        st.success(f"✅ Case filed successfully! ID: `{case_id}`")

        # Run Chain-of-Thought DNA
        section_header("🧬 Case DNA Fingerprinting")

        st.markdown("""
        <div class="glass-panel">
            <span style="color: #6C63FF; font-weight: 600;">Two-Step Chain-of-Thought Process</span>
            <div style="color: #9AA0A6; font-size: 0.85rem; margin-top: 0.5rem;">
                Step 1: AI analyzes the case across 6 dimensions, citing evidence →
                Step 2: AI extracts numerical scores from its reasoning
            </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            llm = get_llm()
            from agents.dna_agent import build_dna_vector, find_case_twin

            with st.spinner("🧠 Step 1: Analyzing case dimensions..."):
                result = build_dna_vector(description, llm)

            vector = result["vector"]
            reasoning = result["reasoning"]
            detected_category = result["category"]

            # Store in DB
            update_case(case_id,
                        dna_vector=json.dumps(vector),
                        cot_reasoning=reasoning,
                        category=detected_category)

            # Display reasoning
            st.markdown("#### 🧠 AI Chain-of-Thought Reasoning")
            cot_reasoning_box(reasoning.replace("\n", "<br>"))

            # Display radar chart
            col_radar, col_scores = st.columns([3, 2])

            with col_radar:
                # Find case twin
                historical = get_historical_cases()
                twin, similarity = find_case_twin(vector, historical)

                twin_vector = None
                if twin:
                    twin_vector = json.loads(twin["dna_vector"]) if isinstance(twin["dna_vector"], str) else twin["dna_vector"]

                fig = render_dna_radar(vector, twin_vector)
                st.plotly_chart(fig, use_container_width=True)

            with col_scores:
                labels = ["Category", "Jurisdiction", "Claim Size", "Evidence", "Emotional", "Novelty"]
                for label, val in zip(labels, vector):
                    pct = int(val * 100)
                    color = "#00E676" if pct > 60 else "#FFB740" if pct > 30 else "#FF5252"
                    st.markdown(f"""
                    <div style="margin-bottom: 0.75rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span style="color: #9AA0A6; font-size: 0.85rem;">{label}</span>
                            <span style="color: {color}; font-weight: 600;">{pct}%</span>
                        </div>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: {pct}%; background: {color};"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Case Twin
            if twin:
                section_header("🔗 Case Twin Match")
                col_tw1, col_tw2 = st.columns([3, 1])
                with col_tw1:
                    st.markdown(f"""
                    <div class="glass-panel">
                        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
                            <span style="font-size: 1.5rem;">🔗</span>
                            <span style="font-size: 0.75rem;">{badge(f'{similarity*100:.0f}% Match', 'success' if similarity > 0.8 else 'warning')}</span>
                        </div>
                        <div style="color: #E8EAED; font-size: 0.95rem; line-height: 1.6;">
                            {twin.get('summary', 'N/A')}
                        </div>
                        <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #2D3143;">
                            <span style="color: #9AA0A6; font-size: 0.8rem;">
                                Outcome: <strong style="color: #00E676;">{twin.get('outcome', 'N/A')}</strong>
                                · {twin.get('jurisdiction', '')} · {twin.get('year', '')}
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Show outcome summary if available
                    if twin.get("outcome_summary"):
                        st.markdown(f"""
                        <div class="cot-box">
                            <div class="cot-label">📋 Twin Case Outcome</div>
                            <div>{twin['outcome_summary']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Show relevant statutes
                    statutes = twin.get("key_statutes", "[]")
                    if isinstance(statutes, str):
                        try:
                            statutes = json.loads(statutes)
                        except:
                            statutes = []
                    if statutes:
                        st.markdown("**📜 Relevant Statutes from Twin Case:**")
                        for s in statutes:
                            st.markdown(f"- `{s}`")

                with col_tw2:
                    metric_card("Similarity", f"{similarity*100:.0f}%")

        except Exception as e:
            st.error(f"⚠️ Could not generate DNA: {str(e)}")
            st.info("Make sure your GROQ_API_KEY environment variable is set.")
