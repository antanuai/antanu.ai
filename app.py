import streamlit as st
import requests
import sqlite3
import pandas as pd
import secrets
from datetime import datetime

# --- تنظیمات دیتابیس ---
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users_access 
                      (username TEXT PRIMARY KEY, password TEXT, code50 TEXT UNIQUE, plan_type TEXT)""")
    # ایجاد ادمین پیش‌فرض
    cursor.execute("INSERT OR IGNORE INTO users_access (username, password, code50, plan_type) VALUES ('admin', 'admin', 'MASTER_KEY_000', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- هسته هوش مصنوعی ---
def call_openrouter(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {st.secrets.get('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    payload = {"model": "openai/gpt-4o-mini", "messages": messages}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        return response.json()['choices'][0]['message']['content']
    except: return "❌ خطا در اتصال به هوش مصنوعی."

# --- رابط کاربری ---
st.set_page_config(page_title="ANTANU System", layout="wide")

# بخش لوگو و عنوان
col1, col2 = st.columns([1, 8])
with col1: st.image("1.jpg", width=80)
with col2: st.title("ANTANU System")

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

# لاگین و ثبت‌نام
if not st.session_state['authenticated']:
    tab1, tab2 = st.tabs(["ورود", "ثبت‌نام"])
    with tab1:
        user = st.text_input("نام کاربری")
        pwd = st.text_input("رمز عبور", type="password")
        if st.button("ورود"):
            conn = sqlite3.connect("ai_brain.db")
            u_data = conn.execute("SELECT * FROM users_access WHERE username=? AND password=?", (user, pwd)).fetchone()
            if u_data:
                st.session_state['authenticated'] = True
                st.session_state['username'] = user
                st.session_state['role'] = u_data[3]
                st.rerun()
            else: st.error("نام کاربری یا رمز اشتباه است.")
    with tab2:
        n_user = st.text_input("یوزرنیم جدید")
        n_pwd = st.text_input("پسورد جدید", type="password")
        n_code = st.text_input("کد ۵۰ رقمی ادمین")
        if st.button("ثبت‌نام"):
            conn = sqlite3.connect("ai_brain.db")
            try:
                conn.execute("UPDATE users_access SET username=?, password=? WHERE code50=?", (n_user, n_pwd, n_code))
                conn.commit()
                st.success("ثبت‌نام موفق! لطفا وارد شوید.")
            except: st.error("کد نامعتبر است.")
            conn.close()
else:
    # --- پنل مدیریت و چت ---
    with st.sidebar:
        st.write(f"👤 کاربر: {st.session_state['username']}")
        if st.session_state.get('role') == 'admin':
            if st.button("تولید کد ۵۰ رقمی"):
                new_code = secrets.token_hex(25)
                conn = sqlite3.connect("ai_brain.db")
                conn.execute("INSERT OR IGNORE INTO users_access (code50, plan_type) VALUES (?, ?)", (new_code, 'user'))
                conn.commit()
                st.code(new_code)
        
        st.write("---")
        file = st.file_uploader("تحلیل آماری (Excel)", type=['xlsx'])
        if file:
            df = pd.read_excel(file)
            st.write("خلاصه آماری:", df.describe())
        
        if st.button("خروج"):
            st.session_state.authenticated = False
            st.rerun()

    # مدیریت تاریخچه چت
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("سوال خود را بپرسید..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            response = call_openrouter(st.session_state.messages)
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
