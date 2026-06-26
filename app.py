import streamlit as st
import requests
import io
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from duckduckgo_search import DDGS

# بارگذاری کلید امنیتی
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- تنظیمات دیتابیس ---
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT UNIQUE, answer TEXT, sources TEXT, quality_score INTEGER DEFAULT 5, last_updated TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS system_settings (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('version', '2.5.0')")
    conn.commit()
    conn.close()

init_db()

# --- لیست کاربران ---
ALLOWED_USERS = {
    "1": {"pass": "1", "role": "admin"},
    "user2": {"pass": "pass2", "role": "user"}
}

# --- هوش مصنوعی ---
def call_openrouter(model_id, prompt, max_tokens=4000):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        return resp.json()['choices'][0]['message']['content'] if resp.status_code == 200 else ""
    except: return "خطا در اتصال به هوش مصنوعی"

def smart_ai_agent(question, sources):
    q = question.strip().lower()
    if any(k in q for k in ["سلام", "کی هستی", "تو کی هستی"]):
        return "سلام! من یک مدل هوش مصنوعی جدید هستم که توسط شرکت **ANTANU** آموزش دیدم و ساخته شدم.", "✨ پاسخ اختصاصی ANTANU"
    
    ans = call_openrouter("openai/gpt-4o-mini", f"پاسخ شیک و کامل به زبان فارسی: {question}", 4000)
    return ans, "🌐 پاسخ آماده شد."

# --- رابط کاربری ---
st.set_page_config(page_title="ANTANU AI", page_icon="🔮")

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    user = st.text_input("نام کاربری:")
    pwd = st.text_input("رمز عبور:", type="password")
    if st.button("ورود"):
        if user in ALLOWED_USERS and ALLOWED_USERS[user]["pass"] == pwd:
            st.session_state.update({'authenticated': True, 'username': user, 'role': ALLOWED_USERS[user]['role']})
            st.rerun()
else:
    st.title("🔮 دستیار هوشمند ANTANU")
    user_input = st.text_area("سوال خود را وارد کنید:")
    if st.button("شروع پردازش"):
        with st.spinner("⏳ در حال پردازش..."):
            res, msg = smart_ai_agent(user_input, [])
            st.info(msg)
            st.markdown(f"<div style='border-right:5px solid #2563eb; padding:20px; background:#f8fafc;'>{res}</div>", unsafe_allow_html=True)