import streamlit as st
import re
import pandas as pd
from googleapiclient.discovery import build
import isodate

# ---------------------------------------------------------
# PAGE CONFIGURATION & HIGH-END ENTERPRISE STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="PulseOps | Enterprise YouTube Audit",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for Modern SaaS Aesthetics
st.markdown("""
    <style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    /* Cards & Containers */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #10B981;
        font-weight: 700;
    }
    /* Modern Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        border-radius: 10px;
        font-weight: 600;
        border: none;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.39);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(16, 185, 129, 0.55);
        color: white;
    }
    /* Table & Editor Styling */
    .stDataFrame {
        border: 1px solid #334155;
        border-radius: 12px;
        overflow: hidden;
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
    """ Fetch up to 50 videos per playlist across multiple playlist IDs """
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
                default_thumb = thumbnails.get('default', {}).get('url') or \
                                thumbnails.get('medium', {}).get('url') or \
                                thumbnails.get('high', {}).get('url') or \
                                fallback_thumb

                seen_video_ids.add(v_id)
                p_video_ids.append(v_id)
                temp_videos.append({"id": v_id, "title": title, "thumbnail": default_thumb})

            # Get Durations
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
# APP SCREEN 1: LOGIN PORTAL
# ---------------------------------------------------------
if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; color: #10B981;'>⚡ PulseOps Engine</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>Enterprise YouTube Reconciler & Ops Suite</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            user_id = st.text_input("Educator / Operations ID", placeholder="e.g. UNAC_58291")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Access Operations Dashboard →")
            if submit:
                if user_id in USER_DATABASE and USER_DATABASE[user_id] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.rerun()
                else:
                    st.error("Invalid Credentials. Check Educator ID / Password.")

# ---------------------------------------------------------
# APP SCREEN 2: MAIN DASHBOARD
# ---------------------------------------------------------
else:
    # Sidebar
    st.sidebar.markdown("### ⚡ PulseOps Control")
    st.sidebar.write(f"Logged in: **{st.session_state['user_id']}**")
    st.sidebar.success("🟢 API Status: Active")
    st.sidebar.markdown("---")
    if st.sidebar.button("Log Out"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = ""
        st.session_state.pop("processed_df", None)
        st.session_state.pop("fetched_videos", None)
        st.rerun()

    # Header
    st.title("📹 Multi-Playlist & Direct Hours Reconciler")
    st.caption("Batch process multiple playlists, select videos, and export auto-split YouTube audit sheets.")
    st.markdown("---")

    mode = st.radio("Select Ingestion Mode:", ["📋 Option A: Direct Video Links", "📺 Option B: Batch Multi-Playlist / Channel Loaders"], horizontal=True)

    api_key = st.secrets.get("YOUTUBE_API_KEY", "")

    # MODE A: DIRECT LINKS
    if "Option A" in mode:
        st.subheader("Step 1: Input Direct YouTube Links")
        raw_links_text = st.text_area("Paste links here (one link per line):", height=140, placeholder="https://www.youtube.com/watch?v=Ez7JwEMh8Xc\nhttps://youtu.be/abc12345")
        
        if st.button("🚀 Process Direct Links"):
            if not api_key:
                st.error("API Key missing in Streamlit Secrets.")
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

    # MODE B: MULTI-PLAYLIST BATCH INGESTION
    else:
        st.subheader("Step 1: Batch Input Multiple Playlists")
        playlists_text = st.text_area(
            "Paste YouTube Playlist URLs (One URL per line for multiple playlists):",
            height=140,
            placeholder="https://www.youtube.com/playlist?list=PL1q4pmfxDpc...\nhttps://www.youtube.com/playlist?list=PL2abc345xyz..."
        )
        
        if st.button("🔍 Fetch All Videos from Playlists"):
            raw_p_urls = [p.strip() for p in playlists_text.split("\n") if p.strip()]
            playlist_ids = [extract_playlist_id(p) for p in raw_p_urls if extract_playlist_id(p)]
            
            if not playlist_ids:
                st.error("No valid playlist links found! Make sure URLs contain 'list=...'")
            else:
                with st.spinner(f"Fetching videos from {len(playlist_ids)} playlist(s)..."):
                    st.session_state["fetched_videos"] = get_multiple_playlists_videos(api_key, playlist_ids)

        if "fetched_videos" in st.session_state and st.session_state["fetched_videos"]:
            st.markdown("---")
            st.subheader("Step 2: Select Videos to Include in Audit")
            videos = st.session_state["fetched_videos"]
            st.info(f"Total Unique Videos Found Across Playlists: **{len(videos)}**")
            
            selected_videos = []
            for idx, vid in enumerate(videos):
                c1, c2, c3 = st.columns([0.4, 1, 4])
                chk = c1.checkbox("", key=f"vid_{idx}", value=True)
                c2.image(vid["thumbnail"], width=110)
                c3.markdown(f"**{vid['title']}**\n\n🆔 Video ID: `{vid['id']}` | ⏱️ Duration: `{vid['duration']} hrs` | 🔗 [Watch Video](https://www.youtube.com/watch?v={vid['id']})")
                
                if chk:
                    selected_videos.append(vid)

            if st.button("✅ Confirm Selected Videos for Reconciliation"):
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

    # STEP 3: RECONCILIATION TABLE & CSV EXPORT
    if "processed_df" in st.session_state and isinstance(st.session_state["processed_df"], pd.DataFrame) and not st.session_state["processed_df"].empty:
        st.markdown("---")
        st.subheader("Step 3: Verification & Multi-Teacher Split Table")
        
        df_to_edit = st.session_state["processed_df"].copy()
        
        if "Video ID" not in df_to_edit.columns:
            df_to_edit["Video ID"] = df_to_edit["Cleaned YT Link"].apply(lambda x: extract_video_id(str(x)) or "-")

        edited_df = st.data_editor(
            df_to_edit,
            column_config={
                "Educator ID": st.column_config.TextColumn("Educator ID", disabled=True),
                "Video ID": st.column_config.TextColumn("Video ID", disabled=True),
                "Cleaned YT Link": st.column_config.LinkColumn("Clean YT Link", disabled=True),
                "Total Duration (Hrs)": st.column_config.NumberColumn("Total Duration", format="%.2f hrs", disabled=True),
                "Teachers Count": st.column_config.SelectboxColumn("Teachers Count", options=[1, 2, 3, 4], help="Split hours across co-educators")
            },
            hide_index=True,
            use_container_width=True
        )
        
        edited_df["Allocated Hours"] = (edited_df["Total Duration (Hrs)"] / edited_df["Teachers Count"]).round(2)
        
        col1, col2 = st.columns(2)
        total_vids = len(edited_df)
        tot_hrs = edited_df["Allocated Hours"].sum()
        
        col1.metric("Total Videos Audited", f"{total_vids} Videos")
        col2.metric("Total Reconciled Hours", f"{tot_hrs:.2f} Hours")
        
        cols_to_export = [c for c in ["Educator ID", "Video ID", "Cleaned YT Link", "Allocated Hours"] if c in edited_df.columns]
        final_df = edited_df[cols_to_export]
        
        total_row = pd.DataFrame([{"Educator ID": "TOTAL", "Video ID": "-", "Cleaned YT Link": "-", "Allocated Hours": round(tot_hrs, 2)}])
        export_df = pd.concat([final_df, total_row], ignore_index=True)
        
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Google Sheet / CSV", data=csv_data, file_name=f"YT_Audit_{st.session_state['user_id']}.csv", mime="text/csv")
