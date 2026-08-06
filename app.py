import streamlit as st
import re
import pandas as pd
from googleapiclient.discovery import build
import isodate

# ---------------------------------------------------------
# PAGE CONFIGURATION & ULTRA-HIGH CONTRAST SAAS STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="PulseOps | Next-Gen YouTube Audit",
    page_icon="⚡",
    layout="wide"
)

# Custom High-Contrast Modern SaaS CSS
st.markdown("""
    <style>
    /* Dark Obsidian Mesh Gradient Background */
    .stApp {
        background: radial-gradient(circle at 50% -10%, #111827 0%, #030712 100%);
        color: #F9FAFB !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Neon Title Branding */
    .neon-title {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 50%, #00C6FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
        letter-spacing: -1.5px;
        filter: drop-shadow(0 0 20px rgba(0, 242, 254, 0.3));
    }
    
    .neon-subtitle {
        text-align: center;
        color: #9CA3AF !important;
        font-size: 1.15rem;
        font-weight: 500;
        margin-bottom: 2rem;
    }

    /* Glassmorphism Form Card */
    div[data-testid="stForm"] {
        background: rgba(17, 24, 39, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 24px;
        padding: 2.5rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(16px);
    }

    /* High-Contrast Label & Inputs */
    .stTextInput label {
        color: #F3F4F6 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    .stTextInput input {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border: 1.5px solid #374151 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
    }
    
    .stTextInput input::placeholder {
        color: #6B7280 !important;
    }
    
    .stTextInput input:focus {
        border-color: #00F2FE !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.4) !important;
    }

    /* Glowing Gradient Button */
    .stButton>button {
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%) !important;
        color: #030712 !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        border: none !important;
        padding: 0.8rem 1.5rem !important;
        box-shadow: 0 4px 20px rgba(0, 242, 254, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 8px 30px rgba(0, 242, 254, 0.7) !important;
        color: #000000 !important;
    }

    /* Metrics High Contrast */
    div[data-testid="stMetricValue"] {
        font-size: 34px;
        color: #00F2FE !important;
        font-weight: 900;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #D1D5DB !important;
    }

    /* Credit Badge right below Login Box */
    .login-credit-badge {
        margin-top: 1.5rem;
        text-align: center;
        background: rgba(31, 41, 55, 0.6);
        border: 1px solid rgba(0, 242, 254, 0.3);
        padding: 10px 18px;
        border-radius: 50px;
        font-size: 0.9rem;
        color: #E5E7EB;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        display: inline-block;
    }
    
    .login-credit-badge a {
        color: #00F2FE;
        font-weight: 800;
        text-decoration: none;
    }
    
    .login-credit-badge a:hover {
        text-decoration: underline;
        color: #38BDF8;
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
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='neon-title'>⚡ PulseOps Engine</h1>", unsafe_allow_html=True)
    st.markdown("<p class='neon-subtitle'>Enterprise YouTube Reconciler & Content Ops Suite</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("<h3 style='color: #FFFFFF; text-align: center; font-weight: 800;'>🔐 Operator Login</h3>", unsafe_allow_html=True)
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            user_id = st.text_input("Educator / Operations ID", placeholder="e.g. UNAC_58291")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("Access Operations Suite →")
            
            if submit:
                if user_id in USER_DATABASE and USER_DATABASE[user_id] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.rerun()
                else:
                    st.error("Invalid Credentials. Check Operator ID.")

        # CREDIT PLACEMENT: EXACTLY BELOW THE LOGIN BOX
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
    st.sidebar.markdown("### ⚡ PulseOps Control Hub")
    st.sidebar.write(f"Logged in as: **{st.session_state['user_id']}**")
    st.sidebar.success("🟢 API Status: Active")
    st.sidebar.markdown("---")
    
    # Sidebar Credit
    st.sidebar.markdown("""
        <div style="padding: 10px; background: rgba(255,255,255,0.05); border-radius: 10px; border: 1px solid rgba(0,242,254,0.2); text-align: center;">
            <small style="color: #9CA3AF;">Engineered by</small><br>
            <a href="https://instagram.com/deepak_patil_7979" target="_blank" style="color: #00F2FE; font-weight: 700; text-decoration: none;">@deepak_patil_7979</a>
        </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("<br>", unsafe_allow_html=True)

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
