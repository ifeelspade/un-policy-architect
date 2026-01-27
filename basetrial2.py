# =====================================================
# UN POLICY ARCHITECT 2050 — CLEAN STABLE VERSION
# =====================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random, os, base64, time
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError
from datetime import datetime

# -----------------------------------------------------
# PAGE CONFIG (FIRST CALL)
# -----------------------------------------------------
st.set_page_config(
    page_title="UN Policy Architect 2050",
    page_icon="🌍",
    layout="wide"
)

# -----------------------------------------------------
# ADMIN PAUSE
# -----------------------------------------------------
ADMIN_PAUSED = st.secrets.get("admin", {}).get("paused", False)
if ADMIN_PAUSED:
    st.error("⏸️ Simulation paused by Admin.")
    st.stop()

# -----------------------------------------------------
# GOOGLE SHEETS SETUP
# -----------------------------------------------------
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

info = dict(st.secrets["gcp_service_account"])
info["private_key"] = info["private_key"].replace("\\n", "\n")
creds = Credentials.from_service_account_info(info, scopes=SCOPE)

@st.cache_resource
def get_master_sheet():
    for i in range(5):
        try:
            client = gspread.authorize(creds)
            return client.open("UN Policy Architect – Master Control").sheet1
        except APIError:
            time.sleep(2 ** i)

# -----------------------------------------------------
# UTILS
# -----------------------------------------------------
def get_base64_image(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_PATH = os.path.join(BASE_DIR, "background.jpg")
LOGO_PATH = os.path.join(BASE_DIR, "LOGO.png")
bg_image = get_base64_image(BG_PATH)

# -----------------------------------------------------
# GLOBAL STYLING (BUTTON FIX INCLUDED)
# -----------------------------------------------------
st.markdown(
    f"""
    <style>
    h1,h2,h3,h4,h5,h6,p,label {{ color: white !important; }}

    button[data-testid="stBaseButton-primary"],
    button[data-testid="baseButton-primary"] {{
        background-color: #020617 !important;
        color: white !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }}

    button[data-testid="baseButton-secondary"] {{
        background-color: #020617 !important;
        color: white !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        opacity: 1 !important;
    }}

    .stApp {{
        background-image:
            linear-gradient(rgba(10,15,25,0.9), rgba(10,15,25,0.9)),
            url("data:image/jpg;base64,{bg_image}");
        background-size: cover;
        background-attachment: fixed;
    }}

    section[data-testid="stSidebar"] {{
        background: rgba(15,20,30,0.95);
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------
# SESSION STATE INIT
# -----------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "landing"

# -----------------------------------------------------
# LANDING PAGE
# -----------------------------------------------------
if st.session_state.page == "landing":
    st.title("🌍 UN Policy Architect 2050")
    st.subheader("Team Registration")

    team = st.text_input("Enter your Team Name")

    if st.button("Enter Simulation", type="primary"):
        if team.strip() == "":
            st.warning("Please enter a team name")
        else:
            st.session_state.team_name = team
            st.session_state.page = "simulation"

    st.stop()

# -----------------------------------------------------
# GAME STATE INIT
# -----------------------------------------------------
if "year" not in st.session_state:
    st.session_state.year = 2025
    st.session_state.game_over = False
    st.session_state.stats = {
        "GDP (Trillion $)": 5.0,
        "CO2 (Gt)": 450,
        "Global Temp Rise": 1.1,
        "Public Approval": 60,
        "Political Capital": 100,
        "Renewable %": 15
    }
    st.session_state.history = pd.DataFrame()
    st.session_state.last_event = "Welcome, Delegate."

# -----------------------------------------------------
# EVENT SYSTEM
# -----------------------------------------------------
EVENTS = [
    {"name": "Tech Breakthrough", "effect": {"Renewable %": 5, "CO2 (Gt)": -10}},
    {"name": "Super Typhoon", "effect": {"GDP (Trillion $)": -0.2}},
    {"name": "Oil Lobby Strike", "effect": {"Political Capital": -20}},
]

def trigger_event():
    if random.random() < 0.4:
        e = random.choice(EVENTS)
        for k, v in e["effect"].items():
            st.session_state.stats[k] += v
        st.session_state.last_event = f"🚨 {e['name']}"
    else:
        st.session_state.last_event = "🕊️ Global situation stable."

# -----------------------------------------------------
# SIMULATION ENGINE
# -----------------------------------------------------
def run_turn(tax, subsidy, regulation):
    s = st.session_state.stats
    cost = tax*2 + subsidy*3 + regulation*4

    if s["Political Capital"] < cost:
        return False, "Not enough Political Capital"

    s["Political Capital"] -= cost
    s["Political Capital"] += 18

    s["GDP (Trillion $)"] *= (1 + 0.02 - tax*0.002)
    s["CO2 (Gt)"] -= (tax*3 + subsidy*2)
    s["Renewable %"] += subsidy

    trigger_event()

    year_data = s.copy()
    year_data["Year"] = st.session_state.year
    st.session_state.history = pd.concat(
        [st.session_state.history, pd.DataFrame([year_data])],
        ignore_index=True
    )

    st.session_state.year += 1
    if st.session_state.year > 2050:
        st.session_state.game_over = True

    return True, "Policy Enacted"

# -----------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------
with st.sidebar:
    st.image(LOGO_PATH, use_container_width=True)
    st.markdown(f"**Team:** {st.session_state.team_name}")
    st.markdown("---")

    tax = st.slider("Carbon Tax (%)", 0, 20, 5)
    subsidy = st.slider("Green Subsidies", 0, 20, 5)
    reg = st.slider("Regulation Level", 0, 10, 3)

    if st.button("Signed & Sealed ✒️", type="primary"):
        if not st.session_state.game_over:
            ok, msg = run_turn(tax, subsidy, reg)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    if st.button("Reset Simulation", type="secondary"):
        st.session_state.clear()
        st.experimental_rerun()

# -----------------------------------------------------
# DASHBOARD
# -----------------------------------------------------
st.title("🌐 UN Sustainability Command Center")
st.write(f"**Year:** {st.session_state.year}")

s = st.session_state.stats
cols = st.columns(5)
cols[0].metric("GDP", f"${s['GDP (Trillion $)']:.2f}T")
cols[1].metric("CO₂", f"{s['CO2 (Gt)']:.0f} Gt")
cols[2].metric("Temp", f"+{s['Global Temp Rise']:.2f}°C")
cols[3].metric("Political Capital", s["Political Capital"])
cols[4].metric("Renewables", f"{s['Renewable %']}%")

st.info(st.session_state.last_event)

# -----------------------------------------------------
# CHART
# -----------------------------------------------------
if not st.session_state.history.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=st.session_state.history["Year"],
        y=st.session_state.history["GDP (Trillion $)"],
        name="GDP"
    ))
    st.plotly_chart(fig, use_container_width=True)
