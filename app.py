import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ==================== CONFIG ====================
st.set_page_config(
    page_title="Stoic Champion Path | MrO Natural + Tiến Sĩ",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PROFILE_FILE = DATA_DIR / "profile.json"
LOG_FILE = DATA_DIR / "daily_logs.json"
STREAK_FILE = DATA_DIR / "streaks.json"
WEIGHT_FILE = DATA_DIR / "weight_log.json"

# ==================== HELPERS ====================
def load_json(path, default=None):
    if default is None:
        default = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_today():
    return date.today().isoformat()

def calculate_bmi(weight_kg, height_cm):
    if height_cm <= 0:
        return 0
    return round(weight_kg / ((height_cm / 100) ** 2), 1)

def estimate_ffmi(weight_kg, height_cm, body_fat_pct=15):
    """Rough FFMI estimate for natural lifters"""
    lean_mass = weight_kg * (1 - body_fat_pct / 100)
    height_m = height_cm / 100
    ffmi = lean_mass / (height_m ** 2)
    # Normalized to 1.8m
    ffmi_norm = ffmi + 6.1 * (1.8 - height_m)
    return round(ffmi_norm, 1)

# ==================== DEFAULT DATA ====================
DEFAULT_PROFILE = {
    "name": "Chiến Binh Khắc Kỷ",
    "height_cm": 175,
    "weight_kg": 75.0,
    "body_fat_pct": 15.0,
    "age": 25,
    "experience_years": 2,
    "goal_mro": "Mr. Olympia Natural - Natural Bodybuilding Champion",
    "goal_phd": "Tiến sĩ Quản trị Kinh doanh trong 2 năm",
    "goal_athlete": "Vận động viên cấp Quốc gia",
    "wake_time": "06:15",
    "sleep_time": "22:30",
    "school_load": "Trung bình",  # Thấp / Trung bình / Cao
    "start_date": get_today()
}

DEFAULT_BOOKS = [
    {"title": "Meditations - Marcus Aurelius", "category": "Khắc kỷ", "pages": 200, "priority": 1, "status": "Chưa đọc"},
    {"title": "Letters from a Stoic - Seneca", "category": "Khắc kỷ", "pages": 250, "priority": 1, "status": "Chưa đọc"},
    {"title": "The Obstacle is the Way - Ryan Holiday", "category": "Khắc kỷ", "pages": 220, "priority": 1, "status": "Chưa đọc"},
    {"title": "Research Design - John Creswell", "category": "PhD Research", "pages": 300, "priority": 1, "status": "Chưa đọc"},
    {"title": "Business Research Methods - Cooper & Schindler", "category": "PhD Research", "pages": 700, "priority": 2, "status": "Chưa đọc"},
    {"title": "Good to Great - Jim Collins", "category": "Quản trị", "pages": 320, "priority": 2, "status": "Chưa đọc"},
    {"title": "Thinking, Fast and Slow - Daniel Kahneman", "category": "Quyết định", "pages": 500, "priority": 2, "status": "Chưa đọc"},
    {"title": "The Lean Startup - Eric Ries", "category": "Kinh doanh", "pages": 300, "priority": 2, "status": "Chưa đọc"},
    {"title": "Atomic Habits - James Clear", "category": "Thói quen", "pages": 250, "priority": 1, "status": "Chưa đọc"},
    {"title": "Science and Development of Muscle Hypertrophy - Brad Schoenfeld", "category": "Bodybuilding", "pages": 300, "priority": 1, "status": "Chưa đọc"},
    {"title": "Starting Strength - Mark Rippetoe", "category": "Bodybuilding", "pages": 350, "priority": 2, "status": "Chưa đọc"},
    {"title": "The War of Art - Steven Pressfield", "category": "Kỷ luật", "pages": 180, "priority": 1, "status": "Chưa đọc"},
]

# Training plan - Upper/Lower 4 days, science-based for natural
TRAINING_PLAN = {
    "Upper A (Push focus)": [
        {"ex": "Bench Press", "sets": "4", "reps": "6-8", "rir": "1-2", "notes": "Compound chính"},
        {"ex": "Incline DB Press", "sets": "3", "reps": "8-12", "rir": "1-2", "notes": ""},
        {"ex": "Overhead Press", "sets": "3", "reps": "6-10", "rir": "1-2", "notes": ""},
        {"ex": "Lateral Raises", "sets": "4", "reps": "12-15", "rir": "0-1", "notes": "Side delts"},
        {"ex": "Triceps Pushdown", "sets": "3", "reps": "10-12", "rir": "1", "notes": ""},
        {"ex": "Face Pulls", "sets": "3", "reps": "15-20", "rir": "1", "notes": "Rear delts + health"},
    ],
    "Lower A (Quad focus)": [
        {"ex": "Back Squat", "sets": "4", "reps": "5-8", "rir": "1-2", "notes": "Compound chính"},
        {"ex": "Romanian Deadlift", "sets": "3", "reps": "8-10", "rir": "1-2", "notes": ""},
        {"ex": "Leg Press", "sets": "3", "reps": "10-15", "rir": "1", "notes": ""},
        {"ex": "Leg Curl", "sets": "3", "reps": "10-12", "rir": "1", "notes": ""},
        {"ex": "Calf Raises", "sets": "4", "reps": "10-15", "rir": "0-1", "notes": ""},
        {"ex": "Hanging Leg Raise", "sets": "3", "reps": "10-15", "rir": "1", "notes": "Core"},
    ],
    "Upper B (Pull focus)": [
        {"ex": "Pull-ups / Lat Pulldown", "sets": "4", "reps": "6-10", "rir": "1-2", "notes": "Compound chính"},
        {"ex": "Barbell Row", "sets": "4", "reps": "6-10", "rir": "1-2", "notes": ""},
        {"ex": "Chest-supported Row", "sets": "3", "reps": "10-12", "rir": "1", "notes": ""},
        {"ex": "Face Pulls / Rear Delt", "sets": "3", "reps": "12-15", "rir": "0-1", "notes": ""},
        {"ex": "Barbell Curl", "sets": "3", "reps": "8-12", "rir": "1", "notes": ""},
        {"ex": "Hammer Curl", "sets": "2", "reps": "10-12", "rir": "1", "notes": ""},
    ],
    "Lower B (Posterior focus)": [
        {"ex": "Trap Bar / Conventional Deadlift", "sets": "3", "reps": "4-6", "rir": "1-2", "notes": "Compound chính"},
        {"ex": "Front Squat / Goblet", "sets": "3", "reps": "8-10", "rir": "1-2", "notes": ""},
        {"ex": "Bulgarian Split Squat", "sets": "3", "reps": "8-12/leg", "rir": "1", "notes": ""},
        {"ex": "Seated Leg Curl", "sets": "3", "reps": "10-12", "rir": "1", "notes": ""},
        {"ex": "Standing Calf Raise", "sets": "4", "reps": "10-15", "rir": "0-1", "notes": ""},
        {"ex": "Ab Wheel / Cable Crunch", "sets": "3", "reps": "10-15", "rir": "1", "notes": ""},
    ],
}

# PhD modules (accelerated 2-year path focus)
PHD_MODULES = [
    {"module": "Năm 1 - Quý 1: Research Foundations", "topics": ["Quantitative Methods", "Qualitative Inquiry", "Research Design & Ethics", "Literature Review"], "hours_week": 15},
    {"module": "Năm 1 - Quý 2: Business Core Theory", "topics": ["Organizational Theory", "Strategic Management", "Leadership & Behavior", "Economics for Business"], "hours_week": 15},
    {"module": "Năm 1 - Quý 3: Advanced Methods", "topics": ["Econometrics / Stats II", "Survey Research", "Case Study Methods", "Data Analysis Tools (Python/R/SPSS)"], "hours_week": 18},
    {"module": "Năm 1 - Quý 4: Specialization Start", "topics": ["Chosen Focus (e.g. Strategy / Entrepreneurship / Analytics)", "Proposal Drafting", "Pilot Study"], "hours_week": 20},
    {"module": "Năm 2 - Quý 1-2: Dissertation Core", "topics": ["Data Collection", "Analysis", "Writing Chapters 1-3"], "hours_week": 25},
    {"module": "Năm 2 - Quý 3-4: Defense & Finish", "topics": ["Full Draft", "Committee Feedback", "Defense Prep", "Publication"], "hours_week": 25},
]

STOIC_QUOTES = [
    "Bạn không kiểm soát được những gì xảy ra với bạn, nhưng bạn kiểm soát được phản ứng của mình. — Epictetus",
    "Trở ngại chính là con đường. — Marcus Aurelius",
    "Chúng ta chịu đựng nhiều hơn trong tưởng tượng hơn là trong thực tế. — Seneca",
    "Hạnh phúc của bạn phụ thuộc vào chất lượng suy nghĩ của bạn. — Marcus Aurelius",
    "Đừng lãng phí những gì còn lại của cuộc đời để suy nghĩ về người khác. — Marcus Aurelius",
    "Khó khăn tăng cường tâm trí, cũng như lao động tăng cường cơ thể. — Seneca",
    "Điều tốt nhất là làm việc với những gì bạn có. — Epictetus",
    "Bạn có quyền lực trên tâm trí của mình — không phải trên các sự kiện bên ngoài. — Marcus Aurelius",
]

# ==================== LOAD DATA ====================
if "profile" not in st.session_state:
    st.session_state.profile = load_json(PROFILE_FILE, DEFAULT_PROFILE)
if "daily_logs" not in st.session_state:
    st.session_state.daily_logs = load_json(LOG_FILE, {})
if "streaks" not in st.session_state:
    st.session_state.streaks = load_json(STREAK_FILE, {"current": 0, "best": 0, "last_date": None})
if "weight_log" not in st.session_state:
    st.session_state.weight_log = load_json(WEIGHT_FILE, [])
if "books" not in st.session_state:
    st.session_state.books = load_json(DATA_DIR / "books.json", DEFAULT_BOOKS)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("🏆 Stoic Champion")
    st.caption("Khắc kỷ • Khoa học • Kỷ luật tuyệt đối")
    
    profile = st.session_state.profile
    st.markdown(f"**{profile.get('name', 'Chiến binh')}**")
    st.markdown(f"🎯 {profile.get('goal_mro', '')[:40]}...")
    st.markdown(f"🎓 {profile.get('goal_phd', '')}")
    
    st.divider()
    
    # Quick metrics
    bmi = calculate_bmi(profile.get("weight_kg", 75), profile.get("height_cm", 175))
    ffmi = estimate_ffmi(profile.get("weight_kg", 75), profile.get("height_cm", 175), profile.get("body_fat_pct", 15))
    st.metric("BMI", bmi)
    st.metric("FFMI ước tính", ffmi, help="Natural elite thường 22-25+")
    
    st.divider()
    page = st.radio(
        "Điều hướng",
        ["🏠 Dashboard", "✅ Checklist Hàng ngày", "🏋️ Tập luyện", "📚 Học tập & PhD", "📖 Sách", "⚖️ Cân nặng & Thể trạng", "🤖 AI Mentor Khắc kỷ", "📊 Điểm số & Cải thiện"],
        label_visibility="collapsed"
    )
    
    st.divider()
    st.caption("Ngủ trước 22:30 • Dậy ~06:15")
    st.caption("Nghỉ ngắn • Không burnout")

# ==================== PAGES ====================

if page == "🏠 Dashboard":
    st.header("🏠 Dashboard — Con đường của Nhà Vô địch")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Chuỗi hiện tại", f"{st.session_state.streaks.get('current', 0)} ngày", "🔥")
    with col2:
        st.metric("Chuỗi tốt nhất", f"{st.session_state.streaks.get('best', 0)} ngày")
    with col3:
        days_left = 730  # ~2 years
        start = profile.get("start_date", get_today())
        try:
            days_passed = (date.today() - date.fromisoformat(start)).days
            days_left = max(0, 730 - days_passed)
        except:
            pass
        st.metric("Ngày còn lại (2 năm)", days_left)
    with col4:
        logs = st.session_state.daily_logs
        completed_today = logs.get(get_today(), {}).get("completed", False)
        st.metric("Hôm nay", "✅ Xong" if completed_today else "⏳ Đang làm")
    
    st.subheader("📜 Lời dạy Khắc kỷ hôm nay")
    quote_idx = date.today().toordinal() % len(STOIC_QUOTES)
    st.info(STOIC_QUOTES[quote_idx])
    
    st.subheader("⏰ Lịch trình khung (khoa học + phục hồi)")
    st.markdown("""
    | Thời gian | Hoạt động | Nguyên tắc |
    |-----------|-----------|------------|
    | 06:15 | Thức dậy + Ánh sáng mặt trời + Nước | Circadian reset |
    | 06:30-07:00 | Di chuyển nhẹ / Mobility | Blood flow |
    | 07:00-08:00 | Bữa sáng protein cao + Planning | Fuel |
    | 08:00-12:00 | Deep Work: Học PhD / Nghiên cứu | Deep focus (90-120p blocks) |
    | 12:00-13:00 | Ăn trưa + Nghỉ ngắn 20p | Recovery |
    | 13:00-16:00 | Học tiếp hoặc Công việc | |
    | 16:30-18:00 | **Tập luyện** (Upper/Lower) | Progressive overload |
    | 18:30-19:30 | Ăn tối + Protein | |
    | 19:30-21:00 | Đọc sách / Review / Light study | |
    | 21:00-22:00 | Wind-down: không màn hình, journal | Sleep hygiene |
    | **22:30** | **Ngủ** | Growth hormone peak |
    """)
    
    st.warning("⚠️ Quy tắc cứng: Ngủ trước 22:30. Dậy sau 6g. Nghỉ ngắn khi cần. Điều chỉnh volume nếu school_load = Cao.")
    
    if st.button("💾 Lưu tất cả dữ liệu"):
        save_json(PROFILE_FILE, st.session_state.profile)
        save_json(LOG_FILE, st.session_state.daily_logs)
        save_json(STREAK_FILE, st.session_state.streaks)
        save_json(WEIGHT_FILE, st.session_state.weight_log)
        save_json(DATA_DIR / "books.json", st.session_state.books)
        st.success("Đã lưu!")

elif page == "✅ Checklist Hàng ngày":
    st.header("✅ Checklist Hàng ngày — Xây dựng chuỗi")
    
    today = get_today()
    logs = st.session_state.daily_logs
    if today not in logs:
        logs[today] = {
            "sleep_ok": False,
            "wake_ok": False,
            "training": False,
            "study_hours": 0.0,
            "reading": False,
            "nutrition": False,
            "recovery": False,
            "stoic_practice": False,
            "notes": "",
            "completed": False
        }
    
    day_log = logs[today]
    
    st.subheader(f"Ngày: {today}")
    
    c1, c2 = st.columns(2)
    with c1:
        day_log["sleep_ok"] = st.checkbox("Ngủ trước 22:30 (hoặc đủ 7.5-9h)", value=day_log.get("sleep_ok", False))
        day_log["wake_ok"] = st.checkbox("Dậy ~06:15 và không trì hoãn", value=day_log.get("wake_ok", False))
        day_log["training"] = st.checkbox("Hoàn thành buổi tập theo plan", value=day_log.get("training", False))
        day_log["reading"] = st.checkbox("Đọc sách ít nhất 30 phút", value=day_log.get("reading", False))
    with c2:
        day_log["nutrition"] = st.checkbox("Protein đủ (1.6-2.2g/kg) + calories đúng mục tiêu", value=day_log.get("nutrition", False))
        day_log["recovery"] = st.checkbox("Có nghỉ ngắn / mobility / không overtrain", value=day_log.get("recovery", False))
        day_log["stoic_practice"] = st.checkbox("Journal hoặc thực hành khắc kỷ (10p)", value=day_log.get("stoic_practice", False))
        day_log["study_hours"] = st.number_input("Số giờ học sâu (PhD/school)", min_value=0.0, max_value=12.0, value=float(day_log.get("study_hours", 0)), step=0.5)
    
    day_log["notes"] = st.text_area("Ghi chú ngày", value=day_log.get("notes", ""))
    
    # Calculate completion
    checks = [day_log["sleep_ok"], day_log["wake_ok"], day_log["training"], day_log["reading"],
              day_log["nutrition"], day_log["recovery"], day_log["stoic_practice"], day_log["study_hours"] >= 2]
    score = sum(checks) / len(checks)
    day_log["completed"] = score >= 0.75  # 75% threshold for streak
    
    st.progress(score)
    st.write(f"Hoàn thành ngày: **{score*100:.0f}%** {'✅ Đủ để giữ chuỗi' if day_log['completed'] else '❌ Cần cố thêm'}")
    
    if st.button("💾 Lưu checklist hôm nay"):
        logs[today] = day_log
        st.session_state.daily_logs = logs
        
        # Update streak
        streaks = st.session_state.streaks
        if day_log["completed"]:
            if streaks.get("last_date") == (date.today() - timedelta(days=1)).isoformat() or streaks.get("last_date") is None:
                streaks["current"] = streaks.get("current", 0) + 1
            elif streaks.get("last_date") != today:
                streaks["current"] = 1
            streaks["last_date"] = today
            streaks["best"] = max(streaks.get("best", 0), streaks["current"])
        else:
            if streaks.get("last_date") != today:
                streaks["current"] = 0
        st.session_state.streaks = streaks
        save_json(LOG_FILE, logs)
        save_json(STREAK_FILE, streaks)
        st.success(f"Đã lưu! Chuỗi hiện tại: {streaks['current']} ngày")

elif page == "🏋️ Tập luyện":
    st.header("🏋️ Kế hoạch Tập luyện Natural Bodybuilding")
    st.markdown("""
    **Nguyên tắc khoa học (Natural):**
    - Mỗi nhóm cơ 2x/tuần
    - Volume: 10-20 sets/nhóm cơ/tuần (bắt đầu 12-16)
    - RIR 0-3 (gần failure)
    - Progressive overload: tăng rep rồi tăng tạ
    - Deload mỗi 4-6 tuần
    - Session < 75 phút để kiểm soát cortisol
    """)
    
    school = st.selectbox("Mức độ học trên trường hiện tại", ["Thấp", "Trung bình", "Cao"], 
                          index=["Thấp", "Trung bình", "Cao"].index(profile.get("school_load", "Trung bình")))
    if school != profile.get("school_load"):
        st.session_state.profile["school_load"] = school
        save_json(PROFILE_FILE, st.session_state.profile)
    
    if school == "Cao":
        st.warning("⚠️ School load CAO → Giảm volume 20-30%, ưu tiên compound, có thể chuyển 3 ngày Full Body.")
    
    day_choice = st.selectbox("Chọn ngày tập", list(TRAINING_PLAN.keys()))
    
    st.subheader(day_choice)
    plan = TRAINING_PLAN[day_choice]
    df = pd.DataFrame(plan)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("**Cách tiến bộ:** Mỗi tuần cố gắng thêm 1 rep hoặc tăng nhẹ tạ khi đạt top rep range với RIR đúng.")
    
    with st.expander("📋 Lịch tuần mẫu"):
        st.markdown("""
        - **Thứ 2**: Upper A
        - **Thứ 3**: Lower A
        - **Thứ 4**: Nghỉ hoặc Active recovery (đi bộ, mobility)
        - **Thứ 5**: Upper B
        - **Thứ 6**: Lower B
        - **Thứ 7-CN**: Nghỉ hoàn toàn hoặc rất nhẹ + đọc sách
        """)
    
    st.info("Protein: 1.6–2.2 g/kg/ngày. Carbs cao hơn ngày tập. Ngủ là phần quan trọng nhất của 'tập'.")

elif page == "📚 Học tập & PhD":
    st.header("📚 Lộ trình Tiến sĩ Quản trị Kinh doanh (Accelerated 2 năm)")
    
    st.markdown("""
    **Thực tế:** PhD/DBA truyền thống 3-5 năm. Để làm trong ~2 năm cần:
    - Đã có Master (hoặc equivalent)
    - Chọn chương trình Executive/Accelerated DBA hoặc PhD applied
    - Full focus, research topic rõ từ sớm
    - Mentorship mạnh
    """)
    
    for mod in PHD_MODULES:
        with st.expander(f"**{mod['module']}** — ~{mod['hours_week']}h/tuần"):
            for t in mod["topics"]:
                st.markdown(f"- {t}")
    
    st.subheader("Điều chỉnh theo school load")
    st.write(f"Hiện tại: **{profile.get('school_load')}** → Nếu Cao, giảm giờ deep work PhD, ưu tiên deadline trường trước.")
    
    st.subheader("Công cụ cần có")
    st.markdown("""
    - Zotero / Mendeley (quản lý tài liệu)
    - Notion hoặc Obsidian (second brain)
    - Python + pandas / R cho analysis
    - Overleaf (LaTeX) cho dissertation
    - ChatGPT/Claude/Grok để brainstorm & outline (nhưng tự viết core)
    """)

elif page == "📖 Sách":
    st.header("📖 Danh sách Sách Bắt buộc")
    
    books = st.session_state.books
    for i, book in enumerate(books):
        col1, col2, col3 = st.columns([4, 2, 2])
        with col1:
            st.write(f"**{book['title']}** ({book['category']}) — {book['pages']} trang")
        with col2:
            new_status = st.selectbox("Trạng thái", ["Chưa đọc", "Đang đọc", "Đã đọc"], 
                                      index=["Chưa đọc", "Đang đọc", "Đã đọc"].index(book.get("status", "Chưa đọc")),
                                      key=f"book_status_{i}")
            books[i]["status"] = new_status
        with col3:
            if book.get("priority", 2) == 1:
                st.write("🔥 Ưu tiên cao")
    
    if st.button("💾 Lưu trạng thái sách"):
        st.session_state.books = books
        save_json(DATA_DIR / "books.json", books)
        st.success("Đã lưu!")

elif page == "⚖️ Cân nặng & Thể trạng":
    st.header("⚖️ Theo dõi Cân nặng & Body Composition")
    
    p = st.session_state.profile
    c1, c2, c3 = st.columns(3)
    with c1:
        new_h = st.number_input("Chiều cao (cm)", value=float(p.get("height_cm", 175)), step=0.5)
    with c2:
        new_w = st.number_input("Cân nặng hiện tại (kg)", value=float(p.get("weight_kg", 75.0)), step=0.1)
    with c3:
        new_bf = st.number_input("% Body fat ước tính", value=float(p.get("body_fat_pct", 15.0)), step=0.5)
    
    if st.button("Cập nhật profile"):
        st.session_state.profile["height_cm"] = new_h
        st.session_state.profile["weight_kg"] = new_w
        st.session_state.profile["body_fat_pct"] = new_bf
        save_json(PROFILE_FILE, st.session_state.profile)
        # Log weight
        wlog = st.session_state.weight_log
        wlog.append({"date": get_today(), "weight": new_w, "bf": new_bf})
        st.session_state.weight_log = wlog
        save_json(WEIGHT_FILE, wlog)
        st.success("Đã cập nhật!")
    
    bmi = calculate_bmi(new_w, new_h)
    ffmi = estimate_ffmi(new_w, new_h, new_bf)
    st.metric("BMI", bmi)
    st.metric("FFMI (ước tính)", ffmi)
    st.caption("FFMI natural elite stage thường 23-25+. Trên 25 hiếm và khó tự nhiên.")
    
    if st.session_state.weight_log:
        dfw = pd.DataFrame(st.session_state.weight_log)
        fig = px.line(dfw, x="date", y="weight", title="Biểu đồ cân nặng", markers=True)
        st.plotly_chart(fig, use_container_width=True)

elif page == "🤖 AI Mentor Khắc kỷ":
    st.header("🤖 AI Mentor — Bậc thầy Khắc kỷ & Tỷ phú sức khỏe 20 tuổi")
    st.caption("Tôi là phiên bản của bạn trong tương lai: nhiều bằng tiến sĩ, tỷ phú, thân hình đỉnh cao, tâm trí thép. Hỏi bất cứ điều gì.")
    
    # Simple rule-based + stoic responses
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    user_input = st.chat_input("Hỏi mentor...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Simple response logic
        lower = user_input.lower()
        if any(w in lower for w in ["mệt", "kiệt", "burnout", "stress", "chán"]):
            reply = """Nghe đây, chiến binh. Cảm giác kiệt sức là tín hiệu, không phải thất bại. 
            
Marcus Aurelius từng viết giữa chiến trận. Seneca bị lưu đày. Họ vẫn hành động.
            
Hôm nay: giảm volume tập 50%, học chỉ những gì bắt buộc, ngủ đúng giờ. Nghỉ ngắn 20 phút sau mỗi 90 phút làm việc. 
Bạn không phải máy. Nhưng bạn cũng không được phép bỏ cuộc vì cảm xúc tạm thời. 
Hành động nhỏ hôm nay > ý định lớn ngày mai."""
        elif any(w in lower for w in ["tập", "gym", "cơ", "muscle", "workout"]):
            reply = """Tập luyện natural là cuộc chơi dài hạn của sự nhất quán + progressive overload + phục hồi.
            
10-20 sets mỗi nhóm cơ mỗi tuần, gần failure, 2x frequency. Ngủ và protein là 70% kết quả. 
Đừng chase pump. Chase performance tăng dần. Deload khi cần. 
Bạn đang xây dựng cơ thể có thể đứng trên sân khấu MrO Natural — không phải cơ thể của người tập 1 năm rồi bỏ."""
        elif any(w in lower for w in ["học", "phd", "tiến sĩ", "nghiên cứu", "luận án"]):
            reply = """Tiến sĩ trong 2 năm là tham vọng cực đoan — và đó chính là điểm mạnh nếu bạn chấp nhận cái giá.
            
Chọn topic sớm. Viết mỗi ngày dù chỉ 300 từ. Đọc có mục đích. Dùng AI để tăng tốc outline và literature, nhưng tư duy và argument phải là của bạn.
Nếu school load cao → tạm giảm PhD hours, không giảm chất lượng ngủ và tập. 
Tiến sĩ không phải tấm bằng. Nó là bằng chứng bạn có thể chịu đựng sự mơ hồ và vẫn tiến về phía trước."""
        elif any(w in lower for w in ["ngủ", "sleep", "thức"]):
            reply = """Ngủ trước 22:30 không phải gợi ý — đó là luật. 
Growth hormone, consolidation trí nhớ, phục hồi cơ, kiểm soát cortisol — tất cả phụ thuộc vào đó.
Dậy cố định ~6:15. Ánh sáng buổi sáng. Không đàm phán với điện thoại sau 21:00.
Người thắng cuộc ngủ như vận động viên chuyên nghiệp, không như sinh viên thi cuối kỳ."""
        else:
            reply = f"""Tôi nghe bạn. 
            
Nhắc nhở khắc kỷ: Bạn chỉ kiểm soát được nỗ lực, thái độ và hành động tiếp theo. 
Không kiểm soát được kết quả cuối cùng, ý kiến người khác, hay tốc độ tiến bộ chính xác.
            
Hôm nay bạn cần làm gì tiếp theo? Một việc nhỏ, rõ ràng, có thể hoàn thành trong 25-90 phút. Làm nó. Rồi làm việc tiếp theo.
            
Chuỗi của bạn đang ở {st.session_state.streaks.get('current', 0)} ngày. Bảo vệ nó."""
        
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

elif page == "📊 Điểm số & Cải thiện":
    st.header("📊 Hệ thống Chấm điểm & Lộ trình Cải thiện")
    
    # Calculate overall score
    streaks = st.session_state.streaks
    logs = st.session_state.daily_logs
    books = st.session_state.books
    
    # Consistency score
    recent_days = 14
    completed_count = 0
    for i in range(recent_days):
        d = (date.today() - timedelta(days=i)).isoformat()
        if logs.get(d, {}).get("completed"):
            completed_count += 1
    consistency = (completed_count / recent_days) * 100
    
    # Book progress
    read_books = sum(1 for b in books if b.get("status") == "Đã đọc")
    book_score = (read_books / max(len(books), 1)) * 100
    
    # Body score (rough)
    ffmi = estimate_ffmi(profile.get("weight_kg", 75), profile.get("height_cm", 175), profile.get("body_fat_pct", 15))
    body_score = min(100, max(0, (ffmi - 18) * 12))  # rough scale
    
    # Streak score
    streak_score = min(100, streaks.get("current", 0) * 5)
    
    overall = (consistency * 0.4 + streak_score * 0.2 + book_score * 0.2 + body_score * 0.2)
    
    st.subheader("Điểm tổng thể hiện tại")
    st.metric("Overall Readiness Score", f"{overall:.1f}/100")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Consistency (14 ngày)", f"{consistency:.0f}%")
    col2.metric("Streak Power", f"{streak_score:.0f}")
    col3.metric("Tri thức (Sách)", f"{book_score:.0f}")
    col4.metric("Thể trạng (FFMI proxy)", f"{body_score:.0f}")
    
    st.progress(overall / 100)
    
    st.subheader("Đánh giá & Việc cần cải thiện để thành Triệu phú + VĐV chuyên nghiệp")
    
    if overall < 40:
        level = "Người mới bắt đầu nghiêm túc"
        advice = """
        **Ưu tiên tuyệt đối:**
        1. Xây dựng thói quen ngủ 22:30 - 6:15 trong 21 ngày liên tiếp (không đàm phán).
        2. Checklist hàng ngày đạt ≥75% ít nhất 5/7 ngày mỗi tuần.
        3. Chọn 1 chương trình tập và bám sát 8 tuần không đổi lung tung.
        4. Đọc xong 2 cuốn khắc kỷ + Atomic Habits trước.
        5. Bắt đầu log cân nặng và protein hàng ngày.
        """
    elif overall < 65:
        level = "Đang trên đường trở thành chuyên nghiệp"
        advice = """
        **Tiếp theo:**
        1. Tăng consistency lên ≥80% trong 30 ngày.
        2. Bắt đầu đo body composition chính xác hơn (DEXA nếu được).
        3. Chọn topic nghiên cứu PhD và viết 500 từ outline mỗi tuần.
        4. Tăng volume tập dần đến MAV (12-18 sets) nếu recovery tốt.
        5. Xây dựng hệ thống thu nhập phụ (skill → offer → client) song song — triệu phú không chỉ đến từ bằng cấp.
        """
    else:
        level = "Sẵn sàng cho cấp độ cao"
        advice = """
        **Tối ưu hóa:**
        1. Tìm coach natural bodybuilding có thành tích thực tế.
        2. Apply chương trình DBA/PhD accelerated phù hợp và bắt đầu ngay.
        3. Xây dựng personal brand + content về hành trình (tài sản dài hạn).
        4. Network với người đã ở nơi bạn muốn đến.
        5. Giữ humility — càng lên cao càng dễ burnout nếu ego dẫn đường.
        """
    
    st.success(f"**Cấp độ hiện tại: {level}**")
    st.markdown(advice)
    
    st.subheader("Lộ trình 24 tháng tóm tắt")
    st.markdown("""
    | Giai đoạn | Tập trung chính | Chỉ số thành công |
    |-----------|-----------------|-------------------|
    | Tháng 1-3 | Foundation: Ngủ + Checklist + Base training + 4 cuốn sách | Chuỗi 60 ngày, FFMI tăng nhẹ |
    | Tháng 4-8 | Intensification: Tăng volume/intensity + Research proposal | Consistency 80%+, đề cương PhD |
    | Tháng 9-14 | Specialization: Peak training blocks + Data collection | Body composition stage-ready direction + data |
    | Tháng 15-20 | Peak + Writing | Contest prep nếu sẵn sàng + full draft |
    | Tháng 21-24 | Defense + Stage | Bảo vệ thành công + thi đấu National/Natural pro |
    """)
    
    st.info("""
    **Lời cuối từ Mentor:**  
    Trở thành nhà vô địch MrO Natural + Tiến sĩ + triệu phú trong 2 năm là tham vọng gần như bất khả thi với hầu hết mọi người.  
    Đó chính là lý do nó đáng giá.  
    Bạn không cần hoàn hảo. Bạn cần không bỏ cuộc vào ngày thứ 47, 183, và 600.  
    Hãy bắt đầu bằng việc hoàn thành checklist hôm nay. Rồi ngày mai. Rồi ngày kia.  
    Đó là cách duy nhất.
    """)

# Footer
st.divider()
st.caption("Stoic Champion Path • Khoa học + Khắc kỷ + Kỷ luật tuyệt đối • Ngủ trước 22:30 • Dậy ~6:15 • Bảo vệ chuỗi")
