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

# --- تنظیمات دیتابیس ---
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT UNIQUE, answer TEXT, sources TEXT, last_updated TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS users_access (username TEXT PRIMARY KEY, password TEXT, code50 TEXT UNIQUE, plan_type TEXT)""")
    cursor.execute("INSERT OR IGNORE INTO users_access (username, password, code50, plan_type) VALUES ('admin', 'admin', 'MASTER_KEY_000', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- توابع هوش مصنوعی ---
def call_openrouter(model_id, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {st.secrets.get('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}], "max_tokens": 3000}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        return response.json()['choices'][0]['message']['content'] if response.status_code == 200 else ""
    except: return ""

def smart_ai_agent(question, selected_sources):
    # ترکیب پاسخ‌ها
    answer = "پاسخ هوشمند ANTANU: " + call_openrouter("openai/gpt-4o-mini", question)
    return answer

# --- رابط کاربری ---
st.set_page_config(page_title="ANTANU PRO", layout="wide")

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    tab1, tab2 = st.tabs(["ورود", "ثبت‌نام"])
    with tab1:
        user = st.text_input("نام کاربری")
        pwd = st.text_input("رمز عبور", type="password")
        if st.button("ورود"):
            conn = sqlite3.connect("ai_brain.db")
            user_data = conn.execute("SELECT * FROM users_access WHERE username=? AND password=?", (user, pwd)).fetchone()
            if user_data:
                st.session_state['authenticated'] = True
                st.session_state['username'] = user
                st.session_state['role'] = 'admin' if user == 'admin' else 'user'
                st.rerun()
    with tab2:
        n_user = st.text_input("یوزرنیم جدید")
        n_pwd = st.text_input("پسورد جدید", type="password")
        n_code = st.text_input("کد ۵۰ رقمی")
        if st.button("ثبت‌نام"):
            conn = sqlite3.connect("ai_brain.db")
            try:
                conn.execute("UPDATE users_access SET username=?, password=? WHERE code50=?", (n_user, n_pwd, n_code))
                conn.commit()
                st.success("ثبت‌نام موفق! حالا وارد شوید.")
            except: st.error("کد نامعتبر است.")
            conn.close()
else:
    # --- پنل اصلی ---
    st.sidebar.title(f"👤 {st.session_state['username']}")
    if st.session_state.get('role') == 'admin':
        if st.sidebar.button("تولید کد ۵۰ رقمی"):
            new_code = secrets.token_hex(25)
            conn = sqlite3.connect("ai_brain.db")
            conn.execute("INSERT INTO users_access (code50) VALUES (?)", (new_code,))
            conn.commit()
            st.sidebar.code(new_code)
    
    st.sidebar.write("---")
    file = st.sidebar.file_uploader("تحلیل آماری (Excel)", type=['xlsx'])
    if file:
        df = pd.read_excel(file)
        st.write("خلاصه آماری:", df.describe())

    st.title("🔮 ANTANU System")
    sources = st.multiselect("منابع:", ["🔎 سرچ گوگل", "🤖 ChatGPT", "🧠 Gemini"])
    query = st.text_area("سوال:")
    if st.button("پردازش"):
        ans = smart_ai_agent(query, sources)
        st.info(ans)
