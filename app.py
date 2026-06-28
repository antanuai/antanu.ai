import streamlit as st
import requests
import sqlite3
import pandas as pd
import secrets
from duckduckgo_search import DDGS

# --- 1. استایل‌های مدرن (CSS) ---
def inject_custom_css():
    st.markdown("""
    <style>
        .stButton>button { border-radius: 12px; border: 2px solid #6e8efb; transition: 0.3s; }
        .stButton>button:hover { transform: scale(1.05); background: #6e8efb; color: white; }
        .menu-item { width: 50px; height: 50px; border-radius: 999px; background: rgba(138, 43, 226, 0.2); 
                     display: flex; align-items: center; overflow: hidden; transition: 0.4s; }
        .menu-item:hover { width: 160px; }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 2. دیتابیس ---
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users_access (username TEXT PRIMARY KEY, password TEXT, code50 TEXT UNIQUE, plan_type TEXT)")
    cursor.execute("INSERT OR IGNORE INTO users_access (username, password, code50, plan_type) VALUES ('admin', 'admin', 'MASTER_KEY_000', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- 3. هسته هوش مصنوعی ---
def call_openrouter(prompt, model_id, use_search):
    if use_search:
        with DDGS() as ddgs:
            res = list(ddgs.text(prompt, max_results=3))
            prompt = f"نتایج جستجو: {res}\n\nسوال کاربر: {prompt}"
    
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
        return r.json()['choices'][0]['message']['content'] if r.status_code == 200 else f"❌ خطای API: {r.status_code}"
    except Exception as e: return f"❌ خطا: {str(e)}"

# --- 4. رابط کاربری اصلی ---
st.set_page_config(page_title="ANTANU System", layout="wide")
st.title("🌌 ANTANU System")

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    tab1, tab2 = st.tabs(["ورود", "ثبت‌نام"])
    with tab1:
        u = st.text_input("نام کاربری"); p = st.text_input("رمز", type="password")
        if st.button("ورود"): st.session_state.update({'authenticated': True, 'username': u, 'is_admin': (u == 'admin')}); st.rerun()
    with tab2:
        n_u = st.text_input("یوزرنیم جدید"); n_p = st.text_input("پسورد جدید", type="password"); n_c = st.text_input("کد ۵۰ رقمی")
        if st.button("ثبت‌نام"): 
            conn = sqlite3.connect("ai_brain.db")
            conn.execute("UPDATE users_access SET username=?, password=? WHERE code50=?", (n_u, n_p, n_c))
            conn.commit(); conn.close(); st.success("ثبت‌نام موفق!")
else:
    with st.sidebar:
        st.write(f"👤 کاربر: {st.session_state.get('username')}")
        if st.session_state.get('is_admin'):
            if st.button("⚙️ تولید کد ۵۰ رقمی"):
                code = secrets.token_hex(25)
                sqlite3.connect("ai_brain.db").execute("INSERT OR IGNORE INTO users_access (code50, plan_type) VALUES (?, ?)", (code, 'user')).connection.commit()
                st.code(code)
        
        use_google = st.checkbox("🔎 سرچ گوگل")
        selected_model = st.selectbox("مدل:", ["openai/gpt-4o-mini", "google/gemini-flash-1.5-8b"])
        if st.button("🚪 خروج"): st.session_state.authenticated = False; st.rerun()

    # مدیریت چت
    if "messages" not in st.session_state: st.session_state.messages = []
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                c1, c2, c3 = st.columns([1, 1, 10])
                if c1.button("📋 کپی", key=f"copy_{i}"): st.code(msg['content'])
                c2.markdown(f"[✈️](https://t.me/share/url?url=ANTANU&text={msg['content'][:150].replace(' ', '%20')})")
                c3.markdown(f"[💬](https://wa.me/?text={msg['content'][:150].replace(' ', '%20')})")

    if prompt := st.chat_input("سوال..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            response = call_openrouter(prompt, selected_model, use_google)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
