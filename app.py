import streamlit as st
import pandas as pd
import datetime
import os

# ---------------------------------------------------------
# 파일 저장소 설정
# ---------------------------------------------------------
DATA_FILE = "promotion_data.csv"
WEEKLY_TASK_FILE = "weekly_tasks.csv"

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
    """주간 업무 데이터 로드"""
    if os.path.exists(WEEKLY_TASK_FILE):
        try:
            df = pd.read_csv(WEEKLY_TASK_FILE)
            # 날짜 컬럼 변환
            if 'Due_Date' in df.columns:
                df['Due_Date'] = pd.to_datetime(df['Due_Date'], errors='coerce').dt.date
            
            # [수정] 필터링을 위해 Week_Start를 반드시 문자열로 변환
            if 'Week_Start' in df.columns:
                df['Week_Start'] = df['Week_Start'].astype(str)
                
            return df
        except:
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

def add_weekly_tasks_batch(new_rows_df):
    """주간 업무 일괄 추가"""
    if new_rows_df.empty:
        return False
        
    df = load_weekly_tasks()
    # 기존 데이터와 병합
    df = pd.concat([df, new_rows_df], ignore_index=True)
    
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
# 2. 주간 업무 페이지
# ---------------------------------------------------------
elif page == "📅 주간 업무":
    st.title("📅 주간 업무 대시보드")
    
    # 1. 날짜 및 주차 선택
    col_date, col_week_info = st.columns([1, 2])
    with col_date:
        pick_date = st.date_input("기준 날짜 선택", datetime.date.today())
    
    start_of_week = pick_date - datetime.timedelta(days=pick_date.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    
    # [수정] 날짜를 문자열로 명확하게 변환 (비교용)
    start_of_week_str = str(start_of_week)
    
    with col_week_info:
        st.info(f"📆 **선택된 주간**: {start_of_week} (월) ~ {end_of_week} (일)")

    st.divider()

    # 2. 업무 등록
    with st.expander("➕ 내 업무 등록 (Click)", expanded=True):
        st.markdown("#### 1️⃣ 작성자 선택")
        managers = list(st.session_state.promotions['담당자'].unique()) if '담당자' in st.session_state.promotions.columns else []
        if "기타(직접입력)" not in managers: managers.append("기타(직접입력)")
        
        col_assignee, _ = st.columns([1, 2])
        with col_assignee:
            selected_assignee = st.selectbox("본인의 이름을 선택하세요", managers, key="task_assignee_selector")
            if selected_assignee == "기타(직접입력)":
                real_assignee = st.text_input("이름 직접 입력")
            else:
                real_assignee = selected_assignee

        st.markdown("#### 2️⃣ 업무 내용 입력")
        st.caption("아래 표에 업무를 입력하세요.")

        input_template = pd.DataFrame(columns=["Category", "Content", "Due_Date"])
        
        column_config = {
            "Category": st.column_config.SelectboxColumn("구분", options=["금주 실적", "차주 계획", "이슈 사항"], required=True, width="medium"),
            "Content": st.column_config.TextColumn("업무 내용", required=True, width="large"),
            "Due_Date": st.column_config.DateColumn("기한", default=datetime.date.today(), required=True),
        }

        edited_input = st.data_editor(
            input_template,
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            key="weekly_input_editor"
        )
        
        if st.button("💾 입력한 업무 등록하기", type="primary"):
            if real_assignee:
                # [수정] 데이터 유효성 검사 강화 (내용이 있는 행만 추출)
                if not edited_input.empty:
                    # Content가 비어있지 않은 행만 유효한 것으로 간주
                    edited_input = edited_input.dropna(subset=['Content'])
                    valid_rows = edited_input[edited_input['Content'].str.strip() != ""].copy()
                    
                    if not valid_rows.empty:
                        valid_rows['Assignee'] = real_assignee
                        valid_rows['Week_Start'] = start_of_week_str # 문자열로 저장
                        valid_rows['Status'] = '진행중'
                        
                        # Category가 비어있으면 기본값 설정
                        if 'Category' not in valid_rows.columns or valid_rows['Category'].isnull().any():
                             valid_rows['Category'] = valid_rows['Category'].fillna("금주 실적")
                        
                        if add_weekly_tasks_batch(valid_rows):
                            st.toast(f"{len(valid_rows)}건의 업무가 등록되었습니다!", icon="✅")
                            safe_rerun()
                    else:
                        st.error("업무 내용을 입력해주세요.")
                else:
                    st.warning("입력된 내용이 없습니다.")
            else:
                st.error("작성자(담당자)를 선택해주세요.")

    st.divider()

    # 3. 주간 업무 전체 조회
    st.subheader(f"📋 {start_of_week} 주간 전체 업무 현황")
    
    all_tasks = load_weekly_tasks()
    
    # [수정] 날짜 필터링 시 둘 다 문자열로 변환하여 비교
    # all_tasks['Week_Start']는 load_weekly_tasks에서 이미 문자열로 변환됨
    current_week_tasks = all_tasks[all_tasks['Week_Start'] == start_of_week_str]
    
    if not current_week_tasks.empty:
        current_week_tasks = current_week_tasks.sort_values(by=['Assignee', 'Category'])
        
        col_achieve, col_plan, col_issue = st.columns(3)
        view_config = {
            "Content": st.column_config.TextColumn("내용", width="large"),
            "Assignee": st.column_config.TextColumn("담당자", width="small"),
            "Due_Date": st.column_config.DateColumn("기한", format="MM-DD", width="small"),
        }
        
        with col_achieve:
            st.markdown("##### ✅ 금주 실적")
            df_view = current_week_tasks[current_week_tasks['Category'] == "금주 실적"][['Assignee', 'Content', 'Due_Date']]
            st.dataframe(df_view, column_config=view_config, use_container_width=True, hide_index=True)
            
        with col_plan:
            st.markdown("##### 🗓️ 차주 계획")
            df_view = current_week_tasks[current_week_tasks['Category'] == "차주 계획"][['Assignee', 'Content', 'Due_Date']]
            st.dataframe(df_view, column_config=view_config, use_container_width=True, hide_index=True)
            
        with col_issue:
            st.markdown("##### ⚠️ 이슈 사항")
            df_view = current_week_tasks[current_week_tasks['Category'] == "이슈 사항"][['Assignee', 'Content', 'Due_Date']]
            st.dataframe(df_view, column_config=view_config, use_container_width=True, hide_index=True)

        with st.expander("🗑️ 업무 삭제하기"):
            task_to_delete = st.selectbox(
                "삭제할 업무 선택", 
                current_week_tasks.index, 
                format_func=lambda x: f"[{current_week_tasks.loc[x, 'Assignee']}] {current_week_tasks.loc[x, 'Content'][:30]}..."
            )
            if st.button("선택한 업무 삭제"):
                if delete_weekly_task(task_to_delete):
                    st.success("삭제되었습니다.")
                    safe_rerun()
    else:
        st.info("해당 주차에 등록된 업무가 없습니다.")

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
