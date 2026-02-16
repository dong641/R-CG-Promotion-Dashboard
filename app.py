import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# 유틸리티 함수
# ---------------------------------------------------------
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def get_week_range(date_obj):
    start = date_obj - datetime.timedelta(days=date_obj.weekday())
    end = start + datetime.timedelta(days=6)
    return start, end

# ---------------------------------------------------------
# 구글 시트 데이터 로드/저장 함수
# ---------------------------------------------------------
def get_db_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name, default_func):
    conn = get_db_connection()
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df.empty:
            return default_func()
        return df
    except:
        return default_func()

def save_data(sheet_name, df):
    conn = get_db_connection()
    try:
        conn.update(worksheet=sheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"저장 실패: {e}")
        return False

# --- 기본 데이터 ---
def create_default_promotions():
    return pd.DataFrame([
        {"프로모션명": "2024 봄 정기 세일", "채널": "Off Trade", "담당자": "김철수", "상태": "진행중", "진척율": 75, "시작일": datetime.date(2024, 3, 1), "종료일": datetime.date(2024, 3, 15)},
        {"프로모션명": "신규 회원 가입 이벤트", "채널": "On Trade", "담당자": "이영희", "상태": "기획단계", "진척율": 20, "시작일": datetime.date(2024, 4, 1), "종료일": datetime.date(2024, 4, 30)},
    ])

def create_default_projects():
    return pd.DataFrame([
        {"Project": "신제품 런칭 프로젝트", "Owner": "박팀장", "Status": "진행중", "Progress": 45, "Start": datetime.date(2024, 3, 1), "End": datetime.date(2024, 5, 31)},
        {"Project": "웹사이트 리뉴얼", "Owner": "최대리", "Status": "기획", "Progress": 10, "Start": datetime.date(2024, 4, 1), "End": datetime.date(2024, 6, 30)},
    ])

def create_empty_report_df():
    return pd.DataFrame(columns=["Week_Start", "Assignee", "Type", "Project", "Content", "Status"])

def create_default_project_tasks():
    return pd.DataFrame([
        {"Project": "신제품 런칭 프로젝트", "Task": "시장 조사 완료", "Department": "기획팀", "Start": "2024-03-01", "End": "2024-03-10", "Progress": 100, "Milestone": "Y"},
        {"Project": "신제품 런칭 프로젝트", "Task": "패키지 디자인", "Department": "디자인팀", "Start": "2024-03-11", "End": "2024-03-25", "Progress": 60, "Milestone": "N"},
        {"Project": "신제품 런칭 프로젝트", "Task": "시제품 생산", "Department": "생산팀", "Start": "2024-03-26", "End": "2024-04-15", "Progress": 0, "Milestone": "Y"},
        {"Project": "웹사이트 리뉴얼", "Task": "메인 페이지 기획", "Department": "기획팀", "Start": "2024-04-01", "End": "2024-04-15", "Progress": 20, "Milestone": "N"}
    ])

# ---------------------------------------------------------
# 데이터 로드
# ---------------------------------------------------------
def load_all_data():
    df_promo = load_data("promotions", create_default_promotions)
    for col in ['시작일', '종료일']:
        if col in df_promo.columns:
            df_promo[col] = pd.to_datetime(df_promo[col], errors='coerce').dt.date
    if '진척율' in df_promo.columns:
        df_promo['진척율'] = pd.to_numeric(df_promo['진척율'].astype(str).str.replace('%', ''), errors='coerce').fillna(0).astype(int)
    st.session_state.promotions = df_promo

    df_projects = load_data("projects", create_default_projects)
    for col in ['Start', 'End']:
        if col in df_projects.columns:
            df_projects[col] = pd.to_datetime(df_projects[col], errors='coerce').dt.date
    if 'Progress' in df_projects.columns:
        df_projects['Progress'] = pd.to_numeric(df_projects['Progress'], errors='coerce').fillna(0).astype(int)
    st.session_state.projects = df_projects

    df_tasks = load_data("project_tasks", create_default_project_tasks)
    for col in ['Start', 'End']:
        if col in df_tasks.columns:
            df_tasks[col] = pd.to_datetime(df_tasks[col], errors='coerce').dt.date
    if 'Progress' in df_tasks.columns:
        df_tasks['Progress'] = pd.to_numeric(df_tasks['Progress'], errors='coerce').fillna(0).astype(int)
    st.session_state.project_tasks = df_tasks


# =========================================================
# 페이지 설정 & 글로벌 스타일
# =========================================================
st.set_page_config(page_title="Promo Hub", page_icon="◈", layout="wide")

# ── 모던 다크 테마 CSS ──
st.markdown("""
<style>
/* ── Import Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root Variables ── */
:root {
    --bg-primary: #08090d;
    --bg-secondary: #0f1116;
    --bg-card: #13151b;
    --bg-card-hover: #191c24;
    --border-subtle: rgba(255,255,255,0.06);
    --border-accent: rgba(99,179,237,0.25);
    --text-primary: #e8eaed;
    --text-secondary: #8b8fa3;
    --text-muted: #555970;
    --accent-blue: #63b3ed;
    --accent-teal: #4fd1c5;
    --accent-violet: #b794f4;
    --accent-amber: #f6c958;
    --accent-rose: #fc8181;
    --accent-green: #68d391;
    --gradient-primary: linear-gradient(135deg, #63b3ed 0%, #4fd1c5 100%);
    --gradient-violet: linear-gradient(135deg, #b794f4 0%, #63b3ed 100%);
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --shadow-card: 0 1px 3px rgba(0,0,0,0.3), 0 0 0 1px var(--border-subtle);
    --shadow-glow: 0 0 20px rgba(99,179,237,0.08);
    --font-main: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

/* ── Global Reset ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-main) !important;
}
[data-testid="stApp"] {
    background-color: var(--bg-primary) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-subtle) !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stRadio label span {
    color: var(--text-secondary) !important;
    font-family: var(--font-main) !important;
}
[data-testid="stSidebar"] .stRadio label[data-checked="true"] span {
    color: var(--accent-blue) !important;
    font-weight: 500 !important;
}

/* ── Typography ── */
h1 {
    font-family: var(--font-main) !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    font-size: 1.75rem !important;
    letter-spacing: -0.02em !important;
}
h2, h3 {
    font-family: var(--font-main) !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.01em !important;
}
h4, h5, h6 {
    font-family: var(--font-main) !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
}
p, span, label, div {
    color: var(--text-primary) !important;
}

/* ── Metric Cards ── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    padding: 20px 24px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stMetric"]:hover {
    background: var(--bg-card-hover) !important;
    border-color: var(--border-accent) !important;
    box-shadow: var(--shadow-glow) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-main) !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 0 !important;
    border-bottom: 1px solid var(--border-subtle) !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--font-main) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
    padding: 10px 20px !important;
    border-radius: 0 !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.15s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-secondary) !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent-blue) !important;
    border-bottom: 2px solid var(--accent-blue) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: var(--font-main) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    border-radius: var(--radius-sm) !important;
    padding: 8px 20px !important;
    transition: all 0.2s ease !important;
    border: 1px solid var(--border-subtle) !important;
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
}
.stButton > button:hover {
    border-color: var(--border-accent) !important;
    box-shadow: var(--shadow-glow) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stFormSubmitButton"] {
    background: var(--gradient-primary) !important;
    border: none !important;
    color: #08090d !important;
    font-weight: 600 !important;
}

/* ── Data Editor & DataFrame ── */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
    border: 1px solid var(--border-subtle) !important;
}

/* ── Form Elements ── */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stDateInput > div > div > input {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-main) !important;
}
.stTextInput > div > div > input:focus,
.stSelectbox > div > div:focus-within {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 2px rgba(99,179,237,0.15) !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-secondary) !important;
    font-family: var(--font-main) !important;
    font-weight: 500 !important;
}
.streamlit-expanderContent {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
}

/* ── Containers ── */
[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
}

/* ── Dividers ── */
hr {
    border-color: var(--border-subtle) !important;
    margin: 1.5rem 0 !important;
}

/* ── Info / Warning / Success boxes ── */
[data-testid="stAlert"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-secondary) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: #2d3041; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3d4057; }

/* ── Custom Metric Cards (HTML) ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}
@media (max-width: 768px) {
    .metric-grid { grid-template-columns: repeat(2, 1fr); }
}
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 24px;
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    opacity: 0;
    transition: opacity 0.25s ease;
}
.metric-card:hover {
    border-color: var(--border-accent);
    transform: translateY(-2px);
    box-shadow: var(--shadow-glow);
}
.metric-card:hover::before { opacity: 1; }
.metric-card:nth-child(1)::before { background: var(--gradient-primary); }
.metric-card:nth-child(2)::before { background: linear-gradient(90deg, var(--accent-teal), var(--accent-green)); }
.metric-card:nth-child(3)::before { background: linear-gradient(90deg, var(--accent-violet), var(--accent-rose)); }
.metric-card:nth-child(4)::before { background: linear-gradient(90deg, var(--accent-amber), var(--accent-rose)); }
.metric-label {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.03em;
    line-height: 1;
}
.metric-sub {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 6px;
}

/* ── Status Chips ── */
.status-chip {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.chip-active { background: rgba(79,209,197,0.12); color: var(--accent-teal); }
.chip-plan { background: rgba(183,148,244,0.12); color: var(--accent-violet); }
.chip-done { background: rgba(104,211,145,0.12); color: var(--accent-green); }
.chip-delay { background: rgba(246,201,88,0.12); color: var(--accent-amber); }
.chip-stop { background: rgba(252,129,129,0.12); color: var(--accent-rose); }

/* ── PPP Report Cards ── */
.ppp-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 28px;
    margin-bottom: 16px;
    transition: all 0.2s ease;
}
.ppp-card:hover {
    border-color: var(--border-accent);
    box-shadow: var(--shadow-glow);
}
.ppp-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-subtle);
}
.ppp-avatar {
    width: 40px; height: 40px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; font-weight: 700;
    color: #08090d;
}
.ppp-name {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text-primary);
}
.ppp-section-title {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 16px 0 8px 0;
}
.ppp-item {
    padding: 8px 12px;
    margin: 4px 0;
    border-radius: var(--radius-sm);
    background: var(--bg-secondary);
    font-size: 0.85rem;
    color: var(--text-secondary);
    line-height: 1.5;
}
.ppp-item-tag {
    color: var(--accent-blue);
    font-weight: 600;
    font-size: 0.78rem;
}

/* ── Page Header ── */
.page-header {
    margin-bottom: 32px;
}
.page-header h1 {
    margin: 0 !important;
    padding: 0 !important;
}
.page-subtitle {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-top: 4px;
}

/* ── Sidebar Title ── */
.sidebar-brand {
    font-family: var(--font-main);
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
}
.sidebar-sub {
    font-size: 0.72rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

/* ── Progress Bar (Custom) ── */
.progress-track {
    width: 100%;
    height: 4px;
    background: rgba(255,255,255,0.06);
    border-radius: 2px;
    overflow: hidden;
    margin-top: 6px;
}
.progress-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.4s ease;
}

/* ── Hide streamlit defaults ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

if 'promotions' not in st.session_state:
    load_all_data()


# ── Plotly 공통 레이아웃 ──
PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Outfit, -apple-system, sans-serif", size=12, color='#8b8fa3'),
    margin=dict(t=30, b=10, l=10, r=10),
    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', zeroline=False),
    yaxis=dict(showgrid=False),
)

# 상태 → 칩 매핑
STATUS_CHIP = {
    "진행중": ("chip-active", "● 진행중"),
    "기획단계": ("chip-plan", "◎ 기획단계"),
    "기획": ("chip-plan", "◎ 기획"),
    "완료": ("chip-done", "✓ 완료"),
    "준비": ("chip-plan", "◎ 준비"),
    "지연": ("chip-delay", "! 지연"),
    "중단": ("chip-stop", "✕ 중단"),
}

def get_status_chip(status):
    cls, txt = STATUS_CHIP.get(status, ("chip-plan", status))
    return f'<span class="status-chip {cls}">{txt}</span>'

# 아바타 색상 팔레트
AVATAR_COLORS = ['#63b3ed', '#4fd1c5', '#b794f4', '#f6c958', '#fc8181', '#68d391', '#f687b3']

def get_avatar_color(name):
    idx = sum(ord(c) for c in str(name)) % len(AVATAR_COLORS)
    return AVATAR_COLORS[idx]


# ---------------------------------------------------------
# 사이드바
# ---------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-brand">◈ Promo Hub</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Promotion Management System</div>', unsafe_allow_html=True)
    st.write("")
    
    page = st.radio(
        "NAVIGATION",
        ["📊 대시보드", "🧩 프로젝트 간트차트", "📅 주간 업무 (PPP)", "⚙️ 관리자 페이지"],
        label_visibility="collapsed"
    )
    
    st.write("")
    st.write("")
    
    if st.button("로그아웃", use_container_width=True):
        st.session_state.is_admin_unlocked = False
        safe_rerun()


# =========================================================
# PAGE 1: 대시보드
# =========================================================
if page == "📊 대시보드":
    st.markdown("""
    <div class="page-header">
        <h1>프로모션 현황</h1>
        <div class="page-subtitle">실시간 프로모션 진행 상태를 한눈에 확인하세요</div>
    </div>
    """, unsafe_allow_html=True)
    
    df = st.session_state.promotions
    
    total = len(df)
    active = len(df[df['상태'] == '진행중'])
    done = len(df[df['상태'] == '완료'])
    active_df = df[df['상태'] != '완료']
    avg_prog = active_df['진척율'].mean() if not active_df.empty else 0
    
    # ── 커스텀 메트릭 카드 ──
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">전체 프로모션</div>
            <div class="metric-value">{total}</div>
            <div class="metric-sub">Total campaigns</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">진행중</div>
            <div class="metric-value" style="color: var(--accent-teal);">{active}</div>
            <div class="metric-sub">Active now</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">완료</div>
            <div class="metric-value" style="color: var(--accent-green);">{done}</div>
            <div class="metric-sub">Completed</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">평균 달성률</div>
            <div class="metric-value">{avg_prog:.0f}<span style="font-size:1rem; color:var(--text-muted);">%</span></div>
            <div class="progress-track"><div class="progress-fill" style="width:{avg_prog}%; background: var(--gradient-primary);"></div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 탭별 리스트 ──
    df_active = df[df['상태'] != '완료']
    df_completed = df[df['상태'] == '완료']
    
    t1, t2, t3 = st.tabs([f"진행 중  {len(df_active)}", f"완료  {len(df_completed)}", "전체 목록"])
    
    cfg = {
        "진척율": st.column_config.ProgressColumn("달성률", format="%d%%", min_value=0, max_value=100),
        "시작일": st.column_config.DateColumn("시작", format="YYYY.MM.DD"),
        "종료일": st.column_config.DateColumn("종료", format="YYYY.MM.DD"),
    }
    
    with t1:
        if df_active.empty:
            st.caption("진행 중인 프로모션이 없습니다.")
        else:
            st.dataframe(df_active, column_config=cfg, use_container_width=True, hide_index=True, height=400)
    with t2:
        if df_completed.empty:
            st.caption("완료된 프로모션이 없습니다.")
        else:
            st.dataframe(df_completed, column_config=cfg, use_container_width=True, hide_index=True, height=400)
    with t3:
        st.dataframe(df, column_config=cfg, use_container_width=True, hide_index=True, height=400)


# =========================================================
# PAGE 2: 프로젝트 간트차트
# =========================================================
elif page == "🧩 프로젝트 간트차트":
    st.markdown("""
    <div class="page-header">
        <h1>프로젝트 타임라인</h1>
        <div class="page-subtitle">프로젝트 일정과 마일스톤을 시각적으로 관리합니다</div>
    </div>
    """, unsafe_allow_html=True)
    
    projects_df = st.session_state.projects.copy()
    tasks_df = st.session_state.project_tasks.copy()
    
    for df_temp in [projects_df, tasks_df]:
        if not df_temp.empty:
            df_temp['Start'] = pd.to_datetime(df_temp['Start'])
            df_temp['End'] = pd.to_datetime(df_temp['End'])

    tab_overview, tab_detail = st.tabs(["전체 현황", "프로젝트 상세"])

    # ── 전체 현황 ──
    with tab_overview:
        if not projects_df.empty:
            fig_ov = px.timeline(
                projects_df,
                x_start="Start", x_end="End", y="Project",
                color="Progress",
                color_continuous_scale=[[0, '#1a365d'], [0.5, '#2b6cb0'], [1, '#63b3ed']],
                range_color=[0, 100],
                hover_data=["Owner", "Status"],
                text="Progress",
            )
            fig_ov.update_traces(
                texttemplate='%{text}%',
                textposition='inside',
                textfont=dict(size=11, color='white', family='Outfit'),
                marker_line_width=0,
                opacity=0.92,
                width=0.55,
            )
            fig_ov.update_xaxes(
                side="top", tickformat="%b %d", dtick="M1",
                showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                zeroline=False, tickfont=dict(size=11, color='#555970')
            )
            fig_ov.update_yaxes(
                autorange="reversed", title="",
                showgrid=False,
                tickfont=dict(size=12, color='#e8eaed', family='Outfit')
            )
            fig_ov.update_layout(
                **PLOTLY_LAYOUT,
                height=250 + len(projects_df) * 55,
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_ov, use_container_width=True)
        else:
            st.info("등록된 프로젝트가 없습니다.")

        st.write("")
        
        with st.expander("프로젝트 관리", expanded=False):
            col_add, col_del = st.columns(2)
            with col_add:
                st.markdown("**새 프로젝트**")
                with st.form("new_project_form"):
                    np_name = st.text_input("프로젝트명")
                    np_owner = st.text_input("PM")
                    c1, c2 = st.columns(2)
                    np_start = c1.date_input("시작일", datetime.date.today())
                    np_end = c2.date_input("종료일", datetime.date.today() + datetime.timedelta(days=30))
                    if st.form_submit_button("생성", type="primary"):
                        if np_name:
                            new_p = pd.DataFrame([{
                                "Project": np_name, "Owner": np_owner, "Status": "준비",
                                "Progress": 0, "Start": str(np_start), "End": str(np_end)
                            }])
                            updated = pd.concat([st.session_state.projects, new_p], ignore_index=True)
                            if save_data("projects", updated):
                                st.session_state.projects = updated
                                st.success(f"'{np_name}' 생성!")
                                safe_rerun()
                        else:
                            st.error("프로젝트명을 입력하세요.")
            with col_del:
                st.markdown("**프로젝트 삭제**")
                if not projects_df.empty:
                    del_target = st.selectbox("삭제 대상", projects_df['Project'].unique(), label_visibility="collapsed")
                    if st.button("삭제", type="secondary"):
                        updated = st.session_state.projects[st.session_state.projects['Project'] != del_target]
                        if save_data("projects", updated):
                            st.session_state.projects = updated
                            st.success("삭제 완료")
                            safe_rerun()

    # ── 프로젝트 상세 ──
    with tab_detail:
        p_list = projects_df['Project'].unique() if not projects_df.empty else []
        
        col_sel, col_info = st.columns([1, 2])
        with col_sel:
            selected_project = st.selectbox("프로젝트 선택", p_list, label_visibility="collapsed")
        
        if selected_project:
            p_info = projects_df[projects_df['Project'] == selected_project].iloc[0]
            with col_info:
                st.caption(f"**PM:** {p_info['Owner']}  ·  {p_info['Start'].strftime('%Y.%m.%d')} → {p_info['End'].strftime('%Y.%m.%d')}")

            p_tasks = tasks_df[tasks_df['Project'] == selected_project].sort_values(by=['Department', 'Start'])
            
            if not p_tasks.empty:
                p_tasks['Label'] = p_tasks.apply(lambda x: f"{x['Department']}  ·  {x['Task']}", axis=1)
                p_tasks = p_tasks.sort_values(by=['Department', 'Start'], ascending=[True, True])

                # 부서별 컬러 (세련된 톤)
                dept_colors = ['#63b3ed', '#4fd1c5', '#b794f4', '#f6c958', '#fc8181', '#68d391']

                fig_d = px.timeline(
                    p_tasks,
                    x_start="Start", x_end="End", y="Label",
                    color="Department",
                    color_discrete_sequence=dept_colors,
                    hover_data=["Task", "Progress"],
                    text="Progress",
                )
                fig_d.update_traces(
                    texttemplate='%{text}%',
                    textposition='auto',
                    textfont=dict(size=10, color='white', family='Outfit'),
                    marker_line_width=0,
                    width=0.55,
                    opacity=0.9,
                )
                fig_d.update_xaxes(
                    side="top", tickformat="%b %d", dtick="D7",
                    showgrid=True, gridcolor='rgba(255,255,255,0.04)',
                    zeroline=False, tickfont=dict(size=11, color='#555970')
                )
                fig_d.update_yaxes(
                    autorange="reversed", title="",
                    showgrid=True, gridcolor='rgba(255,255,255,0.03)',
                    tickfont=dict(size=11, color='#e8eaed', family='Outfit')
                )
                fig_d.update_layout(
                    **PLOTLY_LAYOUT,
                    height=max(350, len(p_tasks) * 55),
                    showlegend=True,
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.06, xanchor="left", x=0,
                        title=None, bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#8b8fa3', size=11, family='Outfit')
                    ),
                )
                
                # 마일스톤
                milestones = p_tasks[p_tasks['Milestone'] == 'Y']
                if not milestones.empty:
                    fig_d.add_scatter(
                        x=milestones['End'], y=milestones['Label'],
                        mode='markers',
                        marker=dict(symbol='diamond', size=10, color='#f6c958', line=dict(width=1, color='#08090d')),
                        name='마일스톤', showlegend=True,
                    )
                
                st.plotly_chart(fig_d, use_container_width=True)
            else:
                st.info("등록된 상세 일정이 없습니다.")

            st.write("")

            manage_tab1, manage_tab2 = st.tabs(["업무 추가", "수정/삭제"])
            
            with manage_tab1:
                with st.form("add_detail_task_form"):
                    col1, col2, col3 = st.columns([1, 2, 1])
                    t_dept = col1.text_input("부서")
                    t_name = col2.text_input("업무명")
                    t_prog = col3.slider("진행률", 0, 100, 0)
                    col4, col5, col6 = st.columns([1, 1, 1])
                    t_start = col4.date_input("시작일", datetime.date.today())
                    t_end = col5.date_input("종료일", datetime.date.today() + datetime.timedelta(days=5))
                    t_mile = col6.checkbox("마일스톤")
                    if st.form_submit_button("추가", type="primary"):
                        if t_name and t_dept:
                            new_task = pd.DataFrame([{
                                "Project": selected_project, "Task": t_name, "Department": t_dept,
                                "Start": str(t_start), "End": str(t_end),
                                "Progress": t_prog, "Milestone": "Y" if t_mile else "N"
                            }])
                            updated = pd.concat([st.session_state.project_tasks, new_task], ignore_index=True)
                            if save_data("project_tasks", updated):
                                st.session_state.project_tasks = updated
                                st.toast("추가 완료!", icon="✅")
                                safe_rerun()
                        else:
                            st.warning("부서와 업무명을 모두 입력하세요.")

            with manage_tab2:
                if not p_tasks.empty:
                    display_cols = ['Department', 'Task', 'Start', 'End', 'Progress', 'Milestone']
                    edit_source = p_tasks[display_cols].reset_index(drop=True)
                    edited_tasks = st.data_editor(
                        edit_source,
                        column_config={
                            "Department": st.column_config.TextColumn("부서", width="small"),
                            "Task": st.column_config.TextColumn("업무명", width="large"),
                            "Start": st.column_config.DateColumn("시작"),
                            "End": st.column_config.DateColumn("종료"),
                            "Progress": st.column_config.NumberColumn("%", width="small"),
                            "Milestone": st.column_config.CheckboxColumn("★", width="small"),
                        },
                        num_rows="dynamic", use_container_width=True,
                        key=f"editor_{selected_project}"
                    )
                    if st.button("저장", type="primary"):
                        other = tasks_df[tasks_df['Project'] != selected_project]
                        if not edited_tasks.empty:
                            edited_tasks['Project'] = selected_project
                            edited_tasks['Start'] = edited_tasks['Start'].astype(str)
                            edited_tasks['End'] = edited_tasks['End'].astype(str)
                            final = pd.concat([other, edited_tasks], ignore_index=True)
                        else:
                            final = other
                        if save_data("project_tasks", final):
                            st.session_state.project_tasks = final
                            st.toast("저장 완료!", icon="✅")
                            safe_rerun()
                else:
                    st.caption("수정할 데이터가 없습니다.")


# =========================================================
# PAGE 3: 주간 업무 (PPP)
# =========================================================
elif page == "📅 주간 업무 (PPP)":
    st.markdown("""
    <div class="page-header">
        <h1>Weekly Review</h1>
        <div class="page-subtitle">주간 업무 실적과 계획을 공유하세요</div>
    </div>
    """, unsafe_allow_html=True)

    col_date, col_info = st.columns([1, 2])
    with col_date:
        pick_date = st.date_input("기준 날짜", datetime.date.today())
    s_week, e_week = get_week_range(pick_date)
    week_str = str(s_week)
    with col_info:
        st.markdown(f"""
        <div style="background:var(--bg-card); border:1px solid var(--border-subtle); border-radius:var(--radius-sm);
                    padding:12px 20px; display:inline-block; margin-top:6px;">
            <span style="color:var(--accent-blue); font-weight:600;">{s_week}</span>
            <span style="color:var(--text-muted); margin:0 8px;">→</span>
            <span style="color:var(--accent-blue); font-weight:600;">{e_week}</span>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    tab_view, tab_write = st.tabs(["보고서 조회", "보고서 작성"])

    # ── 조회 ──
    with tab_view:
        report_df = load_data("weekly_reports", create_empty_report_df)
        if 'Week_Start' in report_df.columns:
            report_df['Week_Start'] = report_df['Week_Start'].astype(str)
        curr = report_df[report_df['Week_Start'] == week_str]

        if curr.empty:
            st.caption("제출된 보고서가 없습니다.")
        else:
            assignees = sorted(curr['Assignee'].unique())
            view_mode = st.radio("보기", ["카드", "테이블"], horizontal=True, label_visibility="collapsed")
            st.write("")
            
            if view_mode == "테이블":
                st.dataframe(curr, use_container_width=True, hide_index=True)
            else:
                cols = st.columns(2)
                for idx, person in enumerate(assignees):
                    p_df = curr[curr['Assignee'] == person]
                    color = get_avatar_color(person)
                    initial = person[0] if person else "?"
                    
                    with cols[idx % 2]:
                        # ── PPP 카드 렌더링 (HTML) ──
                        card_html = f"""
                        <div class="ppp-card">
                            <div class="ppp-header">
                                <div class="ppp-avatar" style="background:{color};">{initial}</div>
                                <div class="ppp-name">{person}</div>
                            </div>
                        """
                        
                        for type_val, icon, label in [
                            ("금주 실적", "✅", "PROGRESS"),
                            ("차주 계획", "📋", "PLAN"),
                            ("이슈사항", "⚠️", "ISSUES")
                        ]:
                            sub = p_df[p_df['Type'] == type_val]
                            if sub.empty and type_val == "이슈사항":
                                continue
                            card_html += f'<div class="ppp-section-title">{icon} {label}</div>'
                            if sub.empty:
                                card_html += '<div class="ppp-item" style="color:var(--text-muted);">—</div>'
                            else:
                                for _, r in sub.iterrows():
                                    status_dot = "🟢" if r.get('Status') == "정상" else "🟡" if r.get('Status') == "지연" else "🔴"
                                    tag = f'<span class="ppp-item-tag">[{r["Project"]}]</span> ' if r.get('Project', '-') != '-' else ''
                                    card_html += f'<div class="ppp-item">{status_dot} {tag}{r["Content"]}</div>'
                        
                        card_html += "</div>"
                        st.markdown(card_html, unsafe_allow_html=True)

    # ── 작성 ──
    with tab_write:
        managers = list(st.session_state.promotions['담당자'].unique()) if '담당자' in st.session_state.promotions.columns else []
        if "기타" not in managers:
            managers.append("기타")
        
        c_sel, _ = st.columns([1, 2])
        me = c_sel.selectbox("작성자", managers, key="writer_select")
        if me == "기타":
            me = c_sel.text_input("이름 입력")
        
        if me:
            full_data = load_data("weekly_reports", create_empty_report_df)
            if 'Week_Start' in full_data.columns:
                full_data['Week_Start'] = full_data['Week_Start'].astype(str)
            my_data = full_data[(full_data['Week_Start'] == week_str) & (full_data['Assignee'] == me)]
            
            if not my_data.empty:
                input_df = my_data.reset_index(drop=True)
            else:
                tmpl = [
                    {"Week_Start": week_str, "Assignee": me, "Type": "금주 실적", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "금주 실적", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "차주 계획", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "차주 계획", "Project": "-", "Content": "", "Status": "정상"},
                ]
                input_df = pd.DataFrame(tmpl)
            
            proj_ops = ["-"] + list(st.session_state.promotions['프로모션명'].unique())
            
            edited_df = st.data_editor(
                input_df,
                column_config={
                    "Week_Start": None, "Assignee": None,
                    "Type": st.column_config.SelectboxColumn("구분", options=["금주 실적", "차주 계획", "이슈사항"], required=True),
                    "Project": st.column_config.SelectboxColumn("프로모션", options=proj_ops, required=True),
                    "Content": st.column_config.TextColumn("내용", required=True, width="large"),
                    "Status": st.column_config.SelectboxColumn("상태", options=["정상", "지연", "중단"], required=True)
                },
                num_rows="dynamic", use_container_width=True
            )
            
            if st.button("저장", type="primary"):
                new_entry = edited_df[edited_df['Content'].str.strip() != ""].copy()
                if not new_entry.empty:
                    new_entry['Week_Start'] = week_str
                    new_entry['Assignee'] = me
                    new_entry['Project'] = new_entry['Project'].fillna("-")
                    new_entry['Status'] = new_entry['Status'].fillna("정상")
                    mask = ~((full_data['Week_Start'] == week_str) & (full_data['Assignee'] == me))
                    final_df = pd.concat([full_data[mask], new_entry], ignore_index=True)
                    if save_data("weekly_reports", final_df):
                        st.toast("저장 완료!", icon="✅")
                        safe_rerun()
                else:
                    st.warning("내용을 입력해주세요.")
        else:
            st.caption("작성자를 먼저 선택해주세요.")


# =========================================================
# PAGE 4: 관리자
# =========================================================
elif page == "⚙️ 관리자 페이지":
    if not st.session_state.get('is_admin_unlocked', False):
        st.markdown("""
        <div class="page-header">
            <h1>관리자 인증</h1>
            <div class="page-subtitle">관리자 암호를 입력해주세요</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("admin_login"):
            p = st.text_input("암호", type="password", label_visibility="collapsed", placeholder="암호 입력")
            if st.form_submit_button("인증", type="primary"):
                if p == "diageorcg":
                    st.session_state.is_admin_unlocked = True
                    st.session_state.draft_df = st.session_state.promotions.copy()
                    safe_rerun()
                else:
                    st.error("인증 실패")
    else:
        st.markdown("""
        <div class="page-header">
            <h1>데이터 관리</h1>
            <div class="page-subtitle">프로모션 데이터를 직접 편집하고 관리합니다</div>
        </div>
        """, unsafe_allow_html=True)

        if 'draft_df' not in st.session_state:
            st.session_state.draft_df = st.session_state.promotions.copy()

        _, c2 = st.columns([3, 1])
        if c2.button("변경사항 저장", type="primary", use_container_width=True):
            with st.spinner("저장 중..."):
                if save_data("promotions", st.session_state.draft_df):
                    st.session_state.promotions = st.session_state.draft_df.copy()
                    st.toast("저장 완료!", icon="✅")

        edited = st.data_editor(st.session_state.draft_df, num_rows="dynamic", use_container_width=True)
        if not edited.equals(st.session_state.draft_df):
            st.session_state.draft_df = edited

        st.write("")

        with st.expander("CSV 관리"):
            col1, col2 = st.columns(2)
            with col1:
                csv = st.session_state.draft_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("CSV 다운로드", csv, "promo_data.csv", "text/csv", use_container_width=True)
            with col2:
                uploaded = st.file_uploader("CSV 업로드", type=["csv"], label_visibility="collapsed")
                if uploaded and st.button("적용"):
                    try:
                        st.session_state.draft_df = pd.read_csv(uploaded)
                        st.success("CSV 로드 완료. 상단 저장 버튼으로 확정하세요.")
                        safe_rerun()
                    except Exception as e:
                        st.error(f"오류: {e}")
