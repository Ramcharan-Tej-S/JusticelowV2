# agents/auto_filter_agent.py — Sequential Reasoning Chain Filter
"""
V2 Improvement: Each filter step receives context from previous steps,
building a cumulative picture. The LLM steps receive all prior results
for smarter decisions.
"""
import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


JURISDICTION_PROMPT = PromptTemplate.from_template("""You are a legal jurisdiction expert.

A case has been filed with these details:
- Title: {title}
- Category: {category}
- Jurisdiction claimed: {jurisdiction}
- Claim amount: ${claim_amount}
- Description: {description}

Prior screening results:
{prior_results}

Determine if this case is filed in the correct court/forum. Consider:
1. Subject matter jurisdiction
2. Pecuniary limits
3. Territorial jurisdiction
4. Whether a specialized tribunal should hear this

Return JSON only, no markdown:
{{"valid": <true/false>, "correct_forum": "<suggested forum if wrong>", "reasoning": "<explanation>", "confidence": <float 0.0-1.0>}}""")


TRIVIALITY_PROMPT = PromptTemplate.from_template("""You are a senior court clerk screening cases for triviality.

Case details:
- Title: {title}
- Category: {category}
- Description: {description}
- Claim amount: ${claim_amount}

All prior screening results:
{prior_results}

Determine if this case is trivial or frivolous. A case is trivial if:
1. The claim has no legal basis
2. The relief sought is absurd or impossible
3. It's clearly filed to harass the defendant
4. The same matter has been conclusively decided

Be CAREFUL: low claim amounts do NOT make a case trivial.
A genuine dispute over $100 is NOT trivial.

Return JSON only, no markdown:
{{"trivial": <true/false>, "reasoning": "<explanation>", "severity": "<genuine|borderline|frivolous>", "confidence": <float 0.0-1.0>}}""")


FINAL_RECOMMENDATION_PROMPT = PromptTemplate.from_template("""You are a court intake officer making the final routing decision.

Case: {title}
Category: {category}
Claim: ${claim_amount}

Complete screening results:
{all_results}

Based on ALL screening steps, provide your final recommendation.
Return JSON only, no markdown:
{{
  "action": "<proceed|redirect|flag|reject>",
  "reasoning": "<2-3 sentence summary of decision>",
  "priority": "<normal|urgent|low>",
  "routing_notes": "<which court/officer should handle this>"
}}""")


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
    return raw.strip()


def run_filter_pipeline(case: dict, llm) -> dict:
    """
    Sequential 6-step filter pipeline. Each step builds on previous results.
    Returns: {steps: list[dict], final_action, passed, routing}
    """
    steps = []
    passed = True

    # ── Step 1: Minimum Claim Threshold (rule-based) ──
    claim = case.get("claim_amount", 0)
    step1 = {
        "name": "Minimum Claim Threshold",
        "icon": "💰",
        "passed": claim >= 500,
        "detail": f"Claim: ${claim:,.0f}" + (" ✓ Exceeds $500 minimum" if claim >= 500 else " ✗ Below $500 minimum"),
        "type": "rule",
    }
    steps.append(step1)
    if not step1["passed"]:
        passed = False

    # ── Step 2: Government Party Detection (rule-based) ──
    desc_lower = case.get("description", "").lower()
    title_lower = case.get("title", "").lower()
    govt_keywords = ["government", "state of", "union of india", "municipality",
                     "panchayat", "ministry", "collector", "district magistrate"]
    is_govt = any(kw in desc_lower or kw in title_lower for kw in govt_keywords)
    step2 = {
        "name": "Government Party Detection",
        "icon": "🏛️",
        "passed": not is_govt,
        "detail": "Government entity detected → Route to Administrative Tribunal" if is_govt
                  else "No government parties detected",
        "type": "rule",
        "routing": "Administrative Tribunal" if is_govt else None,
    }
    steps.append(step2)
    if is_govt:
        passed = False

    # ── Step 3: Duplicate Case Check (DB query) ──
    from db.database import get_all_cases
    all_cases = get_all_cases()
    duplicate = None
    for existing in all_cases:
        if (existing.get("id") != case.get("id") and
            existing.get("category") == case.get("category") and
            existing.get("status") not in ("resolved", "dismissed") and
            case.get("title", "") and existing.get("title", "") and
            any(word in existing.get("title", "").lower()
                for word in case.get("title", "").lower().split()
                if len(word) > 3)):
            duplicate = existing
            break

    step3 = {
        "name": "Duplicate Case Check",
        "icon": "🔍",
        "passed": duplicate is None,
        "detail": f"Potential duplicate: {duplicate['title']}" if duplicate
                  else "No duplicates found in active cases",
        "type": "db_query",
    }
    steps.append(step3)

    # Build prior results context for LLM steps
    prior_text = "\n".join(
        f"- {s['name']}: {'PASSED' if s['passed'] else 'FAILED'} — {s['detail']}"
        for s in steps
    )

    # ── Step 4: AI Jurisdiction Validation (LLM) ──
    chain4 = JURISDICTION_PROMPT | llm | StrOutputParser()
    try:
        raw4 = chain4.invoke({
            "title": case.get("title", ""),
            "category": case.get("category", ""),
            "jurisdiction": case.get("jurisdiction", "Unknown"),
            "claim_amount": case.get("claim_amount", 0),
            "description": case.get("description", ""),
            "prior_results": prior_text,
        })
        data4 = json.loads(_clean_json(raw4))
        j_valid = data4.get("valid", True)
        step4 = {
            "name": "AI Jurisdiction Validation",
            "icon": "⚖️",
            "passed": j_valid,
            "detail": data4.get("reasoning", ""),
            "type": "llm",
            "confidence": data4.get("confidence", 0.7),
            "routing": data4.get("correct_forum") if not j_valid else None,
        }
    except Exception:
        step4 = {
            "name": "AI Jurisdiction Validation",
            "icon": "⚖️",
            "passed": True,
            "detail": "Could not validate jurisdiction. Proceeding with caution.",
            "type": "llm",
            "confidence": 0.3,
        }
    steps.append(step4)
    if not step4["passed"]:
        passed = False

    # Update prior results
    prior_text += f"\n- {step4['name']}: {'PASSED' if step4['passed'] else 'FAILED'} — {step4['detail']}"

    # ── Step 5: AI Triviality Assessment (LLM) ──
    chain5 = TRIVIALITY_PROMPT | llm | StrOutputParser()
    try:
        raw5 = chain5.invoke({
            "title": case.get("title", ""),
            "category": case.get("category", ""),
            "description": case.get("description", ""),
            "claim_amount": case.get("claim_amount", 0),
            "prior_results": prior_text,
        })
        data5 = json.loads(_clean_json(raw5))
        not_trivial = not data5.get("trivial", False)
        step5 = {
            "name": "AI Triviality Assessment",
            "icon": "🧪",
            "passed": not_trivial,
            "detail": data5.get("reasoning", ""),
            "type": "llm",
            "severity": data5.get("severity", "genuine"),
            "confidence": data5.get("confidence", 0.7),
        }
    except Exception:
        step5 = {
            "name": "AI Triviality Assessment",
            "icon": "🧪",
            "passed": True,
            "detail": "Could not assess triviality. Proceeding.",
            "type": "llm",
            "confidence": 0.3,
        }
    steps.append(step5)
    if not step5["passed"]:
        passed = False

    # Update prior results
    prior_text += f"\n- {step5['name']}: {'PASSED' if step5['passed'] else 'FAILED'} — {step5['detail']}"

    # ── Step 6: AI Final Recommendation (LLM) ──
    chain6 = FINAL_RECOMMENDATION_PROMPT | llm | StrOutputParser()
    try:
        raw6 = chain6.invoke({
            "title": case.get("title", ""),
            "category": case.get("category", "other"),
            "claim_amount": case.get("claim_amount", 0),
            "all_results": prior_text,
        })
        data6 = json.loads(_clean_json(raw6))
        action = data6.get("action", "proceed")
        step6 = {
            "name": "AI Final Recommendation",
            "icon": "📋",
            "passed": action in ("proceed", "flag"),
            "detail": data6.get("reasoning", ""),
            "type": "llm",
            "action": action,
            "priority": data6.get("priority", "normal"),
            "routing": data6.get("routing_notes", ""),
        }
    except Exception:
        step6 = {
            "name": "AI Final Recommendation",
            "icon": "📋",
            "passed": passed,
            "detail": "Automated recommendation based on prior steps.",
            "type": "llm",
            "action": "proceed" if passed else "flag",
        }
    steps.append(step6)

    return {
        "steps": steps,
        "passed": all(s["passed"] for s in steps),
        "final_action": step6.get("action", "proceed"),
        "routing": step6.get("routing", ""),
    }
