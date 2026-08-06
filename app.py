import streamlit as st
import re
import pandas as pd
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
import isodate

# ---------------------------------------------------------
# PAGE CONFIGURATION & ULTRA-HIGH END SAAS THEME
# ---------------------------------------------------------
st.set_page_config(
    page_title="PulseOps | Ultra Enterprise Hub",
    page_icon="⚡",
    layout="wide"
)

# Deep Luxury SaaS CSS Styling
st.markdown("""
    <style>
    /* Global Base */
    .stApp, [data-testid="stSidebar"] {
        background: #090D16 !important;
        color: #F1F5F9 !important;
        font-family: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif;
    }
    
    /* Hide Streamlit Header Elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Typography */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        color: #F8FAFC !important;
    }

    /* Premium Neon Brand Header */
    .brand-header {
        font-size: 2.8rem;
        font-weight: 900;
        background: linear-gradient(135deg, #FF1E27 0%, #FF5252 50%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1.2px;
        margin-bottom: 0px;
    }

    .brand-subheader {
        color: #94A3B8 !important;
        font-size: 1.05rem;
        font-weight: 400;
        margin-bottom: 25px;
    }

    /* Glassmorphism Input Cards */
    .stTextInput input, .stTextArea textarea {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        border: 1px solid #1F2937 !important;
        border-radius: 14px !important;
        padding: 14px !important;
        font-size: 0.95rem;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #FF1E27 !important;
        box-shadow: 0 0 18px rgba(255, 30, 39, 0.35) !important;
    }

    /* Primary Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #FF1E27 0%, #D90429 100%) !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        border: none !important;
        padding: 0.75rem 1.6rem !important;
        box-shadow: 0 4px 22px rgba(255, 30, 39, 0.45) !important;
        transition: all 0.25s ease-in-out !important;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }

    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(255, 30, 39, 0.75) !important;
    }

    /* Sidebar Styling & Creator Badge */
    [data-testid="stSidebar"] {
        border-right: 1px solid #1E293B !important;
        padding-top: 2rem;
    }

    .sidebar-creator-card {
        background: linear-gradient(145deg, #111827 0%, #0F172A 100%);
        border: 1px solid #1E293B;
        border-left: 4px solid #38BDF8;
        padding: 16px;
        border-radius: 14px;
        margin-top: 15px;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }

    .sidebar-creator-card .label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748B;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .sidebar-creator-card .creator-name {
        font-size: 0.95rem;
        font-weight: 800;
        color: #38BDF8;
        text-decoration: none;
    }
    .sidebar-creator-card .creator-name:hover {
        color: #7DD3FC;
        text-decoration: underline;
    }

    /* Custom Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 34px !important;
        color: #38BDF8 !important;
        font-weight: 900 !important;
    }

    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }

    /* Radio Tabs Styling */
    div[role="radiogroup"] {
        background: #111827;
        padding: 6px;
        border-radius: 14px;
        border: 1px solid #1F2937;
        gap: 10px;
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
# HELPER FUNCTIONS
# ---------------------------------------------------------
def seconds_to_hhmmss(seconds):
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
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=45)
    
    try:
        next_page_token = None
        while len(all_videos) < 100:
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            temp_list = []
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
                    
                published_at_str = snippet.get('publishedAt')
                if published_at_str:
                    pub_date = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                    if pub_date < cutoff_date:
                        continue

                seen_ids.add(v_id)
                thumbnails = snippet.get('thumbnails', {})
                thumb_url = thumbnails.get('medium', {}).get('url') or thumbnails.get('default', {}).get('url', '')
                
                temp_list.append({
                    "id": v_id,
                    "title": title,
                    "thumbnail": thumb_url
                })
                v_ids.append(v_id)

            if v_ids:
                details = youtube.videos().list(
                    part="contentDetails",
                    id=",".join(v_ids)
                ).execute()
                
                durations_map = {}
                for d_item in details.get('items', []):
                    vid = d_item['id']
                    iso_dur = d_item['contentDetails']['duration']
                    sec = isodate.parse_duration(iso_dur).total_seconds()
                    durations_map[vid] = sec

                for item in temp_list:
                    vid_id = item["id"]
                    total_sec = durations_map.get(vid_id, 0)
                    
                    if total_sec >= 60: # Filter Shorts (<60s)
                        item["duration_hhmmss"] = seconds_to_hhmmss(total_sec)
                        item["raw_seconds"] = total_sec
                        all_videos.append(item)

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

    except Exception as e:
        st.error(f"API Fetch Error: {str(e)}")
        
    return all_videos

# ---------------------------------------------------------
# SCREEN 1: LOGIN PORTAL
# ---------------------------------------------------------
if not st.session_state["logged_in"]:
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;' class='brand-header'>🔴 PulseOps Engine</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;' class='brand-subheader'>Enterprise YouTube Verification & Operations Suite</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center; font-weight: 800;'>🔐 Authorized Sign In</h3>", unsafe_allow_html=True)
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
                    st.error("❌ Authentication Failed: Invalid Credentials.")

        st.markdown("""
            <div style="text-align: center; margin-top: 20px;">
                <span style="color: #64748B; font-size: 0.85rem;">Engineered by</span> 
                <a href="https://instagram.com/deepak_patil_7979" target="_blank" style="color: #38BDF8; font-weight: 700; text-decoration: none;">@deepak_patil_7979</a>
            </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# SCREEN 2: MAIN DASHBOARD
# ---------------------------------------------------------
else:
    # Sidebar
    st.sidebar.markdown("## 🔴 PulseOps Hub")
    st.sidebar.markdown(f"👤 Active Operator: **{st.session_state['user_id']}**")
    
    # Creator Badge in Sidebar
    st.sidebar.markdown("""
        <div class="sidebar-creator-card">
            <div class="label">Platform Developer</div>
            <a class="creator-name" href="https://instagram.com/deepak_patil_7979" target="_blank">
                ⚡ Created by @deepak_patil_7979
            </a>
        </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Secure Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = ""
        st.session_state.pop("processed_df", None)
        st.session_state.pop("fetched_videos", None)
        st.rerun()

    # Main Header
    st.markdown("<h1 class='brand-header'>📹 YouTube Audit & Reconciliation</h1>", unsafe_allow_html=True)
    st.markdown("<p class='brand-subheader'>Extract long-form content, perform split calculations, and export verified HH:MM:SS sheets.</p>", unsafe_allow_html=True)

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
                req = youtube.videos().list(part="contentDetails", id=",".join(v_ids)).execute()
                
                rows = []
                for item in req.get('items', []):
                    vid = item['id']
                    iso_dur = item['contentDetails']['duration']
                    total_sec = isodate.parse_duration(iso_dur).total_seconds()
                    
                    if total_sec < 60:
                        continue
                        
                    hhmmss_str = seconds_to_hhmmss(total_sec)
                    
                    rows.append({
                        "Educator ID": st.session_state["user_id"],
                        "Video ID": vid,
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
            "Enter YouTube Channel Handle or Playlist URL:",
            placeholder="e.g. https://www.youtube.com/@UnacademyNEET"
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
                        # Clear old state completely
                        for k in list(st.session_state.keys()):
                            if k.startswith("chk_"):
                                del st.session_state[k]
                        st.session_state.pop("processed_df", None)
                        st.session_state["fetched_videos"] = fetch_videos_last_45_days(api_key, target_playlist_id)

        if "fetched_videos" in st.session_state and st.session_state["fetched_videos"]:
            st.markdown("---")
            st.subheader("Step 2: Select Videos for Audit")
            videos = st.session_state["fetched_videos"]
            st.info(f"Found **{len(videos)}** long-form items from last 45 days. Select items to include:")
            
            # Form to prevent auto-refreshing state mid-selection
            with st.form("video_selection_form"):
                selected_indices = []
                for idx, vid in enumerate(videos):
                    c1, c2, c3 = st.columns([0.3, 1.2, 4])
                    
                    chk_key = f"chk_{vid.get('id')}_{idx}"
                    chk = c1.checkbox("", key=chk_key, value=False)
                    
                    c2.image(vid.get("thumbnail", ""), width=110)
                    
                    duration_display = vid.get("duration_hhmmss", "00:00:00")
                    c3.markdown(f"**{vid.get('title', 'Video')}**\n\n⏱️ Duration: `{duration_display}` | 🔗 [Open Link](https://www.youtube.com/watch?v={vid.get('id')})")
                    
                    if chk:
                        selected_indices.append(idx)

                confirm_submit = st.form_submit_button("✅ Confirm Selected Videos & Build Audit Sheet")

            if confirm_submit:
                if not selected_indices:
                    st.warning("⚠️ Pehle kam se kam ek video select karo!")
                    st.session_state.pop("processed_df", None)
                else:
                    rows = []
                    for s_idx in selected_indices:
                        sv = videos[s_idx]
                        rows.append({
                            "Educator ID": st.session_state["user_id"],
                            "Video ID": sv.get('id'),
                            "Cleaned YT Link": f"https://www.youtube.com/watch?v={sv.get('id')}",
                            "Duration (HH:MM:SS)": sv.get("duration_hhmmss", "00:00:00"),
                            "Teachers Count": 1,
                            "_raw_sec": sv.get("raw_seconds", 0)
                        })
                    st.session_state["processed_df"] = pd.DataFrame(rows)
                    st.success(f"Success! {len(selected_indices)} videos loaded into Step 3.")

    # TABLE & EXPORT
    if "processed_df" in st.session_state and isinstance(st.session_state["processed_df"], pd.DataFrame) and not st.session_state["processed_df"].empty:
        st.markdown("---")
        st.subheader("Step 3: Verification & Co-Educator Hours Split")
        
        df_to_edit = st.session_state["processed_df"].copy()

        edited_df = st.data_editor(
            df_to_edit[["Educator ID", "Video ID", "Cleaned YT Link", "Duration (HH:MM:SS)", "Teachers Count"]],
            column_config={
                "Educator ID": st.column_config.TextColumn("Educator ID", disabled=True),
                "Video ID": st.column_config.TextColumn("Video ID", disabled=True),
                "Cleaned YT Link": st.column_config.LinkColumn("YT Link", disabled=True),
                "Duration (HH:MM:SS)": st.column_config.TextColumn("Duration (HH:MM:SS)", disabled=True),
                "Teachers Count": st.column_config.SelectboxColumn("Teachers Count", options=[1, 2, 3, 4])
            },
            hide_index=True,
            use_container_width=True
        )
        
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
        
        final_df = edited_df[["Educator ID", "Video ID", "Cleaned YT Link", "Allocated Duration (HH:MM:SS)"]]
        total_row = pd.DataFrame([{
            "Educator ID": "TOTAL", 
            "Video ID": "-", 
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
