import streamlit as st
import pandas as pd
import datetime
import os

# ---------------------------------------------------------
# 파일 저장소 설정
# ---------------------------------------------------------
DATA_FILE = "promotion_data.csv"
WEEKLY_REPORT_FILE = "weekly_reports_v2.csv" # 새로운 포맷의 파일 사용

# ---------------------------------------------------------
# 유틸리티 함수
# ---------------------------------------------------------
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def get_week_range(date_obj):
    """선택한 날짜가 속한 주의 월요일과 일요일을 반환"""
    start = date_obj - datetime.timedelta(days=date_obj.weekday())
    end = start + datetime.timedelta(days=6)
    return start, end

# ---------------------------------------------------------
# 데이터 로드/저장 함수
# ---------------------------------------------------------
def load_promotions():
    """프로모션 데이터 로드"""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            for col in ['시작일', '종료일']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
            if '진척율' in df.columns:
                df['진척율'] = df['진척율'].astype(str).str.replace('%', '').str.strip()
                df['진척율'] = pd.to_numeric(df['진척율'], errors='coerce').fillna(0).astype(int)
            return df
        except:
            return create_default_promotions()
    else:
        return create_default_promotions()

def create_default_promotions():
    return pd.DataFrame([
        {"프로모션명": "2024 봄 정기 세일", "채널": "Off Trade", "담당자": "김철수", "상태": "진행중", "진척율": 75, "시작일": datetime.date(2024, 3, 1), "종료일": datetime.date(2024, 3, 15)},
        {"프로모션명": "신규 회원 가입 이벤트", "채널": "On Trade", "담당자": "이영희", "상태": "기획단계", "진척율": 20, "시작일": datetime.date(2024, 4, 1), "종료일": datetime.date(2024, 4, 30)},
        {"프로모션명": "여름 바캉스 특가", "채널": "Off Trade", "담당자": "박민수", "상태": "대기", "진척율": 0, "시작일": datetime.date(2024, 6, 1), "종료일": datetime.date(2024, 8, 31)},
        {"프로모션명": "설날 효도 선물전", "채널": "On Trade", "담당자": "정수진", "상태": "완료", "진척율": 100, "시작일": datetime.date(2024, 1, 15), "종료일": datetime.date(2024, 2, 9)},
    ])

def save_promotions(df):
    try:
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        st.session_state.promotions = df.copy()
        return True
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False

def load_weekly_reports():
    """주간 업무 리포트 로드 (PPP 방식)"""
    if os.path.exists(WEEKLY_REPORT_FILE):
        try:
            df = pd.read_csv(WEEKLY_REPORT_FILE, dtype={'Week_Start': str})
            return df
        except:
            return create_empty_report_df()
    else:
        return create_empty_report_df()

def create_empty_report_df():
    # PPP 프레임워크에 맞춘 컬럼 구조
    return pd.DataFrame(columns=[
        "Week_Start", "Assignee", "Type", "Project", "Content", "Status"
    ])

def save_weekly_report_entry(new_data_df):
    """주간 업무 저장 (덮어쓰기 및 추가)"""
    try:
        if os.path.exists(WEEKLY_REPORT_FILE):
            existing_df = pd.read_csv(WEEKLY_REPORT_FILE, dtype={'Week_Start': str})
        else:
            existing_df = create_empty_report_df()
        
        # 신규 데이터 저장 (기존 파일에 append 하는 방식이 아니라, 해당 주차/담당자의 데이터를 교체하는 로직이 더 복잡하므로 여기선 Append 후 중복관리는 UI에서 처리하거나 단순 Append)
        # 벤치마킹 Case: 보통 DB를 쓰지만 CSV 환경이므로, 
        # "해당 주차 + 해당 담당자"의 기존 데이터를 삭제하고 새로 넣는 것이 깔끔함.
        
        week_start = new_data_df['Week_Start'].iloc[0]
        assignee = new_data_df['Assignee'].iloc[0]
        
        # 기존 데이터에서 해당 주차+담당자 데이터 제거
        existing_df = existing_df[~((existing_df['Week_Start'] == week_start) & (existing_df['Assignee'] == assignee))]
        
        # 새 데이터 병합
        final_df = pd.concat([existing_df, new_data_df], ignore_index=True)
        final_df.to_csv(WEEKLY_REPORT_FILE, index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        st.error(f"리포트 저장 실패: {e}")
        return False

# ---------------------------------------------------------
# 초기화 및 설정
# ---------------------------------------------------------
st.set_page_config(page_title="프로모션 통합 시스템", page_icon="🔒", layout="wide")

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
# 사이드바 메뉴
# ---------------------------------------------------------
with st.sidebar:
    st.title("메뉴")
    page = st.radio("이동할 페이지", ["📊 대시보드", "📅 주간 업무 (WBR)", "⚙️ 관리자 페이지"])
    st.divider()
    if st.button("🚪 로그아웃"):
        st.session_state.is_global_unlocked = False
        st.session_state.is_admin_unlocked = False
        safe_rerun()

# ---------------------------------------------------------
# PAGE 1: 대시보드 (View Only)
# ---------------------------------------------------------
if page == "📊 대시보드":
    st.title("📊 프로모션 현황 대시보드")
    df = st.session_state.promotions
    
    # 핵심 지표
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체 프로모션", f"{len(df)}건")
    c2.metric("진행중", f"{len(df[df['상태']=='진행중'])}건")
    completed = len(df[df['상태']=='완료'])
    c3.metric("완료", f"{completed}건")
    
    active_df = df[df['상태']!='완료']
    avg_prog = active_df['진척율'].mean() if not active_df.empty else 0
    c4.metric("진행중 평균 달성률", f"{avg_prog:.1f}%")

    st.divider()
    
    # 필터링
    with st.expander("🔍 상세 필터", expanded=False):
        f_cols = st.columns(3)
        filtered_df = df.copy()
        cols = [c for c in df.columns if c not in ['진척율', '시작일', '종료일']]
        for i, col in enumerate(cols):
            with f_cols[i%3]:
                uniqs = sorted(filtered_df[col].astype(str).unique())
                sel = st.multiselect(col, uniqs, key=f"d_{col}")
                if sel: filtered_df = filtered_df[filtered_df[col].astype(str).isin(sel)]
    
    # 리스트
    st.subheader("📋 프로모션 리스트")
    cfg = {"진척율": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)}
    st.dataframe(filtered_df, column_config=cfg, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# PAGE 2: 주간 업무 (WBR) - 벤치마킹 버전
# ---------------------------------------------------------
elif page == "📅 주간 업무 (WBR)":
    st.title("📅 Weekly Business Review")
    st.caption("PPP(Progress, Plans, Problems) 프레임워크 기반의 주간 업무 보고 시스템입니다.")

    # 1. 주차 선택 (공통 컨트롤)
    col_date, col_info = st.columns([1, 3])
    with col_date:
        pick_date = st.date_input("기준 날짜 선택", datetime.date.today())
    
    start_week, end_week = get_week_range(pick_date)
    week_str = str(start_week) # 키값
    
    with col_info:
        st.info(f"**[{start_week} ~ {end_week}]** 주차의 업무를 관리합니다.")

    # 2. 탭 구성 (조회 vs 작성)
    tab_view, tab_write = st.tabs(["📋 전체 팀원 보고서 조회", "✍️ 내 보고서 작성/수정"])

    # --- TAB 1: 조회 (View) ---
    with tab_view:
        report_df = load_weekly_reports()
        current_reports = report_df[report_df['Week_Start'] == week_str]
        
        if current_reports.empty:
            st.warning("해당 주차에 작성된 보고서가 없습니다.")
        else:
            # 담당자별 그룹핑
            assignees = sorted(current_reports['Assignee'].unique())
            
            st.markdown(f"총 **{len(assignees)}명**이 보고서를 제출했습니다.")
            st.divider()
            
            for person in assignees:
                p_df = current_reports[current_reports['Assignee'] == person]
                
                with st.expander(f"👤 **{person}**의 주간 보고", expanded=True):
                    # 3단 컬럼: 실적 / 계획 / 이슈
                    c_prog, c_plan, c_prob = st.columns(3)
                    
                    # 스타일링 함수
                    def show_cards(container, title, type_val, icon):
                        sub_df = p_df[p_df['Type'] == type_val]
                        with container:
                            st.markdown(f"##### {icon} {title}")
                            if sub_df.empty:
                                st.caption("내용 없음")
                            else:
                                for _, row in sub_df.iterrows():
                                    # 상태에 따른 색상
                                    status_color = "🟢" if row['Status'] == "정상" else "🟡" if row['Status'] == "지연" else "🔴"
                                    # 프로젝트 태그
                                    proj_tag = f"**[{row['Project']}]**" if row['Project'] != "-" else ""
                                    
                                    st.markdown(f"""
                                    <div style="background-color:#f0f2f6; padding:10px; border-radius:5px; margin-bottom:10px;">
                                        <div style="font-size:0.8em; color:#666;">{status_color} {row['Status']} {proj_tag}</div>
                                        <div>{row['Content']}</div>
                                    </div>
                                    """, unsafe_allow_html=True)

                    show_cards(c_prog, "금주 실적 (Progress)", "Progress", "✅")
                    show_cards(c_plan, "차주 계획 (Plans)", "Plans", "🗓️")
                    show_cards(c_prob, "이슈 사항 (Problems)", "Problems", "⚠️")

    # --- TAB 2: 작성 (Write) ---
    with tab_write:
        st.markdown("##### 📝 나의 주간 업무 보고서 작성")
        st.caption("좌측은 업무 유형, 중간은 관련된 프로모션(없으면 '-'), 우측은 내용을 입력하세요.")
        
        # 1. 작성자 선택
        managers = list(st.session_state.promotions['담당자'].unique()) if '담당자' in st.session_state.promotions.columns else []
        if "기타" not in managers: managers.append("기타")
        
        c_sel, _ = st.columns([1, 2])
        with c_sel:
            me = st.selectbox("작성자(본인) 선택", managers, key="writer_select")
            if me == "기타":
                me = st.text_input("이름 직접 입력")

        if me:
            # 2. 기존 데이터 불러오기 (Draft)
            # 파일에서 내 데이터를 찾아오거나, 없으면 템플릿 생성
            my_data = load_weekly_reports()
            my_week_data = my_data[(my_data['Week_Start'] == week_str) & (my_data['Assignee'] == me)]
            
            if my_week_data.empty:
                # 기본 템플릿 데이터 (처음 작성 시 가이드라인)
                template_data = [
                    {"Week_Start": week_str, "Assignee": me, "Type": "Progress", "Project": "-", "Content": "", "Status": "정상"},
                    {"Week_Start": week_str, "Assignee": me, "Type": "Plans", "Project": "-", "Content": "", "Status": "정상"},
                ]
                input_df = pd.DataFrame(template_data)
            else:
                input_df = my_week_data.reset_index(drop=True)

            # 3. 데이터 에디터 (입력 폼)
            # 프로젝트 목록 (드롭다운용)
            proj_list = ["-"] + list(st.session_state.promotions['프로모션명'].unique())
            
            edited_df = st.data_editor(
                input_df,
                column_config={
                    "Week_Start": None, # 숨김
                    "Assignee": None,   # 숨김
                    "Type": st.column_config.SelectboxColumn(
                        "구분", 
                        options=["Progress", "Plans", "Problems"],
                        help="Progress: 실적, Plans: 계획, Problems: 이슈",
                        required=True,
                        width="medium"
                    ),
                    "Project": st.column_config.SelectboxColumn(
                        "관련 프로모션",
                        options=proj_list,
                        help="관련된 프로모션이 있다면 선택하세요",
                        required=True,
                        width="medium"
                    ),
                    "Content": st.column_config.TextColumn(
                        "업무 내용",
                        required=True,
                        width="large"
                    ),
                    "Status": st.column_config.SelectboxColumn(
                        "상태",
                        options=["정상", "지연", "중단"],
                        required=True,
                        width="small"
                    )
                },
                num_rows="dynamic",
                use_container_width=True,
                key="wb_editor"
            )

            # 4. 저장 버튼
            col_save_btn, _ = st.columns([1, 4])
            with col_save_btn:
                if st.button("💾 보고서 제출/수정하기", type="primary", use_container_width=True):
                    # 유효성 검사: 내용이 있는 것만 저장
                    to_save = edited_df[edited_df['Content'].str.strip() != ""].copy()
                    
                    # 필수 메타데이터 강제 주입 (사용자가 에디터에서 행을 추가했을 때 비어있을 수 있음)
                    to_save['Week_Start'] = week_str
                    to_save['Assignee'] = me
                    
                    # 빈 값 처리
                    if 'Project' in to_save.columns:
                        to_save['Project'] = to_save['Project'].fillna("-")
                    if 'Status' in to_save.columns:
                        to_save['Status'] = to_save['Status'].fillna("정상")
                    
                    if not to_save.empty:
                        if save_weekly_report_entry(to_save):
                            st.toast("보고서가 성공적으로 제출되었습니다!", icon="🚀")
                            safe_rerun()
                    else:
                        st.warning("저장할 내용이 없습니다. 내용을 입력해주세요.")
        else:
            st.info("작성자를 먼저 선택해주세요.")

# ---------------------------------------------------------
# PAGE 3: 관리자 페이지 (기존 유지)
# ---------------------------------------------------------
elif page == "⚙️ 관리자 페이지":
    # 관리자 인증 로직 유지
    if not st.session_state.get('is_admin_unlocked', False):
        st.title("⚙️ 관리자 인증")
        with st.form("admin_login"):
            pw = st.text_input("관리자 암호", type="password")
            if st.form_submit_button("로그인"):
                if pw == "diageorcg":
                    st.session_state.is_admin_unlocked = True
                    # 관리자 진입 시 라이브 데이터를 draft로 복사
                    st.session_state.draft_df = st.session_state.promotions.copy()
                    safe_rerun()
                else:
                    st.error("암호 오류")
    else:
        # 관리자 기능 (저장 및 편집)
        c1, c2 = st.columns([2,1])
        c1.title("⚙️ 데이터 관리")
        if c2.button("💾 변경사항 저장 및 적용", type="primary"):
            if save_promotions(st.session_state.draft_df):
                st.toast("저장되었습니다.")
        
        st.divider()
        
        # 탭으로 기능 분리
        at1, at2, at3 = st.tabs(["✏️ 데이터 편집", "🛠️ 컬럼/행 관리", "📂 CSV 관리"])
        
        with at1:
            # 데이터 에디터
            edited = st.data_editor(st.session_state.draft_df, num_rows="dynamic", use_container_width=True, key="admin_edit")
            if not edited.equals(st.session_state.draft_df):
                st.session_state.draft_df = edited

        with at2:
            c_add, c_del = st.columns(2)
            with c_add:
                new_col = st.text_input("추가할 컬럼명")
                if st.button("컬럼 추가"):
                    if new_col and new_col not in st.session_state.draft_df.columns:
                        st.session_state.draft_df[new_col] = "-"
                        safe_rerun()
            with c_del:
                # 필수 컬럼 보호
                protected = ['프로모션명', '상태', '진척율']
                removable = [c for c in st.session_state.draft_df.columns if c not in protected]
                target = st.selectbox("삭제할 컬럼", removable)
                if st.button("컬럼 삭제"):
                    st.session_state.draft_df.drop(columns=[target], inplace=True)
                    safe_rerun()

        with at3:
            up = st.file_uploader("CSV 업로드", type=['csv'])
            if up and st.button("데이터 교체"):
                try:
                    ndf = pd.read_csv(up)
                    # 전처리 로직 (날짜, 진척율 변환)
                    for col in ['시작일', '종료일']:
                        if col in ndf.columns: ndf[col] = pd.to_datetime(ndf[col]).dt.date
                    if '진척율' in ndf.columns:
                        ndf['진척율'] = pd.to_numeric(ndf['진척율'].astype(str).str.replace('%',''), errors='coerce').fillna(0).astype(int)
                    
                    st.session_state.draft_df = ndf
                    st.success("데이터 로드됨. 상단 저장 버튼을 눌러 확정하세요.")
                    safe_rerun()
                except Exception as e:
                    st.error(f"CSV 오류: {e}")
            
            csv_data = st.session_state.draft_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("현재 데이터 다운로드", csv_data, "promotions_backup.csv")
