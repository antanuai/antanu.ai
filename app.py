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

# --- 2. هسته هوش مصنوعی ---
def call_openrouter(prompt, model_id):
    headers = {"Authorization": f"Bearer {st.secrets.get('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
        return r.json()['choices'][0]['message']['content'] if r.status_code == 200 else "خطای API"
    except: return "❌ خطا در اتصال"

# --- 3. رابط کاربری ---
st.set_page_config(page_title="ANTANU System", layout="wide")
col1, col2 = st.columns([1, 8])
with col1: st.image("1.jpg", width=80)
with col2: st.title("ANTANU System")

# احراز هویت
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    u = st.text_input("نام کاربری"); p = st.text_input("رمز عبور", type="password")
    if st.button("ورود"): st.session_state.update({'authenticated': True, 'username': u}); st.rerun()
else:
    # سایدبار مدیریت
    with st.sidebar:
        st.write(f"👤 کاربر: {st.session_state.get('username')}")
        sources = st.multiselect("انتخاب منابع هوش مصنوعی:", ["🔎 سرچ گوگل", "🤖 ChatGPT", "🧠 Gemini"], default=["🤖 ChatGPT"])
        
        file = st.file_uploader("تحلیل آماری (Excel)", type=['xlsx'])
        if file: st.write(pd.read_excel(file).describe())
        if st.button("خروج"): st.session_state.authenticated = False; st.rerun()

    # مدیریت چت
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                # دکمه‌های کپی و اشتراک
                c1, c2, c3 = st.columns([1, 1, 10])
                c1.button("📋 کپی", key=f"copy_{i}", on_click=lambda m=msg['content']: st.write(f"متن در کلیپ‌بورد: {m[:20]}..."))
                c2.markdown(f"[✈️](https://t.me/share/url?url=ANTANU_AI&text={msg['content'][:150]})")
                c3.markdown(f"[💬](https://wa.me/?text={msg['content'][:150]})")

    # پردازش سوال
    if prompt := st.chat_input("سوال خود را بپرسید..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            final_ans = ""
            model_map = {"🤖 ChatGPT": "openai/gpt-4o-mini", "🧠 Gemini": "google/gemini-2.0-flash-001", "🔎 سرچ گوگل": "openai/gpt-4o-mini"}
            
            for s in sources:
                res = call_openrouter(prompt, model_map[s])
                final_ans += f"{res}\n\n"
            st.markdown(final_ans)
        
        st.session_state.messages.append({"role": "assistant", "content": final_ans})
        st.rerun()
