import streamlit as st
import pandas as pd
import datetime

# ---------------------------------------------------------
# 호환성 함수 (Streamlit 구버전/신버전 모두 작동)
# ---------------------------------------------------------
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# ---------------------------------------------------------
# 페이지 설정 (가장 먼저 실행)
# ---------------------------------------------------------
st.set_page_config(
    page_title="프로모션 통합 시스템",
    page_icon="🔒",
    layout="wide"
)

# ---------------------------------------------------------
# [1단계] 글로벌 로그인 (입구 컷) - 비밀번호: DK2026
# ---------------------------------------------------------
if 'is_global_unlocked' not in st.session_state:
    st.session_state.is_global_unlocked = False

if not st.session_state.is_global_unlocked:
    st.title("🔒 프로모션 시스템 접근")
    st.markdown("### 접속을 위해 보안 코드를 입력하세요.")
    
    global_password = st.text_input("접속 암호", type="password", key="global_pw")
    
    if st.button("시스템 접속"):
        if global_password == "DK2026":
            st.session_state.is_global_unlocked = True
            st.toast("접속 승인되었습니다.", icon="🔓")
            safe_rerun()
        else:
            st.error("잘못된 암호입니다.")
    st.stop()


# =========================================================
# [메인 앱]
# =========================================================

# 초기 데이터 설정 (채널 컬럼 추가)
if 'promotions' not in st.session_state:
    st.session_state.promotions = pd.DataFrame([
        {"프로모션명": "2024 봄 정기 세일", "채널": "Off Trade", "담당자": "김철수", "상태": "진행중", "진척율": 75, "시작일": datetime.date(2024, 3, 1), "종료일": datetime.date(2024, 3, 15)},
        {"프로모션명": "신규 회원 가입 이벤트", "채널": "On Trade", "담당자": "이영희", "상태": "기획단계", "진척율": 20, "시작일": datetime.date(2024, 4, 1), "종료일": datetime.date(2024, 4, 30)},
        {"프로모션명": "여름 바캉스 특가", "채널": "Off Trade", "담당자": "박민수", "상태": "대기", "진척율": 0, "시작일": datetime.date(2024, 6, 1), "종료일": datetime.date(2024, 8, 31)},
        {"프로모션명": "설날 효도 선물전", "채널": "On Trade", "담당자": "정수진", "상태": "완료", "진척율": 100, "시작일": datetime.date(2024, 1, 15), "종료일": datetime.date(2024, 2, 9)},
    ])

# 관리자 로그인 상태 초기화
if 'is_admin_unlocked' not in st.session_state:
    st.session_state.is_admin_unlocked = False

df = st.session_state.promotions

# 사이드바 설정
with st.sidebar:
    st.title("메뉴")
    page = st.radio("이동할 페이지를 선택하세요", ["📊 대시보드", "⚙️ 관리자 페이지"])
    
    st.divider()
    if st.button("🚪 시스템 종료 (로그아웃)"):
        st.session_state.is_global_unlocked = False
        st.session_state.is_admin_unlocked = False
        safe_rerun()

# ---------------------------------------------------------
# 페이지 1: 대시보드
# ---------------------------------------------------------
if page == "📊 대시보드":
    st.title("📊 프로모션 현황 대시보드")
    
    # [기능 추가] 채널 필터링
    col_filter1, col_filter2 = st.columns([1, 3])
    with col_filter1:
        st.markdown("### 🔍 채널 필터")
        channel_filter = st.radio(
            "보고 싶은 채널을 선택하세요:",
            ["전체", "On Trade", "Off Trade"],
            horizontal=True,
            label_visibility="collapsed"
        )

    # 데이터 필터링 로직
    if channel_filter == "전체":
        display_df = df
    else:
        # 채널 컬럼이 없을 경우를 대비해 예외처리
        if "채널" in df.columns:
            display_df = df[df['채널'] == channel_filter]
        else:
            display_df = df

    st.divider()

    # 1. 핵심 지표 (필터링된 데이터 기준)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 프로모션", f"{len(display_df)}건")
    col2.metric("진행중", f"{len(display_df[display_df['상태'] == '진행중'])}건")
    col3.metric("완료", f"{len(display_df[display_df['상태'] == '완료'])}건")
    
    avg_progress = display_df['진척율'].mean() if not display_df.empty else 0
    col4.metric("평균 진척율", f"{avg_progress:.1f}%")

    st.divider()
    
    # 2. 분류별 목록 조회
    st.subheader(f"📋 {channel_filter} 프로모션 목록")

    df_active = display_df[display_df['상태'] != '완료']
    df_completed = display_df[display_df['상태'] == '완료']

    tab1, tab2 = st.tabs([f"🔥 진행 중 ({len(df_active)})", f"✅ 완료됨 ({len(df_completed)})"])

    # 공통 설정
    common_config = {
        "진척율": st.column_config.ProgressColumn("진척율", format="%d%%", min_value=0, max_value=100),
        "상태": st.column_config.TextColumn("상태"),
    }
    # 채널 컬럼이 있다면 색상을 입혀서 보여줌
    if "채널" in df.columns:
        common_config["채널"] = st.column_config.TextColumn("채널", help="판매 채널 구분")

    with tab1:
        st.dataframe(df_active, column_config=common_config, use_container_width=True, hide_index=True)

    with tab2:
        st.dataframe(df_completed, column_config=common_config, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 페이지 2: 관리자 페이지 (비밀번호: diageorcg)
# ---------------------------------------------------------
elif page == "⚙️ 관리자 페이지":
    st.title("⚙️ 프로모션 데이터 관리")
    
    if not st.session_state.is_admin_unlocked:
        st.warning("⚠️ 관리자 권한이 필요합니다.")
        with st.form("admin_login_form"):
            admin_pw = st.text_input("관리자 암호", type="password")
            if st.form_submit_button("관리자 로그인"):
                if admin_pw == "diageorcg":
                    st.session_state.is_admin_unlocked = True
                    safe_rerun()
                else:
                    st.error("암호 오류")
    else:
        if st.button("🔒 관리자 모드 종료"):
            st.session_state.is_admin_unlocked = False
            safe_rerun()
            
        st.divider()

        # [기능 추가] 컬럼 관리 섹션
        with st.expander("🛠️ 데이터 컬럼(열) 추가하기", expanded=False):
            st.info("새로운 데이터 항목(예: 예산, 지역)이 필요하면 여기서 추가하세요.")
            col_add1, col_add2 = st.columns([3, 1])
            new_col_name = col_add1.text_input("추가할 컬럼 이름")
            if col_add2.button("컬럼 추가", use_container_width=True):
                if new_col_name and new_col_name not in st.session_state.promotions.columns:
                    st.session_state.promotions[new_col_name] = "-"  # 기본값 설정
                    st.success(f"'{new_col_name}' 컬럼이 추가되었습니다.")
                    safe_rerun()
                elif new_col_name in st.session_state.promotions.columns:
                    st.error("이미 존재하는 컬럼입니다.")
                else:
                    st.error("컬럼 이름을 입력하세요.")

        st.divider()

        # 1. 새 프로모션 등록
        with st.expander("➕ 새 프로모션 등록하기", expanded=False):
            with st.form("add_promo_form"):
                st.markdown("**기본 정보**")
                col_a, col_b = st.columns(2)
                new_name = col_a.text_input("프로모션명")
                # 채널 선택 추가
                new_channel = col_b.selectbox("채널 구분", ["On Trade", "Off Trade", "기타"])
                
                col_c, col_d = st.columns(2)
                new_manager = col_c.text_input("담당자")
                new_status = col_d.selectbox("상태", ["기획단계", "대기", "진행중", "완료", "보류"])
                
                new_progress = st.slider("초기 진척율 (%)", 0, 100, 0)
                col_e, col_f = st.columns(2)
                new_start = col_e.date_input("시작일", datetime.date.today())
                new_end = col_f.date_input("종료일", datetime.date.today() + datetime.timedelta(days=7))
                
                if st.form_submit_button("등록하기"):
                    if new_name:
                        new_row = {
                            "프로모션명": new_name,
                            "채널": new_channel,
                            "담당자": new_manager,
                            "상태": new_status,
                            "진척율": new_progress,
                            "시작일": new_start,
                            "종료일": new_end
                        }
                        # 기존에 추가된 다른 동적 컬럼들에 대해서도 빈 값으로 초기화
                        for col in st.session_state.promotions.columns:
                            if col not in new_row:
                                new_row[col] = "-"
                                
                        new_data = pd.DataFrame([new_row])
                        st.session_state.promotions = pd.concat([st.session_state.promotions, new_data], ignore_index=True)
                        st.success("등록 완료")
                        safe_rerun()
                    else:
                        st.error("프로모션명은 필수입니다.")

        st.divider()

        # 2. 데이터 수정 에디터
        st.subheader("✏️ 전체 데이터 수정")
        
        # 컬럼 설정 (채널 선택박스 추가)
        column_configuration = {
            "진척율": st.column_config.NumberColumn("진척율", min_value=0, max_value=100, format="%d%%"),
            "상태": st.column_config.SelectboxColumn("상태", options=["기획단계", "대기", "진행중", "완료", "보류"], required=True),
            "채널": st.column_config.SelectboxColumn("채널", options=["On Trade", "Off Trade", "기타"], required=True),
            "시작일": st.column_config.DateColumn("시작일", format="YYYY-MM-DD"),
            "종료일": st.column_config.DateColumn("종료일", format="YYYY-MM-DD"),
        }

        edited_df = st.data_editor(
            df,
            column_config=column_configuration,
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="editor"
        )

        if not df.equals(edited_df):
            st.session_state.promotions = edited_df
            try:
                st.toast("저장됨!", icon="✅")
            except:
                pass
                
        st.divider()

        # 3. CSV 관리
        st.subheader("📂 데이터 일괄 관리")
        col_csv1, col_csv2 = st.columns(2)
        with col_csv1:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 CSV 다운로드", csv, "promotion_list.csv", "text/csv", use_container_width=True)
        with col_csv2:
            uploaded_file = st.file_uploader("CSV 업로드", type=["csv"], label_visibility="collapsed")
            if uploaded_file and st.button("🔄 교체하기", use_container_width=True):
                try:
                    new_df = pd.read_csv(uploaded_file)
                    # 날짜 변환
                    for col in ['시작일', '종료일']:
                        if col in new_df.columns:
                            new_df[col] = pd.to_datetime(new_df[col]).dt.date
                    st.session_state.promotions = new_df
                    st.success("교체 완료")
                    safe_rerun()
                except Exception as e:
                    st.error(f"오류: {e}")
