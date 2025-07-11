import streamlit as st
import cv2
import mediapipe as mp
import pygame
import os
import time
from streamlit.components.v1 import html

# Custom CSS styling
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Setup with vibrant theme
st.set_page_config(
    page_title="🎵 Hand Gesture Music Maestro", 
    layout="centered", 
    page_icon="🎶",
    initial_sidebar_state="expanded"
)

# Custom HTML/CSS with colorful decorations
st.markdown("""
<style>
    /* Vibrant gradient background */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Glowing title effect */
    .title-text {
        font-family: 'Arial', sans-serif;
        color: white;
        text-shadow: 0 0 10px #ff00ff, 
                     0 0 20px #ff00ff, 
                     0 0 30px #ff00ff;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from {
            text-shadow: 0 0 10px #ff00ff, 
                         0 0 20px #ff00ff, 
                         0 0 30px #ff00ff;
        }
        to {
            text-shadow: 0 0 15px #ff00ff, 
                         0 0 25px #ff00ff, 
                         0 0 35px #ff00ff;
        }
    }
    
    /* Neon buttons */
    .stButton>button {
        border: 2px solid #00ffff;
        border-radius: 25px;
        padding: 12px 28px;
        background: rgba(0, 0, 0, 0.3);
        color: #00ffff;
        font-weight: bold;
        font-size: 16px;
        transition: all 0.3s;
        box-shadow: 0 0 10px #00ffff;
    }
    
    .stButton>button:hover {
        background: rgba(0, 255, 255, 0.2);
        transform: scale(1.05);
        box-shadow: 0 0 20px #00ffff;
    }
    
    /* Song display with pulse animation */
    .song-title {
        font-size: 1.4em;
        color: #ffcc00;
        text-shadow: 0 0 5px #ff6600;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Status box with gradient border */
    .status-box {
        background: rgba(0, 0, 0, 0.4);
        border-radius: 15px;
        padding: 15px;
        margin: 15px 0;
        border-left: 5px solid;
        border-image: linear-gradient(to bottom, #ff00ff, #00ffff) 1;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    /* Animated volume bar */
    .volume-container {
        margin: 20px 0;
    }
    
    .volume-bar {
        height: 15px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        margin: 10px 0;
        overflow: hidden;
    }
    
    .volume-fill {
        height: 100%;
        background: linear-gradient(90deg, #ff5e62, #ff9966);
        border-radius: 10px;
        transition: width 0.5s;
        box-shadow: 0 0 10px #ff9966;
    }
    
    /* Gesture instructions with floating effect */
    .gesture-instruction {
        background: rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: transform 0.3s;
    }
    
    .gesture-instruction:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    }
    
    /* Camera feed styling */
    .stImage>img {
        border-radius: 15px;
        border: 3px solid #00ffff;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
        transition: all 0.3s;
    }
    
    .stImage>img:hover {
        box-shadow: 0 0 30px rgba(0, 255, 255, 0.8);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(#00ffff, #ff00ff);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Fancy title with HTML and glowing effect
st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 class="title-text">🎶 Hand Gesture Music Maestro</h1>
    <p style="color: #e0e0e0; font-size: 18px;">Control your music with magical hand gestures ✨</p>
</div>
""", unsafe_allow_html=True)

# Initialize music system
try:
    pygame.mixer.init()
    volume = 0.5
    pygame.mixer.music.set_volume(volume)
except pygame.error as e:
    st.error(f"❌ Failed to initialize audio system: {e}")
    st.stop()

# Load music files
song_folder = "song"
if not os.path.exists(song_folder):
    os.makedirs(song_folder)
    st.error(f"❌ Created 'song' folder. Please add some MP3 files to it.")
    st.stop()

song_list = sorted([file for file in os.listdir(song_folder) if file.endswith(".mp3")])
if not song_list:
    st.error("No MP3 files found in the 'song' folder. Please add some music files.")
    st.stop()

# Mediapipe init
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_drawing = mp.solutions.drawing_utils

# State variables
if "run_camera" not in st.session_state:
    st.session_state.run_camera = False
if "volume" not in st.session_state:
    st.session_state.volume = 0.5
if "song_index" not in st.session_state:
    st.session_state.song_index = 0
if "status" not in st.session_state:
    st.session_state.status = "Ready"
if "current_song" not in st.session_state:
    st.session_state.current_song = "No song selected"

# Music control functions
def play_song(index):
    try:
        pygame.mixer.music.load(os.path.join(song_folder, song_list[index]))
        pygame.mixer.music.play()
        st.session_state.current_song = song_list[index]
        return f"▶️ Playing: {song_list[index]}"
    except (pygame.error, IndexError) as e:
        st.error(f"❌ Error playing song: {e}")
        return "❌ Error"

def stop_song():
    try:
        pygame.mixer.music.stop()
        st.session_state.current_song = "No song selected"
    except pygame.error:
        pass

def pause_song():
    try:
        pygame.mixer.music.pause()
    except pygame.error:
        pass

def unpause_song():
    try:
        pygame.mixer.music.unpause()
    except pygame.error:
        pass

# Finger counter
def count_fingers(landmarks):
    count = 0
    if landmarks[8].y < landmarks[6].y: count += 1   # Index
    if landmarks[12].y < landmarks[10].y: count += 1 # Middle
    if landmarks[16].y < landmarks[14].y: count += 1 # Ring
    if landmarks[20].y < landmarks[18].y: count += 1 # Pinky
    return count

# Gesture instructions with emoji icons
with st.expander("✨ Gesture Controls Guide", expanded=True):
    st.markdown("""
    <div class="gesture-instruction">
        <p style="font-size: 18px;"><span style="font-size: 24px;">👊</span> <b>Fist (0 fingers)</b> - Mute volume</p>
        <p style="font-size: 18px;"><span style="font-size: 24px;">☝️</span> <b>1 Finger</b> - Play current song</p>
        <p style="font-size: 18px;"><span style="font-size: 24px;">✌️</span> <b>2 Fingers</b> - Volume Down</p>
        <p style="font-size: 18px;"><span style="font-size: 24px;">🤟</span> <b>3 Fingers</b> - Next Song</p>
        <p style="font-size: 18px;"><span style="font-size: 24px;">✋</span> <b>4 Fingers</b> - Volume Up</p>
        <p style="font-size: 18px;"><span style="font-size: 24px;">🖐️</span> <b>5 Fingers</b> - Stop Music</p>
    </div>
    """, unsafe_allow_html=True)

# Current song and volume display with animations
st.markdown(f"""
<div class="volume-container">
    <div class="song-title">🎵 Now Playing: {st.session_state.current_song}</div>
    <div style="margin: 15px 0; font-size: 16px;">🔊 Volume Level</div>
    <div class="volume-bar">
        <div class="volume-fill" style="width: {st.session_state.volume * 100}%;"></div>
    </div>
    <div style="text-align: right; margin-top: 5px; font-size: 16px;">{int(st.session_state.volume * 100)}%</div>
</div>
""", unsafe_allow_html=True)

# Camera control buttons with neon effect
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("📷 Start Camera", key="start_cam"):
        st.session_state.run_camera = True
with col2:
    if st.button("⏸️ Pause Music", key="pause_music"):
        pause_song()
        st.session_state.status = "⏸️ Paused"
with col3:
    if st.button("🛑 Stop Camera", key="stop_cam"):
        st.session_state.run_camera = False
        stop_song()

# Status box with gradient border
status_placeholder = st.empty()

# Camera feed with glowing border
FRAME_WINDOW = st.image([], use_column_width=True)

# Main loop
cap = None
try:
    if st.session_state.run_camera:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("❌ Could not open camera")
            st.session_state.run_camera = False
            st.stop()

        while st.session_state.run_camera:
            ret, frame = cap.read()
            if not ret:
                st.warning("⚠️ Failed to grab frame")
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                for lm in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)
                    fingers = count_fingers(lm.landmark)

                    # Gesture-based music control
                    if fingers == 0:
                        pygame.mixer.music.set_volume(0.0)
                        st.session_state.status = "🔇 Muted"
                    elif fingers == 1:
                        st.session_state.status = play_song(st.session_state.song_index)
                    elif fingers == 2:
                        st.session_state.volume = max(0.0, st.session_state.volume - 0.1)
                        pygame.mixer.music.set_volume(st.session_state.volume)
                        st.session_state.status = f"🔉 Volume Down: {int(st.session_state.volume * 100)}%"
                    elif fingers == 3:
                        st.session_state.song_index = (st.session_state.song_index + 1) % len(song_list)
                        st.session_state.status = play_song(st.session_state.song_index)
                    elif fingers == 4:
                        st.session_state.volume = min(1.0, st.session_state.volume + 0.1)
                        pygame.mixer.music.set_volume(st.session_state.volume)
                        st.session_state.status = f"🔊 Volume Up: {int(st.session_state.volume * 100)}%"
                    elif fingers == 5:
                        stop_song()
                        st.session_state.status = "⏹️ Stopped"

                    # Display text on frame with colorful styling
                    cv2.putText(frame, f"Fingers: {fingers}", (10, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 105, 180), 2)  # Hot pink
                    cv2.putText(frame, f"{st.session_state.status}", (10, 100), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)  # Cyan
                    cv2.putText(frame, f"Volume: {int(st.session_state.volume * 100)}%", (10, 140), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)  # Yellow

            FRAME_WINDOW.image(frame, channels="BGR")
            
            # Update status with HTML styling
            status_placeholder.markdown(f"""
            <div class="status-box">
                <strong style="font-size: 18px; color: #00ffff;">Status:</strong> 
                <span style="font-size: 16px;">{st.session_state.status}</span>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(0.05)

finally:
    if cap is not None:
        cap.release()
    hands.close()

# Footer with colorful gradient
st.markdown("""
<div style="text-align: center; margin-top: 30px; padding: 15px; 
            background: linear-gradient(90deg, #ff00ff, #00ffff);
            border-radius: 10px;">
    <p style="color: white; font-size: 14px;">✨ Hand Gesture Music Controller ✨</p>
</div>
""", unsafe_allow_html=True)