# agents/negotiation_graph.py — LangGraph-style State Machine Negotiation
"""
V2 Improvement: Proper state machine with structured nodes,
conditional transitions, judge intervention, and settlement detection.
Uses a functional graph pattern instead of a simple for-loop.
"""
import json
from typing import TypedDict, Annotated
import operator
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class NegotiationState(TypedDict):
    case_id: str
    case_summary: str
    plaintiff_interests: str
    defendant_interests: str
    claim_amount: float
    turn: int
    max_turns: int
    history: Annotated[list[dict], operator.add]
    current_offer: float
    plaintiff_accepted: bool
    defendant_accepted: bool
    settlement_text: str
    status: str  # negotiating, settled, failed, escalated
    judge_notes: str  # human judge intervention
    convergence_rate: float  # tracks how fast offers are converging


# ─── Prompts ─────────────────────────────────────────────────────────

PLAINTIFF_PROMPT = PromptTemplate.from_template("""You are a skilled AI attorney representing the PLAINTIFF in a legal dispute.

**Case:** {case_summary}
**Plaintiff's Interests:** {plaintiff_interests}
**Original Claim:** ${claim_amount}
**Current Offer on Table:** ${current_offer}
**Round:** {turn} of {max_turns}
**Prior Exchanges:** {history}
{judge_instruction}

**Strategy Guidelines:**
- Round 1-3: Argue strongly from legal principles, demand close to full claim
- Round 4-6: Show willingness to negotiate, make reasonable concessions
- Round 7+: Seek resolution, consider the cost of continued litigation
- If offer is within 15% of your adjusted demand, seriously consider accepting
- Always cite a relevant legal principle or statute in your argument

Return JSON only, no markdown:
{{"message": "<2-3 sentences with legal reasoning>", "counter_offer": <float>, "accept": <true/false>, "legal_basis": "<relevant statute or principle>"}}""")


DEFENDANT_PROMPT = PromptTemplate.from_template("""You are a skilled AI attorney representing the DEFENDANT in a legal dispute.

**Case:** {case_summary}
**Defendant's Position:** {defendant_interests}
**Original Claim Against You:** ${claim_amount}
**Current Offer on Table:** ${current_offer}
**Round:** {turn} of {max_turns}
**Prior Exchanges:** {history}
{judge_instruction}

**Strategy Guidelines:**
- Challenge the basis of the claim with legal arguments
- Acknowledge legitimate grievances while contesting amounts
- Gradually increase offers to show good faith
- If claim has merit, negotiate to minimize exposure
- Always cite a relevant legal defense or precedent

Return JSON only, no markdown:
{{"message": "<2-3 sentences with legal reasoning>", "counter_offer": <float>, "accept": <true/false>, "legal_basis": "<relevant defense or precedent>"}}""")


MEDIATOR_PROMPT = PromptTemplate.from_template("""You are an impartial AI mediator facilitating settlement between plaintiff and defendant.

**Case:** {case_summary}
**Current State:**
- Plaintiff's last offer: ${plaintiff_offer}
- Defendant's last offer: ${defendant_offer}
- Gap: ${gap}
- Round: {turn} of {max_turns}
- Convergence rate: {convergence_rate}% per round

**Your Role:**
- Identify common ground between the parties
- Suggest a specific settlement figure with reasoning
- If gap is narrowing, encourage continued negotiation
- If gap is widening, issue a warning about trial costs
- If round > 80% of max, push strongly for compromise

Return JSON only, no markdown:
{{"message": "<1-2 sentences of mediation guidance>", "suggested_offer": <float>, "assessment": "<converging|stalled|diverging>", "trial_risk_warning": <true/false>}}""")


def _fmt(history: list[dict]) -> str:
    """Format recent history for prompt context."""
    if not history:
        return "No prior exchanges."
    return "\n".join(
        f"[Round {h.get('turn', '?')} - {h['speaker']}]: {h['message']} (Offer: ${h.get('offer_amount', 'N/A')})"
        for h in history[-8:]
    )


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
    return raw.strip()


def _get_judge_instruction(judge_notes: str) -> str:
    if judge_notes:
        return f"\n**⚖️ JUDGE'S DIRECTION (you MUST acknowledge this):** {judge_notes}\n"
    return ""


def plaintiff_node(state: dict, llm) -> dict:
    """Plaintiff argues their case."""
    chain = PLAINTIFF_PROMPT | llm | StrOutputParser()
    try:
        raw = chain.invoke({
            "case_summary": state["case_summary"],
            "plaintiff_interests": state["plaintiff_interests"],
            "claim_amount": state["claim_amount"],
            "current_offer": state["current_offer"],
            "turn": state["turn"],
            "max_turns": state["max_turns"],
            "history": _fmt(state["history"]),
            "judge_instruction": _get_judge_instruction(state.get("judge_notes", "")),
        })
        data = json.loads(_clean_json(raw))
        offer = float(data.get("counter_offer", state["current_offer"]))
        return {
            "history": [{
                "speaker": "Plaintiff Agent",
                "message": data.get("message", ""),
                "offer_amount": offer,
                "legal_basis": data.get("legal_basis", ""),
                "turn": state["turn"],
            }],
            "current_offer": offer,
            "plaintiff_accepted": bool(data.get("accept", False)),
        }
    except Exception:
        return {
            "history": [{
                "speaker": "Plaintiff Agent",
                "message": "I maintain my position and await a reasonable counter-offer.",
                "offer_amount": state["current_offer"],
                "turn": state["turn"],
            }],
            "plaintiff_accepted": False,
        }


def defendant_node(state: dict, llm) -> dict:
    """Defendant responds."""
    chain = DEFENDANT_PROMPT | llm | StrOutputParser()
    try:
        raw = chain.invoke({
            "case_summary": state["case_summary"],
            "defendant_interests": state["defendant_interests"],
            "claim_amount": state["claim_amount"],
            "current_offer": state["current_offer"],
            "turn": state["turn"],
            "max_turns": state["max_turns"],
            "history": _fmt(state["history"]),
            "judge_instruction": _get_judge_instruction(state.get("judge_notes", "")),
        })
        data = json.loads(_clean_json(raw))
        offer = float(data.get("counter_offer", state["current_offer"]))
        return {
            "history": [{
                "speaker": "Defendant Agent",
                "message": data.get("message", ""),
                "offer_amount": offer,
                "legal_basis": data.get("legal_basis", ""),
                "turn": state["turn"],
            }],
            "current_offer": offer,
            "defendant_accepted": bool(data.get("accept", False)),
        }
    except Exception:
        return {
            "history": [{
                "speaker": "Defendant Agent",
                "message": "We need further consideration before making concessions.",
                "offer_amount": state["current_offer"],
                "turn": state["turn"],
            }],
            "defendant_accepted": False,
        }


def mediator_node(state: dict, llm) -> dict:
    """Mediator assesses and guides."""
    # Check for settlement
    if state.get("plaintiff_accepted") and state.get("defendant_accepted"):
        return {
            "status": "settled",
            "settlement_text": f"Settlement reached at ${state['current_offer']:,.2f}",
            "history": [{
                "speaker": "Mediator",
                "message": f"✅ Both parties accepted ${state['current_offer']:,.2f}. Settlement reached!",
                "offer_amount": state["current_offer"],
                "turn": state["turn"],
            }],
        }

    # Check for max turns
    if state["turn"] >= state["max_turns"]:
        return {
            "status": "failed",
            "history": [{
                "speaker": "Mediator",
                "message": "Maximum negotiation rounds reached. Case escalated to trial.",
                "offer_amount": state["current_offer"],
                "turn": state["turn"],
            }],
        }

    # Calculate offers gap
    po = do = state["current_offer"]
    for h in reversed(state.get("history", [])):
        if h["speaker"] == "Plaintiff Agent":
            po = h.get("offer_amount", po)
            break
    for h in reversed(state.get("history", [])):
        if h["speaker"] == "Defendant Agent":
            do = h.get("offer_amount", do)
            break
    gap = abs(po - do)

    # Calculate convergence rate
    prev_gap = state.get("_prev_gap", state["claim_amount"])
    convergence = ((prev_gap - gap) / (prev_gap + 1e-9)) * 100

    # Late-stage push
    if state["turn"] >= state["max_turns"] - 2:
        s = (po + do) / 2
        return {
            "history": [{
                "speaker": "Mediator",
                "message": f"⚠️ Final rounds. I strongly recommend splitting at ${s:,.2f} to avoid costly trial proceedings.",
                "offer_amount": s,
                "turn": state["turn"],
            }],
            "current_offer": s,
            "turn": state["turn"] + 1,
            "convergence_rate": convergence,
        }

    chain = MEDIATOR_PROMPT | llm | StrOutputParser()
    try:
        raw = chain.invoke({
            "case_summary": state["case_summary"],
            "plaintiff_offer": po,
            "defendant_offer": do,
            "gap": gap,
            "turn": state["turn"],
            "max_turns": state["max_turns"],
            "convergence_rate": f"{convergence:.1f}",
        })
        data = json.loads(_clean_json(raw))
        s = float(data.get("suggested_offer", state["current_offer"]))
        return {
            "history": [{
                "speaker": "Mediator",
                "message": data.get("message", ""),
                "offer_amount": s,
                "assessment": data.get("assessment", ""),
                "turn": state["turn"],
            }],
            "current_offer": s,
            "turn": state["turn"] + 1,
            "convergence_rate": convergence,
        }
    except Exception:
        return {
            "history": [{
                "speaker": "Mediator",
                "message": "Let us continue the discussion.",
                "offer_amount": state["current_offer"],
                "turn": state["turn"],
            }],
            "turn": state["turn"] + 1,
        }


def run_negotiation_round(state: dict, llm, judge_notes: str = "") -> dict:
    """Run a single round of negotiation (plaintiff → defendant → mediator)."""
    state["judge_notes"] = judge_notes

    # Add judge intervention to history if provided
    if judge_notes:
        state["history"] = state.get("history", []) + [{
            "speaker": "Judge",
            "message": judge_notes,
            "offer_amount": state["current_offer"],
            "turn": state["turn"],
        }]

    # Store previous gap for convergence tracking
    po = do = state["current_offer"]
    for h in reversed(state.get("history", [])):
        if h["speaker"] == "Plaintiff Agent":
            po = h.get("offer_amount", po)
            break
    for h in reversed(state.get("history", [])):
        if h["speaker"] == "Defendant Agent":
            do = h.get("offer_amount", do)
            break
    state["_prev_gap"] = abs(po - do)

    # Run nodes
    pu = plaintiff_node(state, llm)
    state["history"] = state.get("history", []) + pu.get("history", [])
    state["current_offer"] = pu.get("current_offer", state["current_offer"])
    state["plaintiff_accepted"] = pu.get("plaintiff_accepted", False)

    du = defendant_node(state, llm)
    state["history"] = state.get("history", []) + du.get("history", [])
    state["current_offer"] = du.get("current_offer", state["current_offer"])
    state["defendant_accepted"] = du.get("defendant_accepted", False)

    mu = mediator_node(state, llm)
    state["history"] = state.get("history", []) + mu.get("history", [])
    state["current_offer"] = mu.get("current_offer", state["current_offer"])
    state["turn"] = mu.get("turn", state["turn"])
    state["convergence_rate"] = mu.get("convergence_rate", 0)

    if mu.get("status"):
        state["status"] = mu["status"]
    if mu.get("settlement_text"):
        state["settlement_text"] = mu["settlement_text"]

    return state


def create_initial_state(case_id, case_summary, plaintiff_interests,
                         defendant_interests, claim_amount, max_turns=10) -> dict:
    """Create initial negotiation state."""
    return {
        "case_id": case_id,
        "case_summary": case_summary,
        "plaintiff_interests": plaintiff_interests,
        "defendant_interests": defendant_interests,
        "claim_amount": claim_amount,
        "turn": 1,
        "max_turns": max_turns,
        "history": [],
        "current_offer": claim_amount,
        "plaintiff_accepted": False,
        "defendant_accepted": False,
        "settlement_text": "",
        "status": "negotiating",
        "judge_notes": "",
        "convergence_rate": 0,
    }
