import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import os

# --- 1. 페이지 설정 (가장 먼저 실행되어야 함) ---
st.set_page_config(
    page_title="2025 프로모션 대시보드",
    page_icon="📊",
    layout="wide"
)

# 데이터 파일 경로 설정
DATA_FILE = "promotion_data.csv"

# --- 2. 데이터 관리 함수 ---
def init_data():
    """CSV 파일이 없을 경우, 초기 샘플 데이터를 생성합니다."""
    if not os.path.exists(DATA_FILE):
        data = [
            {"No": 1, "프로모션명": "2025 설날 선물세트 기획", "카테고리": "온트레이드", "담당자": "김철수", "시작일": "2025-01-01", "종료일": "2025-02-15", "진척률": 80, "상태": "진행중"},
            {"No": 2, "신제품 팝업스토어 운영", "카테고리": "오프라인", "담당자": "이영희", "시작일": "2025-02-01", "종료일": "2025-02-28", "진척률": 30, "상태": "지연"},
            {"No": 3, "인플루언서 바이럴 캠페인", "카테고리": "디지털", "담당자": "박지민", "시작일": "2025-01-15", "종료일": "2025-03-31", "진척률": 50, "상태": "진행중"},
            {"No": 4, "VIP 초청 시음회", "카테고리": "행사", "담당자": "최민수", "시작일": "2025-03-01", "종료일": "2025-03-05", "진척률": 10, "상태": "예정"},
        ]
        df = pd.DataFrame(data)
        # 엑셀 호환성을 위해 utf-8-sig 인코딩 사용
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def load_data():
    """CSV 데이터를 불러옵니다."""
    init_data() # 파일이 없으면 생성
    
    # 데이터 읽기
    df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
    
    # [수정됨] 진척률 데이터 안전 처리 로직 추가
    # CSV에 '80%' 같은 문자열이나 빈 값이 섞여있을 경우 숫자로 강제 변환하여 TypeError 방지
    if '진척률' in df.columns:
        # 1. 데이터 타입이 문자열(object)인 경우에만 % 기호 제거 등의 정제 작업 수행
        if df['진척률'].dtype == 'object':
            df['진척률'] = df['진척률'].astype(str).str.replace('%', '').str.strip()
            
        # 2. 숫자로 변환 (변환 불가능한 값은 NaN -> 0으로 처리) 후 정수형(int)으로 변경
        df['진척률'] = pd.to_numeric(df['진척률'], errors='coerce').fillna(0).astype(int)
        
    return df

def save_data(df):
    """데이터프레임을 CSV 파일로 저장합니다."""
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- 3. 사이드바 UI (데이터 추가) ---
st.sidebar.title("📝 프로젝트 등록")
st.sidebar.info("새로운 프로모션을 등록하거나 관리합니다.")

with st.sidebar.form("input_form", clear_on_submit=True):
    st.subheader("신규 입력")
    name = st.text_input("프로모션명")
    
    col1, col2 = st.columns(2)
    category = col1.selectbox("카테고리", ["온트레이드", "오프라인", "디지털", "행사", "가정용", "GWP"])
    manager = col2.text_input("담당자")
    
    col3, col4 = st.columns(2)
    # 기본값을 2025년 1월 1일로 설정
    start_date = col3.date_input("시작일", date(2025, 1, 1))
    end_date = col4.date_input("종료일", date(2025, 1, 31))
    
    progress = st.slider("진척률 (%)", 0, 100, 0)
    status = st.selectbox("상태", ["예정", "진행중", "지연", "완료"])
    
    submitted = st.form_submit_button("등록 저장")

# --- 4. 메인 로직 처리 ---
# 데이터 로드
df = load_data()

# 신규 데이터 등록 로직
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
    st.rerun() # 데이터 갱신을 위해 페이지 새로고침

# --- 5. 메인 대시보드 화면 구성 ---
st.title("🚀 2025 프로모션 현황 대시보드")
st.markdown(f"**기준일:** {date.today().strftime('%Y-%m-%d')} | **전체 프로젝트:** {len(df)}건")
st.divider()

# [섹션 1] 핵심 지표 (KPI Cards)
k1, k2, k3, k4 = st.columns(4)
k1.metric("총 프로젝트", f"{len(df)}건")

# 평균 진척률 계산 (데이터가 없을 때 오류 방지)
avg_p = int(df['진척률'].mean()) if not df.empty else 0
k2.metric("평균 진척률", f"{avg_p}%")

# 상태별 건수 계산
count_active = len(df[df['상태'] == '진행중'])
count_delayed = len(df[df['상태'] == '지연'])

k3.metric("진행중", f"{count_active}건", delta="Active")
k4.metric("지연됨", f"{count_delayed}건", delta="-Warning", delta_color="inverse")

# [섹션 2] 간트 차트 (Gantt Chart)
st.subheader("📅 프로젝트 일정 타임라인")

if not df.empty:
    # 차트 생성을 위해 날짜 형식 변환
    chart_df = df.copy()
    chart_df['시작일'] = pd.to_datetime(chart_df['시작일'])
    chart_df['종료일'] = pd.to_datetime(chart_df['종료일'])
    
    fig = px.timeline(
        chart_df, 
        x_start="시작일", 
        x_end="종료일", 
        y="프로모션명", 
        color="상태",
        title="",
        # 상태별 색상 지정
        color_discrete_map={
            "완료": "#2ECC71",  # 녹색
            "진행중": "#3498DB", # 파란색
            "지연": "#E74C3C",   # 빨간색
            "예정": "#95A5A6"    # 회색
        },
        hover_data=["담당자", "진척률"]
    )
    # Y축 순서 반전 (위에서부터 1번이 나오도록) 및 높이 자동 조절
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=400)
    
    st.plotly_chart(fig, use_container_width=True)

# [섹션 3] 데이터 편집 테이블 (Data Editor)
st.subheader("📋 상세 현황 (수정 가능)")
st.caption("💡 표의 내용을 더블 클릭하여 수정하면 자동 저장됩니다. (행 삭제는 왼쪽 체크박스 선택 후 Del 키)")

edited_df = st.data_editor(
    df,
    num_rows="dynamic", # 행 추가/삭제 허용
    use_container_width=True,
    column_config={
        "진척률": st.column_config.ProgressColumn(
            "진척률", format="%d%%", min_value=0, max_value=100
        ),
        "상태": st.column_config.SelectboxColumn(
            "상태", options=["예정", "진행중", "지연", "완료"], required=True
        ),
        "시작일": st.column_config.DateColumn("시작일", format="YYYY-MM-DD"),
        "종료일": st.column_config.DateColumn("종료일", format="YYYY-MM-DD"),
    },
    hide_index=True,
)

# 데이터 변경 감지 시 저장
if not df.equals(edited_df):
    # 날짜 데이터 포맷을 문자열/Date 객체로 정리하여 저장
    edited_df['시작일'] = pd.to_datetime(edited_df['시작일']).dt.date
    edited_df['종료일'] = pd.to_datetime(edited_df['종료일']).dt.date
    save_data(edited_df)
    st.toast("변경 사항이 저장되었습니다!", icon="💾")
