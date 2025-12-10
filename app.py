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
    
    # 1. 상단: 통합 검색 및 필터 (슬라이서)
    with st.expander("🔍 상세 검색 및 필터 (슬라이서)", expanded=True):
        st.markdown("원하는 조건으로 데이터를 좁혀서 볼 수 있습니다.")
        
        # 동적 필터 생성: 날짜/숫자를 제외한 모든 문자열 컬럼에 대해 멀티셀렉트 생성
        filter_cols = st.columns(3)
        filtered_df = df.copy()
        
        # 제외할 기본 컬럼 (필터링 굳이 필요 없는 것들)
        exclude_cols = ['진척율', '시작일', '종료일']
        
        # 사용 가능한 컬럼 중 필터로 만들 컬럼 선정
        valid_filter_cols = [c for c in df.columns if c not in exclude_cols]
        
        # 필터 적용 로직
        for i, col_name in enumerate(valid_filter_cols):
            with filter_cols[i % 3]:
                # 각 컬럼의 유니크한 값 추출
                unique_vals = df[col_name].unique()
                selected_vals = st.multiselect(
                    f"{col_name}",
                    unique_vals,
                    placeholder="전체"
                )
                
                # 선택된 값이 있으면 해당 값으로 데이터 필터링
                if selected_vals:
                    filtered_df = filtered_df[filtered_df[col_name].isin(selected_vals)]

    st.divider()

    # 2. 핵심 지표 (필터링된 데이터 기준)
    # 필터링 결과가 filtered_df에 있으므로 이를 기준으로 지표 산출
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("조회된 프로모션", f"{len(filtered_df)}건")
    col2.metric("진행중 (조회내)", f"{len(filtered_df[filtered_df['상태'] == '진행중'])}건")
    col3.metric("완료 (조회내)", f"{len(filtered_df[filtered_df['상태'] == '완료'])}건")
    
    avg_progress = filtered_df['진척율'].mean() if not filtered_df.empty else 0
    col4.metric("평균 진척율", f"{avg_progress:.1f}%")

    st.divider()
    
    # 3. 데이터 목록 조회
    st.subheader("📋 프로모션 상세 목록")
    st.caption("헤더를 클릭하면 정렬(Sort)할 수 있습니다.")

    # 탭 구성 (진행중 / 완료 / 전체)
    # 필터링된 데이터 안에서 상태별로 탭을 나눕니다.
    df_active = filtered_df[filtered_df['상태'] != '완료']
    df_completed = filtered_df[filtered_df['상태'] == '완료']

    tab1, tab2, tab3 = st.tabs([f"🔥 진행 중 ({len(df_active)})", f"✅ 완료됨 ({len(df_completed)})", f"📑 전체 목록 ({len(filtered_df)})"])

    # 공통 컬럼 설정
    common_config = {
        "진척율": st.column_config.ProgressColumn("진척율", format="%d%%", min_value=0, max_value=100),
        "상태": st.column_config.TextColumn("상태"),
    }
    
    # 동적 컬럼들을 위해 나머지 컬럼은 기본 텍스트 등으로 자동 처리됨
    # 채널 컬럼이 있다면 설정 추가
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
        if st.button("🔒 관리자 모드 종료"):
            st.session_state.is_admin_unlocked = False
            safe_rerun()
            
        st.divider()

        # [기능 업그레이드] 컬럼 관리 섹션 (추가/삭제)
        st.subheader("🛠️ 데이터 항목(컬럼) 관리")
        
        col_mgt1, col_mgt2 = st.columns(2)
        
        # 1. 컬럼 추가
        with col_mgt1:
            with st.expander("항목 추가하기"):
                new_col_name = st.text_input("추가할 항목 이름 (예: 예산, 지역)")
                if st.button("컬럼 추가", use_container_width=True):
                    if new_col_name and new_col_name not in st.session_state.promotions.columns:
                        st.session_state.promotions[new_col_name] = "-"  # 기본값 설정
                        st.success(f"'{new_col_name}' 항목이 추가되었습니다.")
                        safe_rerun()
                    elif new_col_name in st.session_state.promotions.columns:
                        st.error("이미 존재하는 항목입니다.")
                    else:
                        st.error("항목 이름을 입력하세요.")
        
        # 2. 컬럼 삭제
        with col_mgt2:
            with st.expander("항목 삭제하기"):
                # 삭제 가능한 컬럼 목록 (기본 필수 컬럼 보호 가능, 여기서는 전체 허용하되 경고)
                # 기본적으로 보호해야 할 컬럼들
                protected_cols = ['프로모션명', '상태', '진척율']
                deletable_cols = [c for c in df.columns if c not in protected_cols]
                
                del_col_name = st.selectbox("삭제할 항목 선택", deletable_cols)
                
                if st.button("선택한 항목 삭제", type="primary", use_container_width=True):
                    if del_col_name:
                        st.session_state.promotions = st.session_state.promotions.drop(columns=[del_col_name])
                        st.success(f"'{del_col_name}' 항목이 삭제되었습니다.")
                        safe_rerun()
                    else:
                        st.warning("삭제할 수 있는 항목이 없습니다.")

        st.divider()

        # 1. 새 프로모션 등록
        with st.expander("➕ 새 프로모션 등록하기", expanded=False):
            with st.form("add_promo_form"):
                st.markdown("**기본 정보**")
                # 동적 폼 생성: 현재 존재하는 컬럼에 맞춰 입력창 자동 생성
                # 필수 컬럼과 동적 컬럼 분리
                
                # 고정된 레이아웃을 위한 주요 필드
                col_a, col_b = st.columns(2)
                new_name = col_a.text_input("프로모션명")
                
                # 상태는 셀렉트박스로
                new_status = col_b.selectbox("상태", ["기획단계", "대기", "진행중", "완료", "보류"])
                
                new_progress = st.slider("초기 진척율 (%)", 0, 100, 0)
                
                # 나머지 동적 컬럼들에 대한 입력창 생성
                dynamic_inputs = {}
                
                # 날짜 컬럼 등 특수 처리 제외한 나머지 문자열 컬럼들
                reserved_cols = ['프로모션명', '상태', '진척율', '시작일', '종료일']
                other_cols = [c for c in df.columns if c not in reserved_cols]
                
                # 날짜 입력
                col_c, col_d = st.columns(2)
                new_start = col_c.date_input("시작일", datetime.date.today())
                new_end = col_d.date_input("종료일", datetime.date.today() + datetime.timedelta(days=7))

                # 동적 컬럼 입력창 배치 (3열로 배치)
                if other_cols:
                    st.markdown("**추가 정보 입력**")
                    cols = st.columns(3)
                    for i, col_name in enumerate(other_cols):
                        # 채널 같은 경우 선택박스로 주면 좋겠지만, 동적 컬럼이므로 텍스트 인풋이 안전
                        # 단, '채널'이라는 이름이면 선택박스 제공 등 커스텀 가능
                        if col_name == '채널':
                            dynamic_inputs[col_name] = cols[i % 3].selectbox(col_name, ["On Trade", "Off Trade", "기타"])
                        else:
                            dynamic_inputs[col_name] = cols[i % 3].text_input(col_name)
                
                if st.form_submit_button("등록하기"):
                    if new_name:
                        new_row = {
                            "프로모션명": new_name,
                            "상태": new_status,
                            "진척율": new_progress,
                            "시작일": new_start,
                            "종료일": new_end
                        }
                        # 동적 입력값 병합
                        new_row.update(dynamic_inputs)
                                
                        new_data = pd.DataFrame([new_row])
                        st.session_state.promotions = pd.concat([st.session_state.promotions, new_data], ignore_index=True)
                        st.success("등록 완료")
                        safe_rerun()
                    else:
                        st.error("프로모션명은 필수입니다.")

        st.divider()

        # 2. 데이터 수정 에디터
        st.subheader("✏️ 전체 데이터 수정")
        
        column_configuration = {
            "진척율": st.column_config.NumberColumn("진척율", min_value=0, max_value=100, format="%d%%"),
            "상태": st.column_config.SelectboxColumn("상태", options=["기획단계", "대기", "진행중", "완료", "보류"], required=True),
            "시작일": st.column_config.DateColumn("시작일", format="YYYY-MM-DD"),
            "종료일": st.column_config.DateColumn("종료일", format="YYYY-MM-DD"),
        }
        
        # 채널 컬럼이 존재한다면 selectbox로 설정
        if "채널" in df.columns:
            column_configuration["채널"] = st.column_config.SelectboxColumn("채널", options=["On Trade", "Off Trade", "기타"])

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
