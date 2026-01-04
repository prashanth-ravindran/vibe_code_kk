

import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(page_title="Email WBR Automation", layout="wide")

st.title("📧 Weekly Business Review: Email Campaigns")
st.markdown("""
*Based on Amazon WBR Framework & Handwritten Notes*
- **Focus:** Variance & Lead Indicators (Open Rates)
- **Goal:** Identify defects and assign 'Path to Green'
""")

# --- 1. DATA PREPARATION (Phase 1: Data Freeze) ---
# In a real scenario, this allows CSV upload. For now, we generate sample data.
st.sidebar.header("1. Data Input")
uploaded_file = st.sidebar.file_uploader("Upload Weekly Metrics (CSV)", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    # GENERATING SAMPLE DATA (To vibe code the experience)
    data = {
        'Date': pd.date_range(start='2024-01-01', periods=12, freq='W-MON'),
        'Campaign_Name': [f'Newsletter {i}' for i in range(1, 13)],
        'Emails_Sent': [1000, 1200, 1100, 1500, 1600, 1550, 1700, 1800, 1750, 2000, 2100, 2200],
        'Opens': [200, 250, 210, 300, 280, 270, 340, 360, 250, 400, 420, 310], # Note dips at index 5 and 8
        'Goal_Open_Rate': [0.20] * 12 # Target is 20%
    }
    df = pd.DataFrame(data)

# --- 2. CALCULATIONS (The "Logic" Layer) ---
# Calculating Lead Indicators [Handwritten Note Source: 3]
df['Open_Rate'] = df['Opens'] / df['Emails_Sent']
df['Open_Rate_Pct'] = df['Open_Rate'] * 100
df['Goal_Pct'] = df['Goal_Open_Rate'] * 100

# Calculating Variance (WoW and vs Goal) [Handwritten Note Source: 7]
df['WoW_Variance'] = df['Open_Rate'].pct_change() * 100
df['Goal_Variance'] = df['Open_Rate_Pct'] - df['Goal_Pct']

# Status Logic: "Red" if miss is > 5% relative variance or simply below goal
def get_status(row):
    if row['Goal_Variance'] < -2.0: # If miss is more than 2 percentage points
        return "🔴 Off Track"
    return "🟢 On Track"

df['Status'] = df.apply(get_status, axis=1)

# Initialize Narrative columns if they don't exist
if 'Root_Cause_Hypothesis' not in df.columns:
    df['Root_Cause_Hypothesis'] = ""
if 'Path_to_Green' not in df.columns:
    df['Path_to_Green'] = ""

# --- 3. VISUALIZATION (Trends & Hypotheses) ---
# [Handwritten Note Source: 9, 10, 14] - Using trended data (6-12 weeks)
st.subheader("📈 Lead Indicator Trends (Last 12 Weeks)")

# Create a dual-layer chart: Line for Rate, Rule for Goal
line = alt.Chart(df).mark_line(point=True).encode(
    x='Date:T',
    y=alt.Y('Open_Rate_Pct', title='Open Rate (%)'),
    tooltip=['Date', 'Campaign_Name', 'Open_Rate_Pct', 'Root_Cause_Hypothesis']
).interactive()

goal_line = alt.Chart(df).mark_rule(color='red', strokeDash=[5, 5]).encode(
    y='Goal_Pct'
)

st.altair_chart((line + goal_line).properties(width=800), use_container_width=True)

# --- 4. THE WBR DASHBOARD (Editable) ---
st.subheader("📝 Weekly Review Table")
st.info("Instructions: Filter for 'Off Track' rows. Owners must write a narrative for anomalies.")

# Formatting for display
display_cols = ['Date', 'Campaign_Name', 'Open_Rate_Pct', 'Goal_Pct', 'WoW_Variance', 'Status', 'Root_Cause_Hypothesis', 'Path_to_Green']
df_display = df[display_cols].sort_values(by='Date', ascending=False)

# THE EDITABLE TABLE (Streamlit Data Editor)
# This allows you to type directly into the dashboard
edited_df = st.data_editor(
    df_display,
    column_config={
        "Open_Rate_Pct": st.column_config.NumberColumn("Open Rate %", format="%.1f%%"),
        "Goal_Pct": st.column_config.NumberColumn("Goal %", format="%.1f%%"),
        "WoW_Variance": st.column_config.NumberColumn("WoW Var", format="%.1f%%"),
        "Status": st.column_config.TextColumn("Status", help="Red if >2% below goal"),
        "Root_Cause_Hypothesis": st.column_config.TextColumn("Root Cause / Hypothesis", width="large", help="Why did this happen?"),
        "Path_to_Green": st.column_config.TextColumn("Path to Green", width="medium", help="Corrective Action")
    },
    disabled=["Date", "Campaign_Name", "Open_Rate_Pct", "Goal_Pct", "WoW_Variance", "Status"], # Lock metrics, allow editing text
    hide_index=True,
    num_rows="fixed"
)

# --- 5. CLOSING THE LOOP (Save) ---
# [Handwritten Note Source: 8] - Action Item Tracker persistence
st.download_button(
    label="💾 Save WBR Report (Download CSV)",
    data=edited_df.to_csv(index=False).encode('utf-8'),
    file_name=f'WBR_Report_{datetime.now().strftime("%Y%m%d")}.csv',
    mime='text/csv',
)

st.divider()
st.markdown("### 🔍 WBR Audit Checklist")
st.markdown("""
1. **Data Freeze:** Ensure inputs were frozen by Tuesday[cite: 4].
2. **Variance Check:** Did we explain the 'Why' for every Red metric?.
3. **Hypothesis Loop:** For next week, did we test the 'Path to Green' action?
""")
