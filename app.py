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
# ttl=0 옵션은 캐시를 사용하지 않고 매번 최신 데이터를 가져온다는 뜻입니다.

def get_db_connection():
    # st.connection을 사용하여 구글 시트와 연결
    return st.connection("gsheets", type=GSheetsConnection)

def load_promotions():
    """구글 시트 'promotions' 워크시트에서 데이터 로드"""
    conn = get_db_connection()
    try:
        # 워크시트 이름이 정확해야 합니다.
        df = conn.read(worksheet="promotions", ttl=0)
        if df.empty: return create_default_promotions()
        
        # 전처리: 날짜 및 숫자 변환
        for col in ['시작일', '종료일']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        if '진척율' in df.columns:
            df['진척율'] = df['진척율'].astype(str).str.replace('%', '').str.strip()
            df['진척율'] = pd.to_numeric(df['진척율'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception:
        # 시트가 없거나 에러 발생 시 기본값 반환
        return create_default_promotions()

def save_promotions(df):
    """구글 시트 'promotions' 워크시트에 덮어쓰기 저장"""
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
        # 빈 데이터프레임 처리
        if df.empty: return create_empty_report_df()
        
        # 주차 정보 문자열 변환 (날짜 비교 오류 방지)
        if 'Week_Start' in df.columns:
            df['Week_Start'] = df['Week_Start'].astype(str)
        return df
    except:
        return create_empty_report_df()

def save_weekly_report_entry(new_data_df):
    """주간 업무 저장 (기존 데이터 로드 -> 병합 -> 업데이트)"""
    conn = get_db_connection()
    try:
        # 1. 기존 데이터 읽기
        try:
            existing_df = conn.read(worksheet="weekly_reports", ttl=0)
            if 'Week_Start' in existing_df.columns:
                existing_df['Week_Start'] = existing_df['Week_Start'].astype(str)
        except:
            existing_df = create_empty_report_df()

        # 2. 덮어쓰기 로직: 해당 주차(Week_Start) + 담당자(Assignee)의 기존 데이터 삭제
        if not new_data_df.empty:
            week_start = str(new_data_df['Week_Start'].iloc[0])
            assignee = new_data_df['Assignee'].iloc[0]
            
            if not existing_df.empty:
                # 기존 데이터에서 해당 작성자의 해당 주차 데이터만 제외하고 남김
                mask = ~((existing_df['Week_Start'] == week_start) & (existing_df['Assignee'] == assignee))
                existing_df = existing_df[mask]
        
        # 3. 새 데이터 병합
        final_df = pd.concat([existing_df, new_data_df], ignore_index=True)
        
        # 4. 저장
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
    page = st.radio("이동할 페이지", ["📊 대시보드", "📅 주간 업무 (PPP)", "⚙️ 관리자 페이지"])
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
    
    active_df = df[df['상태']!='완료']
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
    cfg = {"진척율": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)}
    st.dataframe(filtered_df, column_config=cfg, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# PAGE 2: 주간 업무 (PPP - 가시성 개선)
# ---------------------------------------------------------
elif page == "📅 주간 업무 (PPP)":
    st.title("📅 Weekly Business Review")
    
    # 날짜 선택
    col_date, col_view_opt = st.columns([1, 2])
    with col_date:
        pick_date = st.date_input("기준 날짜", datetime.date.today())
    
    start_week, end_week = get_week_range(pick_date)
    week_str = str(start_week)
    
    with col_view_opt:
        st.info(f"📆 **{start_week} ~ {end_week}** 주간 업무 보고")

    st.divider()

    # 탭 구성: 조회(Dashboard) vs 작성
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
            
            # 보기 모드 선택
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
                # 카드 그리드 레이아웃
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
                                        # 상태 아이콘
                                        icon = "🟢" if row['Status']=="정상" else "🟡" if row['Status']=="지연" else "🔴"
                                        # 프로젝트 태그 강조
                                        p_tag = f"**[{row['Project']}]**" if row['Project'] != "-" else ""
                                        
                                        st.markdown(f"{icon} {p_tag} {row['Content']}")

                            st.markdown("**✅ 금주 실적**")
                            render_ppp_section(p_df[p_df['Type'] == 'Progress'])
                            
                            st.divider()
                            st.markdown("**🗓️ 차주 계획**")
                            render_ppp_section(p_df[p_df['Type'] == 'Plans'])
                            
                            prob_df = p_df[p_df['Type'] == 'Problems']
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
            # 기존 데이터 로드 (수정을 위해)
            # 여기서는 최신 데이터를 불러와서 필터링
            full_data = load_weekly_reports()
            my_data = full_data[(full_data['Week_Start'] == week_str) & (full_data['Assignee'] == me)]
            
            if not my_data.empty:
                input_df = my_data.reset_index(drop=True)
            else:
                # 템플릿 생성
                tmpl = [
                    {"Week_Start": week_str, "Assignee": me, "Type": "Progress", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "Progress", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "Plans", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "Plans", "Project": "-", "Content": "", "Status": "정상"},
                ]
                input_df = pd.DataFrame(tmpl)

            proj_list = ["-"] + list(st.session_state.promotions['프로모션명'].unique())
            
            edited_df = st.data_editor(
                input_df,
                column_config={
                    "Week_Start": None, "Assignee": None,
                    "Type": st.column_config.SelectboxColumn("구분", options=["Progress", "Plans", "Problems"], required=True),
                    "Project": st.column_config.SelectboxColumn("관련 프로모션", options=proj_list, required=True),
                    "Content": st.column_config.TextColumn("내용", required=True, width="large"),
                    "Status": st.column_config.SelectboxColumn("상태", options=["정상", "지연", "중단"], required=True)
                },
                num_rows="dynamic", use_container_width=True
            )
            
            if st.button("💾 구글 시트에 저장하기", type="primary"):
                # 유효성 검사 (내용이 있는 행만 저장)
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
        c1, c2 = st.columns([2,1])
        c1.title("⚙️ 데이터 관리")
        if c2.button("💾 변경사항 구글 시트 저장", type="primary"):
            if save_promotions(st.session_state.draft_df):
                st.toast("저장되었습니다.")
        
        st.divider()
        st.subheader("✏️ 데이터 편집 (Draft)")
        edited = st.data_editor(st.session_state.draft_df, num_rows="dynamic", use_container_width=True)
        if not edited.equals(st.session_state.draft_df):
            st.session_state.draft_df = edited
