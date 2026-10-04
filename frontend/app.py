"""
StudyPilot AI — Streamlit Frontend (Bright Modern Redesign)
Run with: streamlit run frontend/app.py
"""
import os
from datetime import date, timedelta
from itertools import groupby

import requests
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="StudyPilot AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Palette ────────────────────────────────────────────────────────────────────
INDIGO = "#6366F1"
VIOLET = "#8B5CF6"
PINK = "#EC4899"
CYAN = "#06B6D4"
EMERALD = "#10B981"
AMBER = "#F59E0B"
ROSE = "#F43F5E"
BLUE = "#3B82F6"
PALETTE = [INDIGO, PINK, CYAN, AMBER, EMERALD, VIOLET, ROSE, BLUE]

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --indigo: #6366F1;
    --violet: #8B5CF6;
    --pink: #EC4899;
    --cyan: #06B6D4;
    --emerald: #10B981;
    --amber: #F59E0B;
    --rose: #F43F5E;
    --ink: #1E1B4B;
    --muted: #64748B;
    --line: #E8EAFD;
    --card: #FFFFFF;
    --grad-main: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%);
    --grad-cool: linear-gradient(135deg, #06B6D4 0%, #6366F1 100%);
    --shadow-sm: 0 2px 8px rgba(99, 102, 241, 0.08);
    --shadow-md: 0 8px 24px rgba(99, 102, 241, 0.14);
}

/* ── Base ─────────────────────────────────────────── */
html, body, [class*="css"], .stApp, button, input, textarea, select {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp {
    background:
        radial-gradient(circle at 0% 0%, rgba(99,102,241,0.10) 0%, transparent 40%),
        radial-gradient(circle at 100% 0%, rgba(236,72,153,0.08) 0%, transparent 40%),
        #F7F8FF;
}
[data-testid="stMain"] .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1240px; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
h1, h2, h3 { color: var(--ink); letter-spacing: -0.02em; }

/* ── Page header ──────────────────────────────────── */
.page-header {
    background: var(--grad-main);
    border-radius: 22px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.5rem;
    color: #fff;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-md);
}
.page-header::after {
    content: ""; position: absolute; right: -60px; top: -60px;
    width: 220px; height: 220px; border-radius: 50%;
    background: rgba(255,255,255,0.14);
}
.page-header::before {
    content: ""; position: absolute; right: 90px; bottom: -80px;
    width: 160px; height: 160px; border-radius: 50%;
    background: rgba(255,255,255,0.10);
}
.page-header .title { font-size: 1.75rem; font-weight: 800; margin: 0; color: #fff; position: relative; z-index: 1; }
.page-header .subtitle { font-size: 0.98rem; opacity: 0.92; margin-top: 0.3rem; position: relative; z-index: 1; color: #fff; }

/* ── Metric cards ─────────────────────────────────── */
.metric-card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.1rem 1.2rem;
    margin-bottom: 0.9rem;
    box-shadow: var(--shadow-sm);
    transition: transform .18s ease, box-shadow .18s ease;
    position: relative;
    overflow: hidden;
}
.metric-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.metric-card .bar { position: absolute; left: 0; top: 0; bottom: 0; width: 5px; }
.metric-card .icon {
    width: 40px; height: 40px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; margin-bottom: 0.7rem;
}
.metric-card .label { font-size: 0.78rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
.metric-card .value { font-size: 1.8rem; font-weight: 800; color: var(--ink); line-height: 1.2; }
.metric-card .sub { font-size: 0.78rem; color: var(--muted); margin-top: 0.15rem; }

/* ── Badges ───────────────────────────────────────── */
.badge { border-radius: 999px; padding: 3px 11px; font-size: 0.72rem; font-weight: 700; display: inline-block; }
.badge-high   { background:#FFE4E6; color:#BE123C; }
.badge-medium { background:#FEF3C7; color:#B45309; }
.badge-low    { background:#D1FAE5; color:#047857; }
.badge-learn    { background:#DBEAFE; color:#1D4ED8; }
.badge-practice { background:#E0E7FF; color:#4338CA; }
.badge-revision { background:#FCE7F3; color:#BE185D; }
.badge-quiz     { background:#CCFBF1; color:#0F766E; }
.badge-mock     { background:#FFEDD5; color:#C2410C; }

/* ── Section headers ──────────────────────────────── */
.section-header {
    font-size: 1.12rem; font-weight: 800; color: var(--ink);
    margin: 1.6rem 0 0.8rem; display: flex; align-items: center; gap: 0.6rem;
}
.section-header::before {
    content: ""; width: 6px; height: 1.3rem; border-radius: 6px;
    background: var(--grad-main); display: inline-block;
}

/* ── Panels & cards ───────────────────────────────── */
.panel {
    background: var(--card); border: 1px solid var(--line);
    border-radius: 18px; padding: 1.1rem 1.3rem; box-shadow: var(--shadow-sm);
}
.session-card {
    background: var(--card);
    border: 1px solid var(--line);
    border-left: 5px solid var(--indigo);
    border-radius: 14px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.6rem;
    box-shadow: var(--shadow-sm);
    line-height: 1.7;
    color: var(--ink);
}
.session-card.p-high   { border-left-color: var(--rose); }
.session-card.p-medium { border-left-color: var(--amber); }
.session-card.p-low    { border-left-color: var(--emerald); }
.session-card.completed { opacity: 0.6; background: #F0FDF4; border-left-color: var(--emerald); }
.session-card .meta { font-size: 0.82rem; color: var(--muted); }

.weak-chip {
    display: inline-block; background: #FFF1F2; color: #BE123C;
    border: 1px solid #FECDD3; border-radius: 999px;
    padding: 4px 12px; margin: 0 6px 8px 0; font-size: 0.82rem; font-weight: 600;
}

.ai-box {
    background: linear-gradient(135deg, #EEF2FF 0%, #FDF2F8 100%);
    border: 1px solid #DDD6FE; border-radius: 16px;
    padding: 1rem 1.3rem; font-size: 0.96rem; line-height: 1.7; color: var(--ink);
}

/* ── Score badges ─────────────────────────────────── */
.score-excellent, .score-good, .score-average, .score-poor {
    border-radius: 12px; padding: 4px 14px; font-weight: 800; display: inline-block;
}
.score-excellent { background:#D1FAE5; color:#047857; }
.score-good      { background:#DBEAFE; color:#1D4ED8; }
.score-average   { background:#FEF3C7; color:#B45309; }
.score-poor      { background:#FFE4E6; color:#BE123C; }

.score-hero {
    background: var(--card); border: 1px solid var(--line); border-radius: 20px;
    padding: 1.4rem; text-align: center; box-shadow: var(--shadow-sm);
}
.score-hero .big { font-size: 3.4rem; font-weight: 800; line-height: 1.1; }
.score-hero .cap { color: var(--muted); font-weight: 600; margin-top: .2rem; }

/* ── Sidebar ──────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #4F46E5 0%, #7C3AED 55%, #DB2777 100%);
}
[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] em { color: #fff; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.25); }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background: #fff; border-radius: 12px; border: none; }
[data-testid="stSidebar"] [data-baseweb="select"] * { color: var(--ink) !important; }

.brand { display: flex; align-items: center; gap: 0.7rem; margin-bottom: 0.2rem; }
.brand .logo {
    width: 44px; height: 44px; border-radius: 14px; background: rgba(255,255,255,0.22);
    display: flex; align-items: center; justify-content: center; font-size: 1.5rem;
    backdrop-filter: blur(6px);
}
.brand .name { font-size: 1.3rem; font-weight: 800; color: #fff; line-height: 1.1; }
.brand .tag { font-size: 0.76rem; color: rgba(255,255,255,0.85); }

.countdown {
    background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.3);
    border-radius: 16px; padding: 0.8rem 1rem; margin-top: 0.8rem; text-align: center;
}
.countdown .num { font-size: 2rem; font-weight: 800; color: #fff; line-height: 1; }
.countdown .txt { font-size: 0.78rem; color: rgba(255,255,255,0.9); margin-top: 0.2rem; }

/* Sidebar nav buttons */
[data-testid="stSidebar"] .stButton > button {
    border-radius: 12px; font-weight: 600; text-align: left; justify-content: flex-start;
    padding: 0.55rem 0.9rem; border: none; transition: all .15s ease;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"],
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {
    background: transparent; color: #fff;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(255,255,255,0.18); color: #fff; transform: translateX(3px);
}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
    background: #fff; color: #4F46E5; box-shadow: 0 6px 16px rgba(0,0,0,0.18);
}
[data-testid="stSidebar"] .stButton > button > div { justify-content: flex-start !important; width: 100%; }
[data-testid="stSidebar"] .stButton > button * { text-align: left; }
/* Inactive nav items: white text */
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] * { color: #fff !important; }
/* Active nav item: white pill with dark indigo text (must beat the generic white-text rule) */
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] *,
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[kind="primary"] * { color: #4F46E5 !important; font-weight: 800; }
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
[data-testid="stSidebar"] .stButton > button[kind="primary"] { background: #fff !important; }

/* Force light look on sidebar select + progress bars even if the browser is in dark mode */
[data-testid="stSidebar"] [data-baseweb="select"] > div { background: #fff !important; }
[data-testid="stSidebar"] [data-baseweb="select"] * { color: #1E1B4B !important; fill: #1E1B4B !important; }
[data-testid="stProgress"] [data-baseweb="progress-bar"] > div { background: #E8EAFD !important; border-radius: 999px; }
[data-testid="stProgress"] [data-baseweb="progress-bar"] > div > div { background: linear-gradient(90deg, #6366F1, #EC4899) !important; border-radius: 999px; }

/* ── Main buttons ─────────────────────────────────── */
[data-testid="stMain"] .stButton > button, [data-testid="stMain"] [data-testid="stFormSubmitButton"] > button {
    border-radius: 12px; font-weight: 700; border: 1px solid var(--line);
    padding: 0.55rem 1.1rem; transition: all .18s ease;
}
[data-testid="stMain"] .stButton > button:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); border-color: var(--indigo); color: var(--indigo); }
[data-testid="stMain"] .stButton > button[kind="primary"],
[data-testid="stMain"] button[data-testid="stBaseButton-primary"],
[data-testid="stMain"] [data-testid="stFormSubmitButton"] > button[kind="primary"],
[data-testid="stMain"] button[data-testid="stBaseButton-primaryFormSubmit"] {
    background: var(--grad-main); color: #fff; border: none;
    box-shadow: 0 8px 20px rgba(139,92,246,0.35);
}
[data-testid="stMain"] .stButton > button[kind="primary"]:hover,
[data-testid="stMain"] button[data-testid="stBaseButton-primary"]:hover { color: #fff; filter: brightness(1.08); }
[data-testid="stMain"] .stButton > button[kind="primary"] p,
[data-testid="stMain"] button[data-testid="stBaseButton-primary"] p,
[data-testid="stMain"] button[data-testid="stBaseButton-primaryFormSubmit"] p { color: #fff; }

/* ── Inputs ───────────────────────────────────────── */
[data-testid="stMain"] [data-baseweb="input"] > div, [data-testid="stMain"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-baseweb="textarea"], [data-testid="stMain"] [data-baseweb="base-input"] {
    border-radius: 12px !important; background: #fff !important;
}
[data-testid="stMain"] [data-baseweb="input"] > div, [data-testid="stMain"] [data-baseweb="select"] > div, [data-testid="stMain"] [data-baseweb="textarea"] {
    border: 1.5px solid var(--line) !important;
}
[data-testid="stMain"] [data-baseweb="input"]:focus-within > div, [data-testid="stMain"] [data-baseweb="textarea"]:focus-within {
    border-color: var(--indigo) !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.18) !important;
}

/* ── Forms, expanders, tabs ───────────────────────── */
[data-testid="stForm"] {
    background: #fff; border: 1px solid var(--line); border-radius: 20px;
    padding: 1.5rem; box-shadow: var(--shadow-sm);
}
[data-testid="stExpander"] {
    background: #fff; border: 1px solid var(--line) !important; border-radius: 16px;
    box-shadow: var(--shadow-sm); margin-bottom: 0.7rem; overflow: hidden;
}
[data-testid="stExpander"] summary { font-weight: 700; color: var(--ink); }
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    background: #fff; border-radius: 12px; padding: 0.5rem 1.1rem;
    border: 1px solid var(--line); font-weight: 700;
}
.stTabs [aria-selected="true"] { background: var(--grad-main) !important; color: #fff !important; border: none; }
.stTabs [aria-selected="true"] p { color: #fff !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* ── Progress bar ─────────────────────────────────── */
.stProgress > div > div > div > div { background: var(--grad-main); border-radius: 999px; }
.stProgress > div > div > div { background: #E8EAFD; border-radius: 999px; }

/* ── Alerts ───────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 14px; border: none; }

/* ── Native metric ────────────────────────────────── */
[data-testid="stMetric"] {
    background: #fff; border: 1px solid var(--line); border-radius: 16px;
    padding: 0.8rem 1rem; box-shadow: var(--shadow-sm);
}

/* ── Quiz options ─────────────────────────────────── */
div[role="radiogroup"] { gap: 0.5rem; }
div[role="radiogroup"] > label {
    background: #fff; border: 1.5px solid var(--line); border-radius: 12px;
    padding: 0.65rem 1rem; transition: all .15s ease; width: 100%;
}
div[role="radiogroup"] > label:hover { border-color: var(--indigo); background: #F5F6FF; transform: translateX(3px); }
div[role="radiogroup"] > label:has(input:checked) { border-color: var(--indigo); background: #EEF2FF; }

.quiz-q {
    background: var(--card); border: 1px solid var(--line); border-radius: 16px;
    padding: 1rem 1.2rem; margin: 0.4rem 0 0.6rem; font-weight: 700; color: var(--ink);
    box-shadow: var(--shadow-sm);
}
.quiz-q .qn {
    background: var(--grad-main); color: #fff; border-radius: 8px;
    padding: 2px 9px; margin-right: 8px; font-size: 0.8rem;
}

/* ── Chat ─────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: #fff; border: 1px solid var(--line); border-radius: 18px;
    box-shadow: var(--shadow-sm);
}
[data-testid="stChatInput"] { border-radius: 16px; }

/* ── Dark-mode safety: keep text readable on our light surfaces ── */
[data-testid="stAlert"], [data-testid="stAlert"] * { color: #1E1B4B !important; }
[data-testid="stAlert"] { font-weight: 500; }
[data-testid="stMain"] [data-testid="stWidgetLabel"] *,
[data-testid="stMain"] label { color: #1E1B4B !important; font-weight: 600; }
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] li { color: #1E1B4B; }
[data-testid="stMain"] [data-testid="stMarkdownContainer"] em { color: #64748B; }
[data-testid="stToolbar"] * { color: #1E1B4B !important; }
[data-testid="stMain"] [data-baseweb="select"] * { color: #1E1B4B !important; }
[data-testid="stMain"] input, [data-testid="stMain"] textarea { color: #1E1B4B !important; }
[data-testid="stSidebar"] [data-baseweb="select"] div { background-color: #fff !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div { border: 2px solid rgba(255,255,255,0.6) !important; }

/* ── Tabs (My Notes) ── */
.stTabs [data-baseweb="tab-list"] { gap: 10px; padding: 6px 0 14px; border-bottom: none; }
.stTabs [data-baseweb="tab"] {
    height: auto; min-height: 44px; padding: 0.55rem 1.3rem; border-radius: 999px;
    background: #fff; border: 1.5px solid var(--line); box-shadow: var(--shadow-sm);
}
.stTabs [data-baseweb="tab"] p { color: #1E1B4B; font-weight: 700; margin: 0; font-size: 0.95rem; }
.stTabs [data-baseweb="tab"]:hover { border-color: var(--indigo); }
.stTabs [aria-selected="true"] { background: var(--grad-main) !important; border: none !important; box-shadow: 0 8px 20px rgba(139,92,246,0.35); }
.stTabs [aria-selected="true"] p { color: #fff !important; }

/* ── Tabs v2 (reliable selectors) ── */
[data-baseweb="tabs"] [role="tablist"] { gap: 12px !important; padding: 6px 0 16px !important; background: transparent !important; border: none !important; }
[data-baseweb="tabs"] [data-baseweb="tab-highlight"],
[data-baseweb="tabs"] [data-baseweb="tab-border"] { display: none !important; height: 0 !important; background: transparent !important; }
[data-baseweb="tabs"] button[role="tab"] {
    height: auto !important; min-height: 46px !important; padding: 0.6rem 1.5rem !important;
    border-radius: 999px !important; background: #FFFFFF !important;
    border: 1.5px solid #E8EAFD !important; box-shadow: 0 2px 8px rgba(99,102,241,0.08) !important;
    margin: 0 !important; transition: all .18s ease;
}
[data-baseweb="tabs"] button[role="tab"] * { color: #1E1B4B !important; font-weight: 700 !important; }
[data-baseweb="tabs"] button[role="tab"]:hover { border-color: #6366F1 !important; transform: translateY(-1px); }
[data-baseweb="tabs"] button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%) !important;
    border: none !important; box-shadow: 0 8px 20px rgba(139,92,246,0.35) !important;
}
[data-baseweb="tabs"] button[role="tab"][aria-selected="true"] * { color: #FFFFFF !important; }

/* Main-area dropdowns: white box, dark text (fixes dark select in dark mode) */
[data-testid="stMain"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-baseweb="select"] > div > div { background-color: #FFFFFF !important; }
[data-testid="stMain"] [data-baseweb="select"] > div { border: 1.5px solid #E8EAFD !important; border-radius: 12px !important; }
[data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] li { background: #FFFFFF !important; color: #1E1B4B !important; }
[data-baseweb="popover"] li * { color: #1E1B4B !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] { background: #EEF2FF !important; }

/* ── File uploader ── */
[data-testid="stFileUploaderDropzone"] {
    background: #fff; border: 2px dashed #C7D2FE; border-radius: 18px; padding: 1.4rem;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--indigo); background: #F5F6FF; }
[data-testid="stFileUploaderDropzone"] *, [data-testid="stFileUploader"] small { color: #475569 !important; }
[data-testid="stFileUploaderDropzone"] button {
    background: var(--grad-main) !important; border: none !important; border-radius: 10px !important;
}
[data-testid="stFileUploaderDropzone"] button, [data-testid="stFileUploaderDropzone"] button * { color: #fff !important; font-weight: 700; }

/* ═══ Force LIGHT inputs on every layer (beats Streamlit dark theme) ═══ */
:root { color-scheme: light; }
[data-testid="stMain"] [data-baseweb="input"],
[data-testid="stMain"] [data-baseweb="base-input"],
[data-testid="stMain"] [data-baseweb="textarea"],
[data-testid="stMain"] [data-baseweb="select"],
[data-testid="stMain"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-baseweb="select"] > div > div,
[data-testid="stMain"] [data-baseweb="input"] > div,
[data-testid="stMain"] [data-testid="stNumberInputContainer"],
[data-testid="stMain"] [data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stMain"] [data-testid="stTextInputRootElement"],
[data-testid="stMain"] [data-testid="stTextArea"] > div > div {
    background: #FFFFFF !important; background-color: #FFFFFF !important;
    border-radius: 12px !important;
}
[data-testid="stMain"] [data-baseweb="input"],
[data-testid="stMain"] [data-baseweb="textarea"],
[data-testid="stMain"] [data-baseweb="select"] > div {
    border: 1.5px solid #D9DCFB !important;
}
[data-testid="stMain"] [data-baseweb="input"] input,
[data-testid="stMain"] [data-baseweb="textarea"] textarea,
[data-testid="stMain"] [data-baseweb="select"] input,
[data-testid="stMain"] [data-baseweb="select"] div[value],
[data-testid="stMain"] [data-baseweb="select"] span,
[data-testid="stMain"] [data-baseweb="select"] [class*="singleValue"] {
    color: #1E1B4B !important; -webkit-text-fill-color: #1E1B4B !important;
    background: transparent !important; caret-color: #6366F1;
}
[data-testid="stMain"] input::placeholder,
[data-testid="stMain"] textarea::placeholder { color: #94A3B8 !important; -webkit-text-fill-color: #94A3B8 !important; opacity: 1; }
[data-testid="stMain"] [data-baseweb="select"] svg,
[data-testid="stMain"] [data-testid="stNumberInput"] svg { fill: #6366F1 !important; color: #6366F1 !important; }
[data-testid="stMain"] [data-testid="stNumberInput"] button {
    background: #EEF2FF !important; color: #6366F1 !important; border: none !important;
}
[data-testid="stMain"] [data-testid="stNumberInput"] button:hover { background: #E0E7FF !important; }
[data-testid="stMain"] [data-baseweb="input"]:focus-within,
[data-testid="stMain"] [data-baseweb="textarea"]:focus-within,
[data-testid="stMain"] [data-baseweb="select"]:focus-within > div {
    border-color: #6366F1 !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.18) !important;
}
/* Open dropdown menus & calendar popups */
[data-baseweb="popover"], [data-baseweb="popover"] > div, [data-baseweb="menu"], [data-baseweb="calendar"] {
    background: #FFFFFF !important; color: #1E1B4B !important;
}
[data-baseweb="calendar"] * { color: #1E1B4B; }
/* Sidebar select: keep white box + dark text */
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div { color: #1E1B4B !important; -webkit-text-fill-color: #1E1B4B !important; }
/* Slider labels/values */
[data-testid="stMain"] [data-testid="stSlider"] * { color: #1E1B4B; }
</style>
""",
    unsafe_allow_html=True,
)

# ── API helpers ────────────────────────────────────────────────────────────────


def api_get(path: str, params: dict = None):
    try:
        r = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=60)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend. Make sure the server is running on port 8000."
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, detail
    except Exception as e:
        return None, f"Unexpected error: {e}"


def api_post(path: str, json_data: dict = None, files=None, data=None):
    try:
        if files or data:
            r = requests.post(f"{BACKEND_URL}{path}", files=files, data=data, timeout=120)
        else:
            r = requests.post(f"{BACKEND_URL}{path}", json=json_data, timeout=120)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend. Make sure the server is running on port 8000."
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, detail
    except Exception as e:
        return None, f"Unexpected error: {e}"


def api_delete(path: str):
    try:
        r = requests.delete(f"{BACKEND_URL}{path}", timeout=30)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)


# ── Session state ──────────────────────────────────────────────────────────────


def init_state():
    defaults = {
        "student_id": None,
        "student_name": None,
        "page": "Dashboard",
        "quiz_questions": None,
        "quiz_subject": "",
        "quiz_topic": "",
        "quiz_difficulty": "Medium",
        "quiz_answers": {},
        "quiz_result": None,
        "chat_history": [],
        "pdf_doc_id": None,
        "pdf_doc_name": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ── Sidebar ────────────────────────────────────────────────────────────────────


def sidebar():
    with st.sidebar:
        st.markdown(
            """<div class="brand">
                <div class="logo">🚀</div>
                <div><div class="name">StudyPilot AI</div>
                <div class="tag">Your AI-powered study copilot</div></div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        students_data, err = api_get("/students")
        if err:
            st.error(f"Backend error: {err}")
            students_data = []

        student_names = ["— Select or create profile —"] + [
            s["name"] for s in (students_data or [])
        ]
        student_map = {s["name"]: s for s in (students_data or [])}

        current_name = st.session_state.get("student_name")
        default_idx = 0
        if current_name and current_name in student_names:
            default_idx = student_names.index(current_name)

        selected = st.selectbox(
            "Student Profile", student_names, index=default_idx, key="sidebar_student"
        )

        if selected != "— Select or create profile —":
            s = student_map[selected]
            st.session_state.student_id = s["id"]
            st.session_state.student_name = s["name"]
        else:
            if st.session_state.get("sidebar_student") == "— Select or create profile —":
                st.session_state.student_id = None
                st.session_state.student_name = None

        if st.session_state.student_id:
            exam = student_map.get(selected, {}).get("exam_date", "")
            if exam:
                days = (date.fromisoformat(exam) - date.today()).days
                if days > 0:
                    st.markdown(
                        f"""<div class="countdown">
                            <div class="num">⏰ {days}</div>
                            <div class="txt">days until your exam</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.warning("Exam date has passed!")

        st.markdown("---")

        pages = [
            ("📊", "Dashboard"),
            ("📅", "Study Planner"),
            ("🗓️", "My Schedule"),
            ("🧠", "AI Quiz"),
            ("💬", "AI Tutor"),
            ("📄", "My Notes"),
            ("📈", "Progress"),
            ("➕", "New Profile"),
        ]

        for icon, name in pages:
            label = f"{icon}  {name}"
            is_active = st.session_state.page == name
            if st.button(
                label,
                use_container_width=True,
                key=f"nav_{name}",
                type="primary" if is_active else "secondary",
            ):
                st.session_state.page = name
                st.rerun()

        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.75rem;text-align:center;opacity:0.85;'>"
            "StudyPilot AI v1.0</div>",
            unsafe_allow_html=True,
        )


# ── Helper widgets ─────────────────────────────────────────────────────────────


def page_header(icon: str, title: str, subtitle: str = ""):
    sub = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""<div class="page-header">
            <div class="title">{icon} {title}</div>{sub}
        </div>""",
        unsafe_allow_html=True,
    )


def section(title: str):
    st.markdown(f"<div class='section-header'>{title}</div>", unsafe_allow_html=True)


def require_student():
    if not st.session_state.student_id:
        st.warning("Please select or create a student profile from the sidebar.")
        if st.button("Create New Profile", type="primary"):
            st.session_state.page = "New Profile"
            st.rerun()
        return False
    return True


def priority_badge(priority: str) -> str:
    return f'<span class="badge badge-{priority.lower()}">{priority}</span>'


def activity_badge(activity: str) -> str:
    cls_map = {
        "Learn": "badge-learn",
        "Practice": "badge-practice",
        "Revision": "badge-revision",
        "Quiz": "badge-quiz",
        "Mock Test": "badge-mock",
    }
    cls = cls_map.get(activity, "badge-learn")
    return f'<span class="badge {cls}">{activity}</span>'


def score_class(score: float) -> str:
    if score >= 80:
        return "score-excellent"
    elif score >= 60:
        return "score-good"
    elif score >= 40:
        return "score-average"
    return "score-poor"


def metric_card(label: str, value: str, sub: str = "", icon: str = "✨", color: str = INDIGO):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    # Single line on purpose: blank/indented lines make Markdown render stray </div> code blocks.
    card = (
        f'<div class="metric-card">'
        f'<div class="bar" style="background:{color};"></div>'
        f'<div class="icon" style="background:{color}22;">{icon}</div>'
        f'<div class="label">{label}</div>'
        f'<div class="value">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )
    st.markdown(card, unsafe_allow_html=True)


def style_fig(fig, height: int = 300, legend: bool = False):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=24, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#334155", size=12),
        showlegend=legend,
        legend=dict(orientation="h", y=1.12, x=0),
        hoverlabel=dict(font_family="Plus Jakarta Sans, sans-serif"),
    )
    fig.update_yaxes(gridcolor="#E8EAFD", zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig


# ── Pages ──────────────────────────────────────────────────────────────────────


def page_new_profile():
    page_header("➕", "Create Student Profile", "Set up your personalised study profile to get started.")

    with st.form("new_profile_form", clear_on_submit=False):
        section("About You")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *", placeholder="e.g. Alex Johnson")
            email = st.text_input("Email (optional)", placeholder="alex@example.com")
            knowledge_level = st.selectbox(
                "Knowledge Level *",
                ["Beginner", "Intermediate", "Advanced"],
            )
        with col2:
            exam_date = st.date_input(
                "Exam Date *",
                min_value=date.today() + timedelta(days=1),
                value=date.today() + timedelta(days=30),
            )
            daily_hours = st.number_input(
                "Daily Study Hours *", min_value=0.5, max_value=16.0, value=3.0, step=0.5
            )

        section("Subjects")
        num_subjects = st.number_input("Number of Subjects", min_value=1, max_value=8, value=2, step=1)

        subject_inputs = []
        for i in range(int(num_subjects)):
            st.markdown(f"**📘 Subject {i + 1}**")
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                sname = st.text_input("Subject Name", key=f"sname_{i}", placeholder="e.g. Mathematics")
            with sc2:
                stopics = st.text_area(
                    "Topics (comma-separated)", key=f"stopics_{i}",
                    placeholder="e.g. Calculus, Algebra, Trigonometry",
                    height=80,
                )
            with sc3:
                sweak = st.text_area(
                    "Weak Topics (comma-separated)", key=f"sweak_{i}",
                    placeholder="e.g. Integration, Matrices",
                    height=80,
                )
            if sname.strip():
                subject_inputs.append(
                    {
                        "name": sname.strip(),
                        "topics": [t.strip() for t in stopics.split(",") if t.strip()],
                        "weak_topics": [t.strip() for t in sweak.split(",") if t.strip()],
                    }
                )

        submitted = st.form_submit_button("✅ Create Profile", type="primary", use_container_width=True)

        if submitted:
            errors = []
            if not name.strip():
                errors.append("Full name is required.")
            if not subject_inputs:
                errors.append("At least one subject with a name is required.")
            if exam_date <= date.today():
                errors.append("Exam date must be in the future.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                payload = {
                    "name": name.strip(),
                    "email": email.strip() or None,
                    "knowledge_level": knowledge_level,
                    "daily_study_hours": daily_hours,
                    "exam_date": exam_date.isoformat(),
                    "subjects": subject_inputs,
                }
                with st.spinner("Creating your profile..."):
                    result, err = api_post("/students", payload)

                if err:
                    st.error(f"Could not create profile: {err}")
                else:
                    st.session_state.student_id = result["id"]
                    st.session_state.student_name = result["name"]
                    st.success(f"Profile created for **{result['name']}**! 🎉")
                    st.info("Next step: Go to **Study Planner** to generate your AI study plan.")
                    st.session_state.page = "Study Planner"
                    st.rerun()


def page_dashboard():
    name = st.session_state.get("student_name")
    page_header(
        "📊",
        f"Welcome back, {name}!" if name else "Dashboard",
        "Here's how your preparation is going today.",
    )

    if not require_student():
        return

    sid = st.session_state.student_id

    with st.spinner("Loading dashboard..."):
        data, err = api_get(f"/dashboard/{sid}")

    if err:
        st.error(f"Could not load dashboard: {err}")
        return

    if not data:
        return

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        metric_card("Days to Exam", str(data["days_remaining"]), "days left", "⏳", ROSE)
    with col2:
        metric_card("Planned Hours", f"{data['total_planned_hours']}h", "", "🗂️", INDIGO)
    with col3:
        metric_card("Completed Hours", f"{data['completed_hours']}h", "", "🔥", AMBER)
    with col4:
        metric_card(
            "Sessions",
            f"{data['completed_sessions']}/{data['total_sessions']}",
            "completed",
            "✅",
            EMERALD,
        )
    with col5:
        metric_card("Progress", f"{data['progress_percentage']}%", "", "🎯", PINK)

    section("Overall Progress")
    st.progress(min(data["progress_percentage"] / 100, 1.0))

    if not data["total_sessions"]:
        st.info("📅 No study sessions yet. Go to **Study Planner** to generate your AI plan!")

    if data["subjects"]:
        subjects = data["subjects"]
        col_left, col_right = st.columns(2)

        with col_left:
            section("Subject-wise Study Hours")
            fig_subj = go.Figure()
            fig_subj.add_trace(
                go.Bar(
                    name="Planned",
                    x=[s["subject_name"] for s in subjects],
                    y=[s["planned_hours"] for s in subjects],
                    marker=dict(color="#C7D2FE", cornerradius=8),
                )
            )
            fig_subj.add_trace(
                go.Bar(
                    name="Completed",
                    x=[s["subject_name"] for s in subjects],
                    y=[s["completed_hours"] for s in subjects],
                    marker=dict(color=INDIGO, cornerradius=8),
                )
            )
            fig_subj.update_layout(barmode="group", bargap=0.35)
            style_fig(fig_subj, 300, legend=True)
            st.plotly_chart(fig_subj, use_container_width=True, theme=None)

        with col_right:
            section("Quiz Performance by Subject")
            quiz_subjects = [s for s in subjects if s["quiz_avg_score"] is not None]
            if quiz_subjects:
                fig_quiz = go.Figure(
                    go.Bar(
                        x=[s["subject_name"] for s in quiz_subjects],
                        y=[s["quiz_avg_score"] for s in quiz_subjects],
                        marker=dict(
                            color=[
                                EMERALD if s["quiz_avg_score"] >= 80
                                else BLUE if s["quiz_avg_score"] >= 60
                                else AMBER if s["quiz_avg_score"] >= 40
                                else ROSE
                                for s in quiz_subjects
                            ],
                            cornerradius=8,
                        ),
                        text=[f"{s['quiz_avg_score']}%" for s in quiz_subjects],
                        textposition="outside",
                    )
                )
                fig_quiz.update_layout(bargap=0.4)
                fig_quiz.update_yaxes(range=[0, 115])
                style_fig(fig_quiz, 300)
                st.plotly_chart(fig_quiz, use_container_width=True, theme=None)
            else:
                st.info("Complete some quizzes to see performance here.")

        section("Subject Progress")
        for i, subj in enumerate(subjects):
            total = subj["total_sessions"]
            done = subj["completed_sessions"]
            pct = round((done / total) * 100) if total > 0 else 0
            color = PALETTE[i % len(PALETTE)]
            score_str = f"{subj['quiz_avg_score']}%" if subj["quiz_avg_score"] is not None else "—"
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(
                        f"<span style='color:{color};font-size:1.1rem;'>●</span> **{subj['subject_name']}**",
                        unsafe_allow_html=True,
                    )
                    st.progress(pct / 100)
                with c2:
                    st.markdown(f"**{done}/{total}** sessions")
                with c3:
                    st.markdown(f"Quiz avg: **{score_str}**")

    col_w, col_u = st.columns([1, 2])

    with col_w:
        section("Weak Topics")
        if data["weak_topics"]:
            chips = "".join(f"<span class='weak-chip'>⚠️ {t}</span>" for t in data["weak_topics"])
            st.markdown(chips, unsafe_allow_html=True)
        else:
            st.markdown("*No weak topics identified yet.*")

    with col_u:
        section("Upcoming Sessions")
        if data["upcoming_sessions"]:
            for s in data["upcoming_sessions"][:5]:
                prio_cls = f"p-{s['priority'].lower()}"
                st.markdown(
                    f"""<div class='session-card {prio_cls}'>
                        <strong>{s['subject_name'] or 'General'}</strong> — {s['topic']}<br>
                        <span class='meta'>📆 {s['date']} · ⏱ {s['duration_hours']}h</span>
                        &nbsp; {activity_badge(s['activity'])} &nbsp; {priority_badge(s['priority'])}
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No upcoming sessions. Generate a study plan first.")


def page_study_planner():
    page_header(
        "📅", "Study Planner",
        "Generate a personalised, AI-powered day-by-day plan based on your profile and exam date.",
    )

    if not require_student():
        return

    sid = st.session_state.student_id

    student_data, err = api_get(f"/students/{sid}")
    if err:
        st.error(f"Could not load profile: {err}")
        return

    days = (date.fromisoformat(student_data["exam_date"]) - date.today()).days
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Student", student_data["name"], "", "🎓", INDIGO)
    with col2:
        metric_card("Exam In", f"{days} days", "", "⏳", ROSE)
    with col3:
        metric_card("Daily Hours", f"{student_data['daily_study_hours']}h", "", "🕒", CYAN)

    existing, _ = api_get(f"/study-plan/{sid}")
    has_plan = existing and len(existing) > 0

    if has_plan:
        st.warning(
            f"You already have **{len(existing)}** study sessions planned. "
            "Regenerating will delete incomplete sessions and create a new plan."
        )

    col_btn1, _ = st.columns([1, 2])
    with col_btn1:
        generate_btn = st.button(
            "🤖 Generate AI Study Plan" if not has_plan else "🔄 Regenerate Plan",
            type="primary",
            use_container_width=True,
        )

    if generate_btn:
        with st.spinner("🧠 AI is building your personalised study plan... (this may take 30-60 seconds)"):
            result, err = api_post("/study-plan/generate", {"student_id": sid})

        if err:
            st.error(f"Could not generate plan: {err}")
        else:
            st.success(f"✅ Study plan generated with **{result['total_sessions']}** sessions!")
            st.session_state.page = "My Schedule"
            st.rerun()

    if has_plan:
        section("Current Plan Preview")

        sessions_df = pd.DataFrame(existing)
        if not sessions_df.empty:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                metric_card("Total Sessions", str(len(sessions_df)), "", "📚", INDIGO)
            with c2:
                metric_card("Total Hours", f"{sessions_df['duration_hours'].sum():.1f}h", "", "⏱️", CYAN)
            with c3:
                metric_card("Completed", str(int(sessions_df["is_completed"].sum())), "", "✅", EMERALD)
            with c4:
                metric_card("High Priority", str(int((sessions_df["priority"] == "High").sum())), "", "🔥", ROSE)

            act_counts = sessions_df["activity"].value_counts()
            fig_pie = go.Figure(
                go.Pie(
                    labels=act_counts.index.tolist(),
                    values=act_counts.values.tolist(),
                    hole=0.55,
                    marker=dict(colors=PALETTE, line=dict(color="#fff", width=3)),
                    textinfo="label+percent",
                )
            )
            style_fig(fig_pie, 320, legend=True)
            st.plotly_chart(fig_pie, use_container_width=True, theme=None)


def page_my_schedule():
    page_header("🗓️", "My Schedule", "Your day-by-day study sessions, all in one place.")

    if not require_student():
        return

    sid = st.session_state.student_id

    sessions, err = api_get(f"/study-plan/{sid}")
    if err:
        st.error(f"Could not load schedule: {err}")
        return

    if not sessions:
        st.info("No study sessions found. Go to **Study Planner** to generate your AI plan.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.selectbox("Status", ["All", "Upcoming", "Completed"], key="sch_status")
    with col2:
        all_subjects = sorted({s["subject_name"] for s in sessions if s["subject_name"]})
        filter_subject = st.selectbox("Subject", ["All"] + all_subjects, key="sch_subject")
    with col3:
        filter_priority = st.selectbox("Priority", ["All", "High", "Medium", "Low"], key="sch_priority")

    today_str = date.today().isoformat()

    filtered = sessions
    if filter_status == "Upcoming":
        filtered = [s for s in filtered if not s["is_completed"] and s["date"] >= today_str]
    elif filter_status == "Completed":
        filtered = [s for s in filtered if s["is_completed"]]
    if filter_subject != "All":
        filtered = [s for s in filtered if s["subject_name"] == filter_subject]
    if filter_priority != "All":
        filtered = [s for s in filtered if s["priority"] == filter_priority]

    st.markdown(f"Showing **{len(filtered)}** sessions")

    filtered.sort(key=lambda x: x["date"])
    grouped = {k: list(v) for k, v in groupby(filtered, key=lambda x: x["date"])}

    for day, day_sessions in grouped.items():
        is_today = day == today_str
        header_suffix = " 📌 Today" if is_today else ""
        total_hours = sum(s["duration_hours"] for s in day_sessions)

        with st.expander(
            f"{day}{header_suffix} — {len(day_sessions)} sessions · {total_hours:.1f}h",
            expanded=is_today,
        ):
            for s in day_sessions:
                completed_class = "completed" if s["is_completed"] else f"p-{s['priority'].lower()}"
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    st.markdown(
                        f"""<div class='session-card {completed_class}'>
                            <strong>{s['subject_name'] or 'General'}</strong> — {s['topic']}<br>
                            ⏱ {s['duration_hours']}h &nbsp; {activity_badge(s['activity'])} &nbsp; {priority_badge(s['priority'])}<br>
                            <span class='meta'>{s.get('objective', '')}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                with col_btn:
                    if not s["is_completed"]:
                        if st.button("✓ Done", key=f"done_{s['id']}", type="secondary"):
                            result, err = api_post(
                                "/study-plan/complete-session",
                                {"session_id": s["id"]},
                            )
                            if err:
                                st.error(f"Could not mark session: {err}")
                            else:
                                st.success("Session completed!")
                                st.rerun()
                    else:
                        st.markdown("### ✅")


def page_ai_quiz():
    page_header("🧠", "AI Quiz", "Test your knowledge with AI-generated multiple-choice questions.")

    if not require_student():
        return

    sid = st.session_state.student_id

    if st.session_state.quiz_result:
        _show_quiz_result()
        if st.button("← Take Another Quiz", type="primary"):
            st.session_state.quiz_questions = None
            st.session_state.quiz_answers = {}
            st.session_state.quiz_result = None
            st.rerun()
        return

    if st.session_state.quiz_questions:
        _show_quiz_questions()
        return

    student_data, _ = api_get(f"/students/{sid}")
    subjects = []
    if student_data:
        dash, _ = api_get(f"/dashboard/{sid}")
        if dash:
            subjects = [s["subject_name"] for s in dash.get("subjects", [])]

    with st.form("quiz_setup"):
        section("Quiz Setup")
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input(
                "Subject *",
                value=subjects[0] if subjects else "",
                placeholder="e.g. Mathematics",
            )
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        with col2:
            topic = st.text_input("Topic *", placeholder="e.g. Integration by Parts")
            num_q = st.slider("Number of Questions", 3, 20, 5)

        start_btn = st.form_submit_button("🚀 Start Quiz", type="primary", use_container_width=True)

        if start_btn:
            if not subject.strip() or not topic.strip():
                st.error("Subject and topic are required.")
            else:
                with st.spinner("🤖 Generating quiz questions..."):
                    result, err = api_post(
                        "/quiz/generate",
                        {
                            "student_id": sid,
                            "subject": subject.strip(),
                            "topic": topic.strip(),
                            "difficulty": difficulty,
                            "num_questions": num_q,
                        },
                    )
                if err:
                    st.error(f"Could not generate quiz: {err}")
                else:
                    st.session_state.quiz_questions = result["questions"]
                    st.session_state.quiz_subject = result["subject"]
                    st.session_state.quiz_topic = result["topic"]
                    st.session_state.quiz_difficulty = result["difficulty"]
                    st.session_state.quiz_answers = {}
                    st.rerun()

    section("Recent Quiz History")
    history, _ = api_get(f"/quiz/history/{sid}")
    if history:
        for r in history[:8]:
            sc = r["score_percentage"]
            cls = score_class(sc)
            st.markdown(
                f"""<div class='session-card'>
                    <span class='{cls}'>{sc}%</span> &nbsp; <strong>{r['topic']}</strong>
                    <span class='meta'>· {r['difficulty']} · {r['taken_at'][:10]}</span>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.markdown("*No quiz history yet.*")


def _show_quiz_questions():
    questions = st.session_state.quiz_questions

    st.markdown(
        f"<span class='badge badge-practice'>{st.session_state.quiz_subject}</span> "
        f"<span class='badge badge-learn'>{st.session_state.quiz_topic}</span> "
        f"<span class='badge badge-mock'>{st.session_state.quiz_difficulty}</span> "
        f"<span class='badge badge-quiz'>{len(questions)} questions</span>",
        unsafe_allow_html=True,
    )

    for q in questions:
        qn = str(q["question_number"])
        st.markdown(
            f"<div class='quiz-q'><span class='qn'>Q{q['question_number']}</span>{q['question']}</div>",
            unsafe_allow_html=True,
        )
        options = {opt["label"]: opt["text"] for opt in q["options"]}
        chosen = st.radio(
            f"q_{qn}",
            options=list(options.keys()),
            format_func=lambda x, options=options: f"{x}. {options[x]}",
            key=f"quiz_q_{qn}",
            label_visibility="collapsed",
            index=None,
        )
        if chosen:
            st.session_state.quiz_answers[qn] = chosen

    answered = len(st.session_state.quiz_answers)
    total = len(questions)
    st.markdown("---")
    st.progress(answered / total)
    st.markdown(f"*{answered}/{total} answered*")

    col1, col2 = st.columns([1, 4])
    with col1:
        submit_btn = st.button(
            "📩 Submit Quiz",
            type="primary",
            disabled=(answered < total),
            use_container_width=True,
        )
    with col2:
        if answered < total:
            st.warning(f"Please answer all {total} questions before submitting.")

    if submit_btn:
        sid = st.session_state.student_id
        with st.spinner("Scoring your quiz..."):
            result, err = api_post(
                "/quiz/submit",
                {
                    "student_id": sid,
                    "subject": st.session_state.quiz_subject,
                    "topic": st.session_state.quiz_topic,
                    "difficulty": st.session_state.quiz_difficulty,
                    "answers": st.session_state.quiz_answers,
                    "questions": questions,
                },
            )
        if err:
            st.error(f"Could not submit quiz: {err}")
        else:
            st.session_state.quiz_result = result
            st.rerun()


def _show_quiz_result():
    result = st.session_state.quiz_result
    score = result["score_percentage"]
    cls = score_class(score)

    section("Quiz Results")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<div class='score-hero'><div class='big'><span class='{cls}'>{score}%</span></div>"
            f"<div class='cap'>Your Score</div></div>",
            unsafe_allow_html=True,
        )
    with col2:
        metric_card("Correct", str(result["correct_answers"]), "", "✅", EMERALD)
    with col3:
        wrong = result["total_questions"] - result["correct_answers"]
        metric_card("Incorrect", str(wrong), "", "❌", ROSE)

    st.info(result["feedback"])

    if result.get("weak_areas"):
        section("Areas to Review")
        chips = "".join(f"<span class='weak-chip'>📌 {a}</span>" for a in result["weak_areas"])
        st.markdown(chips, unsafe_allow_html=True)

    section("Detailed Review")

    for item in result.get("detailed", []):
        icon = "✅" if item["is_correct"] else "❌"
        q_text = item["question"]
        title = f"{icon} Q{item['question_number']}. {q_text[:80]}..." if len(q_text) > 80 else f"{icon} Q{item['question_number']}. {q_text}"
        with st.expander(title):
            st.markdown(f"**Your answer:** {item['chosen']}")
            st.markdown(f"**Correct answer:** {item['correct_answer']}")
            st.markdown(f"**Explanation:** {item['explanation']}")


def page_ai_tutor():
    page_header("💬", "AI Tutor", "Ask any study question and get a clear, friendly explanation.")

    if not require_student():
        return

    sid = st.session_state.student_id
    student_data, _ = api_get(f"/students/{sid}")
    knowledge_level = student_data["knowledge_level"] if student_data else "Intermediate"

    st.markdown(
        f"Explanations are adapted to your <span class='badge badge-practice'>{knowledge_level}</span> level.",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        explanation_type = st.selectbox(
            "Explanation Type",
            ["Simple Explanation", "Detailed Explanation", "Example", "Step-by-Step"],
            key="tutor_exp_type",
        )
    with col2:
        subject_ctx = st.text_input(
            "Subject context (optional)", placeholder="e.g. Physics — Thermodynamics",
            key="tutor_subject_ctx",
        )

    if st.session_state.chat_history:
        section("Conversation")
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
    else:
        st.info("👋 Ask your first question below to get started!")

    question = st.chat_input("Ask your question here...")

    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})

        with st.spinner("Thinking..."):
            result, err = api_post(
                "/tutor/ask",
                {
                    "student_id": sid,
                    "question": question,
                    "explanation_type": explanation_type,
                    "subject_context": subject_ctx or None,
                },
            )

        if err:
            st.error(f"Could not get answer: {err}")
            st.session_state.chat_history.pop()
        else:
            st.session_state.chat_history.append(
                {"role": "assistant", "content": result["answer"]}
            )
            st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()


def page_my_notes():
    page_header("📄", "My Notes", "Upload your study material, then ask questions or get a summary.")

    if not require_student():
        return

    sid = st.session_state.student_id

    tab1, tab2 = st.tabs(["📤 Upload PDF", "📚 My Documents"])

    with tab1:
        st.markdown("Upload lecture notes, textbooks, or study materials (PDF only, max 10 MB).")

        student_data, _ = api_get(f"/students/{sid}")
        subject_options = []
        if student_data:
            dash, _ = api_get(f"/dashboard/{sid}")
            if dash:
                subject_options = [s["subject_name"] for s in dash.get("subjects", [])]

        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        subject_tag = st.selectbox(
            "Tag to Subject (optional)", ["— None —"] + subject_options, key="notes_subj_tag"
        )

        if uploaded_file and st.button("📤 Upload", type="primary"):
            with st.spinner("Uploading and processing PDF..."):
                result, err = api_post(
                    "/notes/upload",
                    files={"file": (uploaded_file.name, uploaded_file.read(), "application/pdf")},
                    data={
                        "student_id": str(sid),
                        "subject_tag": subject_tag if subject_tag != "— None —" else "",
                    },
                )
            if err:
                st.error(f"Upload failed: {err}")
            else:
                st.success(
                    f"✅ **{result['original_name']}** uploaded! "
                    f"{result['page_count']} pages, {result['file_size_kb']:.0f} KB"
                )
                st.session_state.pdf_doc_id = result["document_id"]
                st.session_state.pdf_doc_name = result["original_name"]
                st.rerun()

    with tab2:
        docs, err = api_get(f"/notes/{sid}")
        if err:
            st.error(f"Could not load documents: {err}")
            return

        if not docs:
            st.info("No documents uploaded yet. Upload a PDF to get started.")
            return

        selected_doc = st.selectbox(
            "Select Document",
            docs,
            format_func=lambda d: f"{d['original_name']} ({d['page_count']} pages)",
            key="notes_doc_select",
        )

        if selected_doc:
            doc_id = selected_doc["id"]
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                metric_card("Pages", str(selected_doc["page_count"]), "", "📑", INDIGO)
            with c2:
                metric_card("Size", f"{selected_doc['file_size_kb']:.0f} KB", "", "💾", CYAN)
            with c3:
                metric_card("Subject", selected_doc.get("subject_tag") or "—", "", "🏷️", PINK)
            with c4:
                metric_card("Uploaded", selected_doc["uploaded_at"][:10], "", "📆", AMBER)

            section("Ask a Question")
            doc_question = st.text_input(
                "Ask a question about this document",
                placeholder="e.g. What is the main theorem on page 3?",
                key="notes_question",
            )
            if doc_question and st.button("🤖 Ask", type="primary", key="notes_ask_btn"):
                with st.spinner("Searching document..."):
                    answer, err = api_post(
                        "/notes/ask",
                        {"student_id": sid, "document_id": doc_id, "question": doc_question},
                    )
                if err:
                    st.error(f"Could not get answer: {err}")
                elif answer:
                    with st.container(border=True):
                        st.markdown(answer["answer"])

            section("Document Summary")
            if st.button("📝 Generate Summary & Key Points", key="notes_summarize"):
                with st.spinner("Summarizing document..."):
                    summary, err = api_post(
                        f"/notes/summarize/{doc_id}?student_id={sid}",
                        {},
                    )
                if err:
                    st.error(f"Could not summarize: {err}")
                elif summary:
                    with st.container(border=True):
                        st.markdown(f"**Summary:** {summary['summary']}")
                        if summary.get("key_points"):
                            st.markdown("**Key Points:**")
                            for pt in summary["key_points"]:
                                st.markdown(f"• {pt}")


def page_progress():
    page_header("📈", "Progress", "Track your study hours, consistency, and quiz scores over time.")

    if not require_student():
        return

    sid = st.session_state.student_id

    with st.spinner("Loading progress data..."):
        data, err = api_get(f"/progress/{sid}")

    if err:
        st.error(f"Could not load progress: {err}")
        return

    col1, col2, col3, col4 = st.columns(4)
    pct = round(
        (data["completed_hours"] / data["total_planned_hours"]) * 100, 1
    ) if data["total_planned_hours"] > 0 else 0
    with col1:
        metric_card("Total Hours", f"{data['total_planned_hours']}h", "planned", "🗂️", INDIGO)
    with col2:
        metric_card("Completed Hours", f"{data['completed_hours']}h", "", "🔥", AMBER)
    with col3:
        metric_card("Sessions Done", str(data["completed_sessions"]), "", "✅", EMERALD)
    with col4:
        metric_card("Progress", f"{pct}%", "", "🎯", PINK)

    col_left, col_right = st.columns(2)

    with col_left:
        section("Daily Study Hours")
        daily = data.get("daily_hours", {})
        if daily:
            fig_daily = go.Figure(
                go.Bar(
                    x=list(daily.keys()),
                    y=list(daily.values()),
                    marker=dict(color=INDIGO, cornerradius=8),
                )
            )
            fig_daily.update_layout(bargap=0.35)
            style_fig(fig_daily, 300)
            st.plotly_chart(fig_daily, use_container_width=True, theme=None)
        else:
            st.info("Complete some sessions to see daily progress.")

    with col_right:
        section("Subject-wise Hours")
        subj_hours = data.get("subject_hours", {})
        if subj_hours:
            fig_subj = go.Figure(
                go.Pie(
                    labels=list(subj_hours.keys()),
                    values=list(subj_hours.values()),
                    hole=0.55,
                    marker=dict(colors=PALETTE, line=dict(color="#fff", width=3)),
                )
            )
            style_fig(fig_subj, 300, legend=True)
            st.plotly_chart(fig_subj, use_container_width=True, theme=None)
        else:
            st.info("Complete some sessions to see subject breakdown.")

    weekly = data.get("weekly_hours", {})
    if weekly:
        section("Weekly Study Hours")
        fig_weekly = go.Figure(
            go.Scatter(
                x=list(weekly.keys()),
                y=list(weekly.values()),
                mode="lines+markers",
                line=dict(color=VIOLET, width=3, shape="spline"),
                marker=dict(size=10, color=PINK, line=dict(color="#fff", width=2)),
                fill="tozeroy",
                fillcolor="rgba(139,92,246,0.15)",
            )
        )
        style_fig(fig_weekly, 280)
        st.plotly_chart(fig_weekly, use_container_width=True, theme=None)

    quiz_scores = data.get("quiz_scores", [])
    if quiz_scores:
        section("Quiz Score Trend")
        df_quiz = pd.DataFrame(quiz_scores)
        fig_quiz = go.Figure(
            go.Scatter(
                x=df_quiz["taken_at"],
                y=df_quiz["score"],
                mode="lines+markers",
                line=dict(color=CYAN, width=3, shape="spline"),
                marker=dict(size=10, color=EMERALD, line=dict(color="#fff", width=2)),
                text=df_quiz["topic"],
                hovertemplate="%{text}<br>Score: %{y}%<extra></extra>",
            )
        )
        fig_quiz.update_yaxes(range=[0, 110])
        style_fig(fig_quiz, 280)
        st.plotly_chart(fig_quiz, use_container_width=True, theme=None)


# ── Main router ────────────────────────────────────────────────────────────────


def main():
    sidebar()

    page = st.session_state.page

    if page == "Dashboard":
        page_dashboard()
    elif page == "Study Planner":
        page_study_planner()
    elif page == "My Schedule":
        page_my_schedule()
    elif page == "AI Quiz":
        page_ai_quiz()
    elif page == "AI Tutor":
        page_ai_tutor()
    elif page == "My Notes":
        page_my_notes()
    elif page == "Progress":
        page_progress()
    elif page == "New Profile":
        page_new_profile()
    else:
        page_dashboard()


if __name__ == "__main__":
    main()