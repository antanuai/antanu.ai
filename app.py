import streamlit as st
import requests
import sqlite3
import pandas as pd
import secrets
from duckduckgo_search import DDGS

# --- 1. تنظیمات پایگاه داده ---
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    # جداول مورد نیاز برای کاربران، حافظه و چت‌های اشتراکی
    cursor.execute("CREATE TABLE IF NOT EXISTS users_access (username TEXT PRIMARY KEY, password TEXT, code50 TEXT UNIQUE, plan_type TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS shared_chats (share_id TEXT PRIMARY KEY, content TEXT)")
    cursor.execute("INSERT OR IGNORE INTO users_access (username, password, code50, plan_type) VALUES ('admin', 'admin', 'MASTER_KEY_000', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- 2. توابع هوش مصنوعی ---
def call_openrouter(prompt, model_id, source_name):
    headers = {"Authorization": f"Bearer {st.secrets.get('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        return f"خطای سرور: {r.status_code}"
    except: return f"❌ خطا در اتصال به {source_name}"

# --- 3. رابط کاربری اصلی ---
st.set_page_config(page_title="ANTANU System", layout="wide")

# بخش لوگو و عنوان
col1, col2 = st.columns([1, 8])
with col1: st.image("1.jpg", width=80)
with col2: st.title("ANTANU System")

# احراز هویت
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    tab1, tab2 = st.tabs(["ورود", "ثبت‌نام"])
    with tab1:
        u = st.text_input("نام کاربری"); p = st.text_input("رمز", type="password")
        if st.button("ورود"): st.session_state.update({'authenticated': True, 'username': u, 'role': 'admin' if u == 'admin' else 'user'}); st.rerun()
    with tab2:
        n_u = st.text_input("یوزرنیم جدید"); n_p = st.text_input("پسورد", type="password"); n_c = st.text_input("کد ۵۰ رقمی")
        if st.button("ثبت‌نام"): st.success("در صورت معتبر بودن کد، ثبت شدید.")
else:
    # سایدبار
    with st.sidebar:
        st.write(f"👤 کاربر: {st.session_state.get('username')}")
        sources = st.multiselect("منابع هوشمند:", ["🔎 سرچ گوگل", "🤖 ChatGPT", "🧠 Gemini"], default=["🤖 ChatGPT"])
        if st.session_state.get('role') == 'admin' and st.button("تولید کد ۵۰ رقمی"):
            code = secrets.token_hex(25)
            st.code(code)
        
        file = st.file_uploader("تحلیل آماری (Excel)", type=['xlsx'])
        if file: st.write(pd.read_excel(file).describe())
        if st.button("خروج"): st.session_state.authenticated = False; st.rerun()

    # مدیریت چت
    if "messages" not in st.session_state: st.session_state.messages = []
    
    # نمایش پیام‌ها
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                c1, c2, c3 = st.columns([1, 1, 10])
                c1.markdown(f"[✈️ تلگرام](https://t.me/share/url?url=ANTANU_AI&text={msg['content'][:200]})")
                c2.markdown(f"[💬 واتس‌اپ](https://wa.me/?text={msg['content'][:200]})")
                if c3.button("📋 کپی متن", key=f"copy_{i}"): st.code(msg['content'])

    # پردازش سوال
    if prompt := st.chat_input("سوال خود را بپرسید..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            response = ""
            for s in sources:
                model = {"🤖 ChatGPT": "openai/gpt-4o-mini", "🧠 Gemini": "google/gemini-2.0-flash-001", "🔎 سرچ گوگل": "openai/gpt-4o-mini"}[s]
                ans = call_openrouter(prompt, model, s)
                response += f"### {s}:\n{ans}\n\n"
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
