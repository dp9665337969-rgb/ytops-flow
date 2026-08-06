import streamlit as st
import re
import pandas as pd
from googleapiclient.discovery import build
import isodate

# ---------------------------------------------------------
# PAGE CONFIGURATION & NEXT-GEN SAAS THEME
# ---------------------------------------------------------
st.set_page_config(
    page_title="PulseOps | YouTube Audit & Hours Engine",
    page_icon="⚡",
    layout="wide"
)

# Forceful High-Contrast CSS Overrides for Both Main Area and Sidebar
st.markdown("""
    <style>
    /* Global Background & Base Colors */
    .stApp, [data-testid="stSidebar"] {
        background-color: #090D16 !important;
        color: #F9FAFB !important;
        font-family: 'Inter', system-ui, sans-serif;
    }
    
    /* Main Header Styling */
    .app-title {
        font-size: 2.8rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }

    .app-subtitle {
        color: #9CA3AF !important;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    /* Force all text labels and headings to High-Contrast Pure White */
    p, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #FFFFFF !important;
    }

    /* Radio buttons & text visibility fixes */
    div[data-aria-selected="true"] {
        color: #00F2FE !important;
    }

    /* Input & Textarea Dark High-Contrast Style */
    .stTextInput input, .stTextArea textarea {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        border: 1px solid #374151 !important;
        border-radius: 12px !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #00F2FE !important;
        box-shadow: 0 0 10px rgba(0, 242, 254, 0.4) !important;
    }

    /* Neon Gradient Glow Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #00F2FE 0%, #0072FF 100%) !important;
        color: #000000 !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        border: none !important;
        padding: 0.6rem 1.4rem !important;
        box-shadow: 0 4px 15px rgba(0, 242, 254, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }

    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.6) !important;
    }

    /* Metric Card Custom UI */
    div[data-testid="stMetricValue"] {
        font-size: 30px;
        color: #00F2FE !important;
        font-weight: 800;
    }

    /* Sidebar Custom Glass Card */
    .sidebar-card {
        background: rgba(17, 24, 39, 0.8);
        border: 1px solid rgba(0, 242, 254, 0.2);
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 15px;
        text-align: center;
    }

    /* Developer Credit Badge */
    .login-credit-badge {
        margin-top: 1rem;
        text-align: center;
        background: rgba(17, 24, 39, 0.9);
        border: 1px solid rgba(0, 242, 254, 0.3);
        padding: 10px 18px;
        border-radius: 50px;
        font-size: 0.9rem;
        color: #E5E7EB;
        display: inline-block;
    }
    
    .login-credit-badge a {
        color: #00F2FE;
        font-weight: 800;
        text-decoration: none;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ADMIN & FACULTY ACCESS CONTROL SYSTEM
# ---------------------------------------------------------
# Admin (You) Controls allowed faculty IDs
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
# HELPER FUNCTIONS FOR YOUTUBE DATA API
# ---------------------------------------------------------
def extract_video_id(url):
    regex = r"(?:v=|\/([0-9A-Za-z_-]{11}).*|list=|\/live\/|\/shorts\/)([0-9A-Za-z_-]{11})"
    match = re.search(regex, url)
    return match.group(1) or match.group(2) if match else None

def extract_playlist_id(url):
    match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None

def get_channel_uploads_playlist_id(api_key, channel_input):
    """ Get the uploads playlist ID directly from channel handle or ID """
    youtube = build('youtube', 'v3', developerKey=api_key)
    try:
        # Handle @username format
        if "@" in channel_input:
            handle = channel_input.split("@")[-1].split("/")[0]
            req = youtube.channels().list(part="contentDetails", forHandle=handle)
        else:
            # Assume Direct Channel ID
            ch_id = channel_input.split("/")[-1]
            req = youtube.channels().list(part="contentDetails", id=ch_id)
            
        res = req.execute()
        if res.get('items'):
            return res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except Exception as e:
        st.error(f"Channel Fetch Error: {str(e)}")
    return None

def get_multiple_playlists_videos(api_key, playlist_ids):
    all_videos = []
    seen_video_ids = set()
    fallback_thumb = "https://via.placeholder.com/120x90.png?text=YouTube"
    youtube = build('youtube', 'v3', developerKey=api_key)

    for p_id in playlist_ids:
        try:
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=p_id,
                maxResults=50
            )
            response = request.execute()
            p_video_ids = []
            temp_videos = []

            for item in response.get('items', []):
                snippet = item.get('snippet', {})
                content = item.get('contentDetails', {})
                v_id = content.get('videoId')
                
                if not v_id or v_id in seen_video_ids:
                    continue
                    
                title = snippet.get('title', 'Untitled Video')
                if title in ["Private video", "Deleted video"]:
                    continue

                thumbnails = snippet.get('thumbnails', {})
                default_thumb = thumbnails.get('default', {}).get('url') or fallback_thumb

                seen_video_ids.add(v_id)
                p_video_ids.append(v_id)
                temp_videos.append({"id": v_id, "title": title, "thumbnail": default_thumb})

            if p_video_ids:
                durations = get_video_durations(api_key, p_video_ids)
                for v in temp_videos:
                    v["duration"] = durations.get(v["id"], 0.0)
                    all_videos.append(v)
        except Exception as e:
            st.error(f"Error fetching source ({p_id}): {str(e)}")

    return all_videos

def get_video_durations(api_key, video_ids):
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
            durations[vid] = round(parsed_dur.total_seconds() / 3600.0, 2)
        return durations
    except Exception as e:
        st.error(f"API Duration Error: {str(e)}")
        return {}

# ---------------------------------------------------------
# SCREEN 1: LOGIN PORTAL
# ---------------------------------------------------------
if not st.session_state["logged_in"]:
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;' class='app-title'>⚡ PulseOps Engine</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;' class='app-subtitle'>🔴 YouTube Enterprise Ops & Hours Audit Suite</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### 🔐 Faculty / Operator Sign In")
            user_id = st.text_input("Educator / Operations ID", placeholder="e.g. UNAC_58291")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Access Workspace →")
            
            if submit:
                if user_id in ALLOWED_FACULTY and ALLOWED_FACULTY[user_id] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.rerun()
                else:
                    st.error("❌ Access Denied: Unapproved ID or Incorrect Password.")

        st.markdown("""
            <div style="text-align: center;">
                <div class="login-credit-badge">
                    Crafted with ⚡ by <a href="https://instagram.com/deepak_patil_7979" target="_blank">@deepak_patil_7979</a>
                </div>
            </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# SCREEN 2: MAIN DASHBOARD
# ---------------------------------------------------------
else:
    # Sidebar
    st.sidebar.markdown("## ⚡ PulseOps Hub")
    st.sidebar.markdown(f"👤 Logged: **{st.session_state['user_id']}**")
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("""
        <div class="sidebar-card">
            <span style="font-size: 20px;">🔴 📺</span><br>
            <strong style="color: #00F2FE;">YouTube API Connected</strong><br>
            <small style="color: #9CA3AF;">Engineered by @deepak_patil_7979</small>
        </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = ""
        st.session_state.pop("processed_df", None)
        st.session_state.pop("fetched_videos", None)
        st.rerun()

    # Main Header
    st.markdown("<h1 class='app-title'>📹 YouTube Hours Reconciler</h1>", unsafe_allow_html=True)
    st.markdown("<p class='app-subtitle'>Auto-extract durations, process channel/playlist batches, and split co-educator hours effortlessly.</p>", unsafe_allow_html=True)
    st.markdown("---")

    mode = st.radio("Select Ingestion Mode:", [
        "📋 Mode A: Direct Video Links", 
        "📺 Mode B: Playlists / Direct Channel Loader"
    ], horizontal=True)

    api_key = st.secrets.get("YOUTUBE_API_KEY", "")

    # MODE A: DIRECT LINKS
    if "Mode A" in mode:
        st.subheader("Step 1: Input Direct Video Links")
        raw_links_text = st.text_area("Paste links below (one per line):", height=140, placeholder="https://www.youtube.com/watch?v=Ez7JwEMh8Xc\nhttps://youtu.be/abc12345")
        
        if st.button("🚀 Process Direct Links"):
            if not api_key:
                st.error("API Key missing in Streamlit Secrets!")
            elif raw_links_text.strip():
                links = [l.strip() for l in raw_links_text.split("\n") if l.strip()]
                v_ids = [extract_video_id(l) for l in links if extract_video_id(l)]
                durations = get_video_durations(api_key, v_ids)
                
                rows = []
                for l in links:
                    vid = extract_video_id(l)
                    if vid:
                        rows.append({
                            "Educator ID": st.session_state["user_id"],
                            "Video ID": vid,
                            "Cleaned YT Link": f"https://www.youtube.com/watch?v={vid}",
                            "Total Duration (Hrs)": durations.get(vid, 0.0),
                            "Teachers Count": 1
                        })
                st.session_state["processed_df"] = pd.DataFrame(rows)

    # MODE B: MULTI-PLAYLIST & CHANNEL LOADER
    else:
        st.subheader("Step 1: Ingest YouTube Channel URL or Playlists")
        inputs_text = st.text_area(
            "Paste Channel Handle (e.g. @ChannelName) or Playlist Links (One per line):",
            height=140,
            placeholder="https://www.youtube.com/@UnacademyNEET\nhttps://www.youtube.com/playlist?list=PL1q4pmfxDpc..."
        )
        
        if st.button("🔍 Fetch Channel / Playlist Videos"):
            if not api_key:
                st.error("API Key missing in Secrets!")
            else:
                lines = [line.strip() for line in inputs_text.split("\n") if line.strip()]
                target_playlist_ids = []

                for item in lines:
                    if "list=" in item:
                        p_id = extract_playlist_id(item)
                        if p_id:
                            target_playlist_ids.append(p_id)
                    elif "@" in item or "channel" in item:
                        ch_playlist_id = get_channel_uploads_playlist_id(api_key, item)
                        if ch_playlist_id:
                            target_playlist_ids.append(ch_playlist_id)

                if not target_playlist_ids:
                    st.error("No valid Channel handle (@) or Playlist URLs found!")
                else:
                    with st.spinner("Fetching videos from YouTube Data API..."):
                        st.session_state["fetched_videos"] = get_multiple_playlists_videos(api_key, target_playlist_ids)

        if "fetched_videos" in st.session_state and st.session_state["fetched_videos"]:
            st.markdown("---")
            st.subheader("Step 2: Filter & Select Videos for Audit")
            videos = st.session_state["fetched_videos"]
            st.info(f"Total Unique Videos Retrieved: **{len(videos)}**")
            
            selected_videos = []
            for idx, vid in enumerate(videos):
                c1, c2, c3 = st.columns([0.4, 1, 4])
                chk = c1.checkbox("", key=f"vid_{idx}", value=True)
                c2.image(vid["thumbnail"], width=110)
                c3.markdown(f"**{vid['title']}**\n\n🆔 `{vid['id']}` | ⏱️ `{vid['duration']} hrs` | 🔗 [Watch Video](https://www.youtube.com/watch?v={vid['id']})")
                
                if chk:
                    selected_videos.append(vid)

            if st.button("✅ Confirm Selected Videos"):
                rows = []
                for sv in selected_videos:
                    rows.append({
                        "Educator ID": st.session_state["user_id"],
                        "Video ID": sv['id'],
                        "Cleaned YT Link": f"https://www.youtube.com/watch?v={sv['id']}",
                        "Total Duration (Hrs)": sv["duration"],
                        "Teachers Count": 1
                    })
                st.session_state["processed_df"] = pd.DataFrame(rows)

    # TABLE & EXPORT
    if "processed_df" in st.session_state and isinstance(st.session_state["processed_df"], pd.DataFrame) and not st.session_state["processed_df"].empty:
        st.markdown("---")
        st.subheader("Step 3: Verification & Multi-Teacher Split Table")
        
        df_to_edit = st.session_state["processed_df"].copy()

        edited_df = st.data_editor(
            df_to_edit,
            column_config={
                "Educator ID": st.column_config.TextColumn("Educator ID", disabled=True),
                "Video ID": st.column_config.TextColumn("Video ID", disabled=True),
                "Cleaned YT Link": st.column_config.LinkColumn("Clean YT Link", disabled=True),
                "Total Duration (Hrs)": st.column_config.NumberColumn("Total Duration", format="%.2f hrs", disabled=True),
                "Teachers Count": st.column_config.SelectboxColumn("Teachers Count", options=[1, 2, 3, 4])
            },
            hide_index=True,
            use_container_width=True
        )
        
        edited_df["Allocated Hours"] = (edited_df["Total Duration (Hrs)"] / edited_df["Teachers Count"]).round(2)
        
        col1, col2 = st.columns(2)
        total_vids = len(edited_df)
        tot_hrs = edited_df["Allocated Hours"].sum()
        
        col1.metric("Total Videos Audited", f"{total_vids}")
        col2.metric("Total Reconciled Hours", f"{tot_hrs:.2f} hrs")
        
        final_df = edited_df[["Educator ID", "Video ID", "Cleaned YT Link", "Allocated Hours"]]
        total_row = pd.DataFrame([{"Educator ID": "TOTAL", "Video ID": "-", "Cleaned YT Link": "-", "Allocated Hours": round(tot_hrs, 2)}])
        export_df = pd.concat([final_df, total_row], ignore_index=True)
        
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export CSV Audit Sheet", data=csv_data, file_name=f"YT_Audit_{st.session_state['user_id']}.csv", mime="text/csv")
