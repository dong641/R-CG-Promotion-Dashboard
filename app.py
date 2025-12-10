import streamlit as st
import pandas as pd
import datetime

# ---------------------------------------------------------
# 호환성 함수 (Streamlit 구버전/신버전 모두 작동하도록 설정)
# ---------------------------------------------------------
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# ---------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="프로모션 통합 시스템",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------------
# 초기 데이터 설정 (Session State)
# ---------------------------------------------------------
if 'promotions' not in st.session_state:
    st.session_state.promotions = pd.DataFrame([
        {"프로모션명": "2024 봄 정기 세일", "담당자": "김철수", "상태": "진행중", "진척율": 75, "시작일": datetime.date(2024, 3, 1), "종료일": datetime.date(2024, 3, 15)},
        {"프로모션명": "신규 회원 가입 이벤트", "담당자": "이영희", "상태": "기획단계", "진척율": 20, "시작일": datetime.date(2024, 4, 1), "종료일": datetime.date(2024, 4, 30)},
        {"프로모션명": "여름 바캉스 특가", "담당자": "박민수", "상태": "대기", "진척율": 0, "시작일": datetime.date(2024, 6, 1), "종료일": datetime.date(2024, 8, 31)},
        {"프로모션명": "설날 효도 선물전", "담당자": "정수진", "상태": "완료", "진척율": 100, "시작일": datetime.date(2024, 1, 15), "종료일": datetime.date(2024, 2, 9)},
    ])

# 관리자 로그인 상태 초기화
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# 데이터 로드
df = st.session_state.promotions

# ---------------------------------------------------------
# 사이드바: 페이지 네비게이션
# ---------------------------------------------------------
with st.sidebar:
    st.title("메뉴")
    page = st.radio("이동할 페이지를 선택하세요", ["📊 대시보드", "⚙️ 관리자 페이지"])
    
    st.divider()
    
    # 관리자 페이지일 때만 로그아웃 버튼 표시
    if page == "⚙️ 관리자 페이지" and st.session_state.admin_logged_in:
        if st.button("로그아웃"):
            st.session_state.admin_logged_in = False
            safe_rerun() # 호환성 함수 사용
    
    st.info("💡 대시보드는 현황 조회용이며, 데이터 수정은 관리자 페이지에서 가능합니다.")

# ---------------------------------------------------------
# 페이지 1: 대시보드 (보기 전용)
# ---------------------------------------------------------
if page == "📊 대시보드":
    st.title("📊 프로모션 현황 대시보드")
    st.markdown("현재 진행 중인 프로모션의 핵심 지표를 확인합니다.")

    st.divider()

    # 1. 핵심 지표 (Metrics)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 프로모션", f"{len(df)}건")
    col2.metric("진행중", f"{len(df[df['상태'] == '진행중'])}건")
    col3.metric("완료", f"{len(df[df['상태'] == '완료'])}건")
    col4.metric("평균 진척율", f"{df['진척율'].mean():.1f}%")

    st.divider()
    
    # 2. 조회용 테이블 (수정 불가)
    st.subheader("📋 전체 목록 조회")
    st.dataframe(
        df,
        column_config={
            "진척율": st.column_config.ProgressColumn(
                "진척율", format="%d%%", min_value=0, max_value=100
            ),
        },
        use_container_width=True,
        hide_index=True
    )

# ---------------------------------------------------------
# 페이지 2: 관리자 페이지 (비밀번호 보호)
# ---------------------------------------------------------
elif page == "⚙️ 관리자 페이지":
    st.title("⚙️ 프로모션 데이터 관리")
    
    # 로그인 되지 않은 경우 -> 비밀번호 입력창 표시
    if not st.session_state.admin_logged_in:
        st.markdown("관리자 권한이 필요합니다. 비밀번호를 입력하세요.")
        
        # 비밀번호 입력 폼
        with st.form("login_form"):
            password = st.text_input("비밀번호", type="password")
            submit_login = st.form_submit_button("로그인")
            
            if submit_login:
                if password == "diageorcg":
                    st.session_state.admin_logged_in = True
                    st.success("로그인 성공!")
                    safe_rerun() # 호환성 함수 사용
                else:
                    st.error("비밀번호가 올바르지 않습니다.")
                    
    # 로그인 된 경우 -> 관리자 기능 표시
    else:
        st.markdown("프로모션 데이터를 **추가**하거나 **수정**할 수 있는 관리자 전용 페이지입니다.")

        st.divider()

        # 1. 새 프로모션 등록 (Expander로 깔끔하게 처리)
        with st.expander("➕ 새 프로모션 등록하기", expanded=False):
            with st.form("add_promo_form"):
                col_a, col_b = st.columns(2)
                new_name = col_a.text_input("프로모션명")
                new_manager = col_b.text_input("담당자")
                
                new_status = st.selectbox("상태", ["기획단계", "대기", "진행중", "완료", "보류"])
                new_progress = st.slider("초기 진척율 (%)", 0, 100, 0)
                
                col_c, col_d = st.columns(2)
                new_start = col_c.date_input("시작일", datetime.date.today())
                new_end = col_d.date_input("종료일", datetime.date.today() + datetime.timedelta(days=7))
                
                submitted = st.form_submit_button("등록하기")
                
                if submitted:
                    if new_name and new_manager:
                        new_data = pd.DataFrame([{
                            "프로모션명": new_name,
                            "담당자": new_manager,
                            "상태": new_status,
                            "진척율": new_progress,
                            "시작일": new_start,
                            "종료일": new_end
                        }])
                        st.session_state.promotions = pd.concat([st.session_state.promotions, new_data], ignore_index=True)
                        st.success(f"'{new_name}' 등록이 완료되었습니다.")
                        safe_rerun() # 호환성 함수 사용
                    else:
                        st.error("프로모션명과 담당자는 필수 입력입니다.")

        st.divider()

        # 2. 데이터 수정 에디터
        st.subheader("✏️ 데이터 수정 및 삭제")
        st.caption("아래 표에서 내용을 직접 수정하거나 행을 선택해 관리하세요.")

        # 데이터 에디터 설정
        edited_df = st.data_editor(
            df,
            column_config={
                # 진척율을 숫자로 직접 입력할 수 있도록 NumberColumn으로 변경
                "진척율": st.column_config.NumberColumn(
                    "진척율",
                    help="진척율을 숫자로 입력하세요 (0~100)",
                    min_value=0,
                    max_value=100,
                    step=1,
                    format="%d%%"
                ),
                "상태": st.column_config.SelectboxColumn(
                    "상태",
                    options=["기획단계", "대기", "진행중", "완료", "보류"],
                    required=True,
                ),
                "시작일": st.column_config.DateColumn("시작일", format="YYYY-MM-DD"),
                "종료일": st.column_config.DateColumn("종료일", format="YYYY-MM-DD"),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic", # 행 추가/삭제 허용
            key="editor"
        )