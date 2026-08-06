import streamlit as st
import re
import pandas as pd
from googleapiclient.discovery import build
import isodate

# ---------------------------------------------------------
# PAGE CONFIGURATION & STYLING (Clean Corporate UI)
# ---------------------------------------------------------
st.set_page_config(
    page_title="PulseOps | Unacademy YT Operations",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for Modern Minimalist Design
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .stButton>button {
        background-color: #08BD80;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover { background-color: #069c69; color: white; }
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.02);
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DUMMY CREDENTIALS DATABASE & SESSION SYSTEM
# ---------------------------------------------------------
USER_DATABASE = {
    "UNAC_58291": "Pass@123",
    "UNAC_10021": "Educator@2026",
    "ADMIN_OPS": "UnacademyOps#1"
}

# FIX APPLIED HERE: Used st.session_state instead of st_state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def extract_video_id(url):
    """ Extract standard 11-char YouTube Video ID from any URL format """
    regex = r"(?:v=|\/([0-9A-Za-z_-]{11}).*|list=|\/live\/|\/shorts\/)([0-9A-Za-z_-]{11})"
    match = re.search(regex, url)
    if match:
        return match.group(1) or match.group(2)
    return None

def get_video_durations_in_hours(api_key, video_ids):
    """ Fetch video durations using YouTube Data API v3 """
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.videos().list(
            part="contentDetails",
            id=",".join(video_ids)
        )
        response = request.execute()
        
        durations = {}
        for item in response.get('items', []):
            vid = item['id']
            iso_dur = item['contentDetails']['duration']
            parsed_dur = isodate.parse_duration(iso_dur)
            total_hours = parsed_dur.total_seconds() / 3600.0
            durations[vid] = round(total_hours, 2)
            
        return durations
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return {}

# ---------------------------------------------------------
# APP SCREEN 1: LOGIN PAGE
# ---------------------------------------------------------
if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center; color: #132338;'>⚡ PulseOps - Access Portal</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Unacademy Internal YouTube Audit & Operations Tool</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            user_id = st.text_input("Educator / Ops ID", placeholder="e.g. UNAC_58291")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Log In to Dashboard")
            
            if submit:
                if user_id in USER_DATABASE and USER_DATABASE[user_id] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.success("Authentication successful!")
                    st.rerun()
                else:
                    st.error("Invalid Credentials. Please check your Educator ID / Password.")
        
        st.info("🔒 **Need Access?** Mail your Educator ID to ops-support@deesaoriginals.com to generate your secure password.")

# ---------------------------------------------------------
# APP SCREEN 2: MAIN OPERATIONS DASHBOARD
# ---------------------------------------------------------
else:
    # Sidebar Header & Settings
    st.sidebar.image("https://img.icons8.com/color/96/youtube-play.png", width=50)
    st.sidebar.title("PulseOps Control")
    st.sidebar.write(f"Logged in as: **{st.session_state['user_id']}**")
    
    # API Key Input
    api_key = st.sidebar.text_input("YouTube API Key", type="password", help="Enter Google YouTube Data API v3 Key")
    
    if st.sidebar.button("Log Out"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = ""
        st.rerun()

    # Main Dashboard UI
    st.title("📹 YouTube Hours Reconciliation Engine")
    st.caption("Standardize links, auto-fetch duration, and split multi-teacher hours instantly.")
    
    st.markdown("---")
    
    # Step 1: Input URLs
    st.subheader("Step 1: Paste YouTube Links")
    raw_links_text = st.text_area(
        "Paste links here (One link per line). Direct /live/, /watch?v=, or /youtu.be/ all supported:",
        height=150,
        placeholder="https://www.youtube.com/live/abc12345\nhttps://youtu.be/xyz67890"
    )
    
    if st.button("🚀 Process & Fetch Durations"):
        if not api_key:
            st.warning("⚠️ Please enter a valid YouTube API Key in the left sidebar first!")
        elif not raw_links_text.strip():
            st.warning("⚠️ Please paste at least one YouTube link.")
        else:
            raw_links = [link.strip() for link in raw_links_text.split("\n") if link.strip()]
            
            cleaned_data = []
            video_ids = []
            
            for link in raw_links:
                vid_id = extract_video_id(link)
                if vid_id:
                    video_ids.append(vid_id)
                    clean_url = f"https://www.youtube.com/watch?v={vid_id}"
                    cleaned_data.append({"Raw": link, "VideoID": vid_id, "CleanURL": clean_url})
                else:
                    st.error(f"Invalid URL Skipped: {link}")
            
            if video_ids:
                with st.spinner("Fetching durations from YouTube API..."):
                    durations = get_video_durations_in_hours(api_key, video_ids)
                
                # Store in session state for dynamic table editing
                processed_rows = []
                for item in cleaned_data:
                    vid = item["VideoID"]
                    dur = durations.get(vid, 0.0)
                    processed_rows.append({
                        "Educator ID": st.session_state["user_id"],
                        "Cleaned YT Link": item["CleanURL"],
                        "Total Duration (Hrs)": dur,
                        "Teachers Count": 1
                    })
                
                st.session_state["processed_df"] = pd.DataFrame(processed_rows)

    # Step 2: Interactive Table & Allocation Adjustment
    if "processed_df" in st.session_state:
        st.markdown("---")
        st.subheader("Step 2: Verify & Adjust Multi-Teacher Splits")
        
        # Interactive Data Editor
        edited_df = st.data_editor(
            st.session_state["processed_df"],
            column_config={
                "Educator ID": st.column_config.TextColumn(disabled=True),
                "Cleaned YT Link": st.column_config.LinkColumn("YT Watch Link", disabled=True),
                "Total Duration (Hrs)": st.column_config.NumberColumn(format="%.2f hrs", disabled=True),
                "Teachers Count": st.column_config.SelectboxColumn(
                    "Teachers Count",
                    options=[1, 2, 3, 4],
                    help="Select number of educators who conducted this live stream"
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Calculate Final Split Hours
        edited_df["Allocated Hours"] = (edited_df["Total Duration (Hrs)"] / edited_df["Teachers Count"]).round(2)
        
        # Metrics Display
        st.markdown("<br>", unsafe_allow_html=True)
        col_m1, col_m2 = st.columns(2)
        
        total_videos = len(edited_df)
        total_hours = edited_df["Allocated Hours"].sum()
        
        col_m1.metric("Total Videos Processed", f"{total_videos} Videos")
        col_m2.metric("Total Reconciled Hours", f"{total_hours:.2f} Hours")
        
        # Final Sheet Prep for Export
        final_export_df = edited_df[["Educator ID", "Cleaned YT Link", "Allocated Hours"]]
        
        # Add Total Row at the bottom
        total_row = pd.DataFrame([{
            "Educator ID": "TOTAL",
            "Cleaned YT Link": "",
            "Allocated Hours": round(total_hours, 2)
        }])
        final_export_df_with_total = pd.concat([final_export_df, total_row], ignore_index=True)
        
        st.markdown("---")
        st.subheader("Step 3: Export Audit Sheet")
        
        csv_data = final_export_df_with_total.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Download Formatted Sheet (CSV)",
            data=csv_data,
            file_name=f"YT_Audit_{st.session_state['user_id']}.csv",
            mime="text/csv"
        )
