import streamlit as st
import requests
import sqlite3
import pandas as pd
import secrets
from duckduckgo_search import DDGS

# --- 1. تنظیمات دیتابیس ---
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users_access (username TEXT PRIMARY KEY, password TEXT, code50 TEXT UNIQUE, plan_type TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS shared_chats (share_id TEXT PRIMARY KEY, content TEXT)")
    cursor.execute("INSERT OR IGNORE INTO users_access (username, password, code50, plan_type) VALUES ('admin', 'admin', 'MASTER_KEY_000', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- 2. هسته هوش مصنوعی ---
def call_openrouter(messages, selected_sources):
    model_map = {"🤖 ChatGPT": "openai/gpt-4o-mini", "🧠 Gemini": "google/gemini-2.0-flash-001", "🔎 سرچ گوگل": "openai/gpt-4o-mini"}
    final_res = ""
    prompt = messages[-1]["content"]
    
    for source in selected_sources:
        current_prompt = prompt
        if source == "🔎 سرچ گوگل":
            with DDGS() as ddgs:
                res = list(ddgs.text(prompt, max_results=2))
                current_prompt = f"جستجو برای: {prompt}\nنتایج وب: {res}\nپاسخ جامع بده:"
        
        headers = {"Authorization": f"Bearer {st.secrets.get('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
        payload = {"model": model_map.get(source, "openai/gpt-4o-mini"), "messages": [{"role": "user", "content": current_prompt}]}
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
            answer = r.json()['choices'][0]['message']['content']
            final_res += f"### پاسخ از {source}:\n{answer}\n\n"
        except: final_res += f"❌ خطا در اتصال به {source}\n"
    return final_res

# --- 3. رابط کاربری اصلی ---
st.set_page_config(page_title="ANTANU System", layout="wide")
col1, col2 = st.columns([1, 8])
with col1: st.image("1.jpg", width=80)
with col2: st.title("ANTANU System")

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

# لاگین
if not st.session_state['authenticated']:
    tab1, tab2 = st.tabs(["ورود", "ثبت‌نام"])
    with tab1:
        u = st.text_input("نام کاربری")
        p = st.text_input("رمز عبور", type="password")
        if st.button("ورود"):
            st.session_state.update({'authenticated': True, 'username': u, 'role': 'admin' if u == 'admin' else 'user'})
            st.rerun()
    with tab2:
        n_u = st.text_input("یوزرنیم جدید"); n_p = st.text_input("پسورد", type="password"); n_c = st.text_input("کد ۵۰ رقمی")
        if st.button("ثبت‌نام"):
            conn = sqlite3.connect("ai_brain.db")
            try:
                conn.execute("UPDATE users_access SET username=?, password=? WHERE code50=?", (n_u, n_p, n_c))
                conn.commit()
                st.success("ثبت‌نام موفق!")
            except: st.error("کد اشتباه است.")
            conn.close()
else:
    # سایدبار
    with st.sidebar:
        st.write(f"👤 کاربر: {st.session_state['username']}")
        selected_sources = st.multiselect("منابع:", ["🔎 سرچ گوگل", "🤖 ChatGPT", "🧠 Gemini"], default=["🤖 ChatGPT"])
        if st.session_state.get('role') == 'admin' and st.button("تولید کد ۵۰ رقمی جدید"):
            code = secrets.token_hex(25)
            sqlite3.connect("ai_brain.db").execute("INSERT OR IGNORE INTO users_access (code50, plan_type) VALUES (?, ?)", (code, 'user')).connection.commit()
            st.code(code)
        
        file = st.file_uploader("تحلیل آماری (Excel)", type=['xlsx'])
        if file: st.write(pd.read_excel(file).describe())
        
        if st.button("🔗 اشتراک‌گذاری چت"):
            share_id = secrets.token_urlsafe(8)
            conn = sqlite3.connect("ai_brain.db")
            conn.execute("INSERT INTO shared_chats VALUES (?, ?)", (share_id, str(st.session_state.messages)))
            conn.commit(); conn.close()
            st.success(f"لینک: https://antanuai-9eejbkncmghnkvhgfikz.streamlit.app/?share={share_id}")

    # چت
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("سوال خود را بپرسید..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            response = call_openrouter(st.session_state.messages, selected_sources)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# بررسی اشتراک‌گذاری
if "share" in st.query_params:
    conn = sqlite3.connect("ai_brain.db")
    chat = conn.execute("SELECT content FROM shared_chats WHERE share_id=?", (st.query_params["share"],)).fetchone()
    if chat: st.info(f"محتوای چت اشتراکی: {chat[0]}")
