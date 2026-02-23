# config.py — JusticeFlow V2 configuration
import os

# ─── Paths ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "justiceflow.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "db", "schema.sql")

# ─── Groq LLM ────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

# ─── Design Tokens (Dark Premium Theme) ──────────────────────────────
COLORS = {
    "bg_primary":    "#0F1117",     # Deep dark
    "bg_secondary":  "#1A1D29",     # Card background
    "bg_surface":    "#242736",     # Elevated surface
    "accent_blue":   "#6C63FF",     # Primary accent (indigo)
    "accent_cyan":   "#00D9FF",     # Secondary accent (cyan)
    "accent_green":  "#00E676",     # Success
    "accent_amber":  "#FFB740",     # Warning
    "accent_red":    "#FF5252",     # Danger
    "text_primary":  "#E8EAED",     # Primary text
    "text_secondary":"#9AA0A6",     # Muted text
    "border":        "#2D3143",     # Subtle borders
    "glow_blue":     "rgba(108,99,255,0.3)",
    "glow_cyan":     "rgba(0,217,255,0.2)",
}

# ─── Case Categories ─────────────────────────────────────────────────
CASE_CATEGORIES = [
    "landlord_tenant",
    "employment",
    "contract",
    "personal_injury",
    "family",
    "small_claims",
    "consumer",
    "property",
    "other",
]

CATEGORY_LABELS = {
    "landlord_tenant": "🏠 Landlord-Tenant",
    "employment": "💼 Employment",
    "contract": "📄 Contract",
    "personal_injury": "🏥 Personal Injury",
    "family": "👨‍👩‍👧 Family",
    "small_claims": "💰 Small Claims",
    "consumer": "🛒 Consumer",
    "property": "🏗️ Property",
    "other": "📋 Other",
}

# ─── LLM Factory ─────────────────────────────────────────────────────
def get_llm(temperature: float = 0.2, max_tokens: int = 2048, json_mode: bool = False):
    """Return a ChatGroq instance. Set json_mode=True for structured outputs."""
    from langchain_groq import ChatGroq

    kwargs = dict(
        api_key=GROQ_API_KEY,
        model_name=GROQ_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}

    return ChatGroq(**kwargs)
