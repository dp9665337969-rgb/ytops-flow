import streamlit as st
import re
import pandas as pd
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
import isodate

# ---------------------------------------------------------
# PAGE CONFIGURATION & NEXT-GEN SAAS THEME
# ---------------------------------------------------------
st.set_page_config(
    page_title="PulseOps | YouTube Enterprise Audit Hub",
    page_icon="🔴",
    layout="wide"
)

# Advanced High-Contrast SaaS UI CSS with YouTube Branding
st.markdown("""
    <style>
    /* Global Theme Overrides */
    .stApp, [data-testid="stSidebar"] {
        background: radial-gradient(circle at 50% 0%, #0F172A 0%, #020617 100%) !important;
        color: #F8FAFC !important;
        font-family: 'Inter', system-ui, sans-serif;
    }
    
    /* Typography High Contrast */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        color: #F8FAFC !important;
    }

    /* Gradient Brand Header */
    .brand-header {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #FF0000 0%, #FF5252 50%, #00F2FE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }

    .brand-subheader {
        color: #94A3B8 !important;
        font-size: 1.05rem;
        font-weight: 400;
    }

    /* Glassmorphism Input Cards */
    .stTextInput input, .stTextArea textarea {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #FF0000 !important;
        box-shadow: 0 0 15px rgba(255, 0, 0, 0.3) !important;
    }

    /* Action Buttons with YouTube Red Glow */
    .stButton>button {
        background: linear-gradient(135deg, #FF0000 0%, #CC0000 100%) !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        border: none !important;
        padding: 0.7rem 1.5rem !important;
        box-shadow: 0 4px 20px rgba(255, 0, 0, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(255, 0, 0, 0.7) !important;
    }

    /* Metrics Cards */
    div[data-testid="stMetricValue"] {
        font-size: 32px;
        color: #38BDF8 !important;
        font-weight: 900;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
    }

    /* Sidebar Badge */
    .sidebar-brand-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 0, 0, 0.3);
        padding: 15px;
        border-radius: 16px;
        text-align: center;
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }

    /* Credit Badge */
    .credit-badge {
        margin-top: 2rem;
        text-align: center;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 10px 20px;
        border-radius: 50px;
        font-size: 0.9rem;
        color: #E2E8F0;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .credit-badge a {
        color: #38BDF8;
        font-weight: 700;
        text-decoration: none;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ACCESS CONTROL SYSTEM
# ---------------------------------------------------------
ALLOWED_FACULTY = {
    "UNAC_58291": "Pass@123",
    "UNAC_10021": "Educator@2026",
    "ADMIN_OPS": "UnacademyOps#1"
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""

# ---------------------------------------------------------
# HELPER FUNCTIONS FOR DURATION & API
# ---------------------------------------------------------
def seconds_to_hhmmss(seconds):
    """ Converts total seconds to exact HH:MM:SS format for Excel mapping """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def extract_video_id(url):
    regex = r"(?:v=|\/([0-9A-Za-z_-]{11}).*|list=|\/live\/|\/shorts\/)([0-9A-Za-z_-]{11})"
    match = re.search(regex, url)
    return match.group(1) or match.group(2) if match else None

def extract_playlist_id(url):
    match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None

def get_channel_uploads_playlist_id(api_key, channel_input):
    youtube = build('youtube', 'v3', developerKey=api_key)
    try:
        if "@" in channel_input:
            handle = channel_input.split("@")[-1].split("/")[0]
            req = youtube.channels().list(part="contentDetails", forHandle=handle)
        else:
            ch_id = channel_input.split("/")[-1]
            req = youtube.channels().list(part="contentDetails", id=ch_id)
            
        res = req.execute()
        if res.get('items'):
            return res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except Exception as e:
        st.error(f"Channel Fetch Error: {str(e)}")
    return None

def fetch_videos_last_45_days(api_key, playlist_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    all_videos = []
    seen_ids = set()
    
    # 45 Days Threshold Calculation
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=45)
    
    try:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50
        )
        response = request.execute()
        
        temp_vids = []
        v_ids = []
        
        for item in response.get('items', []):
            snippet = item.get('snippet', {})
            content = item.get('contentDetails', {})
            v_id = content.get('videoId')
            
            if not v_id or v_id in seen_ids:
                continue
                
            title = snippet.get('title', 'Untitled')
            if title in ["Private video", "Deleted video"]:
                continue
                
            # Filter publish date (Last 45 days)
            published_at_str = snippet.get('publishedAt')
            if published_at_str:
                pub_date = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                if pub_date < cutoff_date:
                    continue

            seen_ids.add(v_id)
            thumbnails = snippet.get('thumbnails', {})
            thumb_url = thumbnails.get('medium', {}).get('url') or thumbnails.get('default', {}).get('url', '')
            
            temp_vids.append({
                "id": v_id,
                "title": title,
                "thumbnail": thumb_url
            })
            v_ids.append(v_id)

        if v_ids:
            # Fetch Durations & filter out Shorts (<60s)
            details = youtube.videos().list(
                part="contentDetails,snippet",
                id=",".join(v_ids)
            ).execute()
            
            for item in details.get('items', []):
                vid = item['id']
                iso_dur = item['contentDetails']['duration']
                parsed_dur = isodate.parse_duration(iso_dur)
                total_seconds = parsed_dur.total_seconds()
                
                # Exclude Shorts (under 60 seconds)
                if total_seconds < 60:
                    continue
                    
                hhmmss_str = seconds_to_hhmmss(total_seconds)
                
                for tv in temp_vids:
                    if tv["id"] == vid:
                        tv["duration_hhmmss"] = hhmmss_str
                        tv["raw_seconds"] = total_seconds
                        all_videos.append(tv)
                        break

    except Exception as e:
        st.error(f"API Error: {str(e)}")
        
    return all_videos

# ---------------------------------------------------------
# SCREEN 1: LOGIN PORTAL
# ---------------------------------------------------------
if not st.session_state["logged_in"]:
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;' class='brand-header'>🔴 PulseOps Engine</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;' class='brand-subheader'>Secure YouTube Content Operations & Verification Suite</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center; color: #FFFFFF;'>🔐 Authorized Faculty Sign In</h3>", unsafe_allow_html=True)
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            user_id = st.text_input("Educator / Admin ID", placeholder="e.g. UNAC_58291")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("Access Portal →")
            
            if submit:
                if user_id in ALLOWED_FACULTY and ALLOWED_FACULTY[user_id] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.rerun()
                else:
                    st.error("❌ Authentication Failed: Unrecognized ID or Password.")

        st.markdown("""
            <div style="text-align: center;">
                <div class="credit-badge">
                    Engineered with ⚡ by <a href="https://instagram.com/deepak_patil_7979" target="_blank">@deepak_patil_7979</a>
                </div>
            </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# SCREEN 2: MAIN DASHBOARD
# ---------------------------------------------------------
else:
    # Sidebar
    st.sidebar.markdown("### 🔴 PulseOps Control")
    st.sidebar.markdown(f"👤 Operator: **{st.session_state['user_id']}**")
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("""
        <div class="sidebar-brand-card">
            <span style="font-size: 24px;">📺🔴</span><br>
            <strong style="color: #38BDF8;">API Status: Active</strong><br>
            <small style="color: #94A3B8;">Duration Format: HH:MM:SS</small>
        </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Secure Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = ""
        st.session_state.pop("processed_df", None)
        st.session_state.pop("fetched_videos", None)
        st.rerun()

    # Main Header
    st.markdown("<h1 class='brand-header'>📹 YouTube Audit & Reconciliation Hub</h1>", unsafe_allow_html=True)
    st.markdown("<p class='brand-subheader'>Extract long-form videos & live streams from last 45 days, manage co-educator splits, and export HH:MM:SS Excel sheets.</p>", unsafe_allow_html=True)
    st.markdown("---")

    mode = st.radio("Select Workflow Mode:", [
        "📋 Mode A: Direct Video Links", 
        "📺 Mode B: Channel / Playlist (Last 45 Days)"
    ], horizontal=True)

    api_key = st.secrets.get("YOUTUBE_API_KEY", "")

    # MODE A: DIRECT LINKS
    if "Mode A" in mode:
        st.subheader("Step 1: Input Direct YouTube Links")
        raw_links_text = st.text_area("Paste video/live links below (one per line):", height=140, placeholder="https://www.youtube.com/watch?v=...\nhttps://youtu.be/...")
        
        if st.button("🚀 Process Direct Links"):
            if not api_key:
                st.error("API Key missing in Secrets!")
            elif raw_links_text.strip():
                links = [l.strip() for l in raw_links_text.split("\n") if l.strip()]
                v_ids = [extract_video_id(l) for l in links if extract_video_id(l)]
                
                youtube = build('youtube', 'v3', developerKey=api_key)
                req = youtube.videos().list(part="snippet,contentDetails", id=",".join(v_ids)).execute()
                
                rows = []
                for item in req.get('items', []):
                    vid = item['id']
                    title = item['snippet']['title']
                    
                    iso_dur = item['contentDetails']['duration']
                    total_sec = isodate.parse_duration(iso_dur).total_seconds()
                    
                    if total_sec < 60:
                        continue # Skip shorts
                        
                    hhmmss_str = seconds_to_hhmmss(total_sec)
                    
                    rows.append({
                        "Educator ID": st.session_state["user_id"],
                        "Video ID": vid,
                        "Video Title": title,
                        "Cleaned YT Link": f"https://www.youtube.com/watch?v={vid}",
                        "Duration (HH:MM:SS)": hhmmss_str,
                        "Teachers Count": 1,
                        "_raw_sec": total_sec
                    })
                st.session_state["processed_df"] = pd.DataFrame(rows)

    # MODE B: CHANNEL / PLAYLIST (LAST 45 DAYS)
    else:
        st.subheader("Step 1: Ingest Channel Handle or Playlist URL")
        channel_input = st.text_input(
            "Enter YouTube Channel Handle (e.g. @UnacademyNEET) or Playlist URL:",
            placeholder="https://www.youtube.com/@UnacademyNEET"
        )
        
        if st.button("🔍 Fetch Last 45 Days Videos & Lives"):
            if not api_key:
                st.error("API Key missing in Secrets!")
            elif not channel_input.strip():
                st.error("Please enter a valid channel handle or playlist URL!")
            else:
                target_playlist_id = None
                if "list=" in channel_input:
                    target_playlist_id = extract_playlist_id(channel_input)
                else:
                    target_playlist_id = get_channel_uploads_playlist_id(api_key, channel_input)

                if not target_playlist_id:
                    st.error("Could not resolve channel uploads or playlist ID!")
                else:
                    with st.spinner("Scanning YouTube Data API (Filtering Shorts & >45 Days items)..."):
                        st.session_state["fetched_videos"] = fetch_videos_last_45_days(api_key, target_playlist_id)

        if "fetched_videos" in st.session_state and st.session_state["fetched_videos"]:
            st.markdown("---")
            st.subheader("Step 2: Select Videos for Audit (Last 45 Days)")
            videos = st.session_state["fetched_videos"]
            st.info(f"Found **{len(videos)}** eligible items (Shorts excluded). Select items to include:")
            
            selected_videos = []
            for idx, vid in enumerate(videos):
                c1, c2, c3 = st.columns([0.3, 1.2, 4])
                chk = c1.checkbox("", key=f"vid_{idx}", value=True)
                c2.image(vid["thumbnail"], width=100)
                c3.markdown(f"**{vid['title']}**\n\n⏱️ Duration: `{vid['duration_hhmmss']}` | 🔗 [Open Link](https://www.youtube.com/watch?v={vid['id']})")
                
                if chk:
                    selected_videos.append(vid)

            if st.button("✅ Confirm Selection & Build Audit Sheet"):
                rows = []
                for sv in selected_videos:
                    rows.append({
                        "Educator ID": st.session_state["user_id"],
                        "Video ID": sv['id'],
                        "Video Title": sv['title'],
                        "Cleaned YT Link": f"https://www.youtube.com/watch?v={sv['id']}",
                        "Duration (HH:MM:SS)": sv["duration_hhmmss"],
                        "Teachers Count": 1,
                        "_raw_sec": sv["raw_seconds"]
                    })
                st.session_state["processed_df"] = pd.DataFrame(rows)

    # TABLE & EXPORT
    if "processed_df" in st.session_state and isinstance(st.session_state["processed_df"], pd.DataFrame) and not st.session_state["processed_df"].empty:
        st.markdown("---")
        st.subheader("Step 3: Verification & Co-Educator Hours Split")
        
        df_to_edit = st.session_state["processed_df"].copy()

        edited_df = st.data_editor(
            df_to_edit[["Educator ID", "Video ID", "Video Title", "Cleaned YT Link", "Duration (HH:MM:SS)", "Teachers Count"]],
            column_config={
                "Educator ID": st.column_config.TextColumn("Educator ID", disabled=True),
                "Video ID": st.column_config.TextColumn("Video ID", disabled=True),
                "Video Title": st.column_config.TextColumn("Video Title", disabled=True),
                "Cleaned YT Link": st.column_config.LinkColumn("YT Link", disabled=True),
                "Duration (HH:MM:SS)": st.column_config.TextColumn("Duration (HH:MM:SS)", disabled=True),
                "Teachers Count": st.column_config.SelectboxColumn("Teachers Count", options=[1, 2, 3, 4])
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Calculate split per teacher in HH:MM:SS
        split_durations = []
        tot_seconds = 0
        
        for idx, row in edited_df.iterrows():
            raw_sec = df_to_edit.loc[idx, "_raw_sec"]
            teachers = row["Teachers Count"]
            allocated_sec = raw_sec / teachers
            tot_seconds += allocated_sec
            split_durations.append(seconds_to_hhmmss(allocated_sec))

        edited_df["Allocated Duration (HH:MM:SS)"] = split_durations
        
        col1, col2 = st.columns(2)
        total_vids = len(edited_df)
        total_hhmmss = seconds_to_hhmmss(tot_seconds)
        
        col1.metric("Selected Videos / Lives", f"{total_vids}")
        col2.metric("Total Reconciled Time", f"{total_hhmmss}")
        
        final_df = edited_df[["Educator ID", "Video ID", "Video Title", "Cleaned YT Link", "Allocated Duration (HH:MM:SS)"]]
        total_row = pd.DataFrame([{
            "Educator ID": "TOTAL", 
            "Video ID": "-", 
            "Video Title": "-", 
            "Cleaned YT Link": "-", 
            "Allocated Duration (HH:MM:SS)": total_hhmmss
        }])
        export_df = pd.concat([final_df, total_row], ignore_index=True)
        
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Export Standard CSV Audit Sheet", 
            data=csv_data, 
            file_name=f"YT_Audit_HHMMSS_{st.session_state['user_id']}.csv", 
            mime="text/csv"
        )
