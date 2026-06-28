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
    cursor.execute("INSERT OR IGNORE INTO users_access (username, password, code50, plan_type) VALUES ('admin', 'admin', 'MASTER_KEY_000', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- 2. هسته هوش مصنوعی (با مدیریت خطا) ---
def call_openrouter(prompt, model_id):
    headers = {"Authorization": f"Bearer {st.secrets.get('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        return f"خطای سرور ({r.status_code})"
    except Exception as e:
        return "❌ خطا در اتصال به سرویس"

# --- 3. رابط کاربری ---
st.set_page_config(page_title="ANTANU System", layout="wide")
col1, col2 = st.columns([1, 8])
with col1: st.image("1.jpg", width=80)
with col2: st.title("ANTANU System")

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    # [بخش لاگین قبلی]
    if st.button("ورود"): st.session_state.update({'authenticated': True}); st.rerun()
else:
    # چت‌بات
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # دکمه کپی
            if msg["role"] == "assistant":
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 10])
                if col_btn1.button("📋 کپی", key=f"copy_{i}"):
                    st.write(f"متن کپی شد (در حافظه موقت): {msg['content'][:20]}...")
                
                # اشتراک‌گذاری در رسانه‌ها
                text = msg["content"]
                telegram_link = f"https://t.me/share/url?url=ANTANU_AI&text={text[:300]}"
                whatsapp_link = f"https://wa.me/?text={text[:300]}"
                col_btn2.markdown(f"[✈️ تلگرام]({telegram_link})")
                col_btn3.markdown(f"[💬 واتس‌اپ]({whatsapp_link})")

    if prompt := st.chat_input("سوال..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # پردازش منابع
        sources = st.sidebar.multiselect("منابع:", ["🔎 سرچ گوگل", "🤖 ChatGPT", "🧠 Gemini"], default=["🤖 ChatGPT"])
        response = ""
        for s in sources:
            model = {"🤖 ChatGPT": "openai/gpt-4o-mini", "🧠 Gemini": "google/gemini-2.0-flash-001", "🔎 سرچ گوگل": "openai/gpt-4o-mini"}[s]
            response += f"**{s}:** {call_openrouter(prompt, model)}\n\n"
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
