import streamlit as st
import requests
import io
import sqlite3
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from duckduckgo_search import DDGS
import os

# ---------------- تنظیمات پایگاه داده (مغز هوش مصنوعی شما) ----------------
def init_db():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT UNIQUE,
            answer TEXT,
            sources TEXT,
            quality_score INTEGER DEFAULT 5,
            last_updated TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('version', '2.5.0')")
    conn.commit()
    conn.close()

init_db()

def get_system_version():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_settings WHERE key='version'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "2.5.0"

def update_system_version(new_version):
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE system_settings SET value=? WHERE key='version'", (new_version,))
    conn.commit()
    conn.close()

# ---------------- مدیریت کاربران و سطوح دسترسی ----------------
ALLOWED_USERS = {
    "aslasunli": {"pass": "A159372468z", "role": "admin"},
    "1": {"pass": "1", "role": "user"},
    "user3": {"pass": "pass3", "role": "user"},
}

# ---------------- توابع هوش مصنوعی و اینترنت ----------------

def check_identity_questions(question):
    """بررسی هوشمند سوالات مربوط به هویت هوش مصنوعی و پاسخ اختصاصی شرکت ANTANU"""
    q_clean = question.strip().lower()
    identity_keywords = [
        "سلام", "کی هستی", "تو کی هستی", "نام تو چیست", 
        "خودتو معرفی کن", "اسم تو چیه", "سلاو", "تو کێی"
    ]
    
    if any(keyword in q_clean for keyword in identity_keywords):
        return (
            "سلام! من یک مدل هوش مصنوعی جدید هستم که توسط شرکت **ANTANU** آموزش دیدم و ساخته شدم. "
            "امروز چطور می‌توانم در نگارش مقالات علمی، پژوهش و پاسخ به سوالاتتان به شما کمک کنم؟"
        )
    return None

def search_google_live(query):
    try:
        with DDGS(timeout=8) as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
            if results:
                return "\n".join([f"منبع: {r['title']} - {r['body']}" for r in results])
    except Exception:
        return "امکان دریافت اطلاعات زنده از گوگل در این لحظه فراهم نشد."
    return "اطلاعاتی در گوگل یافت نشد."

def call_openrouter(model_id, prompt, max_tokens=4000):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception:
        pass
    return ""

def process_and_humanize(question, google_data, chatgpt_data, gemini_data, selected_sources):
    active_sources_str = ", ".join(selected_sources) if selected_sources else "حافظه داخلی سیستم"
    
    humanize_prompt = (
        f"شما مغز متفکر هوش مصنوعی اختصاصی شرکت ANTANU هستید. یک مقاله/پاسخ فوق‌العاده شیک، طولانی، ساختاریافته و کاملاً طبیعی به زبان فارسی بنویسید.\n\n"
        f"موضوع درخواست: {question}\n"
        f"منابع فعال استفاده‌شده: {active_sources_str}\n\n"
        f"--- دیتای خام ورودی برای تحلیل و ویرایش شما ---\n"
        f"۱. دیتای زنده گوگل: {google_data}\n\n"
        f"۲. تحلیل مدل ChatGPT: {chatgpt_data}\n\n"
        f"۳. تحلیل مدل Gemini: {gemini_data}\n\n"
        f"قوانین نگارش: متن باید به شدت شیک، منسجم، دارای عناوین واضح، پاراگراف‌بندی عالی و لحنی کاملاً انسانی باشد. از عبارات تکراری پرهیز کنید."
    )
    return call_openrouter("openai/gpt-4o-mini", humanize_prompt, max_tokens=6000)

def smart_ai_agent(question, selected_sources):
    # گام اول: بررسی هویت اختصاصی ANTANU
    identity_response = check_identity_questions(question)
    if identity_response:
        return identity_response, "✨ پاسخ خودکار بر اساس هویت اختصاصی ANTANU"

    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    
    # سناریوی حافظه داخلی
    if not selected_sources:
        cursor.execute("SELECT answer, quality_score FROM knowledge WHERE question=?", (question,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0], "🧠 پاسخ مستقیم از حافظه و دیتابیس داخلی (یادگیری‌های قبلی)"
        else:
            return "❌ این موضوع در حافظه داخلی من یافت نشد. لطفاً برای پاسخ‌دهی حداقل یکی از منابع خارجی را تیک بزنید تا سیستم آن را یاد بگیرد.", "⚠️ عدم وجود دیتا در حافظه"

    # سناریوی استفاده ترکیبی یا تک‌منبعی
    google_data = search_google_live(question) if "🔎 سرچ زنده گوگل" in selected_sources else "غیرفعال"
    chatgpt_data = call_openrouter("openai/gpt-4o-mini", question, max_tokens=3000) if "🤖 هوش مصنوعی ChatGPT" in selected_sources else "غیرفعال"
    gemini_data = call_openrouter("google/gemini-2.5-flash", question, max_tokens=3000) if "🧠 هوش مصنوعی Gemini" in selected_sources else "غیرفعال"
    
    final_answer = process_and_humanize(question, google_data, chatgpt_data, gemini_data, selected_sources)
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("""
        INSERT OR REPLACE INTO knowledge (question, answer, sources, quality_score, last_updated)
        VALUES (?, ?, ?, ?, ?)
    """, (question, final_answer, f"ترکیبی: {selected_sources}", 9, current_time))
    
    conn.commit()
    conn.close()
    return final_answer, f"🌐 اطلاعات از منابع منتخب استخراج، انسانی‌سازی و ذخیره شد."

def self_heal_brain():
    conn = sqlite3.connect("ai_brain.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, answer FROM knowledge")
    records = cursor.fetchall()
    
    updated_count = 0
    for rec_id, q, a in records:
        new_google = search_google_live(q)
        audit_prompt = (
            f"با توجه به دیتای جدید وب، خطاهای پاسخ زیر را اصلاح کنید:\nسوال: {q}\nمتن: {a}\nاطلاعات جدید وب: {new_google}"
        )
        corrected_answer = call_openrouter("openai/gpt-4o-mini", audit_prompt, max_tokens=4000)
        if corrected_answer and corrected_answer != a:
            cursor.execute("UPDATE knowledge SET answer=?, last_updated=? WHERE id=?", 
                           (corrected_answer, datetime.now().strftime("%Y-%m-%d %H:%M"), rec_id))
            updated_count += 1
            
    conn.commit()
    conn.close()
    return updated_count

# ---------------- توابع ساخت فایل خروجی ----------------

def create_styled_word_file(title, text):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(1); section.bottom_margin = Inches(1)
    section.left_margin = Inches(1); section.right_margin = Inches(1)
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run(title)
    run_title.font.name = 'B Nazanin'; run_title.font.size = Pt(22); run_title.bold = True
    
    doc.add_paragraph()
    lines = text.split('\n')
    for line in lines:
        if not line.strip(): continue
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if line.startswith('#') or line.startswith('**') or 'مقدمه' in line or 'نتیجه' in line:
            clean_line = line.replace('#', '').replace('**', '').strip()
            run = p.add_run(clean_line)
            run.font.name = 'B Nazanin'; run.font.size = Pt(15); run.bold = True
        else:
            run = p.add_run(line)
            run.font.name = 'B Nazanin'; run.font.size = Pt(13)
        p.paragraph_format.line_spacing = 1.4
        p.paragraph_format.space_after = Pt(8)
        
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def create_pdf_file(text):
    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=letter)
    lines = text.split('\n')
    y = 750
    for line in lines:
        if y < 50: c.showPage(); y = 750
        c.drawString(50, y, line)
        y -= 20
    c.save(); bio.seek(0)
    return bio

# ---------------- طراحی تم جدید: لایت، مینیمال، شیک و آرامش‌بخش ----------------

st.set_page_config(page_title="پلتفرم هوشمند ANTANU", page_icon="🔮", layout="centered")

st.markdown("""
    <style>
    @import url('https://v1.fontapi.ir/css/Vazir');
    
    /* پس‌زمینه روشن، ملایم و ارگونومیک برای جلوگیری از خستگی چشم */
    .stApp {
        background-color: #fcfcfc !important;
        font-family: 'Vazir', sans-serif !important;
        direction: RTL !important;
        text-align: right !important;
        color: #2d3748 !important;
    }
    
    h1, h2, h3, h4, p, span, label, div {
        direction: RTL !important;
        text-align: right !important;
    }
    
    /* کارت اصلی سفید با سایه فوق‌ملایم گالری آکادمیک */
    div.block-container {
        background: #ffffff !important;
        padding: 40px !important;
        border-radius: 20px !important;
        border: 1px solid #edf2f7 !important;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.03) !important;
    }
    
    /* دکمه با طیف آبی شرکتی و ساختار مینیمال */
    .stButton>button {
        background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 100%) !important;
        color: white !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        border: none !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15) !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.25) !important;
    }
    
    /* باکس نمایش مقاله با کنتراست عالی و تمیز */
    .article-box {
        background: #f8fafc !important;
        border-right: 5px solid #2563eb !important;
        border-top: 1px solid #e2e8f0;
        border-left: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        padding: 30px !important;
        border-radius: 12px !important;
        line-height: 2.2 !important;
        text-align: justify !important;
        color: #1a202c !important;
        font-size: 16px;
    }
    
    /* استایل سایدبار */
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-left: 1px solid #e2e8f0 !important;
    }
    
    textarea {
        background-color: #ffffff !important;
        color: #1a202c !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
    }
    textarea:focus {
        border-color: #2563eb !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'username' not in st.session_state: st.session_state['username'] = ""
if 'role' not in st.session_state: st.session_state['role'] = "user"

# --- صفحه اول: لاگین ---
if not st.session_state['authenticated']:
    st.markdown("<h2 style='text-align: center; color:#1e3a8a; font-weight:700;'>🔮 ورود به سامانه مرکزی ANTANU</h2>", unsafe_allow_html=True)
    st.write("---")
    username = st.text_input("👤 نام کاربری:")
    password = st.text_input("🔑 رمز عبور:", type="password")
    if st.button("ورود به پنل کاربری"):
        if username in ALLOWED_USERS and ALLOWED_USERS[username]["pass"] == password:
            st.session_state['authenticated'] = True
            st.session_state['username'] = username
            st.session_state['role'] = ALLOWED_USERS[username]["role"]
            st.rerun()
        else:
            st.error("❌ نام کاربری یا رمز عبور اشتباه است.")

# --- صفحه دوم: پنل کاربری اصلی پلتفرم با برندینگ اختصاصی ---
else:
    current_version = get_system_version()
    st.markdown(f"<h1>🔮 دستیار هوش مصنوعی <span style='color:#2563eb;'>ANTANU</span> <span style='font-size:12px; color:#64748b; background:#f1f5f9; padding:4px 8px; border-radius:6px; font-weight:normal;'>نسخه {current_version}</span></h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown(f"### 👤 کاربر: `{st.session_state['username']}`")
        st.markdown(f"💼 نقش: **{st.session_state['role'].upper()}**")
        if st.button("🚪 خروج"):
            st.session_state['authenticated'] = False
            st.session_state.pop('dynamic_result', None)
            st.rerun()
            
        if st.session_state['role'] == 'admin':
            st.write("---")
            st.markdown("##### 👑 تنظیمات ارشد سیستم")
            new_ver = st.text_input("تغییر نسخه سیستم:", value=current_version)
            if st.button("💾 ثبت ورژن جدید"):
                update_system_version(new_ver)
                st.success("ورژن ارتقا یافت.")
                st.rerun()
                
            st.write("---")
            st.markdown("##### 🔄 پالایش سراسری دانش")
            if st.button("🧹 اصلاح اطلاعات غلط دیتابیس"):
                with st.spinner("در حال پایش اطلاعات..."):
                    fixed = self_heal_brain()
                    st.success(f"تعداد {fixed} مورد همگام‌سازی شد.")

    st.write("")
    st.markdown("<p style='font-weight:500; color:#475569;'>⚙️ منابع استخراج و ترکیب کلان‌داده‌ها را انتخاب کنید:</p>", unsafe_allow_html=True)
    selected_sources = st.multiselect(
        "انتخاب چندگانه آزاد است. (عدم انتخاب منبع = استفاده کاملاً آفلاین از حافظه داخلی مدل)",
        ["🔎 سرچ زنده گوگل", "🤖 هوش مصنوعی ChatGPT", "🧠 هوش مصنوعی Gemini"],
        default=["🔎 سرچ زنده گوگل", "🤖 هوش مصنوعی ChatGPT", "🧠 هوش مصنوعی Gemini"]
    )
    
    st.write("")
    user_input = st.text_area("🔍 سوال خود را بپرسید یا موضوع مقاله را وارد کنید:", height=140, placeholder="از من سوال بپرسید یا بنویسید: تو کی هستی؟")
    
    st.write("")
    if st.button("🚀 شروع پردازش و نگارش شیک"):
        if user_input.strip() == "":
            st.warning("لطفاً ابتدا متنی بنویسید.")
        else:
            with st.spinner("⏳ در حال بررسی و آماده‌سازی پاسخ نهایی..."):
                final_text, status_msg = smart_ai_agent(user_input, selected_sources)
                st.session_state['dynamic_result'] = final_text
                st.session_state['status_msg'] = status_msg

    if 'dynamic_result' in st.session_state:
        st.write("")
        st.info(st.session_state['status_msg'])
        if "❌" not in st.session_state['dynamic_result']:
            st.markdown("<h3 style='color: #1e3a8a;'>📄 پاسخ نهایی سیستم:</h3>", unsafe_allow_html=True)
            st.markdown("<div class='article-box'>" + st.session_state['dynamic_result'] + "</div>", unsafe_allow_html=True)
            
            st.write("---")
            st.markdown("<h4 style='text-align: center; color: #64748b;'>📥 دریافت فایل رسمی خروجی</h4>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 دانلود فایل Word (DOCX)", data=create_styled_word_file(user_input[:40], st.session_state['dynamic_result']), file_name="antanu_output.docx")
            with col2:
                st.download_button("📥 دانلود فایل PDF", data=create_pdf_file(st.session_state['dynamic_result']), file_name="antanu_output.pdf")
        else:
            st.error(st.session_state['dynamic_result'])
