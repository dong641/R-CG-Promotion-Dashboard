import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# PAGE 2: [업데이트] 프로젝트 간트차트 (디자인 개선)
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
            # 간트차트 디자인: 미니멀 & 가시성 개선
            fig_overview = px.timeline(
                projects_df, 
                x_start="Start", 
                x_end="End", 
                y="Project",
                color="Progress",
                color_continuous_scale="Teal", # 깔끔한 단색 계열
                range_color=[0, 100], # 0~100% 고정
                hover_data=["Owner", "Status"],
                text="Progress"
            )
            
            # 차트 스타일링 (미니멀)
            fig_overview.update_xaxes(
                side="top", 
                title_font=dict(size=12),
                tickformat="%b %d", # 'Mar 01' 형태로 간소화
                dtick="M1", # 1개월 단위
                showgrid=True,
                gridcolor='#f8f9fa', # 아주 연한 그리드
                zeroline=False
            )
            fig_overview.update_yaxes(
                autorange="reversed", 
                title="",
                showgrid=False,
                tickfont=dict(size=13, color="#333")
            )
            fig_overview.update_traces(
                texttemplate='%{text}%', 
                textposition='inside', 
                marker_line_width=0, # 테두리 제거로 플랫 디자인
                opacity=0.9,
                width=0.6 # 바 두께 슬림하게
            )
            fig_overview.update_layout(
                height=300 + (len(projects_df)*50),
                margin=dict(t=40, b=10, l=10, r=10),
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Segoe UI, Arial", size=12),
                coloraxis_showscale=False # 컬러바 숨김 (심플함 유지)
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

    # --- 2. 프로젝트 상세 (Detail - 디자인 개선) ---
    with tab_detail:
        # 프로젝트 선택
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
                # 라벨 가독성
                p_tasks['Label'] = p_tasks.apply(lambda x: f"[{x['Department']}] {x['Task']}", axis=1)
                p_tasks = p_tasks.sort_values(by=['Department', 'Start'], ascending=[True, True])

                # 파스텔 톤 색상 사용
                colors = px.colors.qualitative.Pastel

                fig_detail = px.timeline(
                    p_tasks,
                    x_start="Start", 
                    x_end="End", 
                    y="Label",
                    color="Department", 
                    color_discrete_sequence=colors, # 파스텔 컬러 적용
                    hover_data=["Task", "Progress", "Department"],
                    text="Progress"
                )
                
                # 상세 차트 스타일링 (미니멀)
                fig_detail.update_xaxes(
                    side="top", 
                    tickformat="%b %d", # 간소화 (Mar 01)
                    dtick="D7",  # 1주 단위
                    showgrid=True, 
                    gridwidth=1, 
                    gridcolor='#f8f9fa', # 매우 연한 그리드
                    zeroline=False
                )
                fig_detail.update_yaxes(
                    autorange="reversed", 
                    title="", 
                    showgrid=True,
                    gridcolor='#f8f9fa',
                    tickfont=dict(size=12, color='#555')
                )
                fig_detail.update_layout(
                    height=max(400, len(p_tasks) * 50), # 행 간격 여유 있게
                    margin=dict(t=60, b=20, l=10, r=10),
                    showlegend=True,
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", y=1.05, 
                        xanchor="left", x=0,
                        title=None, # 레전드 제목 제거
                        bgcolor='rgba(0,0,0,0)'
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family="Segoe UI, Arial", size=12)
                )
                # 바 스타일
                fig_detail.update_traces(
                    marker_line_width=0, 
                    width=0.6,
                    opacity=0.9, 
                    texttemplate='%{text}%', 
                    textposition='auto' # 공간 부족시 밖으로
                )

                # 마일스톤 (깔끔한 별)
                milestones = p_tasks[p_tasks['Milestone'] == 'Y']
                if not milestones.empty:
                    fig_detail.add_scatter(
                        x=milestones['End'], 
                        y=milestones['Label'], 
                        mode='markers',
                        marker=dict(symbol='star', size=14, color='#f1c40f', line=dict(width=0)), # 테두리 없는 금색 별
                        name='마일스톤',
                        showlegend=False
                    )
                
                st.plotly_chart(fig_detail, use_container_width=True)
            else:
            # [개선] 업무 관리 패널 (탭 분리)
            st.markdown("#### 📝 업무 관리 패널")
            
            manage_tab1, manage_tab2 = st.tabs(["➕ 새 업무 추가", "✏️ 리스트 수정/삭제"])
            
            # 1. 업무 추가
            with manage_tab1:
                with st.form("add_detail_task_form"):
                    col1, col2, col3 = st.columns([1, 2, 1])
                    # [수정] 부서 입력 방식 변경: Selectbox -> TextInput
                    t_dept = col1.text_input("부서", placeholder="팀명 입력 (예: 기획팀)")
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
                            # [수정] 부서 수정 방식 변경: SelectboxColumn -> TextColumn
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
