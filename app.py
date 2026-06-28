import streamlit as st
import requests
import io
import sqlite3
import pandas as pd
import secrets
from datetime import datetime
from docx import Document
from duckduckgo_search import DDGS

# --- تنظیمات دیتابیس ---
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users_access 
                      (username TEXT PRIMARY KEY, password TEXT, code50 TEXT UNIQUE, plan_type TEXT)""")
    # مقداردهی اولیه ادمین
    cursor.execute("INSERT OR IGNORE INTO users_access (username, password, code50, plan_type) VALUES ('admin', 'admin', 'MASTER_KEY_000', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- هسته هوش مصنوعی ---
def call_openrouter(model_id, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {st.secrets.get('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}], "max_tokens": 3000}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        return response.json()['choices'][0]['message']['content'] if response.status_code == 200 else "خطا در ارتباط با سرور."
    except: return "خطا در پردازش."

# --- رابط کاربری ---
st.set_page_config(page_title="ANTANU System", layout="wide")

# بخش لوگو و عنوان یکپارچه
col1, col2 = st.columns([1, 8])
with col1:
    st.image("1.jpg", width=80) 
with col2:
    st.title("ANTANU System")

# مدیریت وضعیت ورود
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
                st.session_state['role'] = user_data[3]
                st.rerun()
    with tab2:
        n_user = st.text_input("یوزرنیم جدید")
        n_pwd = st.text_input("پسورد جدید", type="password")
        n_code = st.text_input("کد ۵۰ رقمی ادمین")
        if st.button("ثبت‌نام"):
            conn = sqlite3.connect("ai_brain.db")
            try:
                conn.execute("UPDATE users_access SET username=?, password=? WHERE code50=?", (n_user, n_pwd, n_code))
                conn.commit()
                st.success("ثبت‌نام انجام شد.")
            except: st.error("کد نامعتبر است.")
            conn.close()
else:
    # --- پنل مدیریت و تحلیل ---
    st.sidebar.title(f"👤 {st.session_state['username']}")
    if st.session_state.get('role') == 'admin':
        if st.sidebar.button("تولید کد ۵۰ رقمی"):
            new_code = secrets.token_hex(25)
            conn = sqlite3.connect("ai_brain.db")
            conn.execute("INSERT OR IGNORE INTO users_access (code50, plan_type) VALUES (?, ?)", (new_code, 'user'))
            conn.commit()
            st.sidebar.code(new_code)
    
    st.sidebar.write("---")
    file = st.sidebar.file_uploader("تحلیل آماری (Excel)", type=['xlsx'])
    if file:
        df = pd.read_excel(file)
        st.write("خلاصه آماری داده‌های شما:", df.describe())

    # --- بدنه اصلی چت ---
    sources = st.multiselect("منابع استخراج داده:", ["🔎 سرچ گوگل", "🤖 ChatGPT", "🧠 Gemini"], default=["🔎 سرچ گوگل"])
    query = st.text_area("سوال خود را وارد کنید:")
    if st.button("پردازش هوشمند"):
        with st.spinner("در حال تحلیل..."):
            ans = call_openrouter("openai/gpt-4o-mini", query)
            st.info(ans)
