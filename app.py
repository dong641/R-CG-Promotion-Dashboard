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
    """범용 데이터 로드 함수"""
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

def create_default_projects():
    """프로젝트 관리용 별도 데이터"""
    return pd.DataFrame([
        {"Project": "신제품 런칭 프로젝트", "Owner": "박팀장", "Status": "진행중", "Progress": 45, "Start": datetime.date(2024, 3, 1), "End": datetime.date(2024, 5, 31)},
        {"Project": "웹사이트 리뉴얼", "Owner": "최대리", "Status": "기획", "Progress": 10, "Start": datetime.date(2024, 4, 1), "End": datetime.date(2024, 6, 30)},
    ])

def create_empty_report_df():
    return pd.DataFrame(columns=["Week_Start", "Assignee", "Type", "Project", "Content", "Status"])

def create_default_project_tasks():
    """간트차트용 상세 태스크 데이터"""
    return pd.DataFrame([
        {"Project": "신제품 런칭 프로젝트", "Task": "시장 조사 완료", "Department": "기획팀", "Start": "2024-03-01", "End": "2024-03-10", "Progress": 100, "Milestone": "Y"},
        {"Project": "신제품 런칭 프로젝트", "Task": "패키지 디자인", "Department": "디자인팀", "Start": "2024-03-11", "End": "2024-03-25", "Progress": 60, "Milestone": "N"},
        {"Project": "신제품 런칭 프로젝트", "Task": "시제품 생산", "Department": "생산팀", "Start": "2024-03-26", "End": "2024-04-15", "Progress": 0, "Milestone": "Y"},
        {"Project": "웹사이트 리뉴얼", "Task": "메인 페이지 기획", "Department": "기획팀", "Start": "2024-04-01", "End": "2024-04-15", "Progress": 20, "Milestone": "N"}
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

    # 2. 프로젝트 목록 데이터
    df_projects = load_data("projects", create_default_projects)
    for col in ['Start', 'End']:
        if col in df_projects.columns: df_projects[col] = pd.to_datetime(df_projects[col], errors='coerce').dt.date
    if 'Progress' in df_projects.columns:
        df_projects['Progress'] = pd.to_numeric(df_projects['Progress'], errors='coerce').fillna(0).astype(int)
    st.session_state.projects = df_projects

    # 3. 프로젝트 상세 태스크 데이터
    df_tasks = load_data("project_tasks", create_default_project_tasks)
    for col in ['Start', 'End']:
        if col in df_tasks.columns: df_tasks[col] = pd.to_datetime(df_tasks[col], errors='coerce').dt.date
    if 'Progress' in df_tasks.columns:
        df_tasks['Progress'] = pd.to_numeric(df_tasks['Progress'], errors='coerce').fillna(0).astype(int)
    st.session_state.project_tasks = df_tasks

# ---------------------------------------------------------
# 메인 앱 초기화
# ---------------------------------------------------------
st.set_page_config(page_title="프로모션 통합 시스템 (Dark)", page_icon="🧩", layout="wide")

# [디자인] 다크 모드 CSS 강제 적용
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0e1117; color: #fafafa; }
    [data-testid="stSidebar"] { background-color: #262730; }
    .stTextInput > div > div > input { color: #ffffff; }
    .stSelectbox > div > div > div { color: #ffffff; }
    h1, h2, h3, h4, h5, h6, p, label { color: #ffffff !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    .streamlit-expanderHeader { background-color: #262730; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

if 'promotions' not in st.session_state:
    load_all_data()

# ---------------------------------------------------------
# 사이드바
# ---------------------------------------------------------
with st.sidebar:
    st.title("메뉴")
    page = st.radio("이동할 페이지", ["📊 대시보드", "🧩 프로젝트 간트차트", "📅 주간 업무 (PPP)", "⚙️ 관리자 페이지"])
    st.divider()
    # 로그아웃 버튼은 관리자 페이지의 잠금을 푸는 용도로만 사용됨 (전체 로그인은 없음)
    if st.button("🚪 관리자 로그아웃"):
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
# PAGE 2: 프로젝트 간트차트 (디자인 개선 & 다크모드 대응)
# ---------------------------------------------------------
elif page == "🧩 프로젝트 간트차트":
    st.title("🧩 프로젝트 관리 (Gantt Chart)")
    st.caption("프로젝트 일정과 마일스톤을 시각적으로 관리합니다.")
    
    # 데이터 준비
    projects_df = st.session_state.projects.copy()
    tasks_df = st.session_state.project_tasks.copy()
    
    # 날짜 형식 보장
    for df_temp in [projects_df, tasks_df]:
        if not df_temp.empty:
            df_temp['Start'] = pd.to_datetime(df_temp['Start'])
            df_temp['End'] = pd.to_datetime(df_temp['End'])

    # 탭 구성
    tab_overview, tab_detail = st.tabs(["🌐 전체 현황 (Overview)", "🔍 프로젝트 상세 (Detail)"])

    # --- 1. 전체 프로젝트 현황 (Overview) ---
    with tab_overview:
        col_header, col_action = st.columns([3, 1])
        with col_header:
            st.markdown("##### 📌 전체 프로젝트 마스터 플랜")
        
        if not projects_df.empty:
            # 간트차트 디자인: 다크 모드 최적화
            fig_overview = px.timeline(
                projects_df, 
                x_start="Start", 
                x_end="End", 
                y="Project",
                color="Progress",
                color_continuous_scale="Teal",
                range_color=[0, 100],
                hover_data=["Owner", "Status"],
                text="Progress",
                template="plotly_dark" # 다크 테마 적용
            )
            
            fig_overview.update_xaxes(
                side="top", 
                title_font=dict(size=12, color='#ddd'),
                tickformat="%b %d",
                dtick="M1",
                showgrid=True,
                gridcolor='#333', # 어두운 그리드
                zeroline=False
            )
            fig_overview.update_yaxes(
                autorange="reversed", 
                title="",
                showgrid=False,
                tickfont=dict(size=13, color="#eee")
            )
            fig_overview.update_traces(
                texttemplate='%{text}%', 
                textposition='inside', 
                marker_line_width=0,
                opacity=0.9,
                width=0.6
            )
            fig_overview.update_layout(
                height=300 + (len(projects_df)*50),
                margin=dict(t=40, b=10, l=10, r=10),
                plot_bgcolor='#0e1117', # 앱 배경과 동일하게
                paper_bgcolor='#0e1117',
                font=dict(family="Segoe UI, Arial", size=12),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_overview, use_container_width=True)
        else:
            st.info("등록된 프로젝트가 없습니다. 아래에서 생성해주세요.")

        st.divider()
        
        # 프로젝트 생성/삭제
        with st.expander("🛠️ 프로젝트 관리 (생성/삭제)", expanded=False):
            col_add, col_del = st.columns(2)
            
            with col_add:
                st.markdown("**➕ 새 프로젝트 생성**")
                with st.form("new_project_form"):
                    np_name = st.text_input("프로젝트명")
                    np_owner = st.text_input("PM (책임자)")
                    c1, c2 = st.columns(2)
                    np_start = c1.date_input("시작일", datetime.date.today())
                    np_end = c2.date_input("종료일", datetime.date.today() + datetime.timedelta(days=30))
                    
                    if st.form_submit_button("프로젝트 생성", type="primary"):
                        if np_name:
                            new_p = pd.DataFrame([{
                                "Project": np_name, "Owner": np_owner, "Status": "준비", 
                                "Progress": 0, "Start": str(np_start), "End": str(np_end)
                            }])
                            updated_projects = pd.concat([st.session_state.projects, new_p], ignore_index=True)
                            if save_data("projects", updated_projects):
                                st.session_state.projects = updated_projects
                                st.success(f"'{np_name}' 생성 완료!")
                                safe_rerun()
                        else:
                            st.error("프로젝트명을 입력하세요.")

            with col_del:
                st.markdown("**🗑️ 프로젝트 삭제**")
                if not projects_df.empty:
                    del_target = st.selectbox("삭제할 프로젝트", projects_df['Project'].unique())
                    if st.button("삭제 실행", type="secondary"):
                        updated_projects = st.session_state.projects[st.session_state.projects['Project'] != del_target]
                        if save_data("projects", updated_projects):
                            st.session_state.projects = updated_projects
                            st.success(f"삭제 완료!")
                            safe_rerun()

    # --- 2. 프로젝트 상세 (Detail - 다크 모드) ---
    with tab_detail:
        p_list = projects_df['Project'].unique() if not projects_df.empty else []
        col_sel, col_info = st.columns([1, 2])
        with col_sel:
            selected_project = st.selectbox("📂 프로젝트 선택", p_list, label_visibility="collapsed")
        
        if selected_project:
            p_info = projects_df[projects_df['Project'] == selected_project].iloc[0]
            with col_info:
                st.caption(f"**PM:** {p_info['Owner']}  |  **기간:** {p_info['Start'].strftime('%Y.%m.%d')} ~ {p_info['End'].strftime('%Y.%m.%d')}")

            p_tasks = tasks_df[tasks_df['Project'] == selected_project].sort_values(by=['Department', 'Start'])
            
            st.markdown("#### 📅 상세 타임라인")
            
            if not p_tasks.empty:
                p_tasks['Label'] = p_tasks.apply(lambda x: f"[{x['Department']}] {x['Task']}", axis=1)
                p_tasks = p_tasks.sort_values(by=['Department', 'Start'], ascending=[True, True])

                # 다크 모드용 파스텔 컬러
                colors = px.colors.qualitative.Pastel

                fig_detail = px.timeline(
                    p_tasks,
                    x_start="Start", 
                    x_end="End", 
                    y="Label",
                    color="Department", 
                    color_discrete_sequence=colors,
                    hover_data=["Task", "Progress", "Department"],
                    text="Progress",
                    template="plotly_dark" # 다크 테마
                )
                
                fig_detail.update_xaxes(
                    side="top", 
                    tickformat="%b %d",
                    dtick="D7",
                    showgrid=True, 
                    gridwidth=1, 
                    gridcolor='#333',
                    zeroline=False
                )
                fig_detail.update_yaxes(
                    autorange="reversed", 
                    title="", 
                    showgrid=True,
                    gridcolor='#333',
                    tickfont=dict(size=12, color='#eee')
                )
                fig_detail.update_layout(
                    height=max(400, len(p_tasks) * 50),
                    margin=dict(t=60, b=20, l=10, r=10),
                    showlegend=True,
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", y=1.05, 
                        xanchor="left", x=0,
                        title=None,
                        bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white')
                    ),
                    plot_bgcolor='#0e1117',
                    paper_bgcolor='#0e1117',
                    font=dict(family="Segoe UI, Arial", size=12)
                )
                fig_detail.update_traces(
                    marker_line_width=0, 
                    width=0.6,
                    opacity=0.9, 
                    texttemplate='%{text}%', 
                    textposition='auto'
                )

                milestones = p_tasks[p_tasks['Milestone'] == 'Y']
                if not milestones.empty:
                    fig_detail.add_scatter(
                        x=milestones['End'], 
                        y=milestones['Label'], 
                        mode='markers',
                        marker=dict(symbol='star', size=14, color='#f1c40f', line=dict(width=0)),
                        name='마일스톤',
                        showlegend=False
                    )
                
                st.plotly_chart(fig_detail, use_container_width=True)
            else:
                st.info("등록된 상세 일정이 없습니다.")

            st.divider()

            st.markdown("#### 📝 업무 관리 패널")
            manage_tab1, manage_tab2 = st.tabs(["➕ 새 업무 추가", "✏️ 리스트 수정/삭제"])
            
            # 1. 업무 추가
            with manage_tab1:
                with st.form("add_detail_task_form"):
                    col1, col2, col3 = st.columns([1, 2, 1])
                    t_dept = col1.text_input("부서", placeholder="팀명 입력")
                    t_name = col2.text_input("업무명")
                    t_prog = col3.slider("진행률", 0, 100, 0)
                    
                    col4, col5, col6 = st.columns([1, 1, 1])
                    t_start = col4.date_input("시작일", datetime.date.today())
                    t_end = col5.date_input("종료일", datetime.date.today() + datetime.timedelta(days=5))
                    t_mile = col6.checkbox("🚩 마일스톤 여부")
                    
                    st.write("") 
                    if st.form_submit_button("리스트에 추가", type="primary"):
                        if t_name and t_dept:
                            new_task = pd.DataFrame([{
                                "Project": selected_project,
                                "Task": t_name,
                                "Department": t_dept,
                                "Start": str(t_start),
                                "End": str(t_end),
                                "Progress": t_prog,
                                "Milestone": "Y" if t_mile else "N"
                            }])
                            updated_tasks = pd.concat([st.session_state.project_tasks, new_task], ignore_index=True)
                            if save_data("project_tasks", updated_tasks):
                                st.session_state.project_tasks = updated_tasks
                                st.toast("추가되었습니다!", icon="✅")
                                safe_rerun()
                        else:
                            st.warning("부서와 업무명을 모두 입력하세요.")

            # 2. 리스트 수정
            with manage_tab2:
                if not p_tasks.empty:
                    display_cols = ['Department', 'Task', 'Start', 'End', 'Progress', 'Milestone']
                    edit_source = p_tasks[display_cols].reset_index(drop=True)
                    
                    edited_tasks = st.data_editor(
                        edit_source,
                        column_config={
                            "Department": st.column_config.TextColumn("부서", width="small"),
                            "Task": st.column_config.TextColumn("업무명", width="large"),
                            "Start": st.column_config.DateColumn("시작", width="small"),
                            "End": st.column_config.DateColumn("종료", width="small"),
                            "Progress": st.column_config.NumberColumn("%", width="small"),
                            "Milestone": st.column_config.CheckboxColumn("★", width="small"),
                        },
                        num_rows="dynamic",
                        use_container_width=True,
                        key=f"editor_{selected_project}"
                    )
                    
                    if st.button("💾 수정사항 저장", type="primary"):
                        other_tasks = tasks_df[tasks_df['Project'] != selected_project]
                        if not edited_tasks.empty:
                            edited_tasks['Project'] = selected_project
                            edited_tasks['Start'] = edited_tasks['Start'].astype(str)
                            edited_tasks['End'] = edited_tasks['End'].astype(str)
                            final_tasks = pd.concat([other_tasks, edited_tasks], ignore_index=True)
                        else:
                            final_tasks = other_tasks
                            
                        if save_data("project_tasks", final_tasks):
                            st.session_state.project_tasks = final_tasks
                            st.toast("저장되었습니다!", icon="✅")
                            safe_rerun()
                else:
                    st.caption("수정할 데이터가 없습니다.")

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
