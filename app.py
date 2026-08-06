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

    /* TOP DIALOGUE BANNER */
    .hero-dialogue-card {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 2px solid #BFDBFE;
        border-radius: 20px;
        padding: 20px 25px;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.1);
        margin-bottom: 25px;
    }

    .dialogue-wrapper {
        display: flex;
        align-items: center;
        justify-content: space-around;
        gap: 15px;
        flex-wrap: wrap;
    }

    .teacher-box {
        display: flex;
        align-items: center;
        gap: 12px;
        background: #FFFFFF;
        padding: 12px 18px;
        border-radius: 16px;
        border: 1px solid #CBD5E1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        max-width: 45%;
    }

    .teacher-avatar-icon {
        font-size: 40px;
        background: #F1F5F9;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .dialogue-text {
        font-size: 1rem;
        font-weight: 700;
        margin: 0 !important;
        line-height: 1.3;
    }

    .worried-text { color: #DC2626 !important; }
    .smart-text { color: #1E40AF !important; }

    /* Hero Headline Styling */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 900;
        color: #0F172A !important;
        line-height: 1.2;
        letter-spacing: -1px;
        text-align: center;
        margin-bottom: 8px;
    }

    .hero-title span {
        background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        color: #475569 !important;
        font-size: 1rem;
        font-weight: 500;
        text-align: center;
        margin-bottom: 25px;
    }

    /* Input Box Styling */
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 2px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 12px 14px !important;
        font-size: 0.95rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }

    /* PURE WHITE TEXT FOR ALL BUTTONS */
    .stButton>button, .stDownloadButton>button {
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

    .stButton>button *, .stDownloadButton>button * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    .stButton>button:hover, .stDownloadButton>button:hover {
        background: #0F172A !important;
        transform: translateY(-2px) !important;
    }

    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 40px; margin-bottom: 20px;">
        <span style="color: #64748B; font-weight: 600; font-size: 0.95rem;">Made by</span>
        <a href="https://instagram.com/deepak_patil_7979" target="_blank" style="display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color: white !important; padding: 6px 14px; border-radius: 20px; text-decoration: none; font-weight: 700; font-size: 0.9rem; box-shadow: 0 4px 10px rgba(220, 39, 67, 0.25);">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
            </svg>
            @deepak_patil_7979
        </a>
    </div>
""", unsafe_allow_html=True)
    /* BADGE CARDS ON LEFT AND RIGHT OF LOGIN */
    .badge-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }

    .badge-icon {
        font-size: 45px;
        margin-bottom: 8px;
    }

    .badge-title {
        font-size: 0.95rem;
        font-weight: 800;
        color: #1E293B !important;
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
    
    # 1. TOP DIALOGUE BANNER (CRISP & SHORT UNDER 10 WORDS)
    st.markdown("""
        <div class="hero-dialogue-card">
            <div class="dialogue-wrapper">
                <div class="teacher-box">
                    <div class="teacher-avatar-icon">👨‍🏫</div>
                    <p class="dialogue-text worried-text">"Arey sir! Full padhaya, fir bhi salary me cut lag gaya!"</p>
                </div>
                <div style="font-size: 28px; font-weight: 900; color: #2563EB;">⚡</div>
                <div class="teacher-box">
                    <div class="teacher-avatar-icon">👨‍🏫🦄</div>
                    <p class="dialogue-text smart-text">"Arey sir! ReconcileX AI use karo, zero salary cut hoga!"</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="hero-title">Automate content audit with <span>ReconcileX AI</span></div>
        <div class="hero-subtitle">10 Crore+ watch hours reconciled with 100% precision.</div>
    """, unsafe_allow_html=True)

    # 2. CENTERED LOGIN WITH 2 LEFT BADGES & 2 RIGHT BADGES
    col_left, col_center, col_right = st.columns([1, 1.2, 1], gap="medium")

    with col_left:
        st.markdown("""
            <div class="badge-card">
                <div class="badge-icon">⚡</div>
                <div class="badge-title">Automated Audits</div>
            </div>
            <div class="badge-card">
                <div class="badge-icon">📊</div>
                <div class="badge-title">Multi-Host Split Engine</div>
            </div>
        """, unsafe_allow_html=True)

    with col_center:
        with st.form("hero_login_form"):
            st.markdown("<h3 style='text-align: center; margin-bottom: 15px;'>Portal Login</h3>", unsafe_allow_html=True)
            user_id = st.text_input(
                "Mobile Number / Access ID", 
                placeholder="UNAC_58291"
            )
            password = st.text_input(
                "Passkey", 
                type="password", 
                placeholder="Enter key"
            )
            
            submit_btn = st.form_submit_button("Access Portal →")

            if submit_btn:
                if user_id in ALLOWED_USERS and ALLOWED_USERS[user_id] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.rerun()
                else:
                    st.error("❌ Invalid Credentials")

    with col_right:
        st.markdown("""
            <div class="badge-card">
                <div class="badge-icon">🌟</div>
                <div class="badge-title">100% Verified Metadata</div>
            </div>
            <div class="badge-card">
                <div class="badge-icon">🛡️</div>
                <div class="badge-title">Zero Salary Cut Guarantee</div>
            </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# SCREEN 2: MAIN DASHBOARD INTERFACE
# ---------------------------------------------------------
else:
    st.success("🎉 Sir, chinta mat karo es baar aapki salary nahi kategi!")

    # Sidebar
    st.sidebar.markdown("## ⚡ ReconcileX AI")
    st.sidebar.markdown(f"👤 Active Operator: **{st.session_state['user_id']}**")

    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = "deepak_patil_7979"
        st.session_state.pop("processed_df", None)
        st.session_state.pop("fetched_videos", None)
        st.rerun()

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
            st.subheader("Step 2: Select Videos & Set Educator Count")
            videos = st.session_state["fetched_videos"]
            st.info(f"Found **{len(videos)}** long-form items from last 45 days. Select items and set educator count:")
            
            with st.form("video_selection_form"):
                selected_indices = []
                educator_counts = {}

                for idx, vid in enumerate(videos):
                    c1, c2, c3, c4 = st.columns([0.3, 1.2, 3.2, 1.3])
                    
                    chk_key = f"chk_{vid.get('id')}_{idx}"
                    chk = c1.checkbox("", key=chk_key, value=False)
                    
                    c2.image(vid.get("thumbnail", ""), width=110)
                    
                    duration_display = vid.get("duration_hhmmss", "00:00:00")
                    c3.markdown(f"**{vid.get('title', 'Video')}**\n\n⏱️ Duration: `{duration_display}` | 🔗 [Open Link](https://www.youtube.com/watch?v={vid.get('id')})")
                    
                    # Educator Count Selection Box (Defaults to 1)
                    t_count = c4.number_input(
                        "Educators Count", 
                        min_value=1, 
                        max_value=10, 
                        value=1, 
                        key=f"num_{vid.get('id')}_{idx}"
                    )
                    
                    if chk:
                        selected_indices.append(idx)
                        educator_counts[idx] = t_count

                confirm_submit = st.form_submit_button("✅ Build Audit Sheet for Selected Videos Only")

            if confirm_submit:
                if not selected_indices:
                    st.warning("⚠️ Please select at least one video checkbox above!")
                    st.session_state.pop("processed_df", None)
                else:
                    rows = []
                    for s_idx in selected_indices:
                        sv = videos[s_idx]
                        raw_sec = sv.get("raw_seconds", 0)
                        t_cnt = educator_counts.get(s_idx, 1)
                        allocated_sec = raw_sec / t_cnt
                        
                        rows.append({
                            "User ID": st.session_state["user_id"],
                            "Video ID": sv.get('id'),
                            "Cleaned YT Link": f"https://www.youtube.com/watch?v={sv.get('id')}",
                            "Original Duration": sv.get("duration_hhmmss", "00:00:00"),
                            "Teachers Count": t_cnt,
                            "Allocated Duration (HH:MM:SS)": seconds_to_hhmmss(allocated_sec),
                            "_allocated_sec": allocated_sec
                        })
                    st.session_state["processed_df"] = pd.DataFrame(rows)
                    st.success(f"Loaded {len(selected_indices)} videos into Step 3 with precise educator split.")

# TABLE & EXPORT
    if "processed_df" in st.session_state and isinstance(st.session_state["processed_df"], pd.DataFrame) and not st.session_state["processed_df"].empty:
        st.markdown("---")
        st.subheader("Step 3: Verification & Co-Host Hours Split Sheet")
        
        # ---------------------------------------------------------
        # NEW REASSURANCE BANNER FOR FACULTY / USER
        # ---------------------------------------------------------
        st.markdown("""
            <div style="
                background: linear-gradient(135deg, #DCFCE7 0%, #BBF7D0 100%);
                border: 2px solid #86EFAC;
                border-radius: 16px;
                padding: 16px 20px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 15px;
                box-shadow: 0 4px 12px rgba(22, 101, 52, 0.08);
            ">
                <div style="font-size: 32px; flex-shrink: 0;">🎉</div>
                <div>
                    <h4 style="color: #14532D !important; margin: 0 0 4px 0 !important; font-weight: 800; font-size: 1.1rem;">
                        Chinta mat karo, es baar aapki salary nahi kategi!
                    </h4>
                    <p style="color: #166534 !important; margin: 0 !important; font-size: 0.9rem; font-weight: 500;">
                        Aapke sabhi live hours aur videos ReconcileX AI dwaara 100% precision ke saath audit ho chuke hain.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        # ---------------------------------------------------------

        df_display = st.session_state["processed_df"].copy()

        st.dataframe(
            df_display[["User ID", "Video ID", "Cleaned YT Link", "Original Duration", "Teachers Count", "Allocated Duration (HH:MM:SS)"]],
            column_config={
                "User ID": st.column_config.TextColumn("User ID"),
                "Video ID": st.column_config.TextColumn("Video ID"),
                "Cleaned YT Link": st.column_config.LinkColumn("YT Link"),
                "Original Duration": st.column_config.TextColumn("Original Duration"),
                "Teachers Count": st.column_config.NumberColumn("Teachers Count"),
                "Allocated Duration (HH:MM:SS)": st.column_config.TextColumn("Allocated Duration (HH:MM:SS)")
            },
            hide_index=True,
            use_container_width=True
        )
        
        tot_seconds = df_display["_allocated_sec"].sum()
        total_vids = len(df_display)
        total_hhmmss = seconds_to_hhmmss(tot_seconds)
        
        col1, col2 = st.columns(2)
        col1.metric("Selected Content Items", f"{total_vids}")
        col2.metric("Total Reconciled Time (Post-Split)", f"{total_hhmmss}")
        
        final_df = df_display[["User ID", "Video ID", "Cleaned YT Link", "Allocated Duration (HH:MM:SS)"]]
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
