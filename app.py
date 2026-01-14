import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
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

def load_data(sheet_name, default_func):
    """범용 데이터 로드 함수 (TTL=0으로 최신 데이터 보장)"""
    conn = get_db_connection()
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df.empty: return default_func()
        return df
    except:
        return default_func()

def save_data(sheet_name, df):
    """범용 데이터 저장 함수"""
    conn = get_db_connection()
    try:
        conn.update(worksheet=sheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"저장 실패: {e}")
        return False

# --- 데이터 생성 및 전처리 함수들 ---
def create_default_promotions():
    return pd.DataFrame([
        {"프로모션명": "2024 봄 정기 세일", "채널": "Off Trade", "담당자": "김철수", "상태": "진행중", "진척율": 75, "시작일": datetime.date(2024, 3, 1), "종료일": datetime.date(2024, 3, 15)},
        {"프로모션명": "신규 회원 가입 이벤트", "채널": "On Trade", "담당자": "이영희", "상태": "기획단계", "진척율": 20, "시작일": datetime.date(2024, 4, 1), "종료일": datetime.date(2024, 4, 30)},
    ])

def create_empty_report_df():
    return pd.DataFrame(columns=["Week_Start", "Assignee", "Type", "Project", "Content", "Status"])

def create_default_project_tasks():
    """간트차트용 상세 태스크 데이터 (별도 관리)"""
    return pd.DataFrame([
        {"Project": "2024 봄 정기 세일", "Task": "기획안 확정", "Department": "기획팀", "Start": "2024-03-01", "End": "2024-03-05", "Progress": 100, "Milestone": "Y"},
        {"Project": "2024 봄 정기 세일", "Task": "디자인 시안 제작", "Department": "디자인팀", "Start": "2024-03-06", "End": "2024-03-10", "Progress": 60, "Milestone": "N"},
        {"Project": "2024 봄 정기 세일", "Task": "개발 및 QA", "Department": "개발팀", "Start": "2024-03-11", "End": "2024-03-15", "Progress": 0, "Milestone": "Y"},
        {"Project": "신규 회원 가입 이벤트", "Task": "프로모션 페이지 기획", "Department": "기획팀", "Start": "2024-04-01", "End": "2024-04-10", "Progress": 20, "Milestone": "N"}
    ])

# ---------------------------------------------------------
# 데이터 로드 로직 (세션 캐싱 및 전처리)
# ---------------------------------------------------------
def load_all_data():
    # 1. 메인 프로모션 데이터
    df_promo = load_data("promotions", create_default_promotions)
    for col in ['시작일', '종료일']:
        if col in df_promo.columns: df_promo[col] = pd.to_datetime(df_promo[col], errors='coerce').dt.date
    if '진척율' in df_promo.columns:
        df_promo['진척율'] = pd.to_numeric(df_promo['진척율'].astype(str).str.replace('%',''), errors='coerce').fillna(0).astype(int)
    st.session_state.promotions = df_promo

    # 2. 프로젝트 상세 태스크 데이터 (독립적 로드)
    df_tasks = load_data("project_tasks", create_default_project_tasks)
    # 날짜 전처리 (Plotly 호환용)
    for col in ['Start', 'End']:
        if col in df_tasks.columns: df_tasks[col] = pd.to_datetime(df_tasks[col], errors='coerce').dt.date
    # 숫자 전처리
    if 'Progress' in df_tasks.columns:
        df_tasks['Progress'] = pd.to_numeric(df_tasks['Progress'], errors='coerce').fillna(0).astype(int)
        
    st.session_state.project_tasks = df_tasks

# ---------------------------------------------------------
# 메인 앱 초기화
# ---------------------------------------------------------
st.set_page_config(page_title="프로모션 통합 시스템 (Gantt)", page_icon="🧩", layout="wide")

if 'promotions' not in st.session_state:
    load_all_data()
if 'is_global_unlocked' not in st.session_state:
    st.session_state.is_global_unlocked = False

# ---------------------------------------------------------
# 1. 로그인
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
    page = st.radio("이동할 페이지", ["📊 대시보드", "🧩 프로젝트 간트차트", "📅 주간 업무 (PPP)", "⚙️ 관리자 페이지"])
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
    
    # 지표
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체 프로모션", f"{len(df)}건")
    c2.metric("진행중", f"{len(df[df['상태']=='진행중'])}건")
    c3.metric("완료", f"{len(df[df['상태']=='완료'])}건")
    active_df = df[df['상태'] != '완료']
    avg_prog = active_df['진척율'].mean() if not active_df.empty else 0
    c4.metric("평균 달성률(완료제외)", f"{avg_prog:.1f}%")

    st.divider()
    
    # 탭별 리스트
    df_active = df[df['상태'] != '완료']
    df_completed = df[df['상태'] == '완료']
    
    t1, t2, t3 = st.tabs([f"🔥 진행 중 ({len(df_active)})", f"✅ 완료됨 ({len(df_completed)})", "📑 전체 목록"])
    cfg = {"진척율": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)}
    
    with t1: st.dataframe(df_active, column_config=cfg, use_container_width=True, hide_index=True)
    with t2: st.dataframe(df_completed, column_config=cfg, use_container_width=True, hide_index=True)
    with t3: st.dataframe(df, column_config=cfg, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# PAGE 2: [업데이트] 프로젝트 간트차트
# ---------------------------------------------------------
elif page == "🧩 프로젝트 간트차트":
    st.title("🧩 프로젝트 관리 (Gantt Chart)")
    st.caption("프로모션별 상세 일정과 마일스톤을 관리합니다. 데이터는 별도의 시트(project_tasks)에 저장됩니다.")
    
    # 데이터 준비
    tasks_df = st.session_state.project_tasks.copy()
    promos_df = st.session_state.promotions.copy()
    
    # 날짜 형식 보장
    tasks_df['Start'] = pd.to_datetime(tasks_df['Start'])
    tasks_df['End'] = pd.to_datetime(tasks_df['End'])
    promos_df['시작일'] = pd.to_datetime(promos_df['시작일'])
    promos_df['종료일'] = pd.to_datetime(promos_df['종료일'])

    tab_overview, tab_detail = st.tabs(["🌐 전체 현황 (Overview)", "🔍 프로젝트 상세 관리 (Detail)"])

    # --- 1. 전체 프로젝트 현황 (Overview) ---
    with tab_overview:
        if not promos_df.empty:
            # 전체 프로젝트 타임라인
            fig_overview = px.timeline(
                promos_df, 
                x_start="시작일", 
                x_end="종료일", 
                y="프로모션명",
                color="진척율",
                color_continuous_scale="Teal", # 색상 변경
                hover_data=["담당자", "상태"],
                text="진척율"
            )
            # [요청 반영] 날짜 위로 올리기 및 가시성 개선
            fig_overview.update_xaxes(side="top", title_font=dict(size=14, color='gray'))
            fig_overview.update_yaxes(autorange="reversed", title="") # Y축 제목 제거
            fig_overview.update_traces(textposition='inside', marker_line_color='rgb(8,48,107)', marker_line_width=1.5, opacity=0.9)
            fig_overview.update_layout(
                height=400 + (len(promos_df)*40),
                margin=dict(t=50, b=20, l=20, r=20),
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Arial", size=12)
            )
            st.plotly_chart(fig_overview, use_container_width=True)
        else:
            st.info("등록된 프로모션이 없습니다.")

    # --- 2. 프로젝트 상세 (Detail - UX 개선) ---
    with tab_detail:
        # 프로젝트 선택 (모바일 친화적 Selectbox)
        project_list = promos_df['프로모션명'].unique()
        selected_project = st.selectbox("📂 프로젝트 선택", project_list, label_visibility="collapsed", placeholder="프로젝트를 선택하세요")
        
        if selected_project:
            # 해당 프로젝트의 태스크 필터링
            p_tasks = tasks_df[tasks_df['Project'] == selected_project].sort_values(by='Start')
            
            # 1) 요약 지표 (카드형)
            st.markdown("######") # 간격
            col_m1, col_m2, col_m3 = st.columns(3)
            
            total_tasks = len(p_tasks)
            milestones_cnt = len(p_tasks[p_tasks['Milestone'] == 'Y'])
            # 프로젝트 평균 진행률 (태스크 기준)
            task_prog = int(p_tasks['Progress'].mean()) if not p_tasks.empty else 0
            
            col_m1.metric("총 태스크", f"{total_tasks}개")
            col_m2.metric("마일스톤", f"{milestones_cnt}개")
            col_m3.metric("상세 진행률", f"{task_prog}%")
            
            st.divider()

            # 2) 상세 간트차트 (가시성 최적화)
            st.markdown("##### 📅 일정 타임라인")
            
            if not p_tasks.empty:
                fig_detail = px.timeline(
                    p_tasks,
                    x_start="Start", 
                    x_end="End", 
                    y="Department",
                    color="Department", # 부서별 색상 구분
                    hover_data=["Task", "Progress"],
                    text="Task",
                    range_x=[p_tasks['Start'].min() - datetime.timedelta(days=2), p_tasks['End'].max() + datetime.timedelta(days=5)]
                )
                
                # [요청 반영] 날짜 위로, 디자인 개선
                fig_detail.update_xaxes(
                    side="top", 
                    tickformat="%m-%d",
                    dtick="D7", # 1주 단위 눈금
                    showgrid=True, 
                    gridwidth=1, 
                    gridcolor='LightGray'
                )
                fig_detail.update_yaxes(autorange="reversed", title="", showgrid=True, gridcolor='LightGray')
                fig_detail.update_layout(
                    height=300 + (len(p_tasks['Department'].unique()) * 50),
                    margin=dict(t=60, b=20, l=20, r=20),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="right", x=1),
                    plot_bgcolor='white'
                )
                fig_detail.update_traces(marker_line_width=1, opacity=0.8, textposition='inside')

                # 마일스톤 (별 표시)
                milestones = p_tasks[p_tasks['Milestone'] == 'Y']
                if not milestones.empty:
                    fig_detail.add_scatter(
                        x=milestones['End'], 
                        y=milestones['Department'], 
                        mode='markers+text',
                        marker=dict(symbol='star', size=18, color='gold', line=dict(width=1, color='DarkOrange')),
                        text=['★' for _ in range(len(milestones))],
                        textposition="top center",
                        name='마일스톤',
                        showlegend=False
                    )
                
                st.plotly_chart(fig_detail, use_container_width=True)
            else:
                st.info("등록된 상세 일정이 없습니다. 아래에서 추가해주세요.")

            st.divider()

            # 3) 태스크 관리 (Data Editor - 모바일 친화적)
            st.markdown("##### 📝 태스크 리스트 및 편집")
            st.caption("아래 표에서 직접 수정하거나 행을 추가(+)할 수 있습니다. 수정 후 우측 상단의 '변경사항 저장'을 누르세요.")

            # 편집용 데이터프레임 (프로젝트명 제외하고 보여줌 - 깔끔하게)
            edit_df = p_tasks.drop(columns=['Project']).reset_index(drop=True)
            
            # 컬럼 설정
            column_config = {
                "Department": st.column_config.SelectboxColumn("부서", options=["기획팀", "디자인팀", "개발팀", "영업팀", "마케팅팀", "기타"], required=True, width="small"),
                "Task": st.column_config.TextColumn("업무명", required=True, width="medium"),
                "Start": st.column_config.DateColumn("시작일", width="small"),
                "End": st.column_config.DateColumn("종료일", width="small"),
                "Progress": st.column_config.ProgressColumn("진행률", min_value=0, max_value=100, format="%d%%", width="small"),
                "Milestone": st.column_config.CheckboxColumn("마일스톤", width="small")
            }

            edited_tasks = st.data_editor(
                edit_df,
                column_config=column_config,
                num_rows="dynamic", # 행 추가/삭제 가능
                use_container_width=True,
                key=f"editor_{selected_project}"
            )

            # 저장 로직 (Project 컬럼 다시 붙여서 전체 병합)
            if st.button("💾 변경사항 저장 (Google Sheet)", type="primary", use_container_width=True):
                # 1. 현재 프로젝트를 제외한 나머지 데이터 보존
                other_projects_tasks = tasks_df[tasks_df['Project'] != selected_project]
                
                # 2. 현재 프로젝트의 수정된 데이터 준비
                if not edited_tasks.empty:
                    edited_tasks['Project'] = selected_project # 프로젝트명 다시 부여
                    # 날짜 문자열 변환
                    edited_tasks['Start'] = edited_tasks['Start'].astype(str)
                    edited_tasks['End'] = edited_tasks['End'].astype(str)
                    
                    # 3. 데이터 병합
                    final_tasks = pd.concat([other_projects_tasks, edited_tasks], ignore_index=True)
                else:
                    final_tasks = other_projects_tasks # 모든 태스크 삭제 시

                # 4. 저장
                if save_data("project_tasks", final_tasks):
                    st.session_state.project_tasks = final_tasks # 세션 업데이트
                    st.toast("✅ 태스크가 성공적으로 저장되었습니다!")
                    safe_rerun()

# ---------------------------------------------------------
# PAGE 3: 주간 업무 (PPP)
# ---------------------------------------------------------
elif page == "📅 주간 업무 (PPP)":
    st.title("📅 Weekly Business Review")
    
    col_date, col_view_opt = st.columns([1, 2])
    with col_date:
        pick_date = st.date_input("기준 날짜", datetime.date.today())
    s_week, e_week = get_week_range(pick_date)
    week_str = str(s_week)
    
    with col_view_opt:
        st.info(f"📆 **{s_week} ~ {e_week}** 주간 업무 보고")

    st.divider()

    tab_view, tab_write = st.tabs(["📋 전체 보고서 조회", "✍️ 내 보고서 작성"])

    # [조회]
    with tab_view:
        with st.spinner("로딩 중..."):
            report_df = load_data("weekly_reports", create_empty_report_df)
            if 'Week_Start' in report_df.columns: report_df['Week_Start'] = report_df['Week_Start'].astype(str)
            
        curr_reports = report_df[report_df['Week_Start'] == week_str]
        
        if curr_reports.empty:
            st.warning("제출된 보고서가 없습니다.")
        else:
            assignees = sorted(curr_reports['Assignee'].unique())
            view_mode = st.radio("보기 방식", ["카드 뷰", "테이블 뷰"], horizontal=True, label_visibility="collapsed")
            
            if view_mode == "테이블 뷰":
                st.dataframe(curr_reports, use_container_width=True, hide_index=True)
            else:
                cols = st.columns(2)
                for idx, person in enumerate(assignees):
                    p_df = curr_reports[curr_reports['Assignee'] == person]
                    with cols[idx % 2]:
                        with st.container(border=True):
                            st.markdown(f"#### 👤 {person}")
                            
                            def render_ppp(type_val, icon, label):
                                sub = p_df[p_df['Type'] == type_val]
                                st.markdown(f"**{icon} {label}**")
                                if sub.empty: st.caption("-")
                                else:
                                    for _, r in sub.iterrows():
                                        s = "🟢" if r['Status']=="정상" else "🟡" if r['Status']=="지연" else "🔴"
                                        tag = f"**[{r['Project']}]**" if r['Project'] != "-" else ""
                                        st.markdown(f"{s} {tag} {r['Content']}")
                            
                            render_ppp("금주 실적", "✅", "금주 실적")
                            st.write("")
                            render_ppp("차주 계획", "🗓️", "차주 계획")
                            if not p_df[p_df['Type'] == '이슈사항'].empty:
                                st.divider()
                                render_ppp("이슈사항", "⚠️", "이슈 사항")

    # [작성]
    with tab_write:
        st.markdown("##### 📝 보고서 작성")
        managers = list(st.session_state.promotions['담당자'].unique()) if '담당자' in st.session_state.promotions.columns else []
        if "기타" not in managers: managers.append("기타")
        
        c_sel, _ = st.columns([1, 2])
        me = c_sel.selectbox("작성자 선택", managers, key="writer_select")
        if me == "기타": me = c_sel.text_input("이름 입력")
        
        if me:
            full_data = load_data("weekly_reports", create_empty_report_df)
            if 'Week_Start' in full_data.columns: full_data['Week_Start'] = full_data['Week_Start'].astype(str)
            my_data = full_data[(full_data['Week_Start'] == week_str) & (full_data['Assignee'] == me)]
            
            if not my_data.empty:
                input_df = my_data.reset_index(drop=True)
            else:
                tmpl = [
                    {"Week_Start": week_str, "Assignee": me, "Type": "금주 실적", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "금주 실적", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "차주 계획", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "차주 계획", "Project": "-", "Content": "", "Status": "정상"},
                ]
                input_df = pd.DataFrame(tmpl)
            
            proj_ops = ["-"] + list(st.session_state.promotions['프로모션명'].unique())
            
            edited_df = st.data_editor(
                input_df,
                column_config={
                    "Week_Start": None, "Assignee": None,
                    "Type": st.column_config.SelectboxColumn("구분", options=["금주 실적", "차주 계획", "이슈사항"], required=True),
                    "Project": st.column_config.SelectboxColumn("관련 프로모션", options=proj_ops, required=True),
                    "Content": st.column_config.TextColumn("내용", required=True, width="large"),
                    "Status": st.column_config.SelectboxColumn("상태", options=["정상", "지연", "중단"], required=True)
                },
                num_rows="dynamic", use_container_width=True
            )
            
            if st.button("💾 저장", type="primary"):
                new_entry = edited_df[edited_df['Content'].str.strip() != ""].copy()
                if not new_entry.empty:
                    new_entry['Week_Start'] = week_str
                    new_entry['Assignee'] = me
                    if 'Project' in new_entry.columns: new_entry['Project'] = new_entry['Project'].fillna("-")
                    if 'Status' in new_entry.columns: new_entry['Status'] = new_entry['Status'].fillna("정상")
                    
                    # 덮어쓰기 로직
                    mask = ~((full_data['Week_Start'] == week_str) & (full_data['Assignee'] == me))
                    final_df = pd.concat([full_data[mask], new_entry], ignore_index=True)
                    
                    if save_data("weekly_reports", final_df):
                        st.toast("저장되었습니다!", icon="✅")
                        safe_rerun()
                else:
                    st.warning("내용이 없습니다.")
        else:
            st.info("작성자를 먼저 선택해주세요.")

# ---------------------------------------------------------
# PAGE 4: 관리자 페이지
# ---------------------------------------------------------
elif page == "⚙️ 관리자 페이지":
    if not st.session_state.get('is_admin_unlocked', False):
        st.title("⚙️ 관리자 인증")
        with st.form("l"):
            p = st.text_input("암호", type="password")
            if st.form_submit_button("로그인"):
                if p == "diageorcg":
                    st.session_state.is_admin_unlocked = True
                    # 관리자용 Draft 초기화
                    st.session_state.draft_df = st.session_state.promotions.copy()
                    safe_rerun()
                else: st.error("오류")
    else:
        st.title("⚙️ 데이터 관리")
        
        if 'draft_df' not in st.session_state:
            st.session_state.draft_df = st.session_state.promotions.copy()
            
        c1, c2 = st.columns([2,1])
        if c2.button("💾 변경사항 저장", type="primary"):
            with st.spinner("저장 중..."):
                if save_data("promotions", st.session_state.draft_df):
                    st.session_state.promotions = st.session_state.draft_df.copy()
                    st.toast("저장 완료")
        
        st.subheader("데이터 편집 (Promotions)")
        edited = st.data_editor(st.session_state.draft_df, num_rows="dynamic", use_container_width=True)
        if not edited.equals(st.session_state.draft_df):
            st.session_state.draft_df = edited
            
        st.divider()
        
        # CSV 관리
        st.subheader("📂 CSV 관리")
        col_csv1, col_csv2 = st.columns(2)
        with col_csv1:
            csv = st.session_state.draft_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("다운로드", csv, "promo_data.csv", "text/csv")
        with col_csv2:
            uploaded_file = st.file_uploader("업로드 (덮어쓰기)", type=["csv"], label_visibility="collapsed")
            if uploaded_file and st.button("적용"):
                try:
                    new_df = pd.read_csv(uploaded_file)
                    st.session_state.draft_df = new_df
                    st.success("CSV 로드됨. 상단 저장 버튼을 눌러 확정하세요.")
                    safe_rerun()
                except Exception as e:
                    st.error(f"오류: {e}")
