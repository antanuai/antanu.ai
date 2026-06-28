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

# --- 2. هسته هوش مصنوعی ---
def call_openrouter(prompt, model_id):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
        return r.json()['choices'][0]['message']['content'] if r.status_code == 200 else f"❌ خطای API: {r.status_code}"
    except Exception as e:
        return f"❌ خطا: {str(e)}"

# --- 3. رابط کاربری ---
st.set_page_config(page_title="ANTANU System", layout="wide")
col1, col2 = st.columns([1, 8])
with col1: st.image("1.jpg", width=80)
with col2: st.title("ANTANU System")

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    tab1, tab2 = st.tabs(["ورود", "ثبت‌نام"])
    with tab1:
        u = st.text_input("نام کاربری"); p = st.text_input("رمز", type="password")
        if st.button("ورود"): 
            st.session_state.update({'authenticated': True, 'username': u, 'is_admin': (u == 'admin')}); st.rerun()
    with tab2:
        n_u = st.text_input("یوزرنیم جدید"); n_p = st.text_input("پسورد", type="password"); n_c = st.text_input("کد ۵۰ رقمی ادمین")
        if st.button("ثبت‌نام"): st.success("در صورت معتبر بودن کد ثبت شدید.")
else:
    # سایدبار و پنل ادمین
    with st.sidebar:
        st.write(f"👤 کاربر: {st.session_state.get('username')}")
        
        # پنل ادمین (برگردانده شد)
        if st.session_state.get('is_admin'):
            st.subheader("🛠 پنل مدیریت")
            if st.button("تولید کد ۵۰ رقمی جدید"):
                new_code = secrets.token_hex(25)
                st.code(new_code)
        
        selected_model = st.selectbox("انتخاب هوش مصنوعی:", 
            options=["openai/gpt-4o-mini", "google/gemini-flash-1.5-8b", "meta-llama/llama-3.1-8b-instruct"],
            format_func=lambda x: {"openai/gpt-4o-mini": "🤖 ChatGPT", "google/gemini-flash-1.5-8b": "🧠 Gemini", "meta-llama/llama-3.1-8b-instruct": "🦙 Llama"}[x]
        )
        file = st.file_uploader("تحلیل آماری (Excel)", type=['xlsx'])
        if file: st.write(pd.read_excel(file).describe())
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

    if prompt := st.chat_input("سوال خود را بپرسید..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            response = call_openrouter(prompt, selected_model)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
