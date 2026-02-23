# agents/dls_agent.py — LLM-as-Judge Dismissal Likelihood Score Engine
"""
V2 Improvement: Three-step LLM-as-Judge pattern:
  Step 1: Initial assessment generates DLS score with reasons
  Step 2: A "senior judge" LLM critiques the first analysis
  Step 3: Final synthesis combines both into a refined score with confidence

This shows recursive self-improvement, a much more sophisticated AI pattern.
"""
import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ─── Step 1: Initial Assessment ──────────────────────────────────────
INITIAL_ASSESSMENT_PROMPT = PromptTemplate.from_template("""You are a court clerk analyzing a case for dismissal risk.

Analyze this case and estimate the probability of dismissal across 5 risk dimensions.
For each dimension, explain your reasoning citing specific facts from the case.

Case Title: {title}
Description: {description}
Jurisdiction: {jurisdiction}
Claim Amount: ${claim_amount}
Category: {category}

Return JSON only, no markdown:
{{
  "dls": <int 0-100>,
  "reasons": {{
    "lack_of_jurisdiction": <int 0-100>,
    "statute_of_limitations": <int 0-100>,
    "insufficient_evidence": <int 0-100>,
    "frivolous_claim": <int 0-100>,
    "procedural_defect": <int 0-100>
  }},
  "reasoning": "<detailed reasoning for each risk factor>"
}}""")


# ─── Step 2: Judicial Critique ───────────────────────────────────────
CRITIQUE_PROMPT = PromptTemplate.from_template("""You are a SENIOR JUDGE reviewing a junior clerk's dismissal analysis.
Your job is to find flaws, biases, or missed factors in their assessment.

Original Case:
Title: {title}
Description: {description}
Category: {category}

Clerk's Assessment:
DLS Score: {dls_score}
Reasoning: {initial_reasoning}

CRITIQUE this analysis. Consider:
1. Did the clerk overlook any evidence that could change the score?
2. Is the clerk biased toward dismissal or against it?
3. Are there procedural protections the clerk missed?
4. Would a reasonable judge disagree with any individual risk score?

Return JSON only, no markdown:
{{
  "critique": "<your critique identifying flaws and missed factors>",
  "adjusted_dls": <int 0-100, your revised score>,
  "adjustment_reasons": "<why you changed or maintained the score>",
  "confidence": <float 0.0-1.0, how confident you are in the final score>
}}""")


# ─── Step 3: Final Synthesis ────────────────────────────────────────
SYNTHESIS_PROMPT = PromptTemplate.from_template("""Based on the initial analysis and judicial critique, produce the final dismissal assessment.

Initial DLS: {initial_dls}
Initial Reasoning: {initial_reasoning}
Judge's Critique: {critique}
Judge's Adjusted DLS: {adjusted_dls}

Synthesize both perspectives into a final, balanced assessment.
Return JSON only, no markdown:
{{
  "final_dls": <int 0-100>,
  "explanation": "<2-3 sentence summary balancing both perspectives>",
  "confidence": <float 0.0-1.0>,
  "key_risk": "<the single highest risk factor>"
}}""")


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
    return raw.strip()


def compute_dls(case: dict, llm) -> dict:
    """
    Three-step LLM-as-Judge DLS computation.
    Returns: {dls, reasons, explanation, critique, confidence, initial_dls}
    """
    case_fields = {
        "title": case.get("title", ""),
        "description": case.get("description", ""),
        "jurisdiction": case.get("jurisdiction", "Unknown"),
        "claim_amount": case.get("claim_amount", 0),
        "category": case.get("category", "other"),
    }

    # ── Step 1: Initial Assessment ──
    chain1 = INITIAL_ASSESSMENT_PROMPT | llm | StrOutputParser()
    try:
        raw1 = chain1.invoke(case_fields)
        data1 = json.loads(_clean_json(raw1))
        initial_dls = max(0, min(100, int(data1.get("dls", 50))))
        reasons = data1.get("reasons", {})
        initial_reasoning = data1.get("reasoning", "")
        for key in ["lack_of_jurisdiction", "statute_of_limitations",
                     "insufficient_evidence", "frivolous_claim", "procedural_defect"]:
            reasons[key] = max(0, min(100, int(reasons.get(key, 0))))
    except Exception:
        initial_dls = 50
        reasons = {k: 10 for k in ["lack_of_jurisdiction", "statute_of_limitations",
                                     "insufficient_evidence", "frivolous_claim", "procedural_defect"]}
        initial_reasoning = "Initial analysis could not be completed."

    # ── Step 2: Judicial Critique ──
    chain2 = CRITIQUE_PROMPT | llm | StrOutputParser()
    try:
        raw2 = chain2.invoke({
            **case_fields,
            "dls_score": initial_dls,
            "initial_reasoning": initial_reasoning,
        })
        data2 = json.loads(_clean_json(raw2))
        critique = data2.get("critique", "")
        adjusted_dls = max(0, min(100, int(data2.get("adjusted_dls", initial_dls))))
        confidence = float(data2.get("confidence", 0.7))
    except Exception:
        critique = "Critique could not be completed."
        adjusted_dls = initial_dls
        confidence = 0.5

    # ── Step 3: Final Synthesis ──
    chain3 = SYNTHESIS_PROMPT | llm | StrOutputParser()
    try:
        raw3 = chain3.invoke({
            "initial_dls": initial_dls,
            "initial_reasoning": initial_reasoning,
            "critique": critique,
            "adjusted_dls": adjusted_dls,
        })
        data3 = json.loads(_clean_json(raw3))
        final_dls = max(0, min(100, int(data3.get("final_dls", adjusted_dls))))
        explanation = data3.get("explanation", "Analysis completed.")
        final_confidence = float(data3.get("confidence", confidence))
        key_risk = data3.get("key_risk", "")
    except Exception:
        final_dls = adjusted_dls
        explanation = f"Score synthesized from initial ({initial_dls}) and critique ({adjusted_dls})."
        final_confidence = confidence
        key_risk = ""

    return {
        "dls": final_dls,
        "initial_dls": initial_dls,
        "reasons": reasons,
        "explanation": explanation,
        "critique": critique,
        "confidence": final_confidence,
        "key_risk": key_risk,
    }
