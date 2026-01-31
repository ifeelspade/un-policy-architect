import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
import os
import base64
import gspread
import math
from google.oauth2.service_account import Credentials
import time
from gspread.exceptions import APIError

ADMIN_PAUSED = st.secrets.get("admin", {}).get("paused", False)

if ADMIN_PAUSED:
    st.error("⏸️ Simulation is currently paused by the Admin.")
    st.info("Please wait. The session will resume shortly.")
    st.stop()


SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

info = dict(st.secrets["gcp_service_account"])
info["private_key"] = info["private_key"].replace("\\n", "\n")


creds = Credentials.from_service_account_info(info, scopes=SCOPE)

TEAM_CREDENTIALS = {
    "Ssbian": "ssbian@2050",
    "SWOT": "swot@2050",
    "Hilltop": "hilltop@2050",
    "TEAM QUANTA": "teamquanta@2050",
    "Data Dynamos 1": "datadynamos1@2050",
    "Dynamo": "dynamo@2050",
    "The Boys": "theboys@2050",
    "Cuboid": "cuboid@2050",
    "Dil Se FORSE": "dilseforse@2050",
    "Brainy": "brainy@2050",
    "Team Bravo": "teambravo@2050",
    "Quantum Cubed": "quantumcubed@2050",
    "MATAnalytics": "matanalytics@2050",
    "Team Classic": "teamclassic@2050",
    "Zenith": "zenith@2050",
    "Dipesh and Haard": "dipeshandhaard@2050",
    "Decor X": "decorx@2050",
    "Surror": "surror@2050",
    "Mindless Minions": "mindlessminions@2050",
    "Big Brain Energy": "bigbrainenergy@2050",
    "Alchemists": "alchemists@2050",
    "spade papa": "spadepapa@2050"
}


@st.cache_resource
def get_master_sheet():
    for attempt in range(5):
        try:
            client = gspread.authorize(creds)
            return client.open("UN Policy Architect – Master Control").sheet1
        except APIError:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)

from datetime import datetime

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def calculate_cumulative_score(
    initial_gdp,
    final_gdp,
    initial_co2,
    final_co2,
    final_temp,
    political_capital,
    renewable_pct,
    public_approval
):
    # 1. Political Capital (25%)
    political_score = clamp(political_capital, 0, 100)
    political_component = 0.15 * political_score

    # 2. GDP Stability (20%)
    if initial_gdp > 0:
        gdp_growth_pct = ((final_gdp - initial_gdp) / initial_gdp) * 100
    else:
        gdp_growth_pct = 0  # safety fallback

    gdp_score = clamp(50 + gdp_growth_pct, 0, 100)
    gdp_component = 0.25 * gdp_score

    # 3. Carbon Reduction (20%)
    if initial_co2 > 0:
        carbon_reduction_pct = ((initial_co2 - final_co2) / initial_co2) * 100
    else:
        carbon_reduction_pct = 0  # safety fallback

    carbon_score = clamp(carbon_reduction_pct, 0, 100)
    carbon_component = 0.20 * carbon_score

    # 4. Temperature Control (20%)
    if final_temp <= 1.3:
        temp_score = 100
    elif final_temp <= 1.5:
        temp_score = 80
    elif final_temp <= 1.7:
        temp_score = 40
    else:
        temp_score = 0

    temp_component = 0.20 * temp_score

    # 5. Renewable Energy (10%)
    renewable_score = clamp(renewable_pct, 0, 100)
    renewable_component = 0.13 * renewable_score

    # 6. Public Approval (5%)
    approval_score = clamp(public_approval, 0, 100)
    approval_component = 0.07 * approval_score

    final_score = (
        political_component +
        gdp_component +
        carbon_component +
        temp_component +
        renewable_component +
        approval_component
    )

    return round(final_score, 2)


def write_to_master_sheet(sheet):
    s = st.session_state.stats

    cumulative_score = calculate_cumulative_score(
        initial_gdp=5.0,                     # Starting GDP
        final_gdp=s['GDP (Trillion $)'],
        initial_co2=450,                     # Starting CO2
        final_co2=s['CO2 (Gt)'],
        final_temp=s['Global Temp Rise'],
        political_capital=s['Political Capital'],
        renewable_pct=s['Renewable %'],
        public_approval=s['Public Approval']
    )

    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),   # Timestamp
        st.session_state.team_name,                     # Team_Name
        st.session_state.enacted_year,                  # Simulation_Year
        st.session_state.last_tax,                      # Carbon_Tax
        st.session_state.last_subsidy,                  # Green_Subsidy
        st.session_state.last_regulation,               # Regulation_Level
        round(s['GDP (Trillion $)'], 2),                # GDP_Trillion
        round(s['CO2 (Gt)'], 2),                        # CO2_Gt
        round(s['Renewable %'], 2),                     # Renewable_Percent
        s['Public Approval'],                           # Public_Approval
        s['Political Capital'],                         # Political_Capital
        round(s['Global Temp Rise'], 2),                # Global_Temp_Rise
        st.session_state.last_event,                    # Event_Name
        "ONGOING" if not st.session_state.game_over else "ENDED",
        cumulative_score
    ]

    # ✅ SAFE APPEND (NO CRASH)
    for attempt in range(5):
        try:
            sheet.append_row(row, value_input_option="USER_ENTERED")
            break
        except APIError:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)


# ----------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT CALL)
# ----------------------------------------------------
st.set_page_config(
    page_title="UN Policy Architect 2050",
    layout="wide",
    page_icon="🌍"
)

# ----------------------------------------------------
# SESSION STATE INITIALIZATION
# ----------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "landing"
# ----------------------------------------------------
# UTILS
# ----------------------------------------------------
def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "LOGO.png")
BG_PATH = os.path.join(BASE_DIR, "background.jpg")
bg_image = get_base64_image(BG_PATH)

# ----------------------------------------------------
# LANDING PAGE
# ----------------------------------------------------
if st.session_state.page == "landing":
    st.markdown(
        f"""
        <style>
       /* Headings & normal text only */
        h1, h2, h3, h4, h5, h6,
        p, label {{
            color: #ffffff !important;
        }}
        /* PRIMARY BUTTON — ALL STATES */
        button[kind="primary"],
        button[data-testid="stBaseButton-primary"],
        button[data-testid="baseButton-primary"] {{
            background-color: #020617 !important;
            color: #ffffff !important;
            border: 1px solid #334155 !important;
        }}
        
        /* INNER CONTAINER (CRITICAL FIX) */
        button[kind="primary"] > div,
        button[data-testid="stBaseButton-primary"] > div,
        button[data-testid="baseButton-primary"] > div {{
            background-color: #020617 !important;
        }}
        
        /* TEXT INSIDE BUTTON */
        button[kind="primary"] span,
        button[data-testid="stBaseButton-primary"] span,
        button[data-testid="baseButton-primary"] span {{
            color: #ffffff !important;
        }}
        
        /* HOVER / FOCUS / ACTIVE (ALL STATES) */
        button[kind="primary"]:hover,
        button[kind="primary"]:focus,
        button[kind="primary"]:active,
        button[data-testid="stBaseButton-primary"]:hover,
        button[data-testid="stBaseButton-primary"]:focus,
        button[data-testid="stBaseButton-primary"]:active {{
            background-color: #020617 !important;
        }}
        
        button[kind="primary"]:hover > div,
        button[kind="primary"]:focus > div,
        button[kind="primary"]:active > div,
        button[data-testid="stBaseButton-primary"]:hover > div,
        button[data-testid="stBaseButton-primary"]:focus > div,
        button[data-testid="stBaseButton-primary"]:active > div {{
            background-color: #020617 !important;
        }}

        .stApp {{
            background-image:
                linear-gradient(rgba(10,15,25,0.9), rgba(10,15,25,0.9)),
                url("data:image/jpg;base64,{bg_image}");
            background-size: cover;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("🌍 UN Policy Architect 2050")
    st.subheader("Team Registration")
    
    team_name = st.text_input("Enter your Team Name")
    team_password = st.text_input("Enter Team Password", type="password")
    
    if st.button("Enter Simulation", type="primary"):
        if team_name.strip() == "" or team_password.strip() == "":
            st.warning("Please enter both team name and password")
    
        elif team_name not in TEAM_CREDENTIALS:
            st.error("Invalid team name")
    
        elif TEAM_CREDENTIALS[team_name] != team_password:
            st.error("Incorrect password")
    
        else:
            # ✅ AUTH SUCCESS
            st.session_state.team_name = team_name
            st.session_state.authenticated = True
            st.session_state.page = "simulation"
            st.success("Authentication successful")
            st.rerun()
    
    st.stop()  # ⛔ Prevents simulation from loading without auth


# ----------------------------------------------------
# SIMULATION PAGE GUARD
# ----------------------------------------------------
if st.session_state.page != "simulation":
    st.stop()

# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------
with st.sidebar:
    st.image(
        LOGO_PATH,
        use_container_width=True
    )
    st.markdown(
        "<h3 style='text-align:center; color:#93c5fd;'>UN Policy Architect</h3>",
        unsafe_allow_html=True
    )
    st.markdown(f"**Team:** {st.session_state.team_name}")
    st.markdown("---")

# ----------------------------------------------------
# BACKGROUND STYLING
# ----------------------------------------------------
st.markdown(
    f"""
    <style>
    /* Headings & normal text only */
        h1, h2, h3, h4, h5, h6,
        p, label {{
            color: #ffffff !important;
        }}
        /* SECONDARY BUTTON (Reset Simulation) */
        button[data-testid="baseButton-secondary"] {{
            background-color: #020617 !important;   /* dark */
            color: white !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            opacity: 1 !important;
        }}
    .stApp {{
        background-image:
            linear-gradient(rgba(10,15,25,0.85), rgba(10,15,25,0.85)),
            url("data:image/jpg;base64,{bg_image}");
        background-size: cover;
        background-attachment: fixed;
    }}
    section[data-testid="stSidebar"] {{
        background: rgba(15,20,30,0.9);
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------------------------------
# GAME STATE
# ----------------------------------------------------
if 'year' not in st.session_state:
    st.session_state.year = 2025
    st.session_state.stats = {
        'GDP (Trillion $)': 5.0,
        'CO2 (Gt)': 450,
        'Global Temp Rise': 1.1,
        'Public Approval': 60,
        'Political Capital': 100, # Currency to spend on policies
        'Renewable %': 15
    }
    st.session_state.history = pd.DataFrame(columns=st.session_state.stats.keys())
    st.session_state.game_over = False
    st.session_state.last_event = "Welcome, Delegate. The General Assembly awaits your first move."
    st.session_state.event_impact = ""

# --- EVENT SYSTEM ---
EVENTS = [
    {"name": "Tech Breakthrough", "msg": "Scientists discover a fusion efficiency booster!", "effect": {"Renewable %": 5, "CO2 (Gt)": -10}},
    {"name": "Super-Typhoon", "msg": "Coastal cities flooded. Infrastructure damaged.", "effect": {"GDP (Trillion $)": -0.2, "Public Approval": -10}},
    {"name": "Oil Lobby Strike", "msg": "Fossil fuel giants freeze assets.", "effect": {"Political Capital": -20, "GDP (Trillion $)": -0.1}},
    {"name": "Youth Climate Protest", "msg": "Millions march. Pressure mounts for action.", "effect": {"Political Capital": 15, "Public Approval": -5}},
    {"name": "Geopolitical Tension", "msg": "Trade wars slow down solar panel imports.", "effect": {"Renewable %": -2, "GDP (Trillion $)": -0.15}}
]

def trigger_random_event():
    if random.random() < 0.4: # 40% chance of event per turn
        event = random.choice(EVENTS)
        st.session_state.last_event = f"🚨 ALERT: {event['name']} - {event['msg']}"
        
        impact_text = []
        for key, val in event['effect'].items():
            st.session_state.stats[key] += val
            symbol = "⬆️" if val > 0 else "⬇️"
            impact_text.append(f"{key} {symbol} {abs(val)}")
        
        st.session_state.event_impact = " | ".join(impact_text)
    else:
        st.session_state.last_event = "🕊️ Status: Global situation stable."
        st.session_state.event_impact = ""

# --- SIMULATION ENGINE ---
def calculate_turn(tax, subsidy, regulation):
    s = st.session_state.stats
    
    # 1. Costs (Political Capital)
    cost = (tax * 2) + (subsidy * 3) + (regulation * 4)
    if s['Political Capital'] < cost:
        return False, "Not enough Political Capital! Lower your intensity."

    # 2. Update Stats
    s['Political Capital'] -= cost
    s['Political Capital'] += 18 # Natural regeneration per turn
    

    # Economics
    gdp_growth = 0.023 - (tax * 0.002) - (regulation * 0.001) + (subsidy * 0.0015)
    s['GDP (Trillion $)'] *= (1 + gdp_growth)
    
    # Environment
    co2_reduction = (tax * 3.2) + (subsidy * 2.7) + (regulation * 2.2)
    s['CO2 (Gt)'] -= co2_reduction
    s['Renewable %'] += (subsidy * 1.2)
    
    # Feedback Loops
    if s['CO2 (Gt)'] > 400: s['Global Temp Rise'] += 0.05
    else: s['Global Temp Rise'] += 0.01
    
    # Public Opinion
    approval_change = 0
    if gdp_growth < 0: approval_change -= 2
    if s['Global Temp Rise'] > 1.5: approval_change -= 5
    if subsidy > 5: approval_change += 3
    s['Public Approval'] = max(0, min(100, s['Public Approval'] + approval_change))

    # Clamp values
    s['Renewable %'] = min(100, s['Renewable %'])
    s['CO2 (Gt)'] = max(0, s['CO2 (Gt)'])
    # --- Record History (FIXED) ---

# Save the year for which policy is enacted
   # --- Record History ---
    st.session_state.enacted_year = st.session_state.year

    current_year_data = s.copy()
    current_year_data["Year"] = st.session_state.enacted_year

    st.session_state.history = pd.concat(
        [st.session_state.history, pd.DataFrame([current_year_data])],
        ignore_index=True
    )

# --- END CONDITION CHECK (BEFORE increment) ---
    if st.session_state.enacted_year >= 2050:
        st.session_state.game_over = True
        return True, "Final policy enacted. Simulation complete."

# Move to next year ONLY if not finished
    st.session_state.year += 1

    trigger_random_event()
    return True, "Policy Enacted Successfully"



# --- UI LAYOUT ---

# Sidebar: Controls
# Sidebar: Controls
with st.sidebar:
    st.header("🏛️ Policy Controls")
    st.markdown("Draft your legislation for the upcoming fiscal year.")

    tax_input = st.slider(
        "Carbon Tax Rate (%)", 0, 20, 5,
        help="High tax reduces CO2 but hurts GDP."
    )

    subsidy_input = st.slider(
        "Green Subsidies (Billion $)", 0, 20, 5,
        help="Boosts renewables, costs Political Capital."
    )

    reg_input = st.slider(
        "Industrial Regulation Level", 0, 10, 3,
        help="Strict rules lower emissions but anger corporations."
    )

    st.markdown("---")

    if st.button("Signed & Sealed ✒️", type="primary"):

        # 🚫 HARD STOP — Simulation already finished
        if st.session_state.game_over:
            st.warning("Simulation Ended. Please reset.")
            st.stop()

        # 🧾 Store last policy inputs
        st.session_state.last_tax = tax_input
        st.session_state.last_subsidy = subsidy_input
        st.session_state.last_regulation = reg_input

        # ▶️ Run simulation turn
        success, msg = calculate_turn(
            tax_input,
            subsidy_input,
            reg_input
        )

        if success:
            # 📝 Log to Master Sheet
            sheet = get_master_sheet()
            write_to_master_sheet(sheet)


            # 🏁 Final Year Handling
            if st.session_state.game_over:
                st.success("🏁 Final policy enacted. Simulation complete.")
                st.balloons()
            else:
                st.toast("Policy enacted & logged successfully ✅", icon="📊")
        else:
            st.error(msg)

    if st.button("Reset Simulation",type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Main Dashboard
st.title("🌐 UN Sustainability Command Center")
st.markdown(f"**Current Year: {st.session_state.year}** | Target: Net Zero by 2050")

# Top Level Metrics
col1, col2, col3, col4, col5 = st.columns(5)
s = st.session_state.stats
with col1: st.metric("GDP", f"${s['GDP (Trillion $)']:.2f} T", delta_color="normal")
with col2: st.metric("CO2 Output", f"{s['CO2 (Gt)']:.0f} Gt", delta_color="inverse")
with col3: st.metric("Global Temp", f"+{s['Global Temp Rise']:.2f}°C", delta_color="inverse")
with col4: st.metric("Political Capital", f"{s['Political Capital']:.0f}", help="Required to pass laws")
with col5:
    st.metric("Renewables", f"{s['Renewable %']:.0f}%")

# Approval Bar
st.write(f"Public Approval Rating: **{s['Public Approval']}%**")
st.progress(s['Public Approval'] / 100)

# Narrative / Event Box
if st.session_state.last_event:
    if "ALERT" in st.session_state.last_event:
        st.error(f"{st.session_state.last_event} \n\n **Impact:** {st.session_state.event_impact}")
    else:
        st.info(st.session_state.last_event)

# Charts Area
st.markdown("### 📊 Projection Models")
tab1, tab2 = st.tabs(["Economic vs Climate", "Energy Mix"])

if not st.session_state.history.empty:
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=st.session_state.history['Year'], y=st.session_state.history['GDP (Trillion $)'], name='GDP', line=dict(color='#3b82f6', width=3)))
        fig.add_trace(go.Scatter(x=st.session_state.history['Year'], y=st.session_state.history['CO2 (Gt)'], name='CO2', yaxis='y2', line=dict(color='#ef4444', width=3)))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            yaxis=dict(title='GDP (Trillions)', showgrid=False),
            yaxis2=dict(title='CO2 (Gt)', overlaying='y', side='right', showgrid=False),
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Area chart for energy
        fig2 = go.Figure()
        hist = st.session_state.history
        fig2.add_trace(go.Scatter(
            x=hist['Year'], y=hist['Renewable %'], mode='lines', fill='tozeroy', name='Renewables', line=dict(color='#10b981')
        ))
        fig2.add_trace(go.Scatter(
            x=hist['Year'], y=100-hist['Renewable %'], mode='lines', fill='tonexty', name='Fossil Fuels', line=dict(color='#6b7280')
        ))
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            yaxis=dict(range=[0, 100], title='Energy Share %'),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Awaiting first policy decision to generate projections...")

# End Game Logic
if s['Global Temp Rise'] >= 2.0:
    st.error("❌ CRITICAL FAILURE: 2°C Warming Limit Breached. Ecological collapse imminent.")
    st.session_state.game_over = True
elif st.session_state.game_over:  # <--- FIXED: using st.session_state.year
    score = s['GDP (Trillion $)'] + (100 - s['CO2 (Gt)']/10) + s['Public Approval']
    st.success(f"🏆 SIMULATION COMPLETE. Final Sustainability Score: {score:.0f}")
    st.balloons()
    st.session_state.game_over = True	




















































































