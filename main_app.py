import streamlit as st
import textwrap
import json
import os
import time
import random
import requests  
import asyncio
import edge_tts
import tempfile
import google.generativeai as genai
from google.api_core import exceptions
import streamlit.components.v1 as components
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- Voice Mode Requirements ---
import speech_recognition as sr
from gtts import gTTS
import io
from audio_recorder_streamlit import audio_recorder

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Valluvar 2.0 - Dual Language",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 💾 DATA LOGGING SYSTEM (GOOGLE SHEETS)
# ==========================================
def log_to_gsheets(mode, query, response):
    try:
        if "gcp_service_account" not in st.secrets:
            return

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("Valluvar Records").sheet1
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_response = str(response).replace('\n', ' ').replace('\r', '')
        sheet.append_row([timestamp, mode, query, clean_response])
        
    except Exception as e:
        pass

# ==========================================
# 📧 EMAIL ALERT SYSTEM
# ==========================================
def send_error_alert(error_message):
    try:
        if "email" not in st.secrets:
            return

        sender_email = st.secrets["email"]["sender"]
        sender_password = st.secrets["email"]["password"]
        receiver_email = st.secrets["email"]["receiver"]

        subject = "🚨 URGENT: Valluvar App API Error!"
        body = f"Error Details:\n{error_message}"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
    except Exception as e:
        pass

# ==========================================
# 🚀 ELITE 3D UI SCRIPT & MOBILE OPTIMIZATION
# ==========================================
def inject_custom_css_and_js():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;900&family=DM+Sans:wght@300;400;500;600;700&family=Noto+Serif+Tamil:wght@400;700&display=swap');

            /* BASE THEME - FORCE DARK MODE OVERRIDE */
            [data-testid="stAppViewContainer"] {
                background: #050D1F !important;
                background-image: radial-gradient(circle at 50% 0%, #0D1F3C 0%, #050D1F 70%);
                color: #FFFFFF !important; font-family: 'DM Sans', sans-serif !important;
            }
            [data-testid="stHeader"] { background: transparent !important; }
            #MainMenu, header, footer, .stDeployButton {visibility: hidden;}
            p, span, div, label { color: #FFFFFF !important; }

            /* AMBIENT BLOBS */
            .bg-blobs { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
            .bg-blobs::before, .bg-blobs::after { content: ''; position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.5; animation: blobFloat 8s ease-in-out infinite; }
            .bg-blobs::before { width: 400px; height: 400px; background: rgba(201,168,76,0.07); top: -100px; left: -100px; }
            .bg-blobs::after { width: 500px; height: 500px; background: rgba(20,50,150,0.12); bottom: -150px; right: -100px; animation-delay: -3s; }
            @keyframes blobFloat { 0%, 100% { transform: translate(0,0) scale(1); } 50% { transform: translate(20px,-20px) scale(1.05); } }

            /* PURE CSS MODAL IMPLEMENTATION */
            #modal-toggle { display: none; }
            .about-btn { display: inline-block; cursor: pointer; color: #F0C96A !important; font-size: 13px; font-weight: 700; letter-spacing: 1px; margin-top: 15px; padding: 6px 18px; border: 1px solid rgba(201,168,76,0.3); border-radius: 20px; background: rgba(255,255,255,0.05); transition: all 0.3s ease; font-family: 'DM Sans', sans-serif; }
            .about-btn:hover { background: rgba(201,168,76,0.15); border-color: #F0C96A; box-shadow: 0 0 15px rgba(201,168,76,0.2); }
            .modal-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(5,13,31,0.85); backdrop-filter: blur(8px); z-index: 99999; display: flex; align-items: center; justify-content: center; opacity: 0; visibility: hidden; transition: all 0.3s ease; }
            #modal-toggle:checked ~ .modal-overlay { opacity: 1; visibility: visible; }
            .modal-box { background: linear-gradient(145deg, rgba(15,28,58,0.98), rgba(5,13,31,0.98)); border: 1px solid #F0C96A; border-radius: 20px; padding: 30px; width: 90%; max-width: 450px; position: relative; z-index: 100000; transform: scale(0.8) translateY(20px); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); text-align: center; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
            #modal-toggle:checked ~ .modal-overlay .modal-box { transform: scale(1) translateY(0); }
            .close-btn { position: absolute; top: 12px; right: 18px; color: #F0C96A !important; cursor: pointer; font-size: 22px; font-weight: bold; transition: 0.2s; }
            .close-btn:hover { color: #FFF !important; transform: scale(1.1); }
            .modal-bg-close { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 99999; cursor: default; }

            /* LANGUAGE DROPDOWN FIX */
            .stSelectbox label p, [data-testid="stSelectbox"] label p { color: #F0C96A !important; -webkit-text-fill-color: #F0C96A !important; font-weight: 700 !important; }
            .stSelectbox > div, .stSelectbox > div > div, [data-testid="stSelectbox"] > div, [data-baseweb="select"], [data-baseweb="select"] > div { background: #1A0808 !important; background-color: #1A0808 !important; }
            [data-baseweb="select"] > div { border: 2px solid #C9A84C !important; border-radius: 12px !important; }
            [data-baseweb="select"] span, [data-baseweb="select"] [class*="placeholder"], [data-baseweb="select"] [class*="singleValue"], [data-baseweb="select"] [class*="valueContainer"] span { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-weight: 700 !important; font-size: 15px !important; background: transparent !important; }
            [data-baseweb="select"] svg { fill: #C9A84C !important; }
            [data-baseweb="popover"], [data-baseweb="popover"] > div, [data-baseweb="popover"] > div > div, [data-baseweb="popover"] > div > div > div, [data-baseweb="popover"] ul, [data-baseweb="menu"], [data-baseweb="menu"] > div, [data-baseweb="menu"] > div > div, ul[role="listbox"], [data-testid="stVirtualDropdown"], [data-testid="stVirtualDropdown"] > div, [data-testid="stVirtualDropdown"] > div > div { background: #1A0808 !important; background-color: #1A0808 !important; }
            ul[role="listbox"], [data-baseweb="popover"] > div { border: 2px solid #C9A84C !important; border-radius: 12px !important; box-shadow: 0 8px 24px rgba(0,0,0,0.7) !important; overflow: hidden !important; }
            li[role="option"], [data-baseweb="menu"] li, ul[role="listbox"] li { background: transparent !important; background-color: transparent !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-weight: 600 !important; font-size: 15px !important; padding: 12px 18px !important; }
            li[role="option"]:hover, li[role="option"][aria-selected="true"] { background: rgba(201,168,76,0.25) !important; background-color: rgba(201,168,76,0.25) !important; color: #F0C96A !important; -webkit-text-fill-color: #F0C96A !important; }

            /* RADIO BUTTONS */
            div[role="radiogroup"] { background: linear-gradient(145deg, rgba(15,28,58,0.6) 0%, rgba(8,16,38,0.8) 100%); padding: 15px; border-radius: 20px; border: 1px solid rgba(201,168,76,0.2); box-shadow: 0 10px 30px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05); display: flex; justify-content: center; gap: 15px; margin-bottom: 30px; flex-wrap: wrap; }
            div[role="radiogroup"] label { background: rgba(255,255,255,0.08) !important; border-radius: 12px !important; border: 1px solid rgba(201,168,76,0.3) !important; padding: 12px 24px !important; cursor: pointer; }
            div[role="radiogroup"] label p, div[role="radiogroup"] label span, div[role="radiogroup"] label div { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-weight: 700 !important; font-size: 15px !important; text-shadow: 0 1px 2px rgba(0,0,0,0.8); }
            div[role="radiogroup"] label[data-checked="true"], div[role="radiogroup"] label:hover { background: linear-gradient(135deg, #152A5A, #0A1835) !important; border-color: #F0C96A !important; box-shadow: 0 8px 20px rgba(10,30,100,0.5) !important; }
            div[role="radiogroup"] label[data-checked="true"] p { color: #F0C96A !important; -webkit-text-fill-color: #F0C96A !important; }

            /* INPUT TEXT FIXES & AUTOFILL FIX */
            .stTextInput label p, .stChatInput label p { color: #C9A84C !important; font-size: 15px !important; font-weight: 700 !important; }
            .stTextInput input, .stChatInput textarea { background-color: #0D1F3C !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; caret-color: #F0C96A !important; font-weight: 600 !important; border: 1.5px solid rgba(201,168,76,0.5) !important; border-radius: 16px !important; padding: 15px !important; }
            .stChatInput textarea::placeholder, .stTextInput input::placeholder { color: rgba(255,255,255,0.5) !important; -webkit-text-fill-color: rgba(255,255,255,0.5) !important; }
            .stTextInput input:-webkit-autofill, .stTextInput input:-webkit-autofill:hover, .stTextInput input:-webkit-autofill:focus, .stTextInput input:-webkit-autofill:active { -webkit-box-shadow: 0 0 0 30px #0D1F3C inset !important; -webkit-text-fill-color: #FFFFFF !important; transition: background-color 5000s ease-in-out 0s; }

            /* RESULT CARDS FIX */
            .result-card { background: linear-gradient(145deg, rgba(15,28,58,0.9), rgba(8,16,38,0.95)); border: 1px solid rgba(201,168,76,0.3); border-left: 4px solid #F0C96A; border-radius: 16px; padding: 30px 35px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); margin-bottom: 25px; text-align: left; overflow: hidden; max-width: 100%; }
            .result-adhigaaram { display: inline-block; background: rgba(201,168,76,0.15); border: 1px solid rgba(201,168,76,0.3); border-radius: 8px; padding: 8px 16px; font-size: 14.5px; font-weight: 700; color: #F0C96A !important; margin-bottom: 15px; letter-spacing: 0.5px; }
            .verdict-text { font-size: 17px !important; color: #FFFFFF !important; line-height: 1.9 !important; margin-top: 10px; }
            .kural-meaning { margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(201,168,76,0.2); font-size: 16.5px; color: rgba(255,255,255,0.9) !important; line-height: 1.9; letter-spacing: 0.3px;}
            .card-advice, .card-solution, .card-warning { padding: 30px !important; line-height: 1.9; margin-top: 15px; margin-bottom: 25px;}
            
           /* STRICT EERADI VENBA ALIGNMENT & SCROLLBAR FIX */
            .kural-block { margin: 20px 0; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 12px; border-left: 3px solid #C9A84C; width: 100%; box-sizing: border-box; overflow-x: auto !important; display: block; scrollbar-width: thin; scrollbar-color: #F0C96A rgba(255,255,255,0.08); }
            .kural-block::-webkit-scrollbar { height: 10px !important; display: block !important; -webkit-appearance: none !important; }
            .kural-block::-webkit-scrollbar-track { background: rgba(255,255,255,0.08) !important; border-radius: 10px !important; visibility: visible !important; }
            .kural-block::-webkit-scrollbar-thumb { background: linear-gradient(90deg, #F0C96A, #C9A84C) !important; border-radius: 10px !important; border: 2px solid #050D1F !important; visibility: visible !important; }
            .kural-block::-webkit-scrollbar-thumb:hover { background: #FFFFFF !important; }
            .kural-line1, .kural-line2 { font-family: 'Noto Serif Tamil', serif; font-weight: 700; color: #FFFFFF !important; line-height: 2.0; margin: 0 !important; padding-right: 25px !important; padding-left: 0 !important; padding-top: 0 !important; padding-bottom: 0 !important; width: max-content; text-align: left; }
            .venba-tamil { display: block; width: max-content; min-width: 100%; margin:0; padding:0; }
            .venba-tamil .kural-line1, .venba-tamil .kural-line2 { font-size: clamp(14px, 4vw, 22px); white-space: nowrap !important; display: block; }
            .venba-eng { display: block; width: 100%; }
            .venba-eng .kural-line1, .venba-eng .kural-line2 { font-size: clamp(14px, 4vw, 20px); white-space: normal !important; word-wrap: break-word !important; }

            .percentage-container { display: flex; flex-wrap: wrap; justify-content: space-around; background: rgba(13,28,56,0.8); border: 1px solid rgba(201,168,76,0.3); border-radius: 16px; padding: 15px; margin-bottom: 20px; }
            .percentage-item { font-size: 15px; font-weight: 700; margin: 5px; color: #FFFFFF !important; padding: 5px 10px; border-radius: 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(201,168,76,0.2);}
            
            [data-testid="stChatMessage"] { background: linear-gradient(145deg, rgba(15,28,58,0.9), rgba(8,16,38,0.95)) !important; border: 1px solid rgba(201,168,76,0.3) !important; border-radius: 16px !important; padding: 25px !important; box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important; margin-bottom: 30px !important; }
            [data-testid="stBottom"] { position: static !important; background-color: transparent !important; }
            [data-testid="stBottomBlock"] { background: transparent !important; border: none !important; padding-bottom: 80px !important; margin-top: 30px;}
            [data-testid="stBottomBlock"] > div, .stChatInputContainer { background: transparent !important; }
            .stButton button { background: linear-gradient(135deg, #F0C96A, #C9A84C) !important; color: #050D1F !important; -webkit-text-fill-color: #050D1F !important; font-weight: 800 !important; font-size: 16px !important; border: none !important; border-radius: 12px !important; padding: 10px 25px !important; box-shadow: 0 8px 20px rgba(201,168,76,0.3) !important; width: 100%; }
            .footer-nav { position: fixed; left: 0; bottom: 0; width: 100%; height: 50px; background: #050D1F; border-top: 1px solid rgba(201,168,76,0.3); color: #C9A84C; text-align: center; display: flex; flex-direction: column; justify-content: center; z-index: 2000;}
            div.block-container { padding-top: 2rem; padding-bottom: 120px; position: relative; z-index: 10; }

            /* 🎙 INLINE MIC & BUTTON FIXES - HIDES WHITE BOX */
            [data-testid="stIFrame"], [data-testid="stIFrame"] iframe { background-color: transparent !important; border: none !important; }
            iframe[title="audio_recorder_streamlit.audio_recorder"] { border-radius: 50% !important; margin: 0 auto !important; display: block; }
            div[data-testid="stHorizontalBlock"] { align-items: end !important; } 
            .stButton button { margin-bottom: 2px !important; }

            /* MOBILE OPTIMIZATION */
            @media (max-width: 768px) {
                .modal-box { width: 95%; padding: 20px; }
                .modal-box h3 { font-size: 18px !important; }
                .modal-box p, .modal-box span { font-size: 13px !important; }
                .result-card { padding: 18px 12px; border-radius: 12px; margin-bottom: 20px; overflow: hidden; width: 100%; max-width: 100vw; }
                div[role="radiogroup"] { padding: 10px; gap: 8px; }
                div[role="radiogroup"] label { padding: 10px 10px !important; flex-grow: 1; text-align: center; }
                div[role="radiogroup"] label p, div[role="radiogroup"] label span { font-size: 12px !important; }
                .kural-block { padding: 12px 10px; width: 100%; box-sizing: border-box; overflow-x: auto !important; overflow-y: hidden; -webkit-overflow-scrolling: touch !important; display: block; }
                .kural-block::-webkit-scrollbar { display: block !important; height: 6px !important; -webkit-appearance: none !important; }
                .kural-block::-webkit-scrollbar-track { background: rgba(255,255,255,0.08) !important; visibility: visible !important; }
                .kural-block::-webkit-scrollbar-thumb { background: #F0C96A !important; border-radius: 10px !important; visibility: visible !important; }
                .venba-tamil { width: max-content !important; display: block; }
                .venba-tamil .kural-line1, .venba-tamil .kural-line2 { font-size: clamp(11px, 3.3vw, 16px) !important; letter-spacing: -0.1px !important; white-space: nowrap !important; padding-right: 20px !important; margin: 0 !important; display: block; width: max-content !important; }
                .stChatInput textarea, .stTextInput input { font-size: 14px !important; }
                [data-testid="stChatMessage"] { padding: 15px 12px !important; }
            }
        </style>
    """, unsafe_allow_html=True)

    components.html("""
        <script>
            function initEliteUI() {
                const doc = window.parent.document;
                const selectors = ['#MainMenu', 'header', 'footer', '.stDeployButton'];
                selectors.forEach(s => { const els = doc.querySelectorAll(s); els.forEach(e => e.style.display = 'none'); });
                doc.querySelectorAll('[data-baseweb="select"] > div > div').forEach(el => {
                    el.style.backgroundColor = '#1A0808';
                });
            }
            setInterval(initEliteUI, 80);
        </script>
    """, height=0, width=0)

inject_custom_css_and_js()
st.markdown('<div class="bg-blobs"></div>', unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 10px; animation: fadeSlideUp 0.8s ease;">
<span style="font-family: 'Cinzel', serif; font-size: clamp(28px, 6vw, 45px); font-weight: 900; letter-spacing: 2px; background: linear-gradient(135deg, #FFFFFF 30%, #F0C96A 60%, #FFFFFF 90%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1; text-align: center;">VALLUVAR 2.0</span>
<p style="font-size: 13px; font-weight: 600; letter-spacing: 2.5px; text-transform: uppercase; color: rgba(201,168,76,0.8); margin-top: 12px; text-align: center;">திருக்குறள் மின்னுலகம்</p>

<input type="checkbox" id="modal-toggle">
<label for="modal-toggle" class="about-btn">ℹ️️ About Software</label>

<div class="modal-overlay">
<label for="modal-toggle" class="modal-bg-close"></label>
<div class="modal-box">
<label for="modal-toggle" class="close-btn">✖</label>
<h3 style="color: #F0C96A !important; font-size: 22px; font-family: 'Cinzel', serif; margin-top:0; margin-bottom: 15px;">VALLUVAR 2.0</h3>

<p style="color: #FFFFFF !important; font-size: 14px; line-height: 1.6; margin-bottom: 15px; text-align: center;">
வாழ்க்கையில் பிரச்சனைகளா? உங்கள் அனைத்து உளவியல் போராட்டங்களுக்கும் வள்ளுவரின் 1330 குறள்கள் வழியே தீர்வு காண்போம்.<br><br>
<i style="color: rgba(255,255,255,0.8); font-size: 13.5px;">Facing life's challenges? Find solutions to all your emotional and psychological struggles through the wisdom of 1330 Thirukkurals.</i>
</p>

<div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(201,168,76,0.2); border-radius: 10px; padding: 15px; margin-bottom: 15px; text-align: left;">
<span style="color: #F0C96A !important; font-weight: bold; font-size: 14px;">✨ Key Features:</span><br>
<span style="color: #E0E0E0 !important; font-size: 13px;">🌐 Dual Language Support (Tamil/Eng)</span><br>
<span style="color: #E0E0E0 !important; font-size: 13px;">⚖️ Contextual Life Verdicts</span><br>
<span style="color: #E0E0E0 !important; font-size: 13px;">🤖 Interactive AI Mentor</span>
</div>

<div style="background: rgba(255,100,100,0.1); border: 1px solid rgba(255,100,100,0.3); border-radius: 10px; padding: 15px; margin-bottom: 15px; text-align: left;">
<span style="color: #FF8A80 !important; font-weight: bold; font-size: 14px;">📌 Important Note:</span><br>
<p style="color: #E0E0E0 !important; font-size: 12.5px; line-height: 1.6; margin: 8px 0 0 0;">
<b>1. Scroll to Read:</b> திருக்குறள் வரிகள் நீளமாக இருந்தால், பெட்டியை வலதுபுறம் Scroll / Swipe செய்து முழுமையாக வாசிக்கவும்.<br><br>
<b>2. 100% Privacy:</b> உங்கள் பெயர், முகவரி, Phone Number, IP Address போன்ற எந்த தனிப்பட்ட தரவுகளும் (Personal Data) எங்களால் சேகரிக்கப்படாது.
</p>
</div>

<div style="border-top: 1px dashed rgba(201,168,76,0.4); margin-top: 15px; padding-top: 15px; font-size: 13px; color: rgba(255,255,255,0.7) !important;">
Idealogy & Developed by<br><strong style="color: #F0C96A !important; font-size: 15px;">VIGNESH M (MIN E KAVI)</strong>
</div>
</div>
</div>
<div style="width: 200px; height: 1px; background: linear-gradient(90deg, transparent, #C9A84C, transparent); margin: 25px auto 25px;"></div>
</div>
""", unsafe_allow_html=True)

# --- LANGUAGE SELECTOR ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    lang = st.selectbox("🌐 Select Language / மொழி:", ["தமிழ்", "English"])

# ==========================================
# 1. ROBUST API KEY ROTATION & AUTO-DETECT MODEL
# ==========================================
@st.cache_resource
def get_working_model():
    key_list = ["key1", "key2", "key3", "key4", "key5"]
    
    if "current_key_index" not in st.session_state:
        st.session_state.current_key_index = 0

    attempts = 0
    while attempts < len(key_list):
        current_key_name = key_list[st.session_state.current_key_index]
        try:
            api_key = st.secrets.get(current_key_name)
            if api_key:
                genai.configure(api_key=api_key)
                
                valid_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        valid_models.append(m.name)
                
                if valid_models:
                    selected_model = valid_models[0] 
                    for m in valid_models:
                        if "gemini-1.5-flash" in m:
                            selected_model = m
                            break
                    clean_name = selected_model.replace("models/", "")
                    return genai.GenerativeModel(clean_name)
                    
        except Exception:
            pass 
        
        st.session_state.current_key_index = (st.session_state.current_key_index + 1) % len(key_list)
        attempts += 1
        
    st.error("❌ API Keys Error! உங்கள் API Keys சரியாக உள்ளதா என சரிபார்க்கவும்.")
    return None

model = get_working_model()

# ==========================================
# 2. DATA LOADING & FORMATTERS
# ==========================================
@st.cache_data
def load_data():
    file_path = 'thirukkural.json'
    if not os.path.exists(file_path): return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get("kural", data.get("kurals", []))
            return data
    except Exception as e:
        send_error_alert(f"Failed to load thirukkural.json: {e}")
        return []

kurals_list = load_data()

def extract_json_from_text(text):
    try:
        text = text.strip()
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx : end_idx + 1]
            json_str = json_str.replace('\n', ' ').replace('\r', '')
            return json.loads(json_str, strict=False)
        return None
    except: return None

def format_strict_venba(line1, line2):
    full_text = str(line1).strip() + " " + str(line2).strip()
    words = full_text.split()
    if len(words) >= 7:
        return " ".join(words[:4]), " ".join(words[4:])
    return line1, line2

def get_kural_from_local(kural_no, lang_mode):
    try:
        k_no = int(str(kural_no).strip()) if kural_no else 1
        if k_no < 1 or k_no > 1330: k_no = 1
        
        for k in kurals_list:
            if int(k.get('Number', k.get('number', k.get('KuralNo', 0)))) == k_no:
                l1, l2 = format_strict_venba(k.get('Line1', k.get('line1', '')), k.get('Line2', k.get('line2', '')))
                
                if lang_mode == "English":
                    eng_line = k.get('Translation', k.get('translation', k.get('eng', l1)))
                    eng_exp = k.get('explanation', k.get('eng_exp', k.get('Explanation', '')))
                    return {"line1": eng_line, "line2": "", "meaning": eng_exp, "number": k_no}
                else:
                    exp_keys = ['mv', 'tamil_exp', 'vilakkam', 'sp', 'mk']
                    tam_exp = next((k[key] for key in exp_keys if key in k), 'விளக்கம் இல்லை')
                    return {"line1": l1, "line2": l2, "meaning": tam_exp, "number": k_no}
    except Exception as e:
        pass
    
    if lang_mode == "English":
        return {"line1": "'A' leads letters; the Ancient Lord Leads and lords the entire world", "line2": "", "meaning": "As the letter A is the first of all letters, so the eternal God is first in the world", "number": 1}
    else:
        return {"line1": "அகர முதல எழுத்தெல்லாம் ஆதி", "line2": "பகவன் முதற்றே உலகு.", "meaning": "எழுத்துக்கள் எல்லாம் அகரத்தை அடிப்படையாக கொண்டிருக்கின்றன. அதுபோல உலகம் கடவுளை அடிப்படையாக கொண்டிருக்கிறது.", "number": 1}

def simulate_traffic_control(lang):
    loading_container = st.empty()
    with loading_container.container():
        loading_text = "⏳ வள்ளுவர் சிந்தித்துக்கொண்டிருக்கிறார்..." if lang == "தமிழ்" else "⏳ AI Valluvar is analyzing..."
        st.markdown(f"<h3 style='text-align:center; color:#F0C96A; font-family: Cinzel, serif;'>{loading_text}</h3>", unsafe_allow_html=True)
        progress_bar = st.progress(0)
        time.sleep(1)
        progress_bar.progress(100)
    loading_container.empty()

# DUAL LANGUAGE LABELS
if lang == "English":
    menu_options = ["🔍 Kural Search", "⚖️ AI Verdict", "🤖 AI Mentor"]
    placeholder_text = "e.g. Friendship, 100, Love"
    btn_search, btn_verdict = "Search", "Get Verdict"
    lbl_advice, lbl_chap, lbl_kno, lbl_exp, lbl_sol, lbl_warn = "📢 Advice:", "📖 Chapter:", "🔢 Kural No:", "💡 Explanation:", "✅ Solution:", "⚠️ Warning:"
else:
    menu_options = ["🔍 குறள் தேடல்", "⚖️ சூழல் தீர்வு", "🤖 AI வள்ளுவர்"]
    placeholder_text = "எ.கா: நட்பு, 100, அன்பு"
    btn_search, btn_verdict = "தேடு", "தீர்வு வழங்கு"
    lbl_advice, lbl_chap, lbl_kno, lbl_exp, lbl_sol, lbl_warn = "📢 அறிவுரை:", "📖 அதிகாரம்:", "🔢 எண்:", "💡 விளக்கம்:", "✅ தீர்வு:", "⚠️ எச்சரிக்கை:"

# ==================================================
# 3. MASTER TOGGLE (TEXT vs VOICE)
# ==================================================
st.markdown("<br>", unsafe_allow_html=True)
master_mode = st.radio("வள்ளுவருடன் எப்படி பேச விரும்புகிறீர்கள்? / Choose Mode:", 
                       ["📝 எழுத்து முறை (Text Interface)", "🎙️ வள்ளுவர் லைவ் (Voice Interface)"], 
                       horizontal=True)

# --------------------------------------------------
# TEXT INTERFACE (UPDATED WITH FLAWLESS VOICE TYPING)
# --------------------------------------------------
if master_mode == "📝 எழுத்து முறை (Text Interface)":
    
    selected_option = st.radio("", menu_options, horizontal=True)

    if selected_option in ["🔍 குறள் தேடல்", "🔍 Kural Search"]:
        if "search_limit" not in st.session_state: st.session_state.search_limit = 10
        search_term = st.text_input("தேட வேண்டிய சொல் / Search Keyword:", placeholder=placeholder_text)
        
        if st.button(btn_search): st.session_state.search_limit = 10 

        if kurals_list and search_term:
            results = [k for k in kurals_list if search_term.lower() in str(k).lower()]
            if results:
                total_results = len(results)
                st.success(f"✅ Found {total_results} results / {total_results} குறள்கள் கிடைத்தன:")
                for item in results[:st.session_state.search_limit]:
                    venba_class = "venba-eng" if lang == "English" else "venba-tamil"
                    
                    if lang == "English":
                        k_line1 = item.get('Translation', item.get('translation', item.get('eng', item.get('Line1', ''))))
                        k_line2 = "" 
                        k_mean = item.get('explanation', item.get('eng_exp', 'No explanation available.'))
                    else:
                        k_line1, k_line2 = format_strict_venba(item.get('Line1', item.get('line1', '')), item.get('Line2', item.get('line2', '')))
                        exp_keys = ['mv', 'tamil_exp', 'vilakkam', 'sp', 'mk']
                        k_mean = next((item[key] for key in exp_keys if key in item), 'விளக்கம் இல்லை')

                    kural_line2_html = f'<div class="kural-line2">{k_line2}</div>' if k_line2 else ''
                    kno = item.get('Number', item.get('number', item.get('KuralNo', '')))

                    st.markdown(f"""
    <div class="result-card">
    <div class="result-adhigaaram">{lbl_kno} {kno}</div>
    <div class="kural-block">
    <div class="{venba_class}">
    <div class="kural-line1">{k_line1}</div>
    {kural_line2_html}
    </div>
    </div>
    <div class="kural-meaning"><strong>{lbl_exp}</strong><br>{k_mean}</div>
    </div>
    """, unsafe_allow_html=True)
                
                if st.session_state.search_limit < total_results:
                    btn_more = f"⬇️ Show More ({total_results - st.session_state.search_limit})" if lang == "English" else f"⬇️ இன்னும் காட்டு ({total_results - st.session_state.search_limit})"
                    if st.button(btn_more):
                        st.session_state.search_limit += 10
                        st.rerun() 
            else:
                if search_term: st.warning("No related Kural found. / தொடர்புடைய குறள் எதுவும் இல்லை.")

    # --- VERDICT MODE WITH INLINE VOICE TYPING ---
    elif selected_option in ["⚖️ சூழல் தீர்வு", "⚖️ AI Verdict"]:
        if "v_prompt" not in st.session_state: st.session_state.v_prompt = ""
        if "last_v_mic" not in st.session_state: st.session_state.last_v_mic = None
        
        st.markdown(f"<h4 style='color: #F0C96A; font-size: 15px;'>உங்கள் குழப்பம் / Your Situation:</h4>", unsafe_allow_html=True)
        
        v_col1, v_col2, v_col3 = st.columns([7.0, 1.5, 1.5])
        with v_col1:
            # Removed the exact key link to avoid Streamlit modification error
            v_input = st.text_input("Situation", value=st.session_state.v_prompt, key="v_txt_widget", label_visibility="collapsed", placeholder="e.g. கடன் வாங்கலாமா ? / Should I take a loan?")
        with v_col2:
            v_mic = audio_recorder(text="", recording_color="#FF8A80", neutral_color="#F0C96A", icon_name="microphone", icon_size="2x", key="v_mic_rec")
        with v_col3:
            verdict_btn_click = st.button(btn_verdict, key="v_btn", use_container_width=True)
            
        if v_mic and v_mic != st.session_state.last_v_mic:
            st.session_state.last_v_mic = v_mic
            with st.spinner("டைப் செய்கிறேன்..."):
                try:
                    r = sr.Recognizer()
                    with sr.AudioFile(io.BytesIO(v_mic)) as source:
                        audio_data = r.record(source)
                        rec_lang = 'ta-IN' if lang == "தமிழ்" else 'en-IN'
                        transcribed = r.recognize_google(audio_data, language=rec_lang)
                        
                        st.session_state.v_prompt = transcribed
                        st.rerun()
                except sr.UnknownValueError:
                    st.error("குரல் தெளிவாக இல்லை, மீண்டும் பேசவும்.")
                except Exception as e:
                    pass
            
        if v_input != st.session_state.v_prompt:
            st.session_state.v_prompt = v_input
            
        if verdict_btn_click:
            user_input = st.session_state.v_prompt
            if not user_input: st.warning("Please type or speak your question.")
            elif not model: st.error("No AI Connection.")
            else:
                simulate_traffic_control(lang)
                with st.spinner("📜 Analyzing your situation..."):
                    try:
                        venba_class = "venba-eng" if lang == "English" else "venba-tamil"
                        
                        if lang == "English":
                            prompt = f"""Context: '{user_input}'. Act as Thiruvalluvar. Reply strictly in JSON. Is this a general question? 'yes' or 'no' in 'is_general'. If 'yes', provide 3 tags. 
    If 'no', score the situation from 0 to 100 independently for:
    1. 'aram' (Ethics): Is it morally right and harmless? (CRITICAL: Suicide, self-harm, murder, cheating MUST be 0).
    2. 'porul' (Practicality/Wealth): Does it build career or practical life?
    3. 'inbam' (Joy/Love): Does it bring true peace or relationship harmony?
    IMPORTANT: Provide a valid 'kural_number' (1-1330) and EXACT official 'adhigaaram' (Chapter Name). 
    Format: {{"verdict": "Short advice", "is_general": "no", "aram": 0, "porul": 0, "inbam": 0, "tag1": "", "tag2": "", "tag3": "", "kural_number": 120, "adhigaaram": "Chapter Name"}}"""
                            lbl_aram, lbl_porul, lbl_inbam = "⚖️ Virtue", "💰 Wealth", "❤️ Peace/Love"
                        else:
                            prompt = f"""சூழல்: '{user_input}'. நீ திருவள்ளுவர். பதில் JSON-ல் மட்டும். இது பொது கேள்வியா? 'is_general'-ல் 'yes' அல்லது 'no'. 'yes' என்றால் 3 tags. 
    'no' என்றால், இந்தச் செயலை 0 முதல் 100 வரை தனித்தனியாக மதிப்பிடவும்:
    1. 'aram' (அறம்): இது தர்மமா? யாருக்கும் தீங்கு விளைவிக்காததா? (எச்சரிக்கை: தற்கொலை, கொலை, ஏமாற்றுதல் போன்ற தீய செயல்களுக்கு அறம் கண்டிப்பாக 0 ஆக இருக்க வேண்டும்).
    2. 'porul' (பொருள்): இது வாழ்க்கைக்கு அல்லது பொருளாதாரத்திற்கு உதவுமா?
    3. 'inbam' (இன்பம்): இது மனதிற்கு உண்மையான அமைதியையோ அன்பையோ தருமா?
    உண்மையான 'kural_number' (1-1330) மற்றும் சரியான 'adhigaaram' தரவும். 
    Format: {{"verdict": "அறிவுரை", "is_general": "no", "aram": 0, "porul": 0, "inbam": 0, "tag1": "", "tag2": "", "tag3": "", "kural_number": 120, "adhigaaram": "அதிகாரத்தின் பெயர்"}}"""
                            lbl_aram, lbl_porul, lbl_inbam = "⚖️ அறம்", "💰 பொருள்", "❤️ அமைதி/இன்பம்"

                        response = model.generate_content(prompt)
                        res = extract_json_from_text(response.text)
                        
                        if res:
                            log_to_gsheets("Decision Mode", user_input, res.get('verdict', ''))
                            local_data = get_kural_from_local(res.get('kural_number', 1), lang)
                            kural_line2_html = f'<div class="kural-line2">{local_data["line2"]}</div>' if local_data["line2"] else ''
                            ai_chap = res.get('adhigaaram', 'அதிகாரம்')
                            
                            is_gen = str(res.get('is_general', 'no')).strip().lower() == 'yes'
                            dynamic_ui_html = ""
                            
                            if is_gen:
                                t1 = str(res.get('tag1', '')).strip()
                                t2 = str(res.get('tag2', '')).strip()
                                t3 = str(res.get('tag3', '')).strip()
                                dynamic_ui_html = f"""<div class="percentage-container">
    <span class="percentage-item" style="color:#A5D6A7 !important;">🏷️ {t1}</span>
    <span class="percentage-item" style="color:#F0C96A !important;">🏷️ {t2}</span>
    <span class="percentage-item" style="color:#FF8A80 !important;">🏷️ {t3}</span>
    </div>"""
                            else:
                                arm = res.get('aram', 33)
                                prl = res.get('porul', 33)
                                inb = res.get('inbam', 34)
                                dynamic_ui_html = f"""<div class="percentage-container">
    <span class="percentage-item" style="color:#A5D6A7 !important;">{lbl_aram}: {arm}%</span>
    <span class="percentage-item" style="color:#F0C96A !important;">{lbl_porul}: {prl}%</span>
    <span class="percentage-item" style="color:#FF8A80 !important;">{lbl_inbam}: {inb}%</span>
    </div>"""
                            
                            st.markdown(f"""
    <div class="result-card card-advice">
    <div class="result-adhigaaram">{lbl_advice}</div>
    <div class="verdict-text">{res.get('verdict')}</div>
    </div>
    {dynamic_ui_html}
    <div class="result-card">
    <div class="result-adhigaaram">{lbl_chap} {ai_chap} &nbsp;|&nbsp; {lbl_kno} {local_data['number']}</div>
    <div class="kural-block">
    <div class="{venba_class}">
    <div class="kural-line1">{local_data['line1']}</div>
    {kural_line2_html}
    </div>
    </div>
    <div class="kural-meaning"><strong>{lbl_exp}</strong><br>{local_data['meaning']}</div>
    </div>
    """, unsafe_allow_html=True)
                        else:
                            st.error("AI Output Error.")
                    except Exception as e:
                        send_error_alert(f"Verdict Generation Error: {e}")
                        st.error(f"Error: {e}")

    # --- CHAT MODE WITH INLINE VOICE TYPING ---
    elif selected_option in ["🤖 AI வள்ளுவர்", "🤖 AI Mentor"]:
        init_msg = "உங்களால் தீர்க்க முடியாத மனப்போராட்டங்களைச் சொல்லுங்கள். அதற்கான அறிவுரை, தீர்வு மற்றும் செயல்படாவிடில் வரும் அபாயங்களை அறிந்துகொள்ளுங்கள்..." if lang == "தமிழ்" else "Greetings! I am AI Valluvar. Ask your questions to get wisdom from Thirukkural..."
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": init_msg, "kural_data": None}]

        for message in st.session_state.messages:
            role = "assistant" if message["role"] == "assistant" else "user"
            with st.chat_message(role):
                if role == "assistant" and "{" in message["content"]:
                     r = extract_json_from_text(message["content"])
                     if r:
                         venba_class = "venba-eng" if lang == "English" else "venba-tamil"
                         local_data = message.get("kural_data")
                         if not local_data:
                             local_data = get_kural_from_local(r.get('kural_number', 1), lang)
                         
                         kural_line2_html = f'<div class="kural-line2">{local_data["line2"]}</div>' if local_data["line2"] else ''
                         ai_chap = r.get('adhigaaram', 'அதிகாரம்')
                         
                         st.markdown(f"""
    <div class="result-card card-advice">
    <div class="result-adhigaaram">{lbl_advice}</div><div class="verdict-text">{r.get('verdict')}</div>
    </div>
    <div class="result-card">
    <div class="result-adhigaaram">{lbl_chap} {ai_chap} &nbsp;|&nbsp; {lbl_kno} {local_data['number']}</div>
    <div class="kural-block">
    <div class="{venba_class}">
    <div class="kural-line1">{local_data['line1']}</div>
    {kural_line2_html}
    </div>
    </div>
    <div class="kural-meaning">{local_data['meaning']}</div>
    </div>
    <div class="result-card card-solution">
    <div class="result-adhigaaram">{lbl_sol}</div><div class="verdict-text">{r.get('solution')}</div>
    </div>
    <div class="result-card card-warning">
    <div class="result-adhigaaram">{lbl_warn}</div><div class="verdict-text">{r.get('consequence')}</div>
    </div>
    """, unsafe_allow_html=True)
                     else: st.write(message["content"])
                else: st.write(message["content"])

        if "pending_chat_prompt" in st.session_state:
            prompt = st.session_state.pending_chat_prompt
            del st.session_state.pending_chat_prompt
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)

            if model:
                with st.chat_message("assistant"):
                    with st.spinner("📜 வள்ளுவர் is thinking..."):
                        try:
                            venba_class = "venba-eng" if lang == "English" else "venba-tamil"
                            
                            if lang == "English":
                                sys_msg = "Act as Thiruvalluvar. Reply strictly in JSON format. Provide the most apt kural number and its Chapter Name. Format: { \"verdict\": \"Short practical advice\", \"solution\": \"Actionable solution\", \"consequence\": \"Warning if ignored\", \"kural_number\": 120, \"adhigaaram\": \"Chapter Name\" }"
                            else:
                                sys_msg = "நீ திருவள்ளுவர். பதில் JSON வடிவில் மட்டும் தமிழில் இருக்க வேண்டும். இந்த சூழலுக்கு ஏற்ற சரியான திருக்குறள் எண் மற்றும் அதிகாரத்தின் பெயர் தரவும். Format: { \"verdict\": \"அறிவுரை\", \"solution\": \"நடைமுறை தீர்வு\", \"consequence\": \"எச்சரிக்கை\", \"kural_number\": 120, \"adhigaaram\": \"அதிகாரத்தின் பெயர்\" }"
                            
                            response = model.generate_content(sys_msg + "\n\nQuestion/கேள்வி: " + prompt)
                            r = extract_json_from_text(response.text)
                            
                            if r:
                                log_to_gsheets("Chat Mode", prompt, r.get('verdict', ''))
                                local_data = get_kural_from_local(r.get('kural_number', 1), lang)
                                kural_line2_html = f'<div class="kural-line2">{local_data["line2"]}</div>' if local_data["line2"] else ''
                                ai_chap = r.get('adhigaaram', 'அதிகாரம்')

                                st.markdown(f"""
    <div class="result-card card-advice">
    <div class="result-adhigaaram">{lbl_advice}</div><div class="verdict-text">{r.get('verdict')}</div>
    </div>
    <div class="result-card">
    <div class="result-adhigaaram">{lbl_chap} {ai_chap} &nbsp;|&nbsp; {lbl_kno} {local_data['number']}</div>
    <div class="kural-block">
    <div class="{venba_class}">
    <div class="kural-line1">{local_data['line1']}</div>
    {kural_line2_html}
    </div>
    </div>
    <div class="kural-meaning">{local_data['meaning']}</div>
    </div>
    <div class="result-card card-solution">
    <div class="result-adhigaaram">{lbl_sol}</div><div class="verdict-text">{r.get('solution')}</div>
    </div>
    <div class="result-card card-warning">
    <div class="result-adhigaaram">{lbl_warn}</div><div class="verdict-text">{r.get('consequence')}</div>
    </div>
    """, unsafe_allow_html=True)
                                st.session_state.messages.append({"role": "assistant", "content": response.text, "kural_data": local_data})
                            else:
                                st.write(response.text)
                                st.session_state.messages.append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            send_error_alert(f"AI Mentor Generation Error: {e}")
                            st.error(f"Error: {e}")
                            
        # INLINE CHAT INPUT WITH VOICE TYPING
        if "c_prompt" not in st.session_state: st.session_state.c_prompt = ""
        if "last_c_mic" not in st.session_state: st.session_state.last_c_mic = None
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        c_col1, c_col2, c_col3 = st.columns([7.0, 1.5, 1.5])
        with c_col1:
            c_input = st.text_input("Ask", value=st.session_state.c_prompt, key="c_txt_widget", label_visibility="collapsed", placeholder="வள்ளுவரிடம் கேட்க... / Ask Valluvar...")
        with c_col2:
            c_mic = audio_recorder(text="", recording_color="#FF8A80", neutral_color="#F0C96A", icon_name="microphone", icon_size="2x", key="c_mic_rec")
        with c_col3:
            c_btn_text = "கேள் 📤" if lang == "தமிழ்" else "Send 📤"
            send_btn = st.button(c_btn_text, key="c_send", use_container_width=True)
            
        if c_mic and c_mic != st.session_state.last_c_mic:
            st.session_state.last_c_mic = c_mic
            with st.spinner("டைப் செய்கிறேன்..."):
                try:
                    r = sr.Recognizer()
                    with sr.AudioFile(io.BytesIO(c_mic)) as source:
                        audio_data = r.record(source)
                        rec_lang = 'ta-IN' if lang == "தமிழ்" else 'en-IN'
                        transcribed = r.recognize_google(audio_data, language=rec_lang)
                        
                        st.session_state.c_prompt = transcribed
                        st.rerun()
                except sr.UnknownValueError:
                    st.error("குரல் தெளிவாக இல்லை, மீண்டும் பேசவும்.")
                except Exception as e:
                    pass
                
        if c_input != st.session_state.c_prompt:
            st.session_state.c_prompt = c_input
            
        if send_btn and st.session_state.c_prompt:
            st.session_state.pending_chat_prompt = st.session_state.c_prompt
            st.session_state.c_prompt = "" 
            st.rerun()

# --------------------------------------------------
# VOICE INTERFACE (VALLUVAR INTELLIGENCE - CONTEXT AWARE)
# --------------------------------------------------
elif master_mode == "🎙️ வள்ளுவர் லைவ் (Voice Interface)":
    
    # 1. நினைவாற்றலை உருவாக்குதல் (Memory Initialization)
    if "voice_history" not in st.session_state:
        st.session_state.voice_history = []

    st.markdown("""
        <div style='text-align: center; margin-top: 20px; margin-bottom: 20px;'>
            <h2 style='color: #F0C96A; font-family: Cinzel, serif;'>வள்ளுவர் கேட்கிறார்...</h2>
            <p style='color: #a0aab2; font-size: 14px;'>உங்கள் மனக் குழப்பங்களை வாய்மொழியாகக் கூறுங்கள்</p>
        </div>
    """, unsafe_allow_html=True)

    avatar_placeholder = st.empty()
    avatar_placeholder.image("valluvar intelligence.jpg", use_container_width=True) 

    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    audio_bytes = audio_recorder(text="Click to Record 🎙️", recording_color="#FF8A80", neutral_color="#F0C96A", icon_name="microphone", icon_size="3x")
    st.markdown("</div>", unsafe_allow_html=True)

    if audio_bytes:
        with st.spinner("உங்கள் குரலை புரிந்துகொள்கிறேன்..."):
            try:
                r = sr.Recognizer()
                audio_file = io.BytesIO(audio_bytes)
                with sr.AudioFile(audio_file) as source:
                    audio_data = r.record(source)
                    rec_lang = 'ta-IN' if lang == "தமிழ்" else 'en-IN'
                    user_speech_text = r.recognize_google(audio_data, language=rec_lang) 
                
                st.success(f"நீங்கள்: {user_speech_text}")
                
            except sr.UnknownValueError:
                st.error("மன்னிக்கவும், உங்கள் குரல் தெளிவாக இல்லை. மீண்டும் பேசவும்.")
                user_speech_text = None

        if user_speech_text and model:
            with st.spinner("📜 வள்ளுவர் சிந்திக்கிறார்..."):
                try:
                    # முந்தைய உரையாடல்களை மெமரியில் சேர்ப்பது
                    st.session_state.voice_history.append(f"User: {user_speech_text}")
                    if len(st.session_state.voice_history) > 5: # கடைசி 5 உரையாடல்களை மட்டும் நியாபகம் வைத்துக்கொள்ளும்
                        st.session_state.voice_history.pop(0)
                        
                    context_string = "\n".join(st.session_state.voice_history)

                    # 🔥 ADVANCED PROMPT FOR INTELLIGENT CONVERSATION 🔥
                    sys_msg = f"""நீ ஒரு 'Valluvar Intelligence'. அறம் சார்ந்த ஒரு மெய்நிகர் வழிகாட்டி (Virtual Mentor). 
                    இது ஒரு தொடர் உரையாடல். முந்தைய உரையாடல் பின்னணி:
                    {context_string}
                    
                    விதிகள்:
                    1. பயனர் ஒரு புதிய தலைப்பில் கேள்வி கேட்டால், அதற்குப் பொருத்தமான திருக்குறளைத் தேர்ந்தெடுத்து, "type": "new_kural" என செட் செய்.
                    2. பயனர் முந்தைய கேள்வியின் தொடர்ச்சியாக (Follow-up / Cross Question) கேட்டால் (உ-ம்: "அப்ப நான் கடனே வாங்கக் கூடாதா?"), மீண்டும் ஒரு புதிய திருக்குறளை சொல்லாதே! அதற்குப் பதிலாக அறம் சார்ந்த தத்துவத்தின் அடிப்படையில் ஒரு நண்பனைப் போல இயல்பாக வாய்மொழியாகப் புரியவை. அப்போது "type": "follow_up" என செட் செய்.
                    3. இயந்திரத்தனமான வார்த்தைகளைத் தவிர்த்து, மனிதனைப் போல உணர்வுபூர்வமாகப் பேசு.
                    
                    Output strictly in JSON:
                    {{
                        "type": "new_kural" அல்லது "follow_up",
                        "kural_number": 120 (follow_up என்றால் 0 என போடவும்),
                        "adhigaaram": "அதிகாரத்தின் பெயர்" (follow_up என்றால் "" என விடவும்),
                        "audio_script": "குரலாக ஒலிக்க வேண்டிய சரளமான தமிழ் வசனம்"
                    }}"""
                    
                    response = model.generate_content(sys_msg)
                    res_json = extract_json_from_text(response.text)
                    
                    if res_json:
                        # ஏஐயின் பதிலையும் மெமரியில் சேர்ப்பது
                        st.session_state.voice_history.append(f"Valluvar: {res_json.get('audio_script', '')}")
                        
                        final_speech_text = res_json.get('audio_script', '')
                        
                        # UI Logic: புதிய குறள் என்றால் மட்டும் ஸ்க்ரீனில் திருக்குறளைக் காட்டும், இல்லையென்றால் உரையாடலாகவே தொடரும்.
                        if res_json.get('type') == "new_kural":
                            local_data = get_kural_from_local(res_json.get('kural_number', 1), lang)
                            kural_line2_html = f'<div class="kural-line2">{local_data["line2"]}</div>' if local_data["line2"] else ''
                            ai_chap = res_json.get('adhigaaram', 'அதிகாரம்')
                            venba_class = "venba-eng" if lang == "English" else "venba-tamil"
                            
                            st.markdown(f"""
                            <div class="result-card">
                            <div class="result-adhigaaram">{lbl_chap} {ai_chap} &nbsp;|&nbsp; {lbl_kno} {local_data['number']}</div>
                            <div class="kural-block">
                            <div class="{venba_class}">
                            <div class="kural-line1">{local_data['line1']}</div>
                            {kural_line2_html}
                            </div>
                            </div>
                            <div class="kural-meaning">{local_data['meaning']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("தொடர் உரையாடல்...") # Follow-up கேள்விக்கு கார்டு வராது, வாய்ஸ் மட்டுமே வரும்.
                        
                        # மைக்ரோசாஃப்ட் Edge TTS (இலவச Neural Voice) பயன்படுத்துதல்
                        async def generate_valluvar_voice(text, filename):
                            communicate = edge_tts.Communicate(text, "ta-IN-ValluvarNeural")
                            await communicate.save(filename)

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                            temp_path = fp.name

                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        loop.run_until_complete(generate_valluvar_voice(final_speech_text, temp_path))
                        
                        with open(temp_path, "rb") as f:
                            st.audio(f.read(), format="audio/mp3", autoplay=True)
                            
                        log_to_gsheets("Live Voice Mode", user_speech_text, final_speech_text)

                except Exception as e:
                    send_error_alert(f"Live Voice Generation Error: {e}")
                    st.error(f"Error: {e}")
# --- FOOTER ---
st.markdown("""
<div class="footer-nav">
<p>© All rights reserved by <strong style="color:#C9A84C !important;">MIN E KAVI (மின்கவி)</strong> &nbsp;|&nbsp; Idealogy & Developed by <strong style="color:#C9A84C !important;">VIGNESH M</strong></p>
</div>
""", unsafe_allow_html=True)
