import streamlit as st
import asyncio
import edge_tts
import tempfile
import base64
import textwrap
import json
import os
import time
import random
import google.generativeai as genai
from google.api_core import exceptions
import streamlit.components.v1 as components
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import asyncio
import edge_tts
import tempfile
import base64

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Valluvar 2.0 - Dual Language",
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 🔊 MICROSOFT EDGE TTS (VALLUVAR NEURAL VOICE)
# ==========================================
def generate_edge_tts_audio(text_to_read, lang_code, unique_id):
    try:
        voice = 'ta-IN-ValluvarNeural' if lang_code == "தமிழ்" else 'en-US-ChristopherNeural'
        
        async def amain():
            communicate = edge_tts.Communicate(text_to_read, voice)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_path = fp.name
            await communicate.save(temp_path)
            return temp_path
            
        temp_audio_path = asyncio.run(amain())
        
        with open(temp_audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            
        b64 = base64.b64encode(audio_bytes).decode()
        
        # Unique ID-ஐ HTML-ல் சேர்ப்பதன் மூலம் பழைய ஆடியோ ப்ளே ஆவது தடுக்கப்படும்.
        audio_html = f'<audio id="{unique_id}" controls style="width: 100%; height: 40px; margin-top: 15px; border-radius: 8px; outline: none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
        
        os.remove(temp_audio_path)
        return audio_html
    except Exception as e:
        return f"<p style='color:#FF8A80; font-size:12px;'>Audio generation error: {e}</p>"

# ==========================================
# 💾 DATA LOGGING SYSTEM (GOOGLE SHEETS)
# ==========================================
def log_to_gsheets(mode, query, response):
    try:
        if "gcp_service_account" not in st.secrets:
            return
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("Valluvar Records").sheet1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_response = str(response).replace('\n', ' ').replace('\r', '')
        sheet.append_row([timestamp, mode, query, clean_response])
    except Exception as e: pass

# ==========================================
# 📧 EMAIL ALERT SYSTEM
# ==========================================
def send_error_alert(error_message):
    try:
        if "email" not in st.secrets: return
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
    except Exception as e: pass

# ==========================================
# 🚀 ELITE 3D UI SCRIPT & MOBILE OPTIMIZATION
# ==========================================
def inject_custom_css_and_js():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;900&family=DM+Sans:wght@300;400;500;600;700&family=Noto+Serif+Tamil:wght@400;700&display=swap');
            [data-testid="stAppViewContainer"] { background: #050D1F !important; background-image: radial-gradient(circle at 50% 0%, #0D1F3C 0%, #050D1F 70%); color: #FFFFFF !important; font-family: 'DM Sans', sans-serif !important; }
            [data-testid="stHeader"] { background: transparent !important; }
            #MainMenu, header, footer, .stDeployButton {visibility: hidden;}
            p, span, div, label { color: #FFFFFF !important; }
            .bg-blobs { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
            .bg-blobs::before, .bg-blobs::after { content: ''; position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.5; animation: blobFloat 8s ease-in-out infinite; }
            .bg-blobs::before { width: 400px; height: 400px; background: rgba(201,168,76,0.07); top: -100px; left: -100px; }
            .bg-blobs::after { width: 500px; height: 500px; background: rgba(20,50,150,0.12); bottom: -150px; right: -100px; animation-delay: -3s; }
            @keyframes blobFloat { 0%, 100% { transform: translate(0,0) scale(1); } 50% { transform: translate(20px,-20px) scale(1.05); } }
            #modal-toggle { display: none; }
            .about-btn { display: inline-block; cursor: pointer; color: #F0C96A !important; font-size: 13px; font-weight: 700; letter-spacing: 1px; margin-top: 15px; padding: 6px 18px; border: 1px solid rgba(201,168,76,0.3); border-radius: 20px; background: rgba(255,255,255,0.05); transition: all 0.3s ease; }
            .about-btn:hover { background: rgba(201,168,76,0.15); border-color: #F0C96A; box-shadow: 0 0 15px rgba(201,168,76,0.2); }
            .modal-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(5,13,31,0.85); backdrop-filter: blur(8px); z-index: 99999; display: flex; align-items: center; justify-content: center; opacity: 0; visibility: hidden; transition: all 0.3s ease; }
            #modal-toggle:checked ~ .modal-overlay { opacity: 1; visibility: visible; }
            .modal-box { background: linear-gradient(145deg, rgba(15,28,58,0.98), rgba(5,13,31,0.98)); border: 1px solid #F0C96A; border-radius: 20px; padding: 30px; width: 90%; max-width: 450px; position: relative; z-index: 100000; transform: scale(0.8) translateY(20px); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); text-align: center; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
            #modal-toggle:checked ~ .modal-overlay .modal-box { transform: scale(1) translateY(0); }
            .close-btn { position: absolute; top: 12px; right: 18px; color: #F0C96A !important; cursor: pointer; font-size: 22px; font-weight: bold; transition: 0.2s; }
            .close-btn:hover { color: #FFF !important; transform: scale(1.1); }
            .modal-bg-close { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 99999; cursor: default; }
            .stSelectbox label p, [data-testid="stSelectbox"] label p { color: #F0C96A !important; -webkit-text-fill-color: #F0C96A !important; font-weight: 700 !important; }
            .stSelectbox > div, .stSelectbox > div > div, [data-testid="stSelectbox"] > div, [data-baseweb="select"], [data-baseweb="select"] > div { background: #1A0808 !important; background-color: #1A0808 !important; }
            [data-baseweb="select"] > div { border: 2px solid #C9A84C !important; border-radius: 12px !important; }
            [data-baseweb="select"] span, [data-baseweb="select"] [class*="placeholder"], [data-baseweb="select"] [class*="singleValue"], [data-baseweb="select"] [class*="valueContainer"] span { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-weight: 700 !important; font-size: 15px !important; }
            [data-baseweb="select"] svg { fill: #C9A84C !important; }
            [data-baseweb="popover"], ul[role="listbox"], [data-testid="stVirtualDropdown"] { background: #1A0808 !important; background-color: #1A0808 !important; border: 2px solid #C9A84C !important; border-radius: 12px !important; }
            li[role="option"] { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-weight: 600 !important; font-size: 15px !important; }
            li[role="option"]:hover, li[role="option"][aria-selected="true"] { background: rgba(201,168,76,0.25) !important; color: #F0C96A !important; -webkit-text-fill-color: #F0C96A !important; }
            div[role="radiogroup"] { background: linear-gradient(145deg, rgba(15,28,58,0.6) 0%, rgba(8,16,38,0.8) 100%); padding: 15px; border-radius: 20px; border: 1px solid rgba(201,168,76,0.2); display: flex; justify-content: center; gap: 15px; margin-bottom: 30px; flex-wrap: wrap; }
            div[role="radiogroup"] label { background: rgba(255,255,255,0.08) !important; border-radius: 12px !important; border: 1px solid rgba(201,168,76,0.3) !important; padding: 12px 24px !important; cursor: pointer; }
            div[role="radiogroup"] label p { color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-weight: 700 !important; font-size: 15px !important; }
            div[role="radiogroup"] label[data-checked="true"] { background: linear-gradient(135deg, #152A5A, #0A1835) !important; border-color: #F0C96A !important; box-shadow: 0 8px 20px rgba(10,30,100,0.5) !important; }
            div[role="radiogroup"] label[data-checked="true"] p { color: #F0C96A !important; -webkit-text-fill-color: #F0C96A !important; }
            .stTextInput label p, .stChatInput label p { color: #C9A84C !important; font-size: 15px !important; font-weight: 700 !important; }
            .stTextInput input, .stChatInput textarea { background-color: #0D1F3C !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; border: 1.5px solid rgba(201,168,76,0.5) !important; border-radius: 16px !important; padding: 15px !important; }
            .result-card { background: linear-gradient(145deg, rgba(15,28,58,0.9), rgba(8,16,38,0.95)); border: 1px solid rgba(201,168,76,0.3); border-left: 4px solid #F0C96A; border-radius: 16px; padding: 30px 35px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); margin-bottom: 25px; text-align: left; }
            .result-adhigaaram { display: inline-block; background: rgba(201,168,76,0.15); border: 1px solid rgba(201,168,76,0.3); border-radius: 8px; padding: 8px 16px; font-size: 14.5px; font-weight: 700; color: #F0C96A !important; margin-bottom: 15px; }
            .verdict-text { font-size: 17px !important; color: #FFFFFF !important; line-height: 1.9 !important; margin-top: 10px; }
            .kural-meaning { margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(201,168,76,0.2); font-size: 16.5px; color: rgba(255,255,255,0.9) !important; line-height: 1.9; }
            .card-advice, .card-solution, .card-warning { padding: 30px !important; line-height: 1.9; margin-top: 15px; margin-bottom: 25px;}
            .kural-block { margin: 20px 0; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 12px; border-left: 3px solid #C9A84C; width: 100%; box-sizing: border-box; overflow-x: auto !important; display: block; scrollbar-width: thin; scrollbar-color: #F0C96A rgba(255,255,255,0.08); }
            .kural-block::-webkit-scrollbar { height: 10px !important; display: block !important; -webkit-appearance: none !important; }
            .kural-line1, .kural-line2 { font-family: 'Noto Serif Tamil', serif; font-weight: 700; color: #FFFFFF !important; line-height: 2.0; margin: 0 !important; width: max-content; text-align: left; }
            .venba-tamil { display: block; width: max-content; min-width: 100%; }
            .venba-tamil .kural-line1, .venba-tamil .kural-line2 { font-size: clamp(14px, 4vw, 22px); white-space: nowrap !important; }
            .venba-eng { display: block; width: 100%; }
            .venba-eng .kural-line1, .venba-eng .kural-line2 { font-size: clamp(14px, 4vw, 20px); white-space: normal !important; }
            .percentage-container { display: flex; flex-wrap: wrap; justify-content: space-around; background: rgba(13,28,56,0.8); border: 1px solid rgba(201,168,76,0.3); border-radius: 16px; padding: 15px; margin-bottom: 20px; }
            .percentage-item { font-size: 15px; font-weight: 700; margin: 5px; color: #FFFFFF !important; padding: 5px 10px; border-radius: 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(201,168,76,0.2);}
            [data-testid="stChatMessage"] { background: linear-gradient(145deg, rgba(15,28,58,0.9), rgba(8,16,38,0.95)) !important; border: 1px solid rgba(201,168,76,0.3) !important; border-radius: 16px !important; padding: 25px !important; box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important; margin-bottom: 30px !important; }
            [data-testid="stBottomBlock"] { background: transparent !important; border: none !important; padding-bottom: 80px !important; margin-top: 30px;}
            .stButton button { background: linear-gradient(135deg, #F0C96A, #C9A84C) !important; color: #050D1F !important; -webkit-text-fill-color: #050D1F !important; font-weight: 800 !important; font-size: 16px !important; border: none !important; border-radius: 12px !important; padding: 10px 25px !important; width: 100%; }
            .footer-nav { position: fixed; left: 0; bottom: 0; width: 100%; height: 50px; background: #050D1F; border-top: 1px solid rgba(201,168,76,0.3); color: #C9A84C; text-align: center; display: flex; flex-direction: column; justify-content: center; z-index: 2000;}
            div.block-container { padding-top: 2rem; padding-bottom: 120px; position: relative; z-index: 10; }
            @media (max-width: 768px) {
                .modal-box { width: 95%; padding: 20px; }
                .result-card { padding: 18px 12px; border-radius: 12px; margin-bottom: 20px; width: 100%; max-width: 100vw; }
                div[role="radiogroup"] label { padding: 10px 10px !important; flex-grow: 1; text-align: center; }
                .kural-block { padding: 12px 10px; width: 100%; overflow-x: auto !important; overflow-y: hidden; }
                .venba-tamil .kural-line1, .venba-tamil .kural-line2 { font-size: clamp(11px, 3.3vw, 16px) !important; }
            }
        </style>
    """, unsafe_allow_html=True)
    components.html("""
        <script>
            function initEliteUI() {
                const doc = window.parent.document;
                const selectors = ['#MainMenu', 'header', 'footer', '.stDeployButton'];
                selectors.forEach(s => { const els = doc.querySelectorAll(s); els.forEach(e => e.style.display = 'none'); });
                doc.querySelectorAll('[data-baseweb="select"] > div > div').forEach(el => { el.style.backgroundColor = '#1A0808'; });
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
<label for="modal-toggle" class="about-btn">ℹ️ About Software</label>

<div class="modal-overlay">
<label for="modal-toggle" class="modal-bg-close"></label>
<div class="modal-box">
<label for="modal-toggle" class="close-btn">✖</label>
<h3 style="color: #F0C96A !important; font-size: 22px; font-family: 'Cinzel', serif; margin-top:0; margin-bottom: 15px;">VALLUVAR 2.0</h3>
<p style="color: #FFFFFF !important; font-size: 14px; line-height: 1.6; margin-bottom: 15px; text-align: center;">வாழ்க்கையில் பிரச்சனைகளா? உங்கள் அனைத்து உளவியல் போராட்டங்களுக்கும் வள்ளுவரின் 1330 குறள்கள் வழியே தீர்வு காண்போம்.</p>
<div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(201,168,76,0.2); border-radius: 10px; padding: 15px; margin-bottom: 15px; text-align: left;">
<span style="color: #F0C96A !important; font-weight: bold; font-size: 14px;">✨ Key Features:</span><br>
<span style="color: #E0E0E0 !important; font-size: 13px;">🌐 Dual Language Support (Tamil/Eng)</span><br>
<span style="color: #E0E0E0 !important; font-size: 13px;">⚖️ Contextual Life Verdicts</span><br>
<span style="color: #E0E0E0 !important; font-size: 13px;">🤖 Interactive AI Mentor</span>
</div>
<div style="background: rgba(255,100,100,0.1); border: 1px solid rgba(255,100,100,0.3); border-radius: 10px; padding: 15px; margin-bottom: 15px; text-align: left;">
<span style="color: #FF8A80 !important; font-weight: bold; font-size: 14px;">📌 Important Note:</span><br>
<p style="color: #E0E0E0 !important; font-size: 12.5px; line-height: 1.6; margin: 8px 0 0 0;"><b>1. Scroll to Read:</b> திருக்குறள் வரிகள் நீளமாக இருந்தால், பெட்டியை வலதுபுறம் Scroll / Swipe செய்து முழுமையாக வாசிக்கவும்.<br><br><b>2. 100% Privacy:</b> உங்கள் பெயர், முகவரி, Phone Number, IP Address போன்ற எந்த தனிப்பட்ட தரவுகளும் (Personal Data) எங்களால் சேகரிக்கப்படாது.</p>
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
# 1. SMART API & DATA MANAGEMENT
# ==========================================
@st.cache_resource
def load_model():
    key_list = ["key1", "key2", "key3", "key4", "key5"]
    for key_name in key_list:
        try:
            api_key = st.secrets.get(key_name)
            if not api_key: continue
            genai.configure(api_key=api_key)
            list(genai.list_models()) 
            return genai.GenerativeModel("gemini-2.5-flash")
        except: continue
    st.error("❌ All API Keys Failed! Please update secrets.")
    return None

model = load_model()

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
    except: return []

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
    except: pass
    if lang_mode == "English": return {"line1": "'A' leads letters; the Ancient Lord Leads and lords the entire world", "line2": "", "meaning": "As the letter A is the first of all letters, so the eternal God is first in the world", "number": 1}
    else: return {"line1": "அகர முதல எழுத்தெல்லாம் ஆதி", "line2": "பகவன் முதற்றே உலகு.", "meaning": "எழுத்துக்கள் எல்லாம் அகரத்தை அடிப்படையாக கொண்டிருக்கின்றன. அதுபோல உலகம் கடவுளை அடிப்படையாக கொண்டிருக்கிறது.", "number": 1}

def simulate_traffic_control(lang):
    loading_container = st.empty()
    with loading_container.container():
        loading_text = "⏳ வள்ளுவர் சிந்தித்துக்கொண்டிருக்கிறார்..." if lang == "தமிழ்" else "⏳ AI Valluvar is analyzing..."
        st.markdown(f"<h3 style='text-align:center; color:#F0C96A; font-family: Cinzel, serif;'>{loading_text}</h3>", unsafe_allow_html=True)
        progress_bar = st.progress(0)
        time.sleep(1)
        progress_bar.progress(100)
    loading_container.empty()

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

selected_option = st.radio("", menu_options, horizontal=True)

# ==================================================
# 1. KURAL SEARCH
# ==================================================
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
                    k_line2, k_mean = "", item.get('explanation', item.get('eng_exp', 'No explanation available.'))
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
<div class="{venba_class}"><div class="kural-line1">{k_line1}</div>{kural_line2_html}</div>
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

# ==================================================
# 2. VERDICT 
# ==================================================
elif selected_option in ["⚖️ சூழல் தீர்வு", "⚖️ AI Verdict"]:
    user_input = st.text_input("உங்கள் குழப்பம் / Your Situation (e.g. கடன் வாங்கலாமா ? / Should I take a loan?):")
    if st.button(btn_verdict):
        if not user_input: st.warning("Please type your question.")
        elif not model: st.error("No AI Connection.")
        else:
            simulate_traffic_control(lang)
            with st.spinner("📜 Analyzing your situation..."):
              # ... (உங்கள் பழைய கோடு: elif selected_option in ["⚖️ சூழல் தீர்வு", "⚖️ AI Verdict"]: ...)
                try:
                    venba_class = "venba-eng" if lang == "English" else "venba-tamil"
                    
                    # 🔥 STRICT GUARDRAILS & 100% PERCENTAGE FIX
                    if lang == "English":
                        prompt = f"""Context: '{user_input}'. Act as Thiruvalluvar. Reply strictly in JSON. Is this a general question? 'yes' or 'no' in 'is_general'. If 'yes', provide 3 tags. 
If 'no', score the situation for 'aram', 'porul', 'inbam'. CRITICAL: The sum of aram, porul, and inbam MUST EXACTLY equal 100. (e.g., 40, 40, 20).
CRITICAL GUARDRAILS:
1. DO NOT invent Kurals. Use only real 'kural_number' (1-1330).
2. 'adhigaaram' MUST exactly match the official chapter name for that Kural.
3. For money/debt/business queries, MUST use 'Porutpal' kurals (e.g., Chapter 48).
Format: {{"verdict": "Short advice", "is_general": "no", "aram": 0, "porul": 0, "inbam": 0, "tag1": "", "tag2": "", "tag3": "", "kural_number": 120, "adhigaaram": "Chapter Name"}}"""
                        lbl_aram, lbl_porul, lbl_inbam = "⚖️ Virtue", "💰 Wealth", "❤️ Peace/Love"
                    else:
                        prompt = f"""சூழல்: '{user_input}'. நீ திருவள்ளுவர். பதில் JSON-ல் மட்டும். இது பொது கேள்வியா? 'is_general'-ல் 'yes' அல்லது 'no'. 'yes' என்றால் 3 tags. 
'no' என்றால், இந்தச் செயலை 'aram', 'porul', 'inbam' என மதிப்பிடவும். மிக முக்கியம்: அறம், பொருள், இன்பம் ஆகிய மூன்றின் கூடுதல் (Sum) கண்டிப்பாக 100 ஆக மட்டுமே இருக்க வேண்டும் (எ.கா: 30, 50, 20).
முக்கிய கட்டுப்பாடுகள் (CRITICAL GUARDRAILS):
1. சொந்தமாக குறளை உருவாக்கக் கூடாது. 1 முதல் 1330 வரை உள்ள உண்மையான 'kural_number' மட்டுமே பயன்படுத்தவும்.
2. 'adhigaaram' பெயர் தேர்ந்தெடுக்கப்பட்ட குறளுக்கு உரியதாக மட்டுமே இருக்க வேண்டும்.
3. பணம், கடன் சார்ந்த கேள்விக்கு கண்டிப்பாக பொருட்பால் (எ.கா: வலியறிதல்) குறளைத் தரவும்.
Format: {{"verdict": "அறிவுரை", "is_general": "no", "aram": 0, "porul": 0, "inbam": 0, "tag1": "", "tag2": "", "tag3": "", "kural_number": 479, "adhigaaram": "அதிகாரத்தின் பெயர்"}}"""
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
                        
                        # --- AUDIO SCRIPT GENERATION ---
                        verdict_text = res.get('verdict', '')
                        if lang == "தமிழ்":
                            audio_text = f"அறிவுரை: {verdict_text}. "
                        else:
                            audio_text = f"Advice: {verdict_text}. "
                            
                        if is_gen:
                            t1, t2, t3 = str(res.get('tag1', '')).strip(), str(res.get('tag2', '')).strip(), str(res.get('tag3', '')).strip()
                            dynamic_ui_html = f"""<div class="percentage-container">
<span class="percentage-item" style="color:#A5D6A7 !important;">🏷️ {t1}</span>
<span class="percentage-item" style="color:#F0C96A !important;">🏷️ {t2}</span>
<span class="percentage-item" style="color:#FF8A80 !important;">🏷️ {t3}</span>
</div>"""
                        else:
                            arm, prl, inb = int(res.get('aram', 33)), int(res.get('porul', 33)), int(res.get('inbam', 34))
                            dynamic_ui_html = f"""<div class="percentage-container">
<span class="percentage-item" style="color:#A5D6A7 !important;">{lbl_aram}: {arm}%</span>
<span class="percentage-item" style="color:#F0C96A !important;">{lbl_porul}: {prl}%</span>
<span class="percentage-item" style="color:#FF8A80 !important;">{lbl_inbam}: {inb}%</span>
</div>"""
                            if lang == "தமிழ்":
                                audio_text += f" இதில், அறம் {arm} சதவிகிதம், பொருள் {prl} சதவிகிதம், இன்பம் {inb} சதவிகிதம் உள்ளது."
                            else:
                                audio_text += f" In this, Virtue is {arm} percent, Wealth is {prl} percent, and Joy is {inb} percent."
                        
                        # Generate Audio with Unique ID based on timestamp to avoid caching old audio
                        unique_id = f"audio_verdict_{int(time.time())}"
                        audio_player_html = generate_edge_tts_audio(audio_text, lang, unique_id)
                        
                        st.markdown(f"""
<div class="result-card card-advice">
<div class="result-adhigaaram">{lbl_advice}</div>
<div class="verdict-text">{res.get('verdict')}</div>
{audio_player_html}
</div>
{dynamic_ui_html}
<div class="result-card">
<div class="result-adhigaaram">{lbl_chap} {ai_chap} &nbsp;|&nbsp; {lbl_kno} {local_data['number']}</div>
<div class="kural-block">
<div class="{venba_class}"><div class="kural-line1">{local_data['line1']}</div>{kural_line2_html}</div>
</div>
<div class="kural-meaning"><strong>{lbl_exp}</strong><br>{local_data['meaning']}</div>
</div>
""", unsafe_allow_html=True)
                        
                        # 🔥 BUG FIX: Reset Streamlit state input values manually using HTML tricks if needed, 
                        # or let Streamlit handle it natively since we are not using st.form.
                    else:
                        st.error("AI Output Error.")
# ... (உங்கள் பழைய கோடு தொடரும்)
# ==================================================
# 3. AI MENTOR 
# ==================================================
elif selected_option in ["🤖 AI வள்ளுவர்", "🤖 AI Mentor"]:
    init_msg = "உங்களால் தீர்க்க முடியாத மனப்போராட்டங்களைச் சொல்லுங்கள். அதற்கான அறிவுரை, தீர்வு மற்றும் செயல்படாவிடில் வரும் அபாயங்களை அறிந்துகொள்ளுங்கள்..." if lang == "தமிழ்" else "Greetings! I am AI Valluvar. Ask your questions to get wisdom from Thirukkural..."
    
# ... (உங்கள் பழைய கோடு: elif selected_option in ["🤖 AI வள்ளுவர்", "🤖 AI Mentor"]: ...)
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": init_msg, "kural_data": None, "audio_html": ""}]

    # Display Chat History with Audio Embedded
    for idx, msg in enumerate(st.session_state.messages):
        role = "assistant" if msg["role"] == "assistant" else "user"
        with st.chat_message(role):
            if role == "assistant" and "{" in msg["content"]:
                 r = extract_json_from_text(msg["content"])
                 if r:
                     venba_class = "venba-eng" if lang == "English" else "venba-tamil"
                     local_data = msg.get("kural_data")
                     if not local_data: local_data = get_kural_from_local(r.get('kural_number', 1), lang)
                     kural_line2_html = f'<div class="kural-line2">{local_data["line2"]}</div>' if local_data["line2"] else ''
                     ai_chap = r.get('adhigaaram', 'அதிகாரம்')
                     
                     st.markdown(f"""
<div class="result-card card-advice">
<div class="result-adhigaaram">{lbl_advice}</div><div class="verdict-text">{r.get('verdict')}</div>
</div>
<div class="result-card">
<div class="result-adhigaaram">{lbl_chap} {ai_chap} &nbsp;|&nbsp; {lbl_kno} {local_data['number']}</div>
<div class="kural-block">
<div class="{venba_class}"><div class="kural-line1">{local_data['line1']}</div>{kural_line2_html}</div>
</div>
<div class="kural-meaning">{local_data['meaning']}</div>
</div>
<div class="result-card card-solution">
<div class="result-adhigaaram">{lbl_sol}</div><div class="verdict-text">{r.get('solution')}</div>
</div>
<div class="result-card card-warning">
<div class="result-adhigaaram">{lbl_warn}</div><div class="verdict-text">{r.get('consequence')}</div>
</div>
{msg.get("audio_html", "")}
""", unsafe_allow_html=True)
                 else: st.write(msg["content"])
            else: st.write(msg["content"])

    if prompt := st.chat_input("Ask Valluvar... / வள்ளுவரிடம் கேட்க..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        if model:
            with st.chat_message("assistant"):
                with st.spinner("📜 வள்ளுவர் is thinking..."):
                    try:
                        venba_class = "venba-eng" if lang == "English" else "venba-tamil"
                        
                        # 🔥 STRICT GUARDRAILS ADDED FOR MENTOR MODE
                        if lang == "English":
                            sys_msg = """Act as Thiruvalluvar. Reply strictly in JSON format.
CRITICAL GUARDRAILS:
1. DO NOT invent or hallucinate any Thirukkural. Only select a real, existing 'kural_number' between 1 and 1330.
2. The 'adhigaaram' MUST exactly match the official Thirukkural chapter name for the chosen 'kural_number'. Do not mismatch them.
3. For financial/debt queries, explicitly select kurals from 'Porutpal' (e.g., Chapter 48).
Format: { "verdict": "Short practical advice", "solution": "Actionable, direct solution spoken from the perspective of Valluvar himself, without just explaining the Kural", "consequence": "Warning if ignored", "kural_number": 120, "adhigaaram": "Exact Chapter Name" }"""
                        else:
                            sys_msg = """நீ திருவள்ளுவர். பதில் JSON வடிவில் மட்டும் தமிழில் இருக்க வேண்டும்.
முக்கிய கட்டுப்பாடுகள் (CRITICAL GUARDRAILS):
1. நீ எந்த காரணத்தைக் கொண்டும் சொந்தமாக திருக்குறளை உருவாக்கக் கூடாது. 1 முதல் 1330 வரை உள்ள உண்மையான குறள் எண்களை ('kural_number') மட்டுமே பயன்படுத்த வேண்டும்.
2. நீ தேர்ந்தெடுக்கும் 'kural_number'-க்கு உரிய சரியான அதிகாரத்தின் பெயரை மட்டுமே 'adhigaaram'-ல் கொடுக்க வேண்டும் (எ.கா: கடன், பணம் என்றால் கண்டிப்பாக பொருட்பால் - வலியறிதல் போன்ற அதிகாரத்தில் உள்ள குறளைத் தேர்ந்தெடு).
Format: { "verdict": "அறிவுரை", "solution": "திருக்குறளை விளக்காமல், வள்ளுவர் நேரில் சொல்வது போன்ற நேரடியான, நடைமுறை தீர்வு", "consequence": "எச்சரிக்கை", "kural_number": 120, "adhigaaram": "சரியான அதிகாரத்தின் பெயர்" }"""
                        
                        response = model.generate_content(sys_msg + "\n\nQuestion/கேள்வி: " + prompt)
                        r = extract_json_from_text(response.text)
                        
                        if r:
                            log_to_gsheets("Chat Mode", prompt, r.get('verdict', ''))
                            local_data = get_kural_from_local(r.get('kural_number', 1), lang)
                            kural_line2_html = f'<div class="kural-line2">{local_data["line2"]}</div>' if local_data["line2"] else ''
                            ai_chap = r.get('adhigaaram', 'அதிகாரம்')

                            # --- AUDIO SCRIPT GENERATION ---
                            if lang == "தமிழ்":
                                audio_text = f"அறிவுரை: {r.get('verdict', '')}. "
                                audio_text += f"குறள்: {local_data['line1']} {local_data['line2']}. "
                                audio_text += f"விளக்கம்: {local_data['meaning']}. "
                                audio_text += f"தீர்வு: {r.get('solution', '')}. "
                                audio_text += f"எச்சரிக்கை: {r.get('consequence', '')}."
                            else:
                                audio_text = f"Advice: {r.get('verdict', '')}. "
                                audio_text += f"Kural: {local_data['line1']}. "
                                audio_text += f"Explanation: {local_data['meaning']}. "
                                audio_text += f"Solution: {r.get('solution', '')}. "
                                audio_text += f"Warning: {r.get('consequence', '')}."

                            # Generate and embed audio instantly with Unique ID
                            unique_id = f"audio_mentor_{int(time.time())}"
                            audio_player_html = generate_edge_tts_audio(audio_text, lang, unique_id)

                            st.markdown(f"""
<div class="result-card card-advice">
<div class="result-adhigaaram">{lbl_advice}</div><div class="verdict-text">{r.get('verdict')}</div>
</div>
<div class="result-card">
<div class="result-adhigaaram">{lbl_chap} {ai_chap} &nbsp;|&nbsp; {lbl_kno} {local_data['number']}</div>
<div class="kural-block">
<div class="{venba_class}"><div class="kural-line1">{local_data['line1']}</div>{kural_line2_html}</div>
</div>
<div class="kural-meaning">{local_data['meaning']}</div>
</div>
<div class="result-card card-solution">
<div class="result-adhigaaram">{lbl_sol}</div><div class="verdict-text">{r.get('solution')}</div>
</div>
<div class="result-card card-warning">
<div class="result-adhigaaram">{lbl_warn}</div><div class="verdict-text">{r.get('consequence')}</div>
</div>
{audio_player_html}
""", unsafe_allow_html=True)
                            st.session_state.messages.append({"role": "assistant", "content": response.text, "kural_data": local_data, "audio_html": audio_player_html})
                        else:
                            st.write(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text, "audio_html": ""})
                    except Exception as e:
                        send_error_alert(f"AI Mentor Generation Error: {e}")
                        st.error(f"Error: {e}")

# --- FOOTER ---
st.markdown("""
<div class="footer-nav">
<p>© All rights reserved by <strong style="color:#C9A84C !important;">MIN E KAVI (மின்கவி)</strong> &nbsp;|&nbsp; Idealogy & Developed by <strong style="color:#C9A84C !important;">VIGNESH M</strong></p>
</div>
""", unsafe_allow_html=True)
