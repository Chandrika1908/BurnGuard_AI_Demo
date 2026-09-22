import os
import pandas as pd
import streamlit as st
from model import load_data, prepare_data, score_all

BASE=os.path.dirname(__file__)
DEMO_PATH=os.path.join(BASE,"data","demo_burnin_telemetry.csv")
AUDIT_PATH=os.path.join(BASE,"data","audit_log.jsonl")

@st.cache_data
def get_demo_data():
    return load_data(DEMO_PATH)

def setup(title):
    st.set_page_config(page_title=title,page_icon="🛡️",layout="wide",initial_sidebar_state="expanded")
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
    h1,h2,h3{font-family:'Space Grotesk',sans-serif}
    .block-container{max-width:1500px;padding-top:1.2rem}
    [data-testid="stSidebar"]{border-right:1px solid #e2e8f0}
    .hero{padding:30px;border-radius:24px;background:linear-gradient(135deg,#061a33,#0f3c68 60%,#0f766e);color:white}
    .hero h1{color:white;font-size:44px;margin:4px 0}.hero p{color:#dbeafe;max-width:950px;line-height:1.6}
    .eyebrow{font-size:11px;letter-spacing:1.5px;color:#93c5fd;font-weight:700}
    .card{padding:20px;border:1px solid #e2e8f0;border-radius:18px;background:white;box-shadow:0 5px 18px rgba(15,23,42,.04)}
    .section{font-family:'Space Grotesk';font-size:22px;font-weight:700;color:#10243e;margin:24px 0 10px}
    .pill{display:inline-block;padding:5px 11px;border-radius:999px;font-weight:700;font-size:12px}
    .pass{background:#dcfce7;color:#166534}.monitor{background:#fef3c7;color:#92400e}.reject{background:#fee2e2;color:#991b1b}
    .wow{padding:20px;border-radius:20px;background:linear-gradient(145deg,#071a32,#10385f);color:white;min-height:210px}
    .wow h3{color:white}.muted{color:#64748b;font-size:12px}
    </style>
    """,unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("## 🛡️ BurnGuard AI")
        st.caption("Reliability intelligence for burn-in screening")
        st.divider()
        st.markdown("### Demo mode")
        st.caption("Database-free • local telemetry • explainable ML")
        st.divider()
        st.markdown("**Built-in demo dataset**")
        d=get_demo_data()
        st.write(f"**{d.Component_ID.nunique():,}** components")
        st.write(f"**{d.Lot_ID.nunique()}** lots")
        st.write("**4** checkpoints")
        st.divider()
        st.caption("SIH 2026 • Team 106 • SIH26170")

@st.cache_data
def scores_for(df):
    return score_all(df)

def chip(v):
    return f'<span class="pill {v.lower()}">{v}</span>'