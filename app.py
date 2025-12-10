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

# 초기 데이터 설정
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
    
    # [UX 최적화] 모바일에서 핵심 지표를 가장 먼저 보여주기 위해 컨테이너를 상단에 배치
    metrics_container = st.container()

    st.divider()
    
    # 2. 상세 검색 및 필터 (연동형 슬라이서)
    with st.expander("🔍 상세 검색 및 필터 (슬라이서)", expanded=True):
        st.caption("앞쪽(왼쪽) 필터를 선택하면 뒤쪽(오른쪽) 필터의 선택 항목이 자동으로 줄어듭니다.")
        
        # 필터 UI 생성
        filter_cols = st.columns(3)
        filtered_df = df.copy() # 누적 필터링을 위한 임시 DataFrame
        
        exclude_cols = ['진척율', '시작일', '종료일']
        valid_filter_cols = [c for c in df.columns if c not in exclude_cols]
        
        # [핵심 로직] 순차적 필터링 (Cascading Filtering)
        for i, col_name in enumerate(valid_filter_cols):
            with filter_cols[i % 3]:
                # 전체 데이터가 아니라, '앞 단계에서 필터링된 데이터(filtered_df)'의 유니크 값만 가져옵니다.
                unique_vals = sorted(filtered_df[col_name].astype(str).unique())
                
                selected_vals = st.multiselect(
                    f"{col_name}",
                    unique_vals,
                    placeholder="전체"
                )
                
                # 선택된 값이 있다면, filtered_df를 즉시 업데이트하여 다음 루프(다음 필터)에 영향을 줍니다.
                if selected_vals:
                    filtered_df = filtered_df[filtered_df[col_name].astype(str).isin(selected_vals)]

    # 3. [지표 표시] 계산된 filtered_df를 사용하여 상단 컨테이너에 지표 채워넣기
    with metrics_container:
        st.markdown("#### 📈 전체 현황 요약")
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("조회된 프로모션", f"{len(filtered_df)}건")
        col2.metric("진행중", f"{len(filtered_df[filtered_df['상태'] == '진행중'])}건")
        col3.metric("완료", f"{len(filtered_df[filtered_df['상태'] == '완료'])}건")
        
        avg_progress = filtered_df['진척율'].mean() if not filtered_df.empty else 0
        col4.metric("평균 진척율", f"{avg_progress:.1f}%")

    st.divider()
    
    # 4. 데이터 목록 조회
    st.subheader("📋 프로모션 상세 목록")

    # 탭 구성
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
        if st.button("🔒 관리자 모드 종료"):
            st.session_state.is_admin_unlocked = False
            safe_rerun()
            
        st.divider()

        # [컬럼 관리 섹션]
        st.subheader("🛠️ 데이터 항목(컬럼) 관리")
        
        col_mgt1, col_mgt2 = st.columns(2)
        
        # 1. 컬럼 추가
        with col_mgt1:
            with st.expander("항목 추가하기"):
                new_col_name = st.text_input("추가할 항목 이름 (예: 예산, 지역)")
                if st.button("컬럼 추가", use_container_width=True):
                    if new_col_name and new_col_name not in st.session_state.promotions.columns:
                        st.session_state.promotions[new_col_name] = "-"
                        st.success(f"'{new_col_name}' 항목이 추가되었습니다.")
                        safe_rerun()
                    elif new_col_name in st.session_state.promotions.columns:
                        st.error("이미 존재하는 항목입니다.")
                    else:
                        st.error("항목 이름을 입력하세요.")
        
        # 2. 컬럼 삭제
        with col_mgt2:
            with st.expander("항목 삭제하기"):
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
                
                col_a, col_b = st.columns(2)
                new_name = col_a.text_input("프로모션명")
                new_status = col_b.selectbox("상태", ["기획단계", "대기", "진행중", "완료", "보류"])
                new_progress = st.slider("초기 진척율 (%)", 0, 100, 0)
                
                dynamic_inputs = {}
                reserved_cols = ['프로모션명', '상태', '진척율', '시작일', '종료일']
                other_cols = [c for c in df.columns if c not in reserved_cols]
                
                col_c, col_d = st.columns(2)
                new_start = col_c.date_input("시작일", datetime.date.today())
                new_end = col_d.date_input("종료일", datetime.date.today() + datetime.timedelta(days=7))

                if other_cols:
                    st.markdown("**추가 정보 입력**")
                    cols = st.columns(3)
                    for i, col_name in enumerate(other_cols):
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
                    for col in ['시작일', '종료일']:
                        if col in new_df.columns:
                            new_df[col] = pd.to_datetime(new_df[col]).dt.date
                    st.session_state.promotions = new_df
                    st.success("교체 완료")
                    safe_rerun()
                except Exception as e:
                    st.error(f"오류: {e}")
