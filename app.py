import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
# Google API client library import (agar local me install na ho toh: pip install google-api-python-client)
# from googleapiclient.discovery import build

# Page Configuration
st.set_page_config(
    page_title="ReconcileX AI - YouTube Payroll Audit",
    page_icon="⚡",
    layout="wide"
)

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- PAGE 1: LOGIN PAGE (3-COLUMN LAYOUT) ---
def show_login_page():
    st.markdown("<h2 style='text-align: center;'>🔐 ReconcileX AI Portal Access</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Automated YouTube Live Audit & Payroll Reconciliation Engine</p>", unsafe_allow_html=True)
    st.write("")
    st.write("")

    # 3-Column Layout for centered login box
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        with st.form("login_form"):
            st.subheader("Login to Dashboard")
            access_id = st.text_input("Access ID", placeholder="e.g. UNAC_58291")
            passkey = st.text_input("Passkey", type="password", placeholder="Enter Passkey")
            submit_button = st.form_submit_button(label="Authenticate & Launch", use_container_width=True)

            if submit_button:
                # Validating Credentials
                if access_id == "UNAC_58291" and passkey == "Pass@123":
                    st.session_state.authenticated = True
                    st.success("Authentication Successful!")
                    st.rerun()
                else:
                    st.error("Invalid Access ID or Passkey. Please try again.")

# --- PAGE 2: RECONCILIATION & AUDIT DASHBOARD ---
def show_dashboard():
    # Sidebar Logout & Controls
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.write("**Session:** Active")
        st.write(f"**Access ID:** UNAC_58291")
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    # --- TOP BANNER (TERI EXACT REQUIRED LINE) ---
    st.success("✨ **Chinta mat karo, salary nahi kategi is baar!** — Automated Multi-Host Split & Verified Payout Engine.")
    
    st.title("📊 YouTube Audit & Multi-Host Payout Engine")
    st.caption("Automated 45-day lookback window | Zero manual sheet error")

    st.markdown("---")

    # Step 1: Channel & API Configuration
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        channel_id = st.text_input("YouTube Channel ID / Handle", value="UC_example_channel")
    with col_input2:
        lookback_days = st.slider("Audit Lookback Window (Days)", min_value=7, max_value=45, value=45)

    if st.button("Fetch & Audit Videos", type="primary"):
        st.info("Fetching data via YouTube API v3...")
        
        # --- MOCK DATA FOR DEMO PURPOSES (App directly ready to show) ---
        # Actual production logic uses googleapiclient to pull real channel videos
        data = [
            {"Video Title": "NEET 2026 Physics One-Shot Revision", "Duration (Mins)": 180, "Date": "2026-08-01", "Default Host": "Educator A"},
            {"Video Title": "Complete Chemistry Marathon | Organic", "Duration (Mins)": 240, "Date": "2026-07-28", "Default Host": "Educator B & C"},
            {"Video Title": "Biology Mock Test Solving Session", "Duration (Mins)": 120, "Date": "2026-07-20", "Default Host": "Educator A"},
            {"Video Title": "Strategic Strategy & Motivation Session", "Duration (Mins)": 90, "Date": "2026-07-15", "Default Host": "Educator D & A"},
        ]
        st.session_state.audit_data = pd.DataFrame(data)

    # Step 2: Multi-Host Duration Split Logic
    if "audit_data" in st.session_state:
        st.markdown("### 📝 Multi-Host Payout Adjustment")
        st.write("Select videos with multiple educators to automatically split watch-time hours equally.")

        df = st.session_state.audit_data.copy()
        
        # Interactive Host Split
        num_hosts = []
        for i, row in df.iterrows():
            hosts = st.number_input(
                f"Number of Educators for: **{row['Video Title']}** ({row['Duration (Mins)']} Mins)",
                min_value=1,
                max_value=5,
                value=2 if "&" in row['Default Host'] else 1,
                key=f"host_{i}"
            )
            num_hosts.append(hosts)

        df['Educator Count'] = num_hosts
        df['Credited Mins Per Educator'] = df['Duration (Mins)'] / df['Educator Count']
        df['Credited Hours Per Educator'] = (df['Credited Mins Per Educator'] / 60).round(2)

        st.markdown("---")
        st.markdown("### 📋 Final Verified Reconciliation Table")
        st.dataframe(df, use_container_width=True)

        # Step 3: Export Clean CSV
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Verified Payout CSV Audit Report",
            data=csv_data,
            file_name=f"ReconcileX_Payroll_Audit_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary"
        )

# --- MAIN CONTROLLER ---
if not st.session_state.authenticated:
    show_login_page()
else:
    show_dashboard()
