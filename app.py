import streamlit as st
import re
import pandas as pd
from googleapiclient.discovery import build
import isodate

# ---------------------------------------------------------
# PAGE CONFIGURATION & STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="PulseOps | Unacademy YT Operations",
    page_icon="⚡",
    layout="wide"
)

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

def get_playlist_videos(api_key, playlist_id):
    """ Fetch up to 50 videos safely with fallback for thumbnails """
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50
        )
        response = request.execute()
        
        videos = []
        video_ids = []
        
        fallback_thumb = "https://via.placeholder.com/120x90.png?text=No+Image"

        for item in response.get('items', []):
            snippet = item.get('snippet', {})
            content = item.get('contentDetails', {})
            
            v_id = content.get('videoId')
            if not v_id:
                continue
                
            title = snippet.get('title', 'Untitled Video')
            
            # Safe Thumbnail Extraction (FIX APPLIED HERE)
            thumbnails = snippet.get('thumbnails', {})
            default_thumb = thumbnails.get('default', {}).get('url') or \
                            thumbnails.get('medium', {}).get('url') or \
                            thumbnails.get('high', {}).get('url') or \
                            fallback_thumb
            
            # Skip private/deleted videos with no title
            if title in ["Private video", "Deleted video"]:
                continue

            video_ids.append(v_id)
            videos.append({"id": v_id, "title": title, "thumbnail": default_thumb})
            
        # Get Durations in bulk
        if video_ids:
            durations = get_video_durations(api_key, video_ids)
            for v in videos:
                v["duration"] = durations.get(v["id"], 0.0)
            
        return videos
    except Exception as e:
        st.error(f"Error fetching playlist: {str(e)}")
        return []

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
# APP SCREEN 1: LOGIN
# ---------------------------------------------------------
if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>⚡ PulseOps - Access Portal</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Unacademy Internal Audit & Operations Engine</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            user_id = st.text_input("Educator / Ops ID", placeholder="UNAC_58291")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Log In")
            if submit:
                if user_id in USER_DATABASE and USER_DATABASE[user_id] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.rerun()
                else:
                    st.error("Invalid Credentials")

# ---------------------------------------------------------
# APP SCREEN 2: MAIN DASHBOARD
# ---------------------------------------------------------
else:
    st.sidebar.title("PulseOps Control")
    st.sidebar.write(f"Logged in: **{st.session_state['user_id']}**")
    st.sidebar.success("🟢 API Engine: Active")
    if st.sidebar.button("Log Out"):
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = ""
        st.rerun()

    st.title("📹 YouTube Visual Selector & Hours Reconciler")
    st.caption("Paste Playlist / Channel links, visually select videos, and export Google Sheet ready data!")
    st.markdown("---")

    mode = st.radio("Choose Input Mode:", ["📋 Option A: Paste Direct Video Links", "📺 Option B: Load Playlist / Channel Videos (Visual Picker)"], horizontal=True)

    api_key = st.secrets.get("YOUTUBE_API_KEY", "")

    # MODE A: DIRECT LINKS
    if "Option A" in mode:
        st.subheader("Step 1: Paste Links")
        raw_links_text = st.text_area("Paste links (one per line):", height=120)
        
        if st.button("🚀 Process Links"):
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
                            "Cleaned YT Link": f"https://www.youtube.com/watch?v={vid}",
                            "Total Duration (Hrs)": durations.get(vid, 0.0),
                            "Teachers Count": 1
                        })
                st.session_state["processed_df"] = pd.DataFrame(rows)

    # MODE B: VISUAL PLAYLIST / CHANNEL PICKER
    else:
        st.subheader("Step 1: Fetch Playlist / Channel")
        playlist_url = st.text_input("Paste YouTube Playlist URL:", placeholder="https://www.youtube.com/playlist?list=PL...")
        
        if st.button("🔍 Fetch Videos"):
            p_id = extract_playlist_id(playlist_url)
            if not p_id:
                st.error("Invalid Playlist URL! Make sure it contains 'list=...'")
            else:
                with st.spinner("Fetching videos from YouTube..."):
                    st.session_state["fetched_videos"] = get_playlist_videos(api_key, p_id)

        if "fetched_videos" in st.session_state and st.session_state["fetched_videos"]:
            st.subheader("Step 2: Tick / Select Videos to Audit")
            videos = st.session_state["fetched_videos"]
            
            selected_videos = []
            for idx, vid in enumerate(videos):
                c1, c2, c3 = st.columns([0.5, 1, 4])
                chk = c1.checkbox("", key=f"vid_{idx}", value=True)
                c2.image(vid["thumbnail"], width=100)
                c3.markdown(f"**{vid['title']}**\n\n⏱️ Duration: `{vid['duration']} hrs` | 🔗 [Watch Link](https://www.youtube.com/watch?v={vid['id']})")
                
                if chk:
                    selected_videos.append(vid)

            if st.button("✅ Confirm Selected Videos"):
                rows = []
                for sv in selected_videos:
                    rows.append({
                        "Educator ID": st.session_state["user_id"],
                        "Cleaned YT Link": f"https://www.youtube.com/watch?v={sv['id']}",
                        "Total Duration (Hrs)": sv["duration"],
                        "Teachers Count": 1
                    })
                st.session_state["processed_df"] = pd.DataFrame(rows)

    # STEP 3: RECONCILIATION TABLE & EXPORT
    if "processed_df" in st.session_state and not st.session_state["processed_df"].empty:
        st.markdown("---")
        st.subheader("Reconciliation Table & Multi-Teacher Split")
        
        edited_df = st.data_editor(
            st.session_state["processed_df"],
            column_config={
                "Educator ID": st.column_config.TextColumn(disabled=True),
                "Cleaned YT Link": st.column_config.LinkColumn("YT Link", disabled=True),
                "Total Duration (Hrs)": st.column_config.NumberColumn(format="%.2f hrs", disabled=True),
                "Teachers Count": st.column_config.SelectboxColumn("Teachers Count", options=[1, 2, 3, 4])
            },
            hide_index=True,
            use_container_width=True
        )
        
        edited_df["Allocated Hours"] = (edited_df["Total Duration (Hrs)"] / edited_df["Teachers Count"]).round(2)
        
        col1, col2 = st.columns(2)
        total_vids = len(edited_df)
        tot_hrs = edited_df["Allocated Hours"].sum()
        
        col1.metric("Selected Videos", f"{total_vids} Videos")
        col2.metric("Total Final Reconciled Hours", f"{tot_hrs:.2f} Hours")
        
        # CSV / Sheet Export
        final_df = edited_df[["Educator ID", "Cleaned YT Link", "Allocated Hours"]]
        total_row = pd.DataFrame([{"Educator ID": "TOTAL", "Cleaned YT Link": "", "Allocated Hours": round(tot_hrs, 2)}])
        export_df = pd.concat([final_df, total_row], ignore_index=True)
        
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Google Sheet / CSV", data=csv_data, file_name=f"YT_Audit_{st.session_state['user_id']}.csv", mime="text/csv")
