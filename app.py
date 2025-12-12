import streamlit as st
import pandas as pd
import datetime
import os

# ---------------------------------------------------------
# 파일 저장소 설정
# ---------------------------------------------------------
DATA_FILE = "promotion_data.csv"

# ---------------------------------------------------------
# 함수 정의
# ---------------------------------------------------------
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def load_data():
    """CSV 파일에서 데이터를 로드하거나 기본 데이터를 생성합니다."""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # 날짜 컬럼 변환
            for col in ['시작일', '종료일']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
            
            # 진척율 숫자 변환 (안전장치)
            if '진척율' in df.columns:
                df['진척율'] = df['진척율'].astype(str).str.replace('%', '').str.strip()
                df['진척율'] = pd.to_numeric(df['진척율'], errors='coerce').fillna(0).astype(int)
            
            return df
        except Exception as e:
            st.error(f"데이터 파일 로드 중 오류 발생: {e}")
            return create_default_data()
    else:
        return create_default_data()

def create_default_data():
    """기본 예시 데이터를 생성합니다."""
    return pd.DataFrame([
        {"프로모션명": "2024 봄 정기 세일", "채널": "Off Trade", "담당자": "김철수", "상태": "진행중", "진척율": 75, "시작일": datetime.date(2024, 3, 1), "종료일": datetime.date(2024, 3, 15)},
        {"프로모션명": "신규 회원 가입 이벤트", "채널": "On Trade", "담당자": "이영희", "상태": "기획단계", "진척율": 20, "시작일": datetime.date(2024, 4, 1), "종료일": datetime.date(2024, 4, 30)},
        {"프로모션명": "여름 바캉스 특가", "채널": "Off Trade", "담당자": "박민수", "상태": "대기", "진척율": 0, "시작일": datetime.date(2024, 6, 1), "종료일": datetime.date(2024, 8, 31)},
        {"프로모션명": "설날 효도 선물전", "채널": "On Trade", "담당자": "정수진", "상태": "완료", "진척율": 100, "시작일": datetime.date(2024, 1, 15), "종료일": datetime.date(2024, 2, 9)},
    ])

def save_data(df):
    """데이터프레임을 CSV 파일로 저장하고 세션에 반영합니다."""
    try:
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        st.session_state.promotions = df.copy() # 라이브 데이터 업데이트
        return True
    except Exception as e:
        st.error(f"저장 중 오류 발생: {e}")
        return False

# ---------------------------------------------------------
# 페이지 설정 (가장 먼저 실행)
# ---------------------------------------------------------
st.set_page_config(
    page_title="프로모션 통합 시스템",
    page_icon="🔒",
    layout="wide"
)

# ---------------------------------------------------------
# [1단계] 글로벌 로그인 (입구 컷) - 비밀번호: dk2026
# ---------------------------------------------------------
if 'is_global_unlocked' not in st.session_state:
    st.session_state.is_global_unlocked = False

if not st.session_state.is_global_unlocked:
    st.title("🔒 프로모션 시스템 접근")
    st.markdown("### 접속을 위해 보안 코드를 입력하세요.")
    global_password = st.text_input("접속 암호", type="password", key="global_pw")
    
    if st.button("시스템 접속"):
        if global_password == "dk2026":
            st.session_state.is_global_unlocked = True
            st.toast("접속 승인되었습니다.", icon="🔓")
            safe_rerun()
        else:
            st.error("잘못된 암호입니다.")
    st.stop()

# =========================================================
# [메인 앱]
# =========================================================

# 1. 라이브 데이터 로드 (파일 기준)
if 'promotions' not in st.session_state:
    st.session_state.promotions = load_data()

# 2. 관리자용 임시 데이터(Draft) 초기화
if 'draft_df' not in st.session_state:
    st.session_state.draft_df = st.session_state.promotions.copy()

# 관리자 로그인 상태 초기화
if 'is_admin_unlocked' not in st.session_state:
    st.session_state.is_admin_unlocked = False

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
# 페이지 1: 대시보드 (View Only)
# ---------------------------------------------------------
if page == "📊 대시보드":
    st.title("📊 프로모션 현황 대시보드")
    
    # 데이터 소스: 라이브 데이터 (promotions)
    df = st.session_state.promotions
    
    metrics_container = st.container()

    st.divider()
    
    # 상세 검색 및 필터 (슬라이서) - 기본값 접힘 (expanded=False)
    with st.expander("🔍 상세 검색 및 필터 (슬라이서)", expanded=False):
        st.caption("필터를 선택하면 하위 필터의 선택 항목이 자동으로 최적화됩니다.")
        filter_cols = st.columns(3)
        filtered_df = df.copy() 
        exclude_cols = ['진척율', '시작일', '종료일']
        valid_filter_cols = [c for c in df.columns if c not in exclude_cols]
        
        for i, col_name in enumerate(valid_filter_cols):
            with filter_cols[i % 3]:
                unique_vals = sorted(filtered_df[col_name].astype(str).unique())
                selected_vals = st.multiselect(
                    f"{col_name}",
                    unique_vals,
                    placeholder="전체",
                    key=f"dash_filter_{col_name}"
                )
                if selected_vals:
                    filtered_df = filtered_df[filtered_df[col_name].astype(str).isin(selected_vals)]

    # 지표 표시
    with metrics_container:
        st.markdown("#### 📈 전체 현황 요약")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("조회된 프로모션", f"{len(filtered_df)}건")
        col2.metric("진행중", f"{len(filtered_df[filtered_df['상태'] == '진행중'])}건")
        col3.metric("완료", f"{len(filtered_df[filtered_df['상태'] == '완료'])}건")
        
        # [수정] 평균 진척율 계산 시 '완료' 상태 제외
        # 완료되지 않은 건들만 필터링
        active_df = filtered_df[filtered_df['상태'] != '완료']
        try:
            if not active_df.empty:
                avg_progress = active_df['진척율'].mean()
            else:
                avg_progress = 0
        except:
            avg_progress = 0
            
        col4.metric("평균 진척율 (완료제외)", f"{avg_progress:.1f}%")

    st.divider()
    
    # 목록 조회
    st.subheader("📋 프로모션 상세 목록")
    df_active = filtered_df[filtered_df['상태'] != '완료']
    df_completed = filtered_df[filtered_df['상태'] == '완료']

    tab1, tab2, tab3 = st.tabs([f"🔥 진행 중 ({len(df_active)})", f"✅ 완료됨 ({len(df_completed)})", f"📑 전체 목록 ({len(filtered_df)})"])

    common_config = {
        "진척율": st.column_config.ProgressColumn("진척율", format="%d%%", min_value=0, max_value=100),
        "상태": st.column_config.TextColumn("상태"),
    }
    if "채널" in df.columns:
        common_config["채널"] = st.column_config.TextColumn("채널", help="판매 채널 구분")

    with tab1:
        st.dataframe(df_active, column_config=common_config, use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(df_completed, column_config=common_config, use_container_width=True, hide_index=True)
    with tab3:
        st.dataframe(filtered_df, column_config=common_config, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 페이지 2: 관리자 페이지 (비밀번호: diageorcg)
# ---------------------------------------------------------
elif page == "⚙️ 관리자 페이지":
    # 2.1 관리자 인증
    if not st.session_state.is_admin_unlocked:
        st.title("⚙️ 관리자 인증")
        st.warning("⚠️ 관리자 권한이 필요합니다.")
        with st.form("admin_login_form"):
            admin_pw = st.text_input("관리자 암호", type="password")
            if st.form_submit_button("관리자 로그인"):
                if admin_pw == "diageorcg":
                    st.session_state.is_admin_unlocked = True
                    # 관리자 모드 진입 시 draft를 live 데이터와 동기화
                    st.session_state.draft_df = st.session_state.promotions.copy()
                    safe_rerun()
                else:
                    st.error("암호 오류")
    else:
        # 2.2 관리자 메인 화면
        col_title, col_save = st.columns([2, 1])
        with col_title:
            st.title("⚙️ 데이터 관리")
        with col_save:
            st.markdown("######") # 간격 조정용
            # 우측 상단 저장 버튼
            if st.button("💾 저장하고 적용하기", type="primary", use_container_width=True):
                if save_data(st.session_state.draft_df):
                    st.toast("✅ 저장 완료! 대시보드에 적용되었습니다.", icon="🎉")
                    # Draft와 Live 싱크 맞춤
                    st.session_state.promotions = st.session_state.draft_df.copy()
        
        st.info("💡 아래에서 데이터를 수정한 후, 반드시 우측 상단의 **'저장하고 적용하기'** 버튼을 눌러야 반영됩니다.")
        
        # -----------------------------------------------------
        # 기능 1: 컬럼(열) 관리
        # -----------------------------------------------------
        with st.expander("🛠️ 컬럼(열) 추가 및 삭제", expanded=False):
            col_add, col_del = st.columns(2)
            with col_add:
                new_col_name = st.text_input("추가할 컬럼명")
                if st.button("컬럼 추가", use_container_width=True):
                    if new_col_name and new_col_name not in st.session_state.draft_df.columns:
                        st.session_state.draft_df[new_col_name] = "-"
                        st.success(f"'{new_col_name}' 추가됨 (임시)")
                        safe_rerun()
                    elif new_col_name in st.session_state.draft_df.columns:
                        st.error("이미 존재하는 컬럼입니다.")
            
            with col_del:
                # 필수 컬럼 보호
                protected_cols = ['프로모션명', '상태', '진척율']
                deletable = [c for c in st.session_state.draft_df.columns if c not in protected_cols]
                del_col = st.selectbox("삭제할 컬럼 선택", deletable)
                if st.button("컬럼 삭제", type="primary", use_container_width=True):
                    if del_col:
                        st.session_state.draft_df = st.session_state.draft_df.drop(columns=[del_col])
                        st.success(f"'{del_col}' 삭제됨 (임시)")
                        safe_rerun()

        # -----------------------------------------------------
        # 기능 2: 행(Row) 추가
        # -----------------------------------------------------
        with st.expander("➕ 새 데이터(행) 추가", expanded=False):
            with st.form("add_row_form"):
                st.markdown("**기본 정보**")
                c1, c2 = st.columns(2)
                in_name = c1.text_input("프로모션명")
                in_status = c2.selectbox("상태", ["기획단계", "대기", "진행중", "완료", "보류"])
                in_progress = st.slider("진척율 (%)", 0, 100, 0)
                
                c3, c4 = st.columns(2)
                in_start = c3.date_input("시작일", datetime.date.today())
                in_end = c4.date_input("종료일", datetime.date.today() + datetime.timedelta(days=7))
                
                # 동적 컬럼 입력
                dynamic_data = {}
                reserved = ['프로모션명', '상태', '진척율', '시작일', '종료일']
                others = [c for c in st.session_state.draft_df.columns if c not in reserved]
                
                if others:
                    st.markdown("**추가 정보**")
                    dc_cols = st.columns(3)
                    for idx, col in enumerate(others):
                        if col == '채널':
                            dynamic_data[col] = dc_cols[idx % 3].selectbox(col, ["On Trade", "Off Trade", "기타"])
                        else:
                            dynamic_data[col] = dc_cols[idx % 3].text_input(col)

                if st.form_submit_button("추가하기"):
                    if in_name:
                        new_row = {
                            "프로모션명": in_name,
                            "상태": in_status,
                            "진척율": in_progress,
                            "시작일": in_start,
                            "종료일": in_end
                        }
                        new_row.update(dynamic_data)
                        
                        # 기존 DataFrame에 병합
                        st.session_state.draft_df = pd.concat(
                            [st.session_state.draft_df, pd.DataFrame([new_row])], 
                            ignore_index=True
                        )
                        st.success("데이터 추가됨 (임시)")
                        safe_rerun()
                    else:
                        st.error("프로모션명은 필수입니다.")

        # -----------------------------------------------------
        # 기능 3: CSV 업로드 (덮어쓰기)
        # -----------------------------------------------------
        with st.expander("📂 CSV 파일로 덮어쓰기", expanded=False):
            uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"], label_visibility="collapsed")
            if uploaded_file:
                if st.button("🔄 이 파일로 데이터 교체 (임시)", use_container_width=True):
                    try:
                        new_df = pd.read_csv(uploaded_file)
                        # 전처리
                        if '진척율' in new_df.columns:
                            new_df['진척율'] = new_df['진척율'].astype(str).str.replace('%', '').str.strip()
                            new_df['진척율'] = pd.to_numeric(new_df['진척율'], errors='coerce').fillna(0).astype(int)
                        for col in ['시작일', '종료일']:
                            if col in new_df.columns:
                                new_df[col] = pd.to_datetime(new_df[col], errors='coerce').dt.date
                        
                        st.session_state.draft_df = new_df
                        st.success("CSV 데이터 로드됨 (임시). 상단 저장 버튼을 눌러 확정하세요.")
                        safe_rerun()
                    except Exception as e:
                        st.error(f"오류: {e}")

        st.divider()

        # -----------------------------------------------------
        # 기능 4: 데이터 에디터 (수정)
        # -----------------------------------------------------
        st.subheader("✏️ 데이터 편집 (Draft)")
        
        # 컬럼 설정
        column_configuration = {
            "진척율": st.column_config.NumberColumn("진척율", min_value=0, max_value=100, format="%d%%"),
            "상태": st.column_config.SelectboxColumn("상태", options=["기획단계", "대기", "진행중", "완료", "보류"], required=True),
            "시작일": st.column_config.DateColumn("시작일", format="YYYY-MM-DD"),
            "종료일": st.column_config.DateColumn("종료일", format="YYYY-MM-DD"),
        }
        if "채널" in st.session_state.draft_df.columns:
            column_configuration["채널"] = st.column_config.SelectboxColumn("채널", options=["On Trade", "Off Trade", "기타"])

        edited_df = st.data_editor(
            st.session_state.draft_df,
            column_config=column_configuration,
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="draft_editor"
        )

        # 에디터 변경사항 실시간 반영 (임시 상태)
        if not edited_df.equals(st.session_state.draft_df):
            st.session_state.draft_df = edited_df

        st.divider()
        
        # CSV 다운로드
        csv = st.session_state.draft_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 현재 작업중인 데이터 다운로드", csv, "promotion_draft.csv", "text/csv")
