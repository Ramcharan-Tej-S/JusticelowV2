# agents/judge_agent.py — Multi-Signal Aggregation Agent
"""
V2 NEW: Synthesizes all AI signals (DLS, DNA, emotion, negotiation, filter)
into a unified judicial brief with recommendation, risk factors, and citations.
"""
import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


JUDGE_BRIEF_PROMPT = PromptTemplate.from_template("""You are an AI judicial assistant preparing a comprehensive case brief for a judge.

**Case Information:**
- Title: {title}
- Category: {category}
- Jurisdiction: {jurisdiction}
- Claim Amount: ${claim_amount}
- Description: {description}

**AI Analysis Signals:**
1. **Dismissal Likelihood Score**: {dls_score}/100 (Confidence: {dls_confidence})
   - Key Risk: {dls_key_risk}
   - Critique: {dls_critique}

2. **Case DNA Match**: {twin_similarity}% match with historical case
   - Twin Case: {twin_summary}
   - Twin Outcome: {twin_outcome}

3. **Emotional Temperature**: {emotional_temp}/100
   - Dominant Emotion: {dominant_emotion}
   - Escalation Risk: {escalation_risk}

4. **Negotiation Status**: {negotiation_status}
   - Rounds Completed: {negotiation_rounds}
   - Current Offer: ${current_offer}

5. **Filter Pipeline**: {filter_result}

Synthesize ALL signals into a judicial brief. Include:
1. **Recommendation**: proceed_to_trial, dismiss, mediate, or settle
2. **Key Risk Factors**: top 3 risks the judge should consider
3. **Relevant Statutes**: cite specific Indian statutes applicable
4. **Estimated Resolution Time**: based on case complexity and category
5. **Confidence Level**: how confident the AI is in this recommendation

Return JSON only, no markdown:
{{
  "recommendation": "<proceed_to_trial|dismiss|mediate|settle>",
  "recommendation_reasoning": "<3-4 sentence reasoning>",
  "risk_factors": [
    {{"factor": "<risk>", "severity": "<high|medium|low>", "mitigation": "<suggested action>"}}
  ],
  "relevant_statutes": [
    {{"statute": "<statute name and section>", "relevance": "<how it applies>"}}
  ],
  "estimated_days_to_resolution": <int>,
  "confidence": <float 0.0-1.0>,
  "priority_level": "<urgent|high|normal|low>",
  "judge_action_items": ["<action 1>", "<action 2>"]
}}""")


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
    return raw.strip()


def generate_judge_brief(case: dict, dls_result: dict, twin_info: dict,
                         emotion_result: dict, negotiation_state: dict,
                         filter_result: dict, llm) -> dict:
    """
    Aggregate all AI signals into a judicial brief.
    Returns: {recommendation, reasoning, risk_factors, statutes, etc.}
    """
    chain = JUDGE_BRIEF_PROMPT | llm | StrOutputParser()
    try:
        raw = chain.invoke({
            "title": case.get("title", ""),
            "category": case.get("category", ""),
            "jurisdiction": case.get("jurisdiction", ""),
            "claim_amount": case.get("claim_amount", 0),
            "description": case.get("description", ""),
            "dls_score": dls_result.get("dls", "N/A"),
            "dls_confidence": f"{dls_result.get('confidence', 0):.0%}",
            "dls_key_risk": dls_result.get("key_risk", "None identified"),
            "dls_critique": dls_result.get("critique", "No critique available"),
            "twin_similarity": f"{twin_info.get('similarity', 0) * 100:.0f}",
            "twin_summary": twin_info.get("summary", "No matching case found"),
            "twin_outcome": twin_info.get("outcome", "N/A"),
            "emotional_temp": emotion_result.get("temperature", "N/A"),
            "dominant_emotion": emotion_result.get("dominant_emotion", "neutral"),
            "escalation_risk": f"{emotion_result.get('escalation_risk', 0):.0%}",
            "negotiation_status": negotiation_state.get("status", "not_started"),
            "negotiation_rounds": negotiation_state.get("turn", 0),
            "current_offer": negotiation_state.get("current_offer", 0),
            "filter_result": filter_result.get("final_action", "not_run"),
        })
        data = json.loads(_clean_json(raw))

        return {
            "recommendation": data.get("recommendation", "proceed_to_trial"),
            "recommendation_reasoning": data.get("recommendation_reasoning", ""),
            "risk_factors": data.get("risk_factors", []),
            "relevant_statutes": data.get("relevant_statutes", []),
            "estimated_days": data.get("estimated_days_to_resolution", 180),
            "confidence": float(data.get("confidence", 0.5)),
            "priority": data.get("priority_level", "normal"),
            "action_items": data.get("judge_action_items", []),
        }
    except Exception as e:
        return {
            "recommendation": "proceed_to_trial",
            "recommendation_reasoning": f"Unable to generate full brief. Error: {str(e)[:100]}",
            "risk_factors": [],
            "relevant_statutes": [],
            "estimated_days": 180,
            "confidence": 0.0,
            "priority": "normal",
            "action_items": ["Review case manually"],
        }
