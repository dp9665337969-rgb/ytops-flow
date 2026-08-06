import streamlit as st
import pandas as pd
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="ReconcileX AI - Content Audit Portal",
    page_icon="⚡",
    layout="wide"
)

# Custom Styling for Dialogue Box & UI Alignment
st.markdown("""
<style>
    .dialogue-box {
        background-color: #F0F6FF;
        border: 1px solid #D0E1FD;
        border-radius: 12px;
        padding: 15px 25px;
        margin-bottom: 25px;
    }
    .quote-card {
        background: white;
        border-radius: 10px;
        padding: 12px 20px;
        font-weight: 600;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- TOP DIALOGUE BANNER (REUSABLE FOR BOTH PAGES) ---
def render_top_dialogue_banner():
    st.markdown("""
    <div class="dialogue-box">
        <div style="display: flex; justify-content: space-between; align-items: center; text-align: center;">
            <div class="quote-card" style="color: #D32F2F; width: 42%;">
                👨‍🏫 "Arey sir! Full padhaya, fir bhi salary me cut lag gaya!"
            </div>
            <div style="font-size: 22px;">⚡</div>
            <div class="quote-card" style="color: #1976D2; width: 45%;">
                👨‍🏫🦄 "Arey sir! ReconcileX AI use karo, zero salary cut hoga!"
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- PAGE 1: EXACT ORIGINAL LOGIN PAGE ---
def show_login_page():
    # Top Creative Banner
    render_top_dialogue_banner()

    # Title & Subtitle
    st.markdown("<h1 style='text-align: center; font-weight: 800;'>Automate content audit with <span style='color:#1E88E5;'>ReconcileX AI</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666; font-size: 15px;'>10 Crore+ watch hours reconciled with 100% precision.</p>", unsafe_allow_html=True)
    st.write("")

    # 3-Column Layout (Left Features - Center Form - Right Features)
    col_left, col_center, col_right = st.columns([1, 1.2, 1])

    with col_left:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("⚡ **Automated Audits**")
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("📊 **Multi-Host Split Engine**")

    with col_center:
        with st.form("login_form"):
            st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>Portal Login</h2>", unsafe_allow_html=True)
            
            access_id = st.text_input("Mobile Number / Access ID", placeholder="deepak_patil_8554")
            passkey = st.text_input("Passkey", type="password", placeholder="Enter key")
            
            st.write("")
            submit_button = st.form_submit_button(label="Access Portal →", use_container_width=True)

            if submit_button:
                # Login Credential Logic
                if (access_id == "deepak_patil_8554" or access_id == "UNAC_58291") and (passkey == "Pass@123" or passkey != ""):
                    st.session_state.authenticated = True
                    st.session_state.user_id = "deepak_patil_8554"
                    st.success("Access Granted!")
                    st.rerun()
                else:
                    st.error("Invalid Credentials. Please check Access ID and Passkey.")

    with col_right:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("🌟 **100% Verified Metadata**")
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("🛡️ **Zero Salary Cut Guarantee**")

# --- PAGE 2: EXACT CONTENT ENGINE DASHBOARD ---
def show_dashboard():
    # Sidebar matching exact screenshot
    with st.sidebar:
        st.markdown("### ⚡ ReconcileX AI")
        user_display = st.session_state.get("user_id", "deepak_patil_8554")
        st.markdown(f"👤 **Active Operator:** `{user_display}`")
        st.write("")
        if st.button("Logout", type="secondary"):
            st.session_state.authenticated = False
            st.rerun()

    # Top Creative Dialogue Banner on Second Page
    render_top_dialogue_banner()

    # Page Header matching exact screenshot
    st.markdown("## 📹 ReconcileX Content Engine")
    st.markdown("<p style='color: #555;'>Fetch channel content, adjust co-educator live hours, and generate audit sheets.</p>", unsafe_allow_html=True)
    st.write("")

    # Select Workflow Option
    st.markdown("**Select Audit Workflow:**")
    workflow = st.radio(
        "",
        ["📋 Mode A: Direct Video Links", "📺 Mode B: Channel / Playlist (Last 45 Days)"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Step 1 Section
    st.markdown("### Step 1: Input Direct Video Links")
    st.caption("Paste video/live links below (one per line):")
    
    video_links = st.text_area(
        "",
        placeholder="https://www.youtube.com/watch?v=...\nhttps://youtu.be/...",
        height=150,
        label_visibility="collapsed"
    )

    if st.button("🚀 Process Links", type="primary"):
        if video_links.strip():
            st.info("Processing input video metadata...")
            # Mock Data Processing Table
            data = [
                {"Video Title": "NEET 2026 Physics One-Shot Revision", "Duration (Mins)": 180, "Hosts": 1, "Credited Hours": 3.0},
                {"Video Title": "Complete Chemistry Marathon | Organic", "Duration (Mins)": 240, "Hosts": 2, "Credited Hours": 2.0},
            ]
            st.session_state.processed_df = pd.DataFrame(data)
        else:
            st.warning("Kripya kam se kam ek YouTube link paste karein.")

    if "processed_df" in st.session_state:
        st.markdown("---")
        st.markdown("### 📋 Audit Results Table")
        st.dataframe(st.session_state.processed_df, use_container_width=True)
        
        csv_data = st.session_state.processed_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Verified Audit CSV",
            data=csv_data,
            file_name=f"ReconcileX_Audit_{user_display}.csv",
            mime="text/csv"
        )

# --- MAIN ENGINE ---
if not st.session_state.authenticated:
    show_login_page()
else:
    show_dashboard()
