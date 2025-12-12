import streamlit as st
import pandas as pd
import datetime
import os

# ---------------------------------------------------------
# 파일 저장소 설정
# ---------------------------------------------------------
DATA_FILE = "promotion_data.csv"

# 데이터 로드 함수 (파일이 있으면 읽고, 없으면 기본값 생성)
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # 날짜 컬럼 변환
            for col in ['시작일', '종료일']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
            # 진척율 숫자 변환
            if '진척율' in df.columns:
                df['진척율'] = df['진척율'].astype(str).str.replace('%', '').str.strip()
                df['진척율'] = pd.to_numeric(df['진척율'], errors='coerce').fillna(0).astype(int)
            return df
        except Exception as e:
            st.error(f"데이터 파일 로드 중 오류 발생: {e}")
            return create_default_data()
    else:
        return create_default_data()

# 기본 데이터 생성 함수
def create_default_data():
    return pd.DataFrame([
        {"프로모션명": "2024 봄 정기 세일", "채널": "Off Trade", "담당자": "김철수", "상태": "진행중", "진척율": 75, "시작일": datetime.date(2024, 3, 1), "종료일": datetime.date(2024, 3, 15)},
        {"프로모션명": "신규 회원 가입 이벤트", "채널": "On Trade", "담당자": "이영희", "상태": "기획단계", "진척율": 20, "시작일": datetime.date(2024, 4, 1), "종료일": datetime.date(2024, 4, 30)},
        {"프로모션명": "여름 바캉스 특가", "채널": "Off Trade", "담당자": "박민수", "상태": "대기", "진척율": 0, "시작일": datetime.date(2024, 6, 1), "종료일": datetime.date(2024, 8, 31)},
        {"프로모션명": "설날 효도 선물전", "채널": "On Trade", "담당자": "정수진", "상태": "완료", "진척율": 100, "시작일": datetime.date(2024, 1, 15), "종료일": datetime.date(2024, 2, 9)},
    ])

# 데이터 저장 함수 (파일 저장 + 세션 업데이트)
def save_data_to_file(df):
    try:
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        st.session_state.promotions = df  # 대시보드에 즉시 반영
        st.success("✅ 데이터가 성공적으로 저장되고 대시보드에 반영되었습니다!")
    except Exception as e:
        st.error(f"저장 중 오류가 발생했습니다: {e}")

# 호환성 함수
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

# 초기 데이터 로드 (파일 또는 기본값)
if 'promotions' not in st.session_state:
    st.session_state.promotions = load_data()

# 관리자 로그인 상태 초기화
if 'is_admin_unlocked' not in st.session_state:
    st.session_state.is_admin_unlocked = False

# 대시보드에 보여줄 데이터 (Live Data)
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
# 페이지 1: 대시보드 (View Only)
# ---------------------------------------------------------
if page == "📊 대시보드":
    st.title("📊 프로모션 현황 대시보드")
    
    metrics_container = st.container()

    st.divider()
    
    # 상세 검색 및 필터
    with st.expander("🔍 상세 검색 및 필터 (슬라이서)", expanded=True):
        st.caption("앞쪽(왼쪽) 필터를 선택하면 뒤쪽(오른쪽) 필터의 선택 항목이 자동으로 줄어듭니다.")
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
        try:
            avg_progress = filtered_df['진척율'].mean() if not filtered_df.empty else 0
        except:
            avg_progress = 0
        col4.metric("평균 진척율", f"{avg_progress:.1f}%")

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
        # [우측 상단] 저장 버튼 배치 (헤더 옆에)
        col_header, col_save = st.columns([3, 1])
        with col_header:
            st.info("💡 데이터를 수정한 후 반드시 우측의 **'저장하기'** 버튼을 눌러야 반영됩니다.")
        with col_save:
            save_button_clicked = st.button("💾 변경사항 저장 및 반영", type="primary", use_container_width=True)

        # -----------------------------------------------------
        # [데이터 스테이징 로직]
        # 편집 중인 데이터(Draft)를 관리합니다.
        # -----------------------------------------------------
        
        # 1. 초기는 현재 라이브 데이터로 시작
        if 'draft_df' not in st.session_state:
            st.session_state.draft_df = df.copy()

        st.divider()

        # [CSV 업로드 섹션] - 업로드 시 Draft 데이터를 덮어씀
        with st.expander("📂 CSV 파일로 데이터 덮어쓰기 (업로드)", expanded=False):
            uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"], label_visibility="collapsed")
            if uploaded_file:
                try:
                    new_df = pd.read_csv(uploaded_file)
                    # 전처리
                    if '진척율' in new_df.columns:
                        new_df['진척율'] = new_df['진척율'].astype(str).str.replace('%', '').str.strip()
                        new_df['진척율'] = pd.to_numeric(new_df['진척율'], errors='coerce').fillna(0).astype(int)
                    for col in ['시작일', '종료일']:
                        if col in new_df.columns:
                            new_df[col] = pd.to_datetime(new_df[col], errors='coerce').dt.date
                    
                    # Draft 상태 업데이트
                    st.session_state.draft_df = new_df
                    st.success("CSV 파일이 로드되었습니다. 아래 표에서 확인 후 '저장하기'를 누르세요.")
                except Exception as e:
                    st.error(f"CSV 오류: {e}")

        st.divider()

        # [데이터 에디터] - Draft 데이터를 편집
        st.subheader("✏️ 데이터 편집 (미리보기)")
        
        column_configuration = {
            "진척율": st.column_config.NumberColumn("진척율", min_value=0, max_value=100, format="%d%%"),
            "상태": st.column_config.SelectboxColumn("상태", options=["기획단계", "대기", "진행중", "완료", "보류"], required=True),
            "시작일": st.column_config.DateColumn("시작일", format="YYYY-MM-DD"),
            "종료일": st.column_config.DateColumn("종료일", format="YYYY-MM-DD"),
        }
        if "채널" in df.columns:
            column_configuration["채널"] = st.column_config.SelectboxColumn("채널", options=["On Trade", "Off Trade", "기타"])

        # 사용자가 수정한 내용이 edited_df에 담김
        edited_df = st.data_editor(
            st.session_state.draft_df,  # 편집 대상은 Draft 데이터
            column_config=column_configuration,
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="admin_editor"
        )

        # 에디터의 수정사항을 실시간으로 Draft 세션에 동기화
        if not edited_df.equals(st.session_state.draft_df):
            st.session_state.draft_df = edited_df

        # -----------------------------------------------------
        # [저장 버튼 동작]
        # -----------------------------------------------------
        if save_button_clicked:
            save_data_to_file(edited_df)
            
        st.divider()
        
        # [CSV 다운로드] - 현재 편집 중인 데이터 기준
        csv = edited_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 현재 데이터 CSV 다운로드", csv, "promotion_data.csv", "text/csv")
