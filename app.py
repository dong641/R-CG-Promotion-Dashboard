import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import os

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="2025 프로모션 대시보드",
    page_icon="📊",
    layout="wide"
)

# 데이터 파일 경로 (같은 폴더에 저장됨)
DATA_FILE = "promotion_data.csv"

# --- 2. 초기 데이터 및 로드 함수 ---
def init_data():
    """CSV 파일이 없으면 초기 샘플 데이터를 생성합니다."""
    if not os.path.exists(DATA_FILE):
        data = [
            {"No": 1, "프로모션명": "2025 설날 선물세트 기획", "카테고리": "온트레이드", "담당자": "김철수", "시작일": "2025-01-01", "종료일": "2025-02-15", "진척률": 80, "상태": "진행중"},
            {"No": 2, "신제품 팝업스토어 운영", "카테고리": "오프라인", "담당자": "이영희", "시작일": "2025-02-01", "종료일": "2025-02-28", "진척률": 30, "상태": "지연"},
            {"No": 3, "인플루언서 바이럴 캠페인", "카테고리": "디지털", "담당자": "박지민", "시작일": "2025-01-15", "종료일": "2025-03-31", "진척률": 50, "상태": "진행중"},
            {"No": 4, "VIP 초청 시음회", "카테고리": "행사", "담당자": "최민수", "시작일": "2025-03-01", "종료일": "2025-03-05", "진척률": 10, "상태": "예정"},
        ]
        df = pd.DataFrame(data)
        df.to_csv(DATA_FILE, index=False)

def load_data():
    """CSV 데이터를 불러옵니다."""
    init_data() # 파일 없으면 생성
    return pd.read_csv(DATA_FILE)

def save_data(df):
    """데이터를 CSV로 저장합니다."""
    df.to_csv(DATA_FILE, index=False)

# --- 3. 사이드바 (데이터 입력) ---
st.sidebar.title("📝 관리자 메뉴")
st.sidebar.info("새로운 프로젝트를 등록하거나 기존 데이터를 관리하세요.")

with st.sidebar.form("input_form", clear_on_submit=True):
    st.subheader("신규 프로젝트 등록")
    name = st.text_input("프로모션명")
    
    c1, c2 = st.columns(2)
    category = c1.selectbox("카테고리", ["온트레이드", "오프라인", "디지털", "행사", "가정용", "GWP"])
    manager = c2.text_input("담당자")
    
    c3, c4 = st.columns(2)
    start_date = c3.date_input("시작일", date(2025, 1, 1))
    end_date = c4.date_input("종료일", date(2025, 1, 31))
    
    progress = st.slider("진척률 (%)", 0, 100, 0)
    status = st.selectbox("상태", ["예정", "진행중", "지연", "완료"])
    
    submitted = st.form_submit_button("등록 저장")

# --- 4. 메인 화면 로직 ---
# 데이터 로드
df = load_data()

# 폼 제출 처리
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
    st.success("✅ 프로젝트가 등록되었습니다!")
    st.rerun()

# 타이틀
st.title("🚀 2025 프로모션 현황 대시보드")
st.markdown(f"**기준일:** {date.today().strftime('%Y-%m-%d')} | **전체 프로젝트:** {len(df)}건")
st.markdown("---")

# [섹션 1] 핵심 지표 (KPI)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("총 프로젝트", f"{len(df)}건")
avg_prog = int(df['진척률'].mean()) if not df.empty else 0
kpi2.metric("평균 진척률", f"{avg_prog}%")
kpi3.metric("진행중", f"{len(df[df['상태']=='진행중'])}건", delta="Active")
kpi4.metric("지연됨", f"{len(df[df['상태']=='지연'])}건", delta="-Warning", delta_color="inverse")

# [섹션 2] 간트 차트 (시각화)
st.subheader("📅 프로젝트 일정 (Gantt Chart)")
if not df.empty:
    df['시작일'] = pd.to_datetime(df['시작일'])
    df['종료일'] = pd.to_datetime(df['종료일'])
    
    fig = px.timeline(
        df, x_start="시작일", x_end="종료일", y="프로모션명", color="상태",
        title="",
        color_discrete_map={"완료": "#2ECC71", "진행중": "#3498DB", "지연": "#E74C3C", "예정": "#95A5A6"},
        hover_data=["담당자", "진척률"]
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

# [섹션 3] 데이터 편집 테이블
st.subheader("📋 상세 현황 (직접 수정 가능)")
st.caption("💡 팁: 표의 내용을 더블 클릭하면 바로 수정됩니다. 수정 후 엔터를 치면 자동 저장됩니다.")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "진척률": st.column_config.ProgressColumn("진척률", format="%d%%", min_value=0, max_value=100),
        "상태": st.column_config.SelectboxColumn("상태", options=["예정", "진행중", "지연", "완료"]),
        "시작일": st.column_config.DateColumn("시작일", format="YYYY-MM-DD"),
        "종료일": st.column_config.DateColumn("종료일", format="YYYY-MM-DD"),
    },
    hide_index=True,
)

# 수정 사항 감지 및 저장
if not df.equals(edited_df):
    # 날짜 컬럼을 다시 문자열로 변환하여 저장 (CSV 호환성)
    edited_df['시작일'] = pd.to_datetime(edited_df['시작일']).dt.date
    edited_df['종료일'] = pd.to_datetime(edited_df['종료일']).dt.date
    save_data(edited_df)
    st.toast("변경 사항이 저장되었습니다!", icon="💾")
