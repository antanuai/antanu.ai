import streamlit as st
import requests
import sqlite3
import pandas as pd
import secrets

# --- 1. تنظیمات دیتابیس ---
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    # ستون code50 برای ذخیره کدهای تولید شده
    cursor.execute("CREATE TABLE IF NOT EXISTS users_access (username TEXT PRIMARY KEY, password TEXT, code50 TEXT UNIQUE, plan_type TEXT)")
    cursor.execute("INSERT OR IGNORE INTO users_access (username, password, code50, plan_type) VALUES ('admin', 'admin', 'MASTER_KEY_000', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- 2. مدیریت پنل ادمین (ذخیره در دیتابیس) ---
def add_new_code(code):
    conn = sqlite3.connect("ai_brain.db")
    try:
        conn.execute("INSERT INTO users_access (code50, plan_type) VALUES (?, ?)", (code, 'user'))
        conn.commit()
    except Exception as e:
        st.error(f"خطا در ثبت کد: {e}")
    conn.close()

# --- 3. هسته هوش مصنوعی ---
def call_openrouter(prompt, model_id):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
        return r.json()['choices'][0]['message']['content'] if r.status_code == 200 else f"❌ خطای API: {r.status_code}"
    except Exception as e:
        return f"❌ خطا: {str(e)}"

# --- 4. رابط کاربری ---
st.set_page_config(page_title="ANTANU System", layout="wide")
col1, col2 = st.columns([1, 8])
with col1: st.image("1.jpg", width=80)
with col2: st.title("ANTANU System")

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    u = st.text_input("نام کاربری"); p = st.text_input("رمز", type="password")
    if st.button("ورود"): 
        st.session_state.update({'authenticated': True, 'username': u, 'is_admin': (u == 'admin')}); st.rerun()
else:
    with st.sidebar:
        # اصلاحیه: این بخش دقیقاً کدی می‌سازد و در دیتابیس ثبت می‌کند
        if st.session_state.get('is_admin'):
            st.subheader("🛠 پنل مدیریت")
            if st.button("تولید و ثبت کد جدید"):
                new_code = secrets.token_hex(25) # تولید کد ۵۰ کاراکتری (hex)
                add_new_code(new_code)
                st.success("کد جدید تولید و در دیتابیس ذخیره شد:")
                st.code(new_code)
        
        selected_model = st.selectbox("انتخاب هوش مصنوعی:", 
            options=["openai/gpt-4o-mini", "google/gemini-flash-1.5-8b"],
            format_func=lambda x: "🤖 ChatGPT" if "gpt" in x else "🧠 Gemini"
        )
        if st.button("خروج"): st.session_state.authenticated = False; st.rerun()

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
            response = call_openrouter(prompt, selected_model)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
