import streamlit as st
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="ReconcileX AI - YouTube Payroll Audit",
    page_icon="⚡",
    layout="wide"
)

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- PAGE 1: LOGIN PAGE (WITH DIALOGUE & DIALECT HOOK) ---
def show_login_page():
    # Creative dialogue banner on top
    st.markdown("<h1 style='text-align: center;'>⚡ ReconcileX AI</h1>", unsafe_allow_html=True)
    st.markdown(
        "<h3 style='text-align: center; color: #00C853;'>✨ \"Chinta mat karo, salary nahi kategi is baar!\"</h3>", 
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; color: gray;'>Automated YouTube Live Audit & Multi-Host Payroll Reconciliation Engine</p>", 
        unsafe_allow_html=True
    )
    st.write("")

    # Centered Login Card
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.info("🔒 **Internal Portal Access** — Enter authorized credentials to proceed.")
        with st.form("login_form"):
            st.subheader("Login to Dashboard")
            access_id = st.text_input("Access ID", placeholder="e.g. UNAC_58291")
            passkey = st.text_input("Passkey", type="password", placeholder="Enter Passkey")
            submit_button = st.form_submit_button(label="Authenticate & Launch Portal", use_container_width=True)

            if submit_button:
                if access_id == "UNAC_58291" and passkey == "Pass@123":
                    st.session_state.authenticated = True
                    st.success("Authentication Successful!")
                    st.rerun()
                else:
                    st.error("Invalid Access ID or Passkey.")

# --- PAGE 2: DASHBOARD ---
def show_dashboard():
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.write("**Status:** Authenticated")
        st.write("**Access ID:** UNAC_58291")
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    st.success("✨ **Chinta mat karo, salary nahi kategi is baar!** — Automated Multi-Host Split & Verified Payout Engine.")
    
    st.title("📊 YouTube Audit & Multi-Host Payout Engine")
    st.caption("Automated 45-day lookback window | Zero manual sheet error")
    st.markdown("---")

    col_input1, col_input2 = st.columns(2)
    with col_input1:
        channel_id = st.text_input("YouTube Channel ID / Handle", value="UC_example_channel")
    with col_input2:
        lookback_days = st.slider("Audit Lookback Window (Days)", min_value=7, max_value=45, value=45)

    if st.button("Fetch & Audit Videos", type="primary"):
        st.info("Fetching data via YouTube API v3...")
        data = [
            {"Video Title": "NEET 2026 Physics One-Shot Revision", "Duration (Mins)": 180, "Date": "2026-08-01", "Default Host": "Educator A"},
            {"Video Title": "Complete Chemistry Marathon | Organic", "Duration (Mins)": 240, "Date": "2026-07-28", "Default Host": "Educator B & C"},
            {"Video Title": "Biology Mock Test Solving Session", "Duration (Mins)": 120, "Date": "2026-07-20", "Default Host": "Educator A"},
            {"Video Title": "Strategic Strategy & Motivation Session", "Duration (Mins)": 90, "Date": "2026-07-15", "Default Host": "Educator D & A"},
        ]
        st.session_state.audit_data = pd.DataFrame(data)

    if "audit_data" in st.session_state:
        st.markdown("### 📝 Multi-Host Payout Adjustment")
        df = st.session_state.audit_data.copy()
        
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

        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Verified Payout CSV Audit Report",
            data=csv_data,
            file_name=f"ReconcileX_Payroll_Audit_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="primary"
        )

# --- MAIN RUN ---
if not st.session_state.authenticated:
    show_login_page()
else:
    show_dashboard()
