# agents/dna_agent.py — Chain-of-Thought Case DNA Fingerprinting
"""
V2 Improvement: Instead of a single prompt → 6 numbers,
this agent uses a two-step Chain-of-Thought approach:
  Step 1: LLM analyzes the case and reasons about each dimension
  Step 2: LLM extracts numerical scores from its own reasoning

The reasoning is stored and displayed to users, showing WHY the AI scored each dimension.
"""
import json
import math
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ─── Step 1: Chain-of-Thought Analysis ──────────────────────────────
COT_ANALYSIS_PROMPT = PromptTemplate.from_template("""You are an expert legal analyst performing Case DNA Fingerprinting.

Analyze this case across 6 dimensions. For each dimension, cite specific evidence from the case text to justify your assessment. Think step by step.

**Dimensions to analyze:**
1. **Category Classification**: What type of dispute is this? (landlord_tenant, employment, contract, personal_injury, family, small_claims, consumer, property, other)
2. **Jurisdiction Clarity**: How clearly is the correct court/forum identified? Consider if the parties, subject matter, and location align with a specific court.
3. **Claim Magnitude**: Assess the financial scale relative to court thresholds.
4. **Evidence Strength**: How strong is the documentary and testimonial evidence described? Look for specifics like dates, documents, witnesses, records.
5. **Emotional Intensity**: How emotionally charged is the language and situation? Consider personal harm, family impact, violation of trust.
6. **Legal Novelty**: Is this a routine case with clear precedent, or does it raise novel legal questions?

Case:
{case_text}

Write your analysis as a structured reasoning paragraph for each dimension. Be specific and cite the case text.""")


# ─── Step 2: Extract Scores from Reasoning ──────────────────────────
SCORE_EXTRACTION_PROMPT = PromptTemplate.from_template("""Based on this legal analysis, extract numerical scores for each dimension.

Analysis:
{analysis}

Return ONLY a JSON object (no markdown, no extra text):
{{
  "category": "<one of: landlord_tenant, employment, contract, personal_injury, family, small_claims, consumer, property, other>",
  "jurisdiction_score": <float 0.0-1.0, where 1.0 = perfectly clear jurisdiction>,
  "claim_bucket": <int 1-4, where 1=<$1k, 2=$1k-10k, 3=$10k-100k, 4=>$100k>,
  "evidence_strength": <float 0.0-1.0>,
  "emotional_intensity": <float 0.0-1.0>,
  "novelty": <float 0.0-1.0, where 0=routine, 1=highly novel>
}}""")


CATEGORY_MAP = {
    "landlord_tenant": 0.1, "employment": 0.2, "contract": 0.3,
    "personal_injury": 0.4, "family": 0.5, "small_claims": 0.6,
    "consumer": 0.7, "property": 0.8, "other": 0.9,
}


def _clean_json(raw: str) -> str:
    """Strip markdown fences and whitespace from LLM JSON output."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
    return raw.strip()


def build_dna_vector(case_text: str, llm) -> dict:
    """
    Two-step Chain-of-Thought DNA fingerprinting.
    Returns: {vector: list[float], reasoning: str, category: str, raw_scores: dict}
    """
    # Step 1: Chain-of-Thought Analysis
    chain_cot = COT_ANALYSIS_PROMPT | llm | StrOutputParser()
    try:
        reasoning = chain_cot.invoke({"case_text": case_text})
    except Exception:
        reasoning = "Analysis could not be completed due to an error."

    # Step 2: Extract numerical scores from the reasoning
    chain_score = SCORE_EXTRACTION_PROMPT | llm | StrOutputParser()
    try:
        raw = chain_score.invoke({"analysis": reasoning})
        data = json.loads(_clean_json(raw))

        category = data.get("category", "other")
        vector = [
            CATEGORY_MAP.get(category, 0.9),
            float(data.get("jurisdiction_score", 0.5)),
            float(data.get("claim_bucket", 2)) / 4.0,
            float(data.get("evidence_strength", 0.5)),
            float(data.get("emotional_intensity", 0.5)),
            float(data.get("novelty", 0.5)),
        ]

        return {
            "vector": vector,
            "reasoning": reasoning,
            "category": category,
            "raw_scores": data,
        }

    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {
            "vector": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
            "reasoning": reasoning,
            "category": "other",
            "raw_scores": {},
        }


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x ** 2 for x in a))
    mag_b = math.sqrt(sum(x ** 2 for x in b))
    return dot / (mag_a * mag_b + 1e-9)


def find_case_twin(vector: list[float], historical_cases: list[dict]) -> tuple[dict | None, float]:
    """Find the most similar historical case using cosine similarity."""
    best_match, best_score = None, -1.0
    for case in historical_cases:
        try:
            hv = json.loads(case["dna_vector"]) if isinstance(case["dna_vector"], str) else case["dna_vector"]
            score = cosine_similarity(vector, hv)
            if score > best_score:
                best_score, best_match = score, case
        except (json.JSONDecodeError, TypeError):
            continue
    return best_match, best_score
