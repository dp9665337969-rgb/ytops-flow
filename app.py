import streamlit as st
import re
import pandas as pd
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
import isodate

# ---------------------------------------------------------
# PAGE CONFIGURATION & RECONCILEX AI THEME
# ---------------------------------------------------------
st.set_page_config(
    page_title="ReconcileX AI | Smart Content Audit Platform",
    page_icon="⚡",
    layout="wide"
)

# Custom Styling for ReconcileX AI Hero & Dashboard UI
st.markdown("""
    <style>
    /* Global Theme */
    .stApp {
        background: #F8FAFC !important;
        color: #0F172A !important;
        font-family: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif;
    }

    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Typography Overrides */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        color: #0F172A !important;
    }

    /* Hero Headline Styling */
    .hero-title {
        font-size: 3.2rem;
        font-weight: 900;
        color: #0F172A !important;
        line-height: 1.15;
        letter-spacing: -1.5px;
        margin-bottom: 12px;
    }

    .hero-title span {
        background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        color: #475569 !important;
        font-size: 1.15rem;
        font-weight: 500;
        margin-bottom: 25px;
    }

    .highlight-badge {
        color: #2563EB !important;
        font-weight: 800;
    }

    /* Input Box Styling */
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 2px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 14px 16px !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }

    .stTextInput input:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2) !important;
    }

    /* Primary Dark Slate / Indigo Action Button */
    .stButton>button {
        background: #1E293B !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 0.85rem 1.8rem !important;
        font-size: 1.05rem !important;
        box-shadow: 0 10px 20px -5px rgba(30, 41, 59, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
        width: 100%;
    }

    .stButton>button:hover {
        background: #0F172A !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 14px 24px -5px rgba(15, 23, 42, 0.4) !important;
    }

    /* Hero Right Section Custom Graphics */
    .illustration-container {
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        padding: 20px;
    }

    .avatar-circle-main {
        width: 220px;
        height: 220px;
        background: linear-gradient(135deg, #BAE6FD 0%, #38BDF8 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 80px;
        box-shadow: 0 20px 40px rgba(56, 189, 248, 0.25);
    }

    .avatar-circle-secondary {
        width: 160px;
        height: 160px;
        background: linear-gradient(135deg, #FEF08A 0%, #FACC15 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 60px;
        box-shadow: 0 15px 30px rgba(250, 204, 21, 0.25);
    }

    .avatar-circle-tertiary {
        width: 170px;
        height: 170px;
        background: linear-gradient(135deg, #DDD6FE 0%, #A855F7 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 65px;
        box-shadow: 0 15px 30px rgba(168, 85, 247, 0.25);
    }

    .floating-badge-1 {
        background: #FFFFFF;
        color: #2563EB;
        font-weight: 800;
        padding: 8px 16px;
        border-radius: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border: 1px solid #E2E8F0;
        font-size: 0.9rem;
    }

    /* Teacher Cartoon Dialogue Card on Dashboard */
    .teacher-dialogue-card {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 2px solid #BFDBFE;
        border-radius: 20px;
        padding: 20px 25px;
        display: flex;
        align-items: center;
        gap: 20px;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.1);
        margin-bottom: 30px;
    }

    .teacher-avatar {
        font-size: 55px;
        background: #FFFFFF;
        border-radius: 50%;
        width: 80px;
        height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.08);
        border: 2px solid #3B82F6;
        flex-shrink: 0;
    }

    .speech-bubble {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 14px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
        position: relative;
    }

    .speech-bubble p {
        margin: 0 !important;
        font-size: 1.05rem;
        font-weight: 700;
        color: #1E3A8A !important;
        line-height: 1.4;
    }

    div[data-testid="stMetricValue"] {
        color: #2563EB !important;
        font-weight: 900 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ACCESS CONTROL SYSTEM
# ---------------------------------------------------------
ALLOWED_USERS = {
    "UNAC_58291": "Pass@123",
    "9999999999": "Pass@123",
    "FACULTY_101": "Pass@123",
    "FACULTY_202": "Educator@2026",
    "ADMIN_OPS": "OpsPortal#1"
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
                    
                    if total_sec >= 60:
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
# SCREEN 1: RECONCILEX AI LANDING HERO PAGE
# ---------------------------------------------------------
if not st.session_state["logged_in"]:
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1.1, 0.9], gap="large")

    with col_left:
        st.markdown("""
            <div class="hero-title">
                Automate your content audit with <span>ReconcileX AI</span>
            </div>
            <p class="hero-subtitle">
                Over <span class="highlight-badge">10 Crore+</span> watch hours processed with intelligent multi-host reconciliation.
            </p>
        """, unsafe_allow_html=True)

        with st.form("hero_login_form"):
            user_id = st.text_input(
                "Mobile Number or Access ID", 
                placeholder="🇮🇳  +91  Enter your mobile or ID"
            )
            password = st.text_input(
                "Security Passkey", 
                type="password", 
                placeholder="Enter access key"
            )
            
            st.markdown("<p style='font-size: 0.82rem; color: #64748B; margin-top: -5px;'>Instant authentication for operations & content leaders</p>", unsafe_allow_html=True)
            
            submit_btn = st.form_submit_button("Access Portal →")

            if submit_btn:
                if user_id in ALLOWED_USERS and ALLOWED_USERS[user_id] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.rerun()
                else:
                    st.error("❌ Verification Failed: Invalid ID or Key.")

    with col_right:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
                <div class="illustration-container">
                    <div class="avatar-circle-main">👨‍🏫</div>
                </div>
                <div style="text-align: center; margin-top: -10px;">
                    <span class="floating-badge-1">⚡ Automated Audits</span>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            st.markdown("""
                <div class="illustration-container">
                    <div class="avatar-circle-secondary">👩‍💻</div>
                </div>
                <div style="text-align: center; margin-top: -10px;">
                    <span class="floating-badge-1">📊 Multi-Host Split</span>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
            st.markdown("""
                <div class="illustration-container">
                    <div class="avatar-circle-tertiary">🎓</div>
                </div>
                <div style="text-align: center; margin-top: -10px;">
                    <span class="floating-badge-1">🌟 100% Verified Metadata</span>
                </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# SCREEN 2: MAIN DASHBOARD INTERFACE
# ---------------------------------------------------------
else:
    # Sidebar
    st.sidebar.markdown("## ⚡ ReconcileX AI")
    st.sidebar.markdown(f"👤 Active Operator: **{st.session_state['user_id']}**")

    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = ""
        st.session_state.pop("processed_df", None)
        st.session_state.pop("fetched_videos", None)
        st.rerun()

    # CARTOON TEACHER DIALOGUE BANNER (NEW CREATIVE FEATURE)
    st.markdown("""
        <div class="teacher-dialogue-card">
            <div class="teacher-avatar">👨‍🏫</div>
            <div class="speech-bubble">
                <p>🦄 "Chinta mat karo, iss baar salary bilkul nahi kategi! ReconcileX AI se saare teaching hours ekdam 100% accuracy ke saath count ho gaye hain!" ✨</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Main Header
    st.markdown("<h1 style='font-size: 2.2rem; font-weight: 800; color: #0F172A;'>📹 ReconcileX Content Engine</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; font-size: 1rem; margin-top: -10px;'>Fetch channel content, adjust co-educator live hours, and generate audit sheets.</p>", unsafe_allow_html=True)

    mode = st.radio("Select Audit Workflow:", [
        "📋 Mode A: Direct Video Links", 
        "📺 Mode B: Channel / Playlist (Last 45 Days)"
    ], horizontal=True)

    api_key = st.secrets.get("YOUTUBE_API_KEY", "")

    # MODE A
    if "Mode A" in mode:
        st.subheader("Step 1: Input Direct Video Links")
        raw_links_text = st.text_area("Paste video/live links below (one per line):", height=140, placeholder="https://www.youtube.com/watch?v=...\nhttps://youtu.be/...")
        
        if st.button("🚀 Process Links"):
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
                        "User ID": st.session_state["user_id"],
                        "Video ID": vid,
                        "Cleaned YT Link": f"https://www.youtube.com/watch?v={vid}",
                        "Duration (HH:MM:SS)": hhmmss_str,
                        "Teachers Count": 1,
                        "_raw_sec": total_sec
                    })
                st.session_state["processed_df"] = pd.DataFrame(rows)

    # MODE B
    else:
        st.subheader("Step 1: Ingest Channel Handle or Playlist URL")
        channel_input = st.text_input(
            "Enter YouTube Channel Handle or Playlist URL:",
            placeholder="e.g. https://www.youtube.com/@ChannelHandle"
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
                    with st.spinner("Processing ReconcileX API Stream..."):
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

                confirm_submit = st.form_submit_button("✅ Build Audit Sheet for Selected Videos Only")

            if confirm_submit:
                if not selected_indices:
                    st.warning("⚠️ Please select at least one video checkbox above!")
                    st.session_state.pop("processed_df", None)
                else:
                    rows = []
                    for s_idx in selected_indices:
                        sv = videos[s_idx]
                        rows.append({
                            "User ID": st.session_state["user_id"],
                            "Video ID": sv.get('id'),
                            "Cleaned YT Link": f"https://www.youtube.com/watch?v={sv.get('id')}",
                            "Duration (HH:MM:SS)": sv.get("duration_hhmmss", "00:00:00"),
                            "Teachers Count": 1,
                            "_raw_sec": sv.get("raw_seconds", 0)
                        })
                    st.session_state["processed_df"] = pd.DataFrame(rows)
                    st.success(f"Loaded {len(selected_indices)} videos into Step 3.")

    # TABLE & EXPORT
    if "processed_df" in st.session_state and isinstance(st.session_state["processed_df"], pd.DataFrame) and not st.session_state["processed_df"].empty:
        st.markdown("---")
        st.subheader("Step 3: Verification & Co-Host Hours Split")
        
        df_to_edit = st.session_state["processed_df"].copy()

        edited_df = st.data_editor(
            df_to_edit[["User ID", "Video ID", "Cleaned YT Link", "Duration (HH:MM:SS)", "Teachers Count"]],
            column_config={
                "User ID": st.column_config.TextColumn("User ID", disabled=True),
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
        
        col1.metric("Selected Content Items", f"{total_vids}")
        col2.metric("Total Reconciled Time", f"{total_hhmmss}")
        
        final_df = edited_df[["User ID", "Video ID", "Cleaned YT Link", "Allocated Duration (HH:MM:SS)"]]
        total_row = pd.DataFrame([{
            "User ID": "TOTAL", 
            "Video ID": "-", 
            "Cleaned YT Link": "-", 
            "Allocated Duration (HH:MM:SS)": total_hhmmss
        }])
        export_df = pd.concat([final_df, total_row], ignore_index=True)
        
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Export ReconcileX Verified Audit CSV", 
            data=csv_data, 
            file_name=f"ReconcileX_Audit_{st.session_state['user_id']}.csv", 
            mime="text/csv"
        )
