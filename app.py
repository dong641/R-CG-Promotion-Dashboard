import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="2025 프로모션 대시보드",
    page_icon="📊",
    layout="wide"
)

# 데이터 파일 경로
DATA_FILE = "promotion_data.csv"

# --- 2. 데이터 관리 함수 ---
def init_data():
    """데이터 파일이 없을 경우 초기 샘플 데이터를 생성합니다."""
    if not os.path.exists(DATA_FILE):
        data = [
            {"No": 1, "프로모션명": "2025 설날 선물세트 기획", "카테고리": "온트레이드", "담당자": "김철수", "시작일": "2025-01-01", "종료일": "2025-02-15", "진척률": 80, "상태": "진행중"},
            {"No": 2, "프로모션명": "신제품 팝업스토어 운영", "카테고리": "오프라인", "담당자": "이영희", "시작일": "2025-02-01", "종료일": "2025-02-28", "진척률": 30, "상태": "지연"},
            {"No": 3, "프로모션명": "인플루언서 바이럴 캠페인", "카테고리": "디지털", "담당자": "박지민", "시작일": "2025-01-15", "종료일": "2025-03-31", "진척률": 50, "상태": "진행중"},
            {"No": 4, "프로모션명": "VIP 초청 시음회", "카테고리": "행사", "담당자": "최민수", "시작일": "2025-03-01", "종료일": "2025-03-05", "진척률": 10, "상태": "예정"},
        ]
        df = pd.DataFrame(data)
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def load_data():
    """CSV 데이터를 불러오고 전처리합니다."""
    init_data()
    # 날짜 컬럼을 문자로 읽어오도록 지정하여 추후 변환 충돌 방지
    df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
    
    # [안전장치] 진척률 데이터 정제 (문자열 -> 숫자)
    if '진척률' in df.columns:
        if df['진척률'].dtype == 'object':
            df['진척률'] = df['진척률'].astype(str).str.replace('%', '').str.strip()
        df['진척률'] = pd.to_numeric(df['진척률'], errors='coerce').fillna(0).astype(int)
    
    return df

def save_data(df):
    """데이터를 CSV로 저장합니다."""
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- 3. 사이드바 (입력 폼) ---
st.sidebar.title("📝 프로젝트 등록")
st.sidebar.info("새로운 프로모션을 등록하거나 관리합니다.")

with st.sidebar.form("input_form", clear_on_submit=True):
    st.subheader("신규 입력")
    name = st.text_input("프로모션명")
    
    col1, col2 = st.columns(2)
    category = col1.selectbox("카테고리", ["온트레이드", "오프라인", "디지털", "행사", "가정용", "GWP"])
    manager = col2.text_input("담당자")
    
    col3, col4 = st.columns(2)
    start_date = col3.date_input("시작일", date(2025, 1, 1))
    end_date = col4.date_input("종료일", date(2025, 1, 31))
    
    progress = st.slider("진척률 (%)", 0, 100, 0)
    status = st.selectbox("상태", ["예정", "진행중", "지연", "완료"])
    
    submitted = st.form_submit_button("등록 저장")

# --- 4. 메인 로직 ---
df = load_data()

# 신규 데이터 추가
if submitted and name:
    new_no = df['No'].max() + 1 if not df.empty else 1
    new_row = pd.DataFrame([{
        "No": new_no, 
        "프로모션명": name, 
        "카테고리": category, 
        "담당자": manager,
        "시작일": start_date, 
        "종료일": end_date, 
        "진척률": progress, 
        "상태": status
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    st.success(f"✅ '{name}' 프로젝트가 등록되었습니다!")
    st.rerun()

# --- 5. 대시보드 화면 구성 ---
st.title("🚀 2025 프로모션 현황 대시보드")
st.markdown(f"**기준일:** {date.today()} | **전체 프로젝트:** {len(df)}건")
st.divider()

# [KPI 지표]
k1, k2, k3, k4 = st.columns(4)
k1.metric("총 프로젝트", f"{len(df)}건")

avg_p = int(df['진척률'].mean()) if not df.empty else 0
k2.metric("평균 진척률", f"{avg_p}%")

count_active = len(df[df['상태'] == '진행중'])
count_delayed = len(df[df['상태'] == '지연'])
k3.metric("진행중", f"{count_active}건", delta="Active")
k4.metric("지연됨", f"{count_delayed}건", delta="-Warning", delta_color="inverse")

# [간트 차트]
st.subheader("📅 프로젝트 일정 타임라인")
if not df.empty:
    chart_df = df.copy()
    # 차트용 날짜 변환 (오류 방지)
    chart_df['시작일'] = pd.to_datetime(chart_df['시작일'], errors='coerce')
    chart_df['종료일'] = pd.to_datetime(chart_df['종료일'], errors='coerce')
    
    # 유효한 날짜가 있는 데이터만 필터링
    chart_df = chart_df.dropna(subset=['시작일', '종료일'])
    
    if not chart_df.empty:
        fig = px.timeline(
            chart_df, 
            x_start="시작일", x_end="종료일", y="프로모션명", color="상태",
            color_discrete_map={"완료": "#2ECC71", "진행중": "#3498DB", "지연": "#E74C3C", "예정": "#95A5A6"},
            hover_data=["담당자", "진척률"]
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=max(400, len(chart_df) * 40)) # 데이터 양에 따라 높이 자동 조절
        st.plotly_chart(fig, use_container_width=True)

# [데이터 에디터]
st.subheader("📋 상세 현황 (수정 가능)")
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "진척률": st.column_config.ProgressColumn("진척률", format="%d%%", min_value=0, max_value=100),
        "상태": st.column_config.SelectboxColumn("상태", options=["예정", "진행중", "지연", "완료"], required=True),
        "시작일": st.column_config.DateColumn("시작일", format="YYYY-MM-DD"),
        "종료일": st.column_config.DateColumn("종료일", format="YYYY-MM-DD"),
    },
    hide_index=True,
)

# 데이터 변경 저장 로직
if not df.equals(edited_df):
    # 날짜 형식 표준화 (CSV 저장 시 문자열 충돌 방지)
    try:
        edited_df['시작일'] = pd.to_datetime(edited_df['시작일']).dt.date
        edited_df['종료일'] = pd.to_datetime(edited_df['종료일']).dt.date
        save_data(edited_df)
        st.toast("변경 사항이 저장되었습니다!", icon="💾")
    except Exception as e:
        st.error(f"저장 중 오류가 발생했습니다: {e}")
