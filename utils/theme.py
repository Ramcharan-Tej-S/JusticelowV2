# utils/theme.py — Premium Dark Theme CSS Design System
import streamlit as st


def inject_css():
    """Inject the full CSS design system into the Streamlit app."""
    st.markdown("""
    <style>
    /* ─── Import Google Font ─────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ─── Global Reset ───────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; }

    .stApp {
        background: linear-gradient(135deg, #0F1117 0%, #1A1D29 50%, #0F1117 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #E8EAED;
    }

    /* ─── Hide Streamlit Defaults ────────────────────────────── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; max-width: 1200px; }

    /* ─── Sidebar ────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1D29 0%, #0F1117 100%);
        border-right: 1px solid #2D3143;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #9AA0A6 !important;
        font-size: 0.95rem;
        padding: 0.5rem 0.75rem;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        color: #E8EAED !important;
        background: rgba(108,99,255,0.1);
    }
    [data-testid="stSidebar"] .stRadio [data-checked="true"] + label,
    [data-testid="stSidebar"] .stRadio label[data-checked="true"] {
        color: #6C63FF !important;
        background: rgba(108,99,255,0.15);
    }

    /* ─── Metric Cards ───────────────────────────────────────── */
    .metric-card {
        background: linear-gradient(145deg, #1A1D29, #242736);
        border: 1px solid #2D3143;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #6C63FF, #00D9FF);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    .metric-card:hover {
        border-color: rgba(108,99,255,0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(108,99,255,0.15);
    }
    .metric-card:hover::before { opacity: 1; }
    .metric-card h3 {
        margin: 0 0 0.5rem 0;
        font-size: 0.85rem;
        font-weight: 500;
        color: #9AA0A6;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-card .value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6C63FF, #00D9FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .metric-card .subtitle {
        font-size: 0.8rem;
        color: #9AA0A6;
        margin-top: 0.3rem;
    }

    /* ─── Glass Panel ────────────────────────────────────────── */
    .glass-panel {
        background: rgba(26, 29, 41, 0.8);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(45, 49, 67, 0.6);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    /* ─── Status Badges ──────────────────────────────────────── */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }
    .badge-success {
        background: rgba(0, 230, 118, 0.15);
        color: #00E676;
        border: 1px solid rgba(0, 230, 118, 0.3);
    }
    .badge-warning {
        background: rgba(255, 183, 64, 0.15);
        color: #FFB740;
        border: 1px solid rgba(255, 183, 64, 0.3);
    }
    .badge-danger {
        background: rgba(255, 82, 82, 0.15);
        color: #FF5252;
        border: 1px solid rgba(255, 82, 82, 0.3);
    }
    .badge-info {
        background: rgba(108, 99, 255, 0.15);
        color: #6C63FF;
        border: 1px solid rgba(108, 99, 255, 0.3);
    }

    /* ─── COT Reasoning Box ──────────────────────────────────── */
    .cot-box {
        background: rgba(108, 99, 255, 0.08);
        border: 1px solid rgba(108, 99, 255, 0.25);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        font-size: 0.9rem;
        line-height: 1.6;
        color: #C4C7CC;
    }
    .cot-box .cot-label {
        display: inline-block;
        background: linear-gradient(135deg, #6C63FF, #00D9FF);
        color: #0F1117;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.75rem;
    }

    /* ─── Progress Steps ─────────────────────────────────────── */
    .step-indicator {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }
    .step-active {
        background: rgba(108, 99, 255, 0.1);
        border-left: 3px solid #6C63FF;
    }
    .step-passed {
        background: rgba(0, 230, 118, 0.08);
        border-left: 3px solid #00E676;
    }
    .step-failed {
        background: rgba(255, 82, 82, 0.08);
        border-left: 3px solid #FF5252;
    }

    /* ─── Chat Messages (Negotiation) ────────────────────────── */
    .chat-message {
        padding: 1rem 1.25rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        animation: fadeInUp 0.3s ease;
    }
    .chat-plaintiff {
        background: rgba(108, 99, 255, 0.1);
        border-left: 3px solid #6C63FF;
    }
    .chat-defendant {
        background: rgba(255, 183, 64, 0.1);
        border-left: 3px solid #FFB740;
    }
    .chat-mediator {
        background: rgba(0, 217, 255, 0.1);
        border-left: 3px solid #00D9FF;
    }
    .chat-judge {
        background: rgba(0, 230, 118, 0.1);
        border-left: 3px solid #00E676;
    }
    .chat-speaker {
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.4rem;
    }

    /* ─── Buttons ─────────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #6C63FF, #5A52E0) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(108, 99, 255, 0.4) !important;
    }

    /* ─── Text Inputs ────────────────────────────────────────── */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: #242736 !important;
        border: 1px solid #2D3143 !important;
        border-radius: 10px !important;
        color: #E8EAED !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #6C63FF !important;
        box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.2) !important;
    }

    /* ─── Hero Section ───────────────────────────────────────── */
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6C63FF 0%, #00D9FF 50%, #00E676 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 1.15rem;
        color: #9AA0A6;
        max-width: 600px;
        line-height: 1.6;
    }

    /* ─── Section Headers ────────────────────────────────────── */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #E8EAED;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #2D3143;
    }

    /* ─── Animations ─────────────────────────────────────────── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    .animate-in {
        animation: fadeInUp 0.5s ease forwards;
    }
    .pulse { animation: pulse 2s ease-in-out infinite; }

    /* ─── Confidence Bar ─────────────────────────────────────── */
    .confidence-bar {
        height: 6px;
        border-radius: 3px;
        background: #2D3143;
        overflow: hidden;
        margin-top: 0.5rem;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ─── Scrollbar ──────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0F1117; }
    ::-webkit-scrollbar-thumb { background: #2D3143; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #6C63FF; }

    /* ─── Expander styling ───────────────────────────────────── */
    .streamlit-expanderHeader {
        background: #1A1D29 !important;
        border-radius: 10px !important;
        color: #E8EAED !important;
    }

    /* ─── Tab styling ────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(36, 39, 54, 0.5);
        border-radius: 8px;
        color: #9AA0A6;
        border: 1px solid #2D3143;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(108, 99, 255, 0.15) !important;
        color: #6C63FF !important;
        border-color: rgba(108, 99, 255, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    """Render a page header with gradient title."""
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str):
    """Render a section divider with title."""
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, subtitle: str = ""):
    """Render a single metric card."""
    sub_html = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="metric-card">
        <h3>{label}</h3>
        <div class="value">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def glass_panel(content: str):
    """Render content inside a glassmorphism panel."""
    st.markdown(f'<div class="glass-panel">{content}</div>', unsafe_allow_html=True)


def badge(text: str, variant: str = "info"):
    """Return HTML for a status badge. variant: success|warning|danger|info"""
    return f'<span class="badge badge-{variant}">{text}</span>'


def cot_reasoning_box(reasoning: str):
    """Display a chain-of-thought reasoning box."""
    st.markdown(f"""
    <div class="cot-box">
        <div class="cot-label">🧠 AI Chain-of-Thought</div>
        <div>{reasoning}</div>
    </div>
    """, unsafe_allow_html=True)


def confidence_bar(score: float, color: str = "#6C63FF"):
    """Render a confidence bar (0.0 to 1.0)."""
    pct = max(0, min(100, int(score * 100)))
    st.markdown(f"""
    <div class="confidence-bar">
        <div class="confidence-fill" style="width: {pct}%; background: {color};"></div>
    </div>
    """, unsafe_allow_html=True)
