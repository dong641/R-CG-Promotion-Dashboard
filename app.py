import streamlit as st
import pandas as pd
import datetime
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
# [핵심] 구글 시트 데이터 로드/저장 함수
# ---------------------------------------------------------
def get_db_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def load_promotions():
    """구글 시트 'promotions' 워크시트에서 데이터 로드"""
    conn = get_db_connection()
    try:
        df = conn.read(worksheet="promotions", ttl=0)
        if df.empty: return create_default_promotions()
        
        # 전처리
        for col in ['시작일', '종료일']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        if '진척율' in df.columns:
            df['진척율'] = df['진척율'].astype(str).str.replace('%', '').str.strip()
            df['진척율'] = pd.to_numeric(df['진척율'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception:
        return create_default_promotions()

def save_promotions(df):
    """구글 시트 'promotions' 워크시트에 저장"""
    conn = get_db_connection()
    try:
        conn.update(worksheet="promotions", data=df)
        st.session_state.promotions = df.copy()
        return True
    except Exception as e:
        st.error(f"구글 시트 저장 실패: {e}")
        return False

def load_weekly_reports():
    """구글 시트 'weekly_reports' 워크시트에서 로드"""
    conn = get_db_connection()
    try:
        df = conn.read(worksheet="weekly_reports", ttl=0)
        if df.empty: return create_empty_report_df()
        if 'Week_Start' in df.columns:
            df['Week_Start'] = df['Week_Start'].astype(str)
        return df
    except:
        return create_empty_report_df()

def save_weekly_report_entry(new_data_df):
    """주간 업무 저장"""
    conn = get_db_connection()
    try:
        try:
            existing_df = conn.read(worksheet="weekly_reports", ttl=0)
            if 'Week_Start' in existing_df.columns:
                existing_df['Week_Start'] = existing_df['Week_Start'].astype(str)
        except:
            existing_df = create_empty_report_df()

        if not new_data_df.empty:
            week_start = str(new_data_df['Week_Start'].iloc[0])
            assignee = new_data_df['Assignee'].iloc[0]
            
            if not existing_df.empty:
                mask = ~((existing_df['Week_Start'] == week_start) & (existing_df['Assignee'] == assignee))
                existing_df = existing_df[mask]
        
        final_df = pd.concat([existing_df, new_data_df], ignore_index=True)
        conn.update(worksheet="weekly_reports", data=final_df)
        return True
    except Exception as e:
        st.error(f"리포트 저장 실패: {e}")
        return False

# 기본 데이터 생성 함수들
def create_default_promotions():
    return pd.DataFrame([
        {"프로모션명": "샘플 프로모션", "채널": "On Trade", "담당자": "관리자", "상태": "진행중", "진척율": 50, "시작일": datetime.date.today(), "종료일": datetime.date.today()}
    ])

def create_empty_report_df():
    return pd.DataFrame(columns=["Week_Start", "Assignee", "Type", "Project", "Content", "Status"])

# ---------------------------------------------------------
# 메인 앱 초기화
# ---------------------------------------------------------
st.set_page_config(page_title="프로모션 통합 시스템 (Google)", page_icon="📊", layout="wide")

if 'promotions' not in st.session_state:
    st.session_state.promotions = load_promotions()
if 'is_global_unlocked' not in st.session_state:
    st.session_state.is_global_unlocked = False

# ---------------------------------------------------------
# 1. 로그인 화면
# ---------------------------------------------------------
if not st.session_state.is_global_unlocked:
    st.title("🔒 프로모션 시스템 접근")
    c1, c2 = st.columns([2,1])
    with c1:
        pw = st.text_input("접속 암호를 입력하세요", type="password")
    if st.button("접속"):
        if pw == "dk2026":
            st.session_state.is_global_unlocked = True
            safe_rerun()
        else:
            st.error("암호가 일치하지 않습니다.")
    st.stop()

# ---------------------------------------------------------
# 사이드바
# ---------------------------------------------------------
with st.sidebar:
    st.title("메뉴")
    page = st.radio("이동할 페이지", ["📊 대시보드", "📅 주간 업무", "⚙️ 관리자 페이지"])
    st.divider()
    if st.button("🚪 로그아웃"):
        st.session_state.is_global_unlocked = False
        st.session_state.is_admin_unlocked = False
        safe_rerun()

# ---------------------------------------------------------
# PAGE 1: 대시보드
# ---------------------------------------------------------
if page == "📊 대시보드":
    st.title("📊 프로모션 현황 대시보드")
    df = st.session_state.promotions
    
    # 핵심 지표
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체 프로모션", f"{len(df)}건")
    c2.metric("진행중", f"{len(df[df['상태']=='진행중'])}건")
    c3.metric("완료", f"{len(df[df['상태']=='완료'])}건")
    
    # [수정] 평균 진척율 계산 시 완료 상태 제외
    active_df = df[df['상태'] != '완료']
    avg_prog = active_df['진척율'].mean() if not active_df.empty else 0
    c4.metric("평균 달성률(완료제외)", f"{avg_prog:.1f}%")

    st.divider()
    
    # 필터 및 리스트
    with st.expander("🔍 상세 필터", expanded=False):
        f_cols = st.columns(3)
        filtered_df = df.copy()
        cols = [c for c in df.columns if c not in ['진척율', '시작일', '종료일']]
        for i, col in enumerate(cols):
            with f_cols[i%3]:
                uniqs = sorted(filtered_df[col].astype(str).unique())
                sel = st.multiselect(col, uniqs, key=f"d_{col}")
                if sel: filtered_df = filtered_df[filtered_df[col].astype(str).isin(sel)]
    
    st.subheader("📋 프로모션 리스트")
    
    # [추가] 탭으로 구분하여 보기 (진행중 / 완료 / 전체)
    df_active = filtered_df[filtered_df['상태'] != '완료']
    df_completed = filtered_df[filtered_df['상태'] == '완료']
    
    tab1, tab2, tab3 = st.tabs([
        f"🔥 진행 중 ({len(df_active)})", 
        f"✅ 완료됨 ({len(df_completed)})", 
        f"📑 전체 목록 ({len(filtered_df)})"
    ])
    
    cfg = {"진척율": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)}
    
    with tab1:
        st.dataframe(df_active, column_config=cfg, use_container_width=True, hide_index=True)
        
    with tab2:
        st.dataframe(df_completed, column_config=cfg, use_container_width=True, hide_index=True)
        
    with tab3:
        st.dataframe(filtered_df, column_config=cfg, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# PAGE 2: 주간 업무
# ---------------------------------------------------------
elif page == "📅 주간 업무":
    st.title("📅 Weekly Business Review")
    
    col_date, col_view_opt = st.columns([1, 2])
    with col_date:
        pick_date = st.date_input("기준 날짜", datetime.date.today())
    
    start_week, end_week = get_week_range(pick_date)
    week_str = str(start_week)
    
    with col_view_opt:
        st.info(f"📆 **{start_week} ~ {end_week}** 주간 업무 보고")

    st.divider()

    tab_view, tab_write = st.tabs(["📋 전체 팀원 보고서 조회 (Dashboard)", "✍️ 내 보고서 작성/수정"])

    # --- TAB 1: 조회 ---
    with tab_view:
        with st.spinner("데이터를 불러오는 중..."):
            report_df = load_weekly_reports()
            
        current_reports = report_df[report_df['Week_Start'] == week_str]
        
        if current_reports.empty:
            st.warning("해당 주차에 제출된 보고서가 없습니다.")
        else:
            assignees = sorted(current_reports['Assignee'].unique())
            view_mode = st.radio("보기 방식", ["카드 뷰 (Card View)", "요약 테이블 (Summary)"], horizontal=True, label_visibility="collapsed")
            
            if view_mode == "요약 테이블 (Summary)":
                st.dataframe(
                    current_reports,
                    column_config={
                        "Assignee": st.column_config.TextColumn("담당자", width="small"),
                        "Content": st.column_config.TextColumn("업무 내용", width="large"),
                        "Week_Start": None
                    },
                    use_container_width=True, hide_index=True
                )
            else:
                cols = st.columns(2)
                for idx, person in enumerate(assignees):
                    p_df = current_reports[current_reports['Assignee'] == person]
                    with cols[idx % 2]:
                        with st.container(border=True):
                            st.markdown(f"#### 👤 {person}")
                            
                            def render_ppp_section(df_subset):
                                if df_subset.empty:
                                    st.caption("내용 없음")
                                else:
                                    for _, row in df_subset.iterrows():
                                        icon = "🟢" if row['Status']=="정상" else "🟡" if row['Status']=="지연" else "🔴"
                                        p_tag = f"**[{row['Project']}]**" if row['Project'] != "-" else ""
                                        st.markdown(f"{icon} {p_tag} {row['Content']}")

                            st.markdown("**✅ 금주 실적**")
                            render_ppp_section(p_df[p_df['Type'] == '금주 실적'])
                            st.divider()
                            st.markdown("**🗓️ 차주 계획**")
                            render_ppp_section(p_df[p_df['Type'] == '차주 계획'])
                            
                            prob_df = p_df[p_df['Type'] == '이슈사항']
                            if not prob_df.empty:
                                st.divider()
                                st.markdown("**⚠️ 이슈 사항**")
                                render_ppp_section(prob_df)

    # --- TAB 2: 작성 ---
    with tab_write:
        st.markdown("##### 📝 보고서 작성")
        managers = list(st.session_state.promotions['담당자'].unique()) if '담당자' in st.session_state.promotions.columns else []
        if "기타" not in managers: managers.append("기타")
        
        c_sel, _ = st.columns([1, 2])
        me = c_sel.selectbox("작성자(본인) 선택", managers, key="writer_select")
        if me == "기타": me = c_sel.text_input("이름 직접 입력")

        if me:
            full_data = load_weekly_reports()
            my_data = full_data[(full_data['Week_Start'] == week_str) & (full_data['Assignee'] == me)]
            
            if not my_data.empty:
                input_df = my_data.reset_index(drop=True)
            else:
                # 템플릿 생성 (한글로 변경)
                tmpl = [
                    {"Week_Start": week_str, "Assignee": me, "Type": "금주 실적", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "금주 실적", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "차주 계획", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "차주 계획", "Project": "-", "Content": "", "Status": "정상"},
                ]
                input_df = pd.DataFrame(tmpl)

            proj_list = ["-"] + list(st.session_state.promotions['프로모션명'].unique())
            
            edited_df = st.data_editor(
                input_df,
                column_config={
                    "Week_Start": None, "Assignee": None,
                    "Type": st.column_config.SelectboxColumn("구분", options=["금주 실적", "차주 계획", "이슈사항"], required=True),
                    "Content": st.column_config.TextColumn("내용", required=True, width="large"),
                    "Status": st.column_config.SelectboxColumn("상태", options=["정상", "지연", "중단"], required=True)
                },
                num_rows="dynamic", use_container_width=True
            )
            
            if st.button("💾 저장", type="primary"):
                to_save = edited_df[edited_df['Content'].str.strip() != ""].copy()
                if not to_save.empty:
                    to_save['Week_Start'] = week_str
                    to_save['Assignee'] = me
                    if 'Project' in to_save.columns: to_save['Project'] = to_save['Project'].fillna("-")
                    if 'Status' in to_save.columns: to_save['Status'] = to_save['Status'].fillna("정상")
                    
                    with st.spinner("저장 중..."):
                        if save_weekly_report_entry(to_save):
                            st.toast("저장되었습니다!", icon="✅")
                            safe_rerun()
                else:
                    st.warning("내용을 입력해주세요.")
        else:
            st.info("작성자를 먼저 선택해주세요.")

# ---------------------------------------------------------
# PAGE 3: 관리자 페이지
# ---------------------------------------------------------
elif page == "⚙️ 관리자 페이지":
    # 3.1 관리자 인증
    if not st.session_state.get('is_admin_unlocked', False):
        st.title("⚙️ 관리자 인증")
        with st.form("admin_login"):
            pw = st.text_input("관리자 암호", type="password")
            if st.form_submit_button("로그인"):
                if pw == "diageorcg":
                    st.session_state.is_admin_unlocked = True
                    st.session_state.draft_df = st.session_state.promotions.copy()
                    safe_rerun()
                else:
                    st.error("암호 오류")
    else:
        # 3.2 관리자 메인 화면
        c1, c2 = st.columns([2, 1])
        with c1:
            st.title("⚙️ 데이터 관리")
        with c2:
            st.markdown("######") # 간격
            if st.button("💾 저장", type="primary", use_container_width=True):
                with st.spinner("구글 시트에 저장 중..."):
                    if save_promotions(st.session_state.draft_df):
                        st.toast("✅ 저장 완료! 대시보드에 적용되었습니다.", icon="🎉")
        
        st.info("💡 아래에서 데이터를 수정(Draft)한 후, 우측 상단의 **'저장'** 버튼을 눌러야 구글 시트에 반영됩니다.")

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
        # 기능 4: 데이터 에디터 (수정) & 다운로드
        # -----------------------------------------------------
        st.subheader("✏️ 데이터 편집 (Draft)")
        
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

        if not edited_df.equals(st.session_state.draft_df):
            st.session_state.draft_df = edited_df

        st.divider()
        
        csv = st.session_state.draft_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 현재 데이터 CSV 다운로드", csv, "promotion_data.csv", "text/csv")

