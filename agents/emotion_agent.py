# agents/emotion_agent.py — Aspect-Level Emotional Intelligence
"""
V2 Improvement: Instead of a single temperature number,
analyzes emotion per party, per issue, with confidence scores
and trigger phrases extracted from the text.
"""
import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


EMOTION_PROMPT = PromptTemplate.from_template("""You are an expert in conflict psychology and legal mediation.

Analyze the emotional state in this legal text. Provide a detailed breakdown:

1. **Overall Temperature** (0-100): 0=calm, 100=explosive
2. **Dominant Emotion**: anger, fear, grief, frustration, desperation, neutral
3. **Party-Level Analysis**: separate emotional reading for each party mentioned
4. **Trigger Phrases**: exact quotes from the text that indicate emotional escalation
5. **De-escalation Risk**: how likely this case is to escalate if not managed
6. **Recommended Action**: specific mediator/judge intervention

Text to analyze:
{text}

Return JSON only, no markdown:
{{
  "temperature": <int 0-100>,
  "dominant_emotion": "<anger|fear|grief|frustration|desperation|neutral>",
  "party_emotions": [
    {{"party": "<name or role>", "emotion": "<emotion>", "intensity": <int 0-100>, "reasoning": "<why>"}},
  ],
  "trigger_phrases": ["<exact quote 1>", "<exact quote 2>"],
  "escalation_risk": <float 0.0-1.0>,
  "recommendation": "<specific mediator action>",
  "confidence": <float 0.0-1.0>
}}""")


EMOTION_COLORS = {
    "anger": "#FF5252",
    "fear": "#FFB740",
    "grief": "#A78BFA",
    "frustration": "#FF7043",
    "desperation": "#FF5252",
    "neutral": "#00E676",
}
EMOTION_ICONS = {
    "anger": "🔥",
    "fear": "😰",
    "grief": "💔",
    "frustration": "😤",
    "desperation": "😫",
    "neutral": "😌",
}


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
    return raw.strip()


def analyze_emotion(text: str, llm) -> dict:
    """
    Aspect-level emotion analysis.
    Returns: {temperature, dominant_emotion, party_emotions, trigger_phrases,
              escalation_risk, recommendation, confidence}
    """
    chain = EMOTION_PROMPT | llm | StrOutputParser()
    try:
        raw = chain.invoke({"text": text})
        data = json.loads(_clean_json(raw))

        temperature = max(0, min(100, int(data.get("temperature", 50))))
        emotion = data.get("dominant_emotion", "neutral").lower()
        if emotion not in EMOTION_COLORS:
            emotion = "neutral"

        return {
            "temperature": temperature,
            "dominant_emotion": emotion,
            "party_emotions": data.get("party_emotions", []),
            "trigger_phrases": data.get("trigger_phrases", []),
            "escalation_risk": float(data.get("escalation_risk", 0.5)),
            "recommendation": data.get("recommendation", "Continue monitoring."),
            "confidence": float(data.get("confidence", 0.7)),
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        # Fallback: try basic sentiment with TextBlob
        try:
            from textblob import TextBlob
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            temp = int((1 - polarity) * 50)  # map to 0-100
            return {
                "temperature": temp,
                "dominant_emotion": "frustration" if polarity < -0.3 else "neutral",
                "party_emotions": [],
                "trigger_phrases": [],
                "escalation_risk": 0.5,
                "recommendation": "Unable to perform detailed analysis. Monitor situation.",
                "confidence": 0.3,
            }
        except ImportError:
            return {
                "temperature": 50,
                "dominant_emotion": "neutral",
                "party_emotions": [],
                "trigger_phrases": [],
                "escalation_risk": 0.5,
                "recommendation": "Analysis unavailable.",
                "confidence": 0.0,
            }
