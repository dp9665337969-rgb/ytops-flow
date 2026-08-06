import streamlit as st
import re
import pandas as pd
from googleapiclient.discovery import build
import isodate

# ---------------------------------------------------------
# PAGE CONFIGURATION & ULTRA-MODERN SAAS STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="PulseOps | Next-Gen YouTube Audit",
    page_icon="⚡",
    layout="wide"
)

# Custom High-End Cyber/SaaS CSS
st.markdown("""
    <style>
    /* Dark Obsidian Background with Subtle Mesh Gradient */
    .stApp {
        background: radial-gradient(circle at 50% -20%, #1E1B4B 0%, #0F172A 60%, #020617 100%);
        color: #F8FAFC;
        font-family: 'Inter', sans-serif;
    }
    
    /* Neon Title Branding */
    .neon-title {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
        letter-spacing: -1px;
    }
    
    .neon-subtitle {
        text-align: center;
        color: #94A3B8;
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 2rem;
    }

    /* Custom Form Card Styling */
    div[data-testid="stForm"] {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(12px);
    }

    /* Input Field Fixes (Readable Dark Theme) */
    .stTextInput input {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
    }
    
    .stTextInput input:focus {
        border-color: #8B5CF6 !important;
        box-shadow: 0 0 12px rgba(139, 92, 246, 0.4) !important;
    }

    /* Glowing Gradient Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px) scale(1.01) !important;
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.6) !important;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
    }

    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 32px;
        color: #38BDF8;
        font-weight: 800;
    }

    /* Footer Branding Credit */
    .developer-credit {
        position: fixed;
        bottom: 15px;
        right: 20px;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(139, 92, 246, 0.3);
        padding: 8px 16px;
        border-radius: 30px;
        font-size: 0.85rem;
        color: #CBD5E1;
        backdrop-filter: blur(8px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        z-index: 9999;
    }
    
    .developer-credit a {
        color: #A855F7;
        font-weight: 700;
        text-decoration: none;
    }
    
    .developer-credit a:hover {
        text-decoration: underline;
        color: #EC4899;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CREDENTIALS & SESSION SYSTEM
# ---------------------------------------------------------
USER_DATABASE = {
    "UNAC_58291": "Pass@123",
    "UNAC_10021": "Educator@2026",
    "ADMIN_OPS": "UnacademyOps#1"
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""

# ---------------------------------------------------------
# HELPER FUNCTIONS FOR YOUTUBE API
# ---------------------------------------------------------
def extract_video_id(url):
    regex = r"(?:v=|\/([0-9A-Za-z_-]{11}).*|list=|\/live\/|\/shorts\/)([0-9A-Za-z_-]{11})"
    match = re.search(regex, url)
    return match.group(1) or match.group(2) if match else None

def extract_playlist_id(url):
    match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None

def get_multiple_playlists_videos(api_key, playlist_ids):
    all_videos = []
    seen_video_ids = set()
    fallback_thumb = "https://via.placeholder.com/120x90.png?text=No+Image"
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
            st.error(f"Error fetching playlist ({p_id}): {str(e)}")

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
        st.error(f"API Error: {str(e)}")
        return {}

# ---------------------------------------------------------
# SCREEN 1: LOGIN PORTAL
# ---------------------------------------------------------
if not st.session_state["logged_in"]:
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='neon-title'>⚡ PulseOps Engine</h1>", unsafe_allow_html=True)
    st.markdown("<p class='neon-subtitle'>Enterprise YouTube Reconciler & Content Ops Suite</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("🔐 Sign In")
            user_id = st.text_input("Educator / Operations ID", placeholder="e.g. UNAC_58291")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Access Operations Suite →")
            
            if submit:
                if user_id in USER_DATABASE and USER_DATABASE[user_id] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.rerun()
                else:
                    st.error("Invalid Credentials. Please check your Operator ID.")

# ---------------------------------------------------------
# SCREEN 2: MAIN DASHBOARD
# ---------------------------------------------------------
else:
    # Sidebar
    st.sidebar.markdown("### ⚡ PulseOps Control Hub")
    st.sidebar.write(f"Logged in as: **{st.session_state['user_id']}**")
    st.sidebar.success("🟢 API Status: Connected")
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout Station"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = ""
        st.session_state.pop("processed_df", None)
        st.session_state.pop("fetched_videos", None)
        st.rerun()

    # Dashboard Header
    st.title("📹 YouTube Hours Reconciler & Batch Auditor")
    st.caption("Streamline video duration extraction, co-educator splits, and automated reconciliation sheets.")
    st.markdown("---")

    mode = st.radio("Select Processing Mode:", ["📋 Mode A: Direct Video Links", "📺 Mode B: Batch Multi-Playlist Loader"], horizontal=True)

    api_key = st.secrets.get("YOUTUBE_API_KEY", "")

    # MODE A
    if "Mode A" in mode:
        st.subheader("Step 1: Input Direct YouTube Links")
        raw_links_text = st.text_area("Paste links below (one per line):", height=140, placeholder="https://www.youtube.com/watch?v=Ez7JwEMh8Xc\nhttps://youtu.be/abc12345")
        
        if st.button("🚀 Process Direct Links"):
            if not api_key:
                st.error("API Key missing in Secrets.")
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

    # MODE B
    else:
        st.subheader("Step 1: Ingest Playlist Batches")
        playlists_text = st.text_area("Paste YouTube Playlist URLs (One per line):", height=140, placeholder="https://www.youtube.com/playlist?list=PL1q4pmfxDpc...")
        
        if st.button("🔍 Fetch All Videos across Playlists"):
            raw_p_urls = [p.strip() for p in playlists_text.split("\n") if p.strip()]
            playlist_ids = [extract_playlist_id(p) for p in raw_p_urls if extract_playlist_id(p)]
            
            if not playlist_ids:
                st.error("No valid playlist links found!")
            else:
                with st.spinner("Processing Playlists via YouTube Data API..."):
                    st.session_state["fetched_videos"] = get_multiple_playlists_videos(api_key, playlist_ids)

        if "fetched_videos" in st.session_state and st.session_state["fetched_videos"]:
            st.markdown("---")
            st.subheader("Step 2: Filter Videos for Audit")
            videos = st.session_state["fetched_videos"]
            st.info(f"Total Unique Videos Found: **{len(videos)}**")
            
            selected_videos = []
            for idx, vid in enumerate(videos):
                c1, c2, c3 = st.columns([0.4, 1, 4])
                chk = c1.checkbox("", key=f"vid_{idx}", value=True)
                c2.image(vid["thumbnail"], width=110)
                c3.markdown(f"**{vid['title']}**\n\n🆔 `{vid['id']}` | ⏱️ `{vid['duration']} hrs` | 🔗 [Open Link](https://www.youtube.com/watch?v={vid['id']})")
                
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
        st.subheader("Step 3: Verification & Co-Educator Split")
        
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
        
        col1.metric("Total Videos", f"{total_vids}")
        col2.metric("Total Reconciled Hours", f"{tot_hrs:.2f} hrs")
        
        final_df = edited_df[["Educator ID", "Video ID", "Cleaned YT Link", "Allocated Hours"]]
        total_row = pd.DataFrame([{"Educator ID": "TOTAL", "Video ID": "-", "Cleaned YT Link": "-", "Allocated Hours": round(tot_hrs, 2)}])
        export_df = pd.concat([final_df, total_row], ignore_index=True)
        
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export CSV Audit Sheet", data=csv_data, file_name=f"YT_Audit_{st.session_state['user_id']}.csv", mime="text/csv")

# ---------------------------------------------------------
# FOOTER CREDIT BADGE
# ---------------------------------------------------------
st.markdown("""
    <div class="developer-credit">
        Crafted with ⚡ by <a href="https://instagram.com/deepak_patil_7979" target="_blank">@deepak_patil_7979</a>
    </div>
""", unsafe_allow_html=True)
