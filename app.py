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
    # ایجاد ادمین پیش‌فرض
    cursor.execute("INSERT OR IGNORE INTO users_access (username, password, code50, plan_type) VALUES ('admin', 'admin', 'MASTER_KEY_000', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- 2. هسته هوش مصنوعی (با پشتیبانی از سرچ) ---
def call_openrouter(prompt, model_id, use_search):
    if use_search:
        with DDGS() as ddgs:
            res = list(ddgs.text(prompt, max_results=3))
            prompt = f"نتایج جستجو: {res}\n\nپاسخ جامع به سوال کاربر بر اساس نتایج بالا: {prompt}"
    
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
        return r.json()['choices'][0]['message']['content'] if r.status_code == 200 else f"❌ خطای API: {r.status_code}"
    except Exception as e:
        return f"❌ خطا در اتصال: {str(e)}"

# --- 3. رابط کاربری (UI) ---
st.set_page_config(page_title="ANTANU System", layout="wide")
col1, col2 = st.columns([1, 8])
with col1: st.image("1.jpg", width=80)
with col2: st.title("ANTANU System")

# مدیریت وضعیت کاربر
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    tab1, tab2 = st.tabs(["ورود", "ثبت‌نام"])
    with tab1:
        u = st.text_input("نام کاربری")
        p = st.text_input("رمز عبور", type="password")
        if st.button("ورود"):
            st.session_state.update({'authenticated': True, 'username': u, 'is_admin': (u == 'admin')})
            st.rerun()
    with tab2:
        n_u = st.text_input("یوزرنیم جدید")
        n_p = st.text_input("پسورد جدید", type="password")
        n_c = st.text_input("کد ۵۰ رقمی دریافتی")
        if st.button("ثبت‌نام"):
            conn = sqlite3.connect("ai_brain.db")
            try:
                conn.execute("UPDATE users_access SET username=?, password=? WHERE code50=?", (n_u, n_p, n_c))
                conn.commit()
                st.success("ثبت‌نام موفق بود. اکنون وارد شوید.")
            except: st.error("کد نامعتبر است.")
            conn.close()
else:
    # --- سایدبار ---
    with st.sidebar:
        st.write(f"👤 کاربر: {st.session_state.get('username')}")
        
        # پنل ادمین
        if st.session_state.get('is_admin'):
            st.subheader("🛠 پنل مدیریت")
            if st.button("تولید و ثبت کد جدید"):
                new_code = secrets.token_hex(25)
                conn = sqlite3.connect("ai_brain.db")
                conn.execute("INSERT OR IGNORE INTO users_access (code50, plan_type) VALUES (?, ?)", (new_code, 'user'))
                conn.commit(); conn.close()
                st.code(new_code)
        
        use_google = st.checkbox("🔎 فعال‌سازی سرچ گوگل")
        selected_model = st.selectbox("مدل:", ["openai/gpt-4o-mini", "google/gemini-flash-1.5-8b"])
        
        file = st.file_uploader("📊 تحلیل اکسل", type=['xlsx'])
        if file: st.write(pd.read_excel(file).describe())
        
        if st.button("خروج"): st.session_state.authenticated = False; st.rerun()

    # --- نمایش چت ---
    if "messages" not in st.session_state: st.session_state.messages = []
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                c1, c2, c3 = st.columns([1, 1, 10])
                if c1.button("📋 کپی", key=f"copy_{i}"): st.code(msg['content'])
                c2.markdown(f"[✈️](https://t.me/share/url?url=ANTANU&text={msg['content'][:150].replace(' ', '%20')})")
                c3.markdown(f"[💬](https://wa.me/?text={msg['content'][:150].replace(' ', '%20')})")

    # --- دریافت ورودی ---
    if prompt := st.chat_input("سوال خود را بپرسید..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            response = call_openrouter(prompt, selected_model, use_google)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
        
