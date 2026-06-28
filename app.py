import streamlit as st
import requests
import sqlite3
import pandas as pd
import secrets

# --- 1. تنظیمات دیتابیس ---
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users_access (username TEXT PRIMARY KEY, password TEXT, code50 TEXT UNIQUE, plan_type TEXT)")
    cursor.execute("INSERT OR IGNORE INTO users_access (username, password, code50, plan_type) VALUES ('admin', 'admin', 'MASTER_KEY_000', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- 2. تابع اصلاح شده برای مدیریت خطا ---
def call_openrouter(prompt, model_id):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        return "❌ خطای تنظیمات: کلید API یافت نشد."
        
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}
    
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        else:
            return f"❌ خطای API (کد {r.status_code}): {r.text[:50]}" # نمایش بخشی از خطا برای عیب‌یابی
    except Exception as e:
        return f"❌ خطا در اتصال: {str(e)}"

# --- 3. رابط کاربری ---
st.set_page_config(page_title="ANTANU System", layout="wide")
col1, col2 = st.columns([1, 8])
with col1: st.image("1.jpg", width=80)
with col2: st.title("ANTANU System")

# احراز هویت ساده
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    if st.button("ورود به سیستم"): st.session_state.authenticated = True; st.rerun()
else:
    with st.sidebar:
        sources = st.multiselect("انتخاب منابع:", ["🤖 ChatGPT", "🧠 Gemini"], default=["🤖 ChatGPT"])
    
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                # لینک‌های اشتراک‌گذاری تمیز
                clean_text = msg["content"][:100].replace("\n", " ")
                c1, c2 = st.columns([1, 10])
                c1.markdown(f"[✈️ تلگرام](https://t.me/share/url?url=ANTANU&text={clean_text})")
                c2.markdown(f"[💬 واتس‌اپ](https://wa.me/?text={clean_text})")

    if prompt := st.chat_input("سوال..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            final_ans = ""
            model_map = {"🤖 ChatGPT": "openai/gpt-4o-mini", "🧠 Gemini": "google/gemini-2.0-flash-001"}
            for s in sources:
                res = call_openrouter(prompt, model_map[s])
                final_ans += res + "\n\n"
            st.markdown(final_ans)
        st.session_state.messages.append({"role": "assistant", "content": final_ans})
        st.rerun()
