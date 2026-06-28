import streamlit as st
import requests
import sqlite3
import pandas as pd
import secrets
from duckduckgo_search import DDGS

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users_access (username TEXT PRIMARY KEY, password TEXT, code50 TEXT UNIQUE, plan_type TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS shared_chats (share_id TEXT PRIMARY KEY, content TEXT)")
    cursor.execute("INSERT OR IGNORE INTO users_access (username, password, code50, plan_type) VALUES ('admin', 'admin', 'MASTER_KEY_000', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- هسته هوش مصنوعی ---
def call_openrouter(messages, selected_sources):
    model_map = {"🤖 ChatGPT": "openai/gpt-4o-mini", "🧠 Gemini": "google/gemini-2.0-flash-001", "🔎 سرچ گوگل": "openai/gpt-4o-mini"}
    final_res = ""
    for source in selected_sources:
        prompt = messages[-1]["content"]
        if source == "🔎 سرچ گوگل":
            with DDGS() as ddgs:
                res = list(ddgs.text(prompt, max_results=2))
                prompt = f"جستجو: {res}\nسوال: {prompt}"
        
        headers = {"Authorization": f"Bearer {st.secrets.get('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
        payload = {"model": model_map.get(source, "openai/gpt-4o-mini"), "messages": [{"role": "user", "content": prompt}]}
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
            final_res += f"**{source}**: {r.json()['choices'][0]['message']['content']}\n\n"
        except: return "❌ خطا در اتصال به سرور."
    return final_res

# --- رابط کاربری ---
st.set_page_config(page_title="ANTANU System", layout="wide")
st.image("1.jpg", width=80)
st.title("ANTANU System")

# لاگین
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    # [بخش لاگین قبلی]
    u = st.text_input("نام کاربری"); p = st.text_input("رمز", type="password")
    if st.button("ورود"): st.session_state.update({'authenticated': True, 'username': u}); st.rerun()
else:
    # سایدبار
    with st.sidebar:
        selected_sources = st.multiselect("منابع:", ["🔎 سرچ گوگل", "🤖 ChatGPT", "🧠 Gemini"], default=["🤖 ChatGPT"])
        if st.button("🔗 اشتراک‌گذاری این چت"):
            share_id = secrets.token_urlsafe(8)
            conn = sqlite3.connect("ai_brain.db")
            conn.execute("INSERT INTO shared_chats VALUES (?, ?)", (share_id, str(st.session_state.messages)))
            conn.commit()
            st.success(f"لینک چت: {st.request.host}/?share={share_id}")

    # مدیریت چت
    if "messages" not in st.session_state: st.session_state.messages = []
    
    # نمایش پیام‌ها
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("سوال..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            response = call_openrouter(st.session_state.messages, selected_sources)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# --- قابلیت اشتراک‌گذاری ---
params = st.query_params
if "share" in params:
    conn = sqlite3.connect("ai_brain.db")
    chat = conn.execute("SELECT content FROM shared_chats WHERE share_id=?", (params["share"],)).fetchone()
    if chat: st.info(f"شما در حال مشاهده چت به اشتراک گذاشته شده هستید: {chat[0]}")
