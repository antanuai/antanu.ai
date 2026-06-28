import streamlit as st
import requests
import io
import sqlite3
import pandas as pd
import secrets
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from duckduckgo_search import DDGS

# ---------------- تنظیمات پایگاه داده ----------------
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS knowledge 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT UNIQUE, answer TEXT, sources TEXT, quality_score INTEGER DEFAULT 5, last_updated TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS system_settings 
                      (key TEXT PRIMARY KEY, value TEXT)""")
    # جدول جدید برای مدیریت کاربران و کدهای ۵۰ رقمی
    cursor.execute("""CREATE TABLE IF NOT EXISTS users_access 
                      (username TEXT PRIMARY KEY, code50 TEXT UNIQUE, plan_type TEXT)""")
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('version', '2.5.0')")
    conn.commit()
    conn.close()

init_db()

# ---------------- توابع هوش مصنوعی و پردازش ----------------
def get_system_version():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_settings WHERE key='version'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "2.5.0"

def search_google_live(query):
    try:
        with DDGS(timeout=8) as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
            if results: return "\n".join([f"منبع: {r['title']} - {r['body']}" for r in results])
    except: return "خطا در اتصال به گوگل."
    return "اطلاعاتی یافت نشد."

def call_openrouter(model_id, prompt, max_tokens=4000):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {st.secrets.get('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200: return response.json()['choices'][0]['message']['content']
    except: pass
    return ""

def smart_ai_agent(question, selected_sources):
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    
    google_data = search_google_live(question) if "🔎 سرچ زنده گوگل" in selected_sources else ""
    chatgpt_data = call_openrouter("openai/gpt-4o-mini", question) if "🤖 هوش مصنوعی ChatGPT" in selected_sources else ""
    gemini_data = call_openrouter("google/gemini-2.5-flash", question) if "🧠 هوش مصنوعی Gemini" in selected_sources else ""
    
    final_answer = f"پاسخ تحلیلی بر اساس منابع: {question} \n\n {google_data[:200]}..." 
    
    cursor.execute("INSERT OR REPLACE INTO knowledge (question, answer, sources, last_updated) VALUES (?, ?, ?, ?)", 
                   (question, final_answer, str(selected_sources), datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    return final_answer, "عملیات موفقیت‌آمیز بود."

# ---------------- طراحی رابط کاربری ----------------
st.set_page_config(page_title="ANTANU PRO", layout="wide")

# مدیریت لاگین
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("🔐 ورود به سامانه ANTANU")
    user = st.text_input("نام کاربری")
    code = st.text_input("کد ۵۰ رقمی", type="password")
    if st.button("ورود"):
        st.session_state['authenticated'] = True
        st.rerun()
else:
    st.sidebar.title(f"👤 کاربر: {st.session_state['username']}")
    
    # بخش مدیریت ادمین (تولید کد)
    if st.sidebar.button("تولید کد ۵۰ رقمی جدید"):
        new_code = secrets.token_hex(25)
        st.sidebar.code(new_code)
    
    # بخش تحلیل آماری فایل
    st.sidebar.write("---")
    st.sidebar.markdown("### 📊 تحلیل آماری فایل")
    stat_file = st.sidebar.file_uploader("آپلود اکسل جهت تحلیل", type=['xlsx'])
    if stat_file:
        df = pd.read_excel(stat_file)
        st.write("خلاصه آماری داده‌های شما:", df.describe())

    # هسته اصلی پرسش و پاسخ
    st.title("🔮 ANTANU Super System")
    selected_sources = st.multiselect("منابع:", ["🔎 سرچ زنده گوگل", "🤖 هوش مصنوعی ChatGPT", "🧠 هوش مصنوعی Gemini"])
    user_input = st.text_area("سوال:")
    
    if st.button("🚀 پردازش"):
        ans, msg = smart_ai_agent(user_input, selected_sources)
        st.markdown(f"<div class='article-box'>{ans}</div>", unsafe_allow_html=True)
