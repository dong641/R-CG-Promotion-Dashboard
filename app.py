import streamlit as st
import pandas as pd
import datetime
import os

# ---------------------------------------------------------
# 파일 저장소 설정
# ---------------------------------------------------------
DATA_FILE = "promotion_data.csv"
WEEKLY_FILE = "weekly_data.csv"  # 주간 업무 데이터 저장용

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

def load_weekly_data():
    """주간 업무 데이터 로드"""
    if os.path.exists(WEEKLY_FILE):
        try:
            return pd.read_csv(WEEKLY_FILE, dtype=str)
        except:
            return pd.DataFrame(columns=["Week_Start", "Achievements", "Plans", "Issues"])
    else:
        return pd.DataFrame(columns=["Week_Start", "Achievements", "Plans", "Issues"])

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

def save_weekly_report(week_start, achieve, plan, issue):
    """특정 주차의 업무 보고를 저장"""
    df = load_weekly_data()
    new_row = {"Week_Start": str(week_start), "Achievements": achieve, "Plans": plan, "Issues": issue}
    
    # 기존 데이터가 있으면 업데이트, 없으면 추가
    if str(week_start) in df['Week_Start'].values:
        df.loc[df['Week_Start'] == str(week_start), ["Achievements", "Plans", "Issues"]] = [achieve, plan, issue]
    else:
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    try:
        df.to_csv(WEEKLY_FILE, index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        st.error(f"주간 보고 저장 오류: {e}")
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
    # [변경] 주간 업무 메뉴 추가
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
# [신규] 2. 주간 업무 페이지
# ---------------------------------------------------------
elif page == "📅 주간 업무":
    st.title("📅 주간 업무 보고")
    st.caption("해당 주차의 진행되는 프로모션을 확인하고 주간 보고를 작성합니다.")
    
    # 날짜 선택
    col_date, col_dummy = st.columns([1, 2])
    with col_date:
        pick_date = st.date_input("기준 날짜 선택", datetime.date.today())
    
    # 해당 날짜가 속한 주의 월요일(Start), 일요일(End) 계산
    start_of_week = pick_date - datetime.timedelta(days=pick_date.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    
    st.info(f"📆 **선택된 주간**: {start_of_week} (월) ~ {end_of_week} (일)")
    
    st.divider()
    
    # 1) 해당 주간에 걸쳐있는 프로모션 자동 필터링
    st.subheader("🔥 금주 진행 프로모션 (자동 집계)")
    df = st.session_state.promotions
    
    # 날짜 범위 겹치는 데이터 찾기: (시작일 <= 이번주끝) AND (종료일 >= 이번주시작)
    weekly_active_df = df[
        (df['시작일'] <= end_of_week) & 
        (df['종료일'] >= start_of_week)
    ]
    
    if not weekly_active_df.empty:
        st.dataframe(
            weekly_active_df,
            column_config={
                "진척율": st.column_config.ProgressColumn(format="%d%%"),
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("금주 진행되는 프로모션이 없습니다.")
        
    st.divider()
    
    # 2) 주간 업무 보고 작성 (저장된 내용 불러오기)
    st.subheader("📝 주간 보고 작성")
    
    weekly_data = load_weekly_data()
    current_report = weekly_data[weekly_data['Week_Start'] == str(start_of_week)]
    
    # 저장된 값이 있으면 가져오고 없으면 빈 값
    def_achieve = current_report.iloc[0]['Achievements'] if not current_report.empty else ""
    def_plan = current_report.iloc[0]['Plans'] if not current_report.empty else ""
    def_issue = current_report.iloc[0]['Issues'] if not current_report.empty else ""
    
    with st.form("weekly_report_form"):
        c1, c2 = st.columns(2)
        with c1:
            achievements = st.text_area("✅ 금주 주요 실적", value=def_achieve, height=200, placeholder="- 프로모션 A 기획 완료\n- B 프로모션 예산 확정")
        with c2:
            plans = st.text_area("🗓️ 차주 계획", value=def_plan, height=200, placeholder="- C 프로모션 런칭 준비\n- 영업팀 미팅 예정")
        
        issues = st.text_area("⚠️ 특이사항 및 이슈", value=def_issue, height=100, placeholder="특이사항 없음")
        
        if st.form_submit_button("💾 주간 보고 저장하기", type="primary", use_container_width=True):
            if save_weekly_report(start_of_week, achievements, plans, issues):
                st.toast("주간 보고가 저장되었습니다!", icon="✅")
                safe_rerun()

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
