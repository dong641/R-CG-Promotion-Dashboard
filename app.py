import streamlit as st
import pandas as pd
import datetime
import os

# ---------------------------------------------------------
# 파일 저장소 설정
# ---------------------------------------------------------
DATA_FILE = "promotion_data.csv"
WEEKLY_TASK_FILE = "weekly_tasks.csv"  # 데이터 구조 변경으로 파일명 변경

# ---------------------------------------------------------
# 함수 정의
# ---------------------------------------------------------
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def load_data():
    """메인 프로모션 데이터 로드"""
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
        except Exception as e:
            st.error(f"데이터 로드 오류: {e}")
            return create_default_data()
    else:
        return create_default_data()

def load_weekly_tasks():
    """주간 업무 데이터 로드 (개별 Task 단위)"""
    if os.path.exists(WEEKLY_TASK_FILE):
        try:
            df = pd.read_csv(WEEKLY_TASK_FILE)
            if 'Due_Date' in df.columns:
                df['Due_Date'] = pd.to_datetime(df['Due_Date'], errors='coerce').dt.date
            return df
        except:
            # 파일이 깨졌거나 없으면 헤더 생성
            return pd.DataFrame(columns=["Week_Start", "Assignee", "Category", "Content", "Due_Date", "Status"])
    else:
        return pd.DataFrame(columns=["Week_Start", "Assignee", "Category", "Content", "Due_Date", "Status"])

def create_default_data():
    return pd.DataFrame([
        {"프로모션명": "2024 봄 정기 세일", "채널": "Off Trade", "담당자": "김철수", "상태": "진행중", "진척율": 75, "시작일": datetime.date(2024, 3, 1), "종료일": datetime.date(2024, 3, 15)},
        {"프로모션명": "신규 회원 가입 이벤트", "채널": "On Trade", "담당자": "이영희", "상태": "기획단계", "진척율": 20, "시작일": datetime.date(2024, 4, 1), "종료일": datetime.date(2024, 4, 30)},
        {"프로모션명": "여름 바캉스 특가", "채널": "Off Trade", "담당자": "박민수", "상태": "대기", "진척율": 0, "시작일": datetime.date(2024, 6, 1), "종료일": datetime.date(2024, 8, 31)},
        {"프로모션명": "설날 효도 선물전", "채널": "On Trade", "담당자": "정수진", "상태": "완료", "진척율": 100, "시작일": datetime.date(2024, 1, 15), "종료일": datetime.date(2024, 2, 9)},
    ])

def save_data(df):
    try:
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        st.session_state.promotions = df.copy()
        return True
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False

def add_weekly_task(week_start, assignee, category, content, due_date):
    """주간 업무 추가"""
    df = load_weekly_tasks()
    new_row = {
        "Week_Start": str(week_start),
        "Assignee": assignee,
        "Category": category,
        "Content": content,
        "Due_Date": due_date,
        "Status": "진행중" # 기본값
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    try:
        df.to_csv(WEEKLY_TASK_FILE, index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        st.error(f"주간 업무 저장 오류: {e}")
        return False

def delete_weekly_task(index):
    """주간 업무 삭제"""
    df = load_weekly_tasks()
    try:
        df = df.drop(index)
        df.to_csv(WEEKLY_TASK_FILE, index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        st.error(f"삭제 오류: {e}")
        return False

# ---------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------
st.set_page_config(page_title="프로모션 통합 시스템", page_icon="🔒", layout="wide")

# ---------------------------------------------------------
# 로그인
# ---------------------------------------------------------
if 'is_global_unlocked' not in st.session_state:
    st.session_state.is_global_unlocked = False

if not st.session_state.is_global_unlocked:
    st.title("🔒 프로모션 시스템 접근")
    pw = st.text_input("접속 암호", type="password")
    if st.button("접속"):
        if pw == "dk2026":
            st.session_state.is_global_unlocked = True
            safe_rerun()
        else:
            st.error("암호 오류")
    st.stop()

# ---------------------------------------------------------
# 메인 로직
# ---------------------------------------------------------
if 'promotions' not in st.session_state:
    st.session_state.promotions = load_data()
if 'draft_df' not in st.session_state:
    st.session_state.draft_df = st.session_state.promotions.copy()
if 'is_admin_unlocked' not in st.session_state:
    st.session_state.is_admin_unlocked = False

# 사이드바
with st.sidebar:
    st.title("메뉴")
    page = st.radio("이동할 페이지", ["📊 대시보드", "📅 주간 업무", "⚙️ 관리자 페이지"])
    st.divider()
    if st.button("🚪 로그아웃"):
        st.session_state.is_global_unlocked = False
        st.session_state.is_admin_unlocked = False
        safe_rerun()

# ---------------------------------------------------------
# 1. 대시보드
# ---------------------------------------------------------
if page == "📊 대시보드":
    st.title("📊 프로모션 현황 대시보드")
    df = st.session_state.promotions
    
    metrics_container = st.container()
    st.divider()
    
    with st.expander("🔍 상세 검색 및 필터", expanded=False):
        filter_cols = st.columns(3)
        filtered_df = df.copy() 
        valid_cols = [c for c in df.columns if c not in ['진척율', '시작일', '종료일']]
        
        for i, col in enumerate(valid_cols):
            with filter_cols[i % 3]:
                vals = sorted(filtered_df[col].astype(str).unique())
                sel = st.multiselect(col, vals, key=f"dash_{col}")
                if sel: filtered_df = filtered_df[filtered_df[col].astype(str).isin(sel)]

    with metrics_container:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("조회 건수", f"{len(filtered_df)}건")
        c2.metric("진행중", f"{len(filtered_df[filtered_df['상태']=='진행중'])}건")
        c3.metric("완료", f"{len(filtered_df[filtered_df['상태']=='완료'])}건")
        
        active = filtered_df[filtered_df['상태']!='완료']
        avg = active['진척율'].mean() if not active.empty else 0
        c4.metric("평균 진척율(완료제외)", f"{avg:.1f}%")

    st.subheader("📋 프로모션 목록")
    t1, t2, t3 = st.tabs([f"진행중 ({len(active)})", f"완료 ({len(filtered_df)-len(active)})", "전체"])
    
    cfg = {"진척율": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)}
    with t1: st.dataframe(active, column_config=cfg, use_container_width=True, hide_index=True)
    with t2: st.dataframe(filtered_df[filtered_df['상태']=='완료'], column_config=cfg, use_container_width=True, hide_index=True)
    with t3: st.dataframe(filtered_df, column_config=cfg, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# [수정] 2. 주간 업무 페이지 (개인별 입력 및 조회)
# ---------------------------------------------------------
elif page == "📅 주간 업무":
    st.title("📅 주간 업무 대시보드")
    
    # 1. 날짜 및 주차 선택
    col_date, col_week_info = st.columns([1, 2])
    with col_date:
        pick_date = st.date_input("기준 날짜 선택", datetime.date.today())
    
    start_of_week = pick_date - datetime.timedelta(days=pick_date.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    
    with col_week_info:
        st.info(f"📆 **선택된 주간**: {start_of_week} (월) ~ {end_of_week} (일)")

    st.divider()

    # 2. 업무 등록 (개인별)
    with st.expander("➕ 내 업무 등록하기 (Click)", expanded=True):
        with st.form("add_weekly_task_form"):
            st.markdown("**새로운 업무 등록**")
            
            # 담당자 선택 (기존 프로모션 담당자 리스트 활용 + 직접 입력)
            managers = list(st.session_state.promotions['담당자'].unique()) if '담당자' in st.session_state.promotions.columns else []
            if "기타(직접입력)" not in managers:
                managers.append("기타(직접입력)")
                
            c1, c2, c3 = st.columns(3)
            with c1:
                selected_assignee = st.selectbox("담당자 선택", managers)
                if selected_assignee == "기타(직접입력)":
                    assignee = st.text_input("담당자명 입력")
                else:
                    assignee = selected_assignee
            
            with c2:
                category = st.selectbox("업무 구분", ["금주 실적", "차주 계획", "이슈 사항"])
            
            with c3:
                due_date = st.date_input("Due Date (기한)", datetime.date.today())
            
            content = st.text_area("업무 내용", placeholder="구체적인 업무 내용을 입력하세요.")
            
            if st.form_submit_button("등록", type="primary", use_container_width=True):
                if assignee and content:
                    if add_weekly_task(start_of_week, assignee, category, content, due_date):
                        st.toast("업무가 등록되었습니다.", icon="✅")
                        safe_rerun()
                else:
                    st.error("담당자와 내용을 입력해주세요.")

    st.divider()

    # 3. 주간 업무 조회 (담당자별 필터링)
    st.subheader(f"📋 {start_of_week} 주간 업무 현황")
    
    # 데이터 로드 및 해당 주차 필터링
    all_tasks = load_weekly_tasks()
    current_week_tasks = all_tasks[all_tasks['Week_Start'] == str(start_of_week)]
    
    if not current_week_tasks.empty:
        # 필터링 UI
        assignee_list = sorted(current_week_tasks['Assignee'].unique())
        selected_view_assignees = st.multiselect("👤 담당자별 모아보기", assignee_list, placeholder="전체 보기")
        
        # 필터 적용
        if selected_view_assignees:
            display_tasks = current_week_tasks[current_week_tasks['Assignee'].isin(selected_view_assignees)]
        else:
            display_tasks = current_week_tasks
            
        # 데이터프레임 표시 (삭제 기능 포함을 위해 data_editor 사용하되 수정은 제한적)
        # 삭제를 위해서는 key 관리 필요. 간단하게 보여주기 위주로 구현.
        
        st.dataframe(
            display_tasks[['Category', 'Content', 'Assignee', 'Due_Date']],
            column_config={
                "Category": st.column_config.TextColumn("구분", width="small"),
                "Content": st.column_config.TextColumn("업무 내용", width="large"),
                "Assignee": st.column_config.TextColumn("담당자", width="small"),
                "Due_Date": st.column_config.DateColumn("기한", format="YYYY-MM-DD", width="small"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        # 삭제 기능 (선택적)
        with st.expander("🗑️ 업무 삭제하기"):
            task_to_delete = st.selectbox("삭제할 업무 선택", display_tasks.index, format_func=lambda x: f"{display_tasks.loc[x, 'Assignee']} - {display_tasks.loc[x, 'Content'][:20]}...")
            if st.button("선택한 업무 삭제"):
                if delete_weekly_task(task_to_delete):
                    st.success("삭제되었습니다.")
                    safe_rerun()
            
    else:
        st.info("등록된 주간 업무가 없습니다.")

# ---------------------------------------------------------
# 3. 관리자 페이지
# ---------------------------------------------------------
elif page == "⚙️ 관리자 페이지":
    if not st.session_state.is_admin_unlocked:
        st.title("⚙️ 관리자 인증")
        with st.form("login"):
            pw = st.text_input("암호", type="password")
            if st.form_submit_button("로그인"):
                if pw == "diageorcg":
                    st.session_state.is_admin_unlocked = True
                    st.session_state.draft_df = st.session_state.promotions.copy()
                    safe_rerun()
                else:
                    st.error("오류")
    else:
        c_title, c_btn = st.columns([2, 1])
        c_title.title("⚙️ 데이터 관리")
        if c_btn.button("💾 저장하고 적용하기", type="primary"):
            if save_data(st.session_state.draft_df):
                st.toast("저장 완료")
        
        # 컬럼 관리
        with st.expander("🛠️ 컬럼 관리"):
            a, b = st.columns(2)
            new = a.text_input("추가할 컬럼")
            if a.button("추가"):
                if new and new not in st.session_state.draft_df.columns:
                    st.session_state.draft_df[new] = "-"
                    safe_rerun()
            
            dels = [c for c in st.session_state.draft_df.columns if c not in ['프로모션명','상태','진척율']]
            target = b.selectbox("삭제할 컬럼", dels)
            if b.button("삭제"):
                st.session_state.draft_df.drop(columns=[target], inplace=True)
                safe_rerun()

        # 행 추가
        with st.expander("➕ 데이터 추가"):
            with st.form("add"):
                st.markdown("**기본 정보**")
                c1, c2 = st.columns(2)
                nm = c1.text_input("이름")
                stt = c2.selectbox("상태", ["기획단계", "대기", "진행중", "완료"])
                prg = st.slider("진척율", 0, 100)
                d1, d2 = st.columns(2)
                s_dt = d1.date_input("시작", datetime.date.today())
                e_dt = d2.date_input("종료", datetime.date.today())
                
                dyn = {}
                others = [c for c in st.session_state.draft_df.columns if c not in ['프로모션명','상태','진척율','시작일','종료일']]
                if others:
                    cols = st.columns(3)
                    for i, c in enumerate(others):
                        dyn[c] = cols[i%3].text_input(c)
                
                if st.form_submit_button("추가"):
                    row = {"프로모션명":nm, "상태":stt, "진척율":prg, "시작일":s_dt, "종료일":e_dt}
                    row.update(dyn)
                    st.session_state.draft_df = pd.concat([st.session_state.draft_df, pd.DataFrame([row])], ignore_index=True)
                    safe_rerun()

        # CSV 업로드
        with st.expander("📂 CSV 업로드"):
            up = st.file_uploader("CSV", type=['csv'])
            if up and st.button("교체"):
                ndf = pd.read_csv(up)
                if '진척율' in ndf.columns:
                     ndf['진척율'] = pd.to_numeric(ndf['진척율'].astype(str).str.replace('%',''), errors='coerce').fillna(0).astype(int)
                for c in ['시작일','종료일']: 
                    if c in ndf.columns: ndf[c] = pd.to_datetime(ndf[c]).dt.date
                st.session_state.draft_df = ndf
                safe_rerun()

        st.subheader("✏️ 편집")
        edited = st.data_editor(st.session_state.draft_df, num_rows="dynamic", use_container_width=True)
        if not edited.equals(st.session_state.draft_df):
            st.session_state.draft_df = edited
        
        csv = st.session_state.draft_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("다운로드", csv, "data.csv")
