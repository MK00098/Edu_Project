import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# ─── 1) 세션 상태 초기화 ──────────────────────────────────────────────────────
for key in (
    'temp_input',
    'user_input',
    'select_title',
    'selected_title',
    'selected_tag',
    'history'
):
    if key not in st.session_state:
        if key == 'history':
            st.session_state[key] = []
        elif 'input' in key or 'select' in key:
            st.session_state[key] = ''
        else:
            st.session_state[key] = None

# ─── 2) 내비게이션 헬퍼 ───────────────────────────────────────────────────────
def push_history():
    st.session_state.history.append({
        'selected_title': st.session_state.selected_title,
        'selected_tag':   st.session_state.selected_tag
    })

def go_back():
    if st.session_state.history:
        last = st.session_state.history.pop()
        st.session_state.selected_title = last['selected_title']
        st.session_state.selected_tag   = last['selected_tag']

def clear_selection():
    st.session_state.selected_title = None
    st.session_state.selected_tag   = None
    st.session_state.history        = []

# ─── 3) 콜백 정의 ─────────────────────────────────────────────────────────────
def update_input():
    st.session_state.user_input   = st.session_state.temp_input
    st.session_state.select_title = ''
    clear_selection()

def update_select():
    sel = st.session_state.select_title
    if sel and sel != "── 선택 없음 ──":
        push_history()
        st.session_state.selected_title = sel
        st.session_state.selected_tag   = None

def select_tag(tag):
    push_history()
    st.session_state.selected_tag   = tag
    st.session_state.selected_title = None

def select_title_callback(title):
    push_history()
    st.session_state.selected_title = title
    st.session_state.selected_tag   = None

# ─── 4) 구글 인증 & 시트 로드 ─────────────────────────────────────────────────
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ],
)
gc = gspread.authorize(credentials)
worksheet = gc.open_by_key(
    "1flo64cRwCCpI5B9dS3C2_4AdcI1alMZeD7D8GQKz32Y"
).worksheet("students(for API)")

# ─── 5) 데이터 로딩 & 전처리 ─────────────────────────────────────────────────────
data = worksheet.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0]).rename(
    columns={'타이틀':'교재명','키워드':'에듀넷 키워드'}
)[['교재명','카테고리','난이도','에듀넷 키워드','주요 키워드','교수 전략']]
df['추가예시'] = ''

# ─── 6) 페이지 헤더 ───────────────────────────────────────────────────────────
st.markdown("<h2>📚 초등 AI 교재 인사이트</h2>", unsafe_allow_html=True)

# ─── 7) 검색창 & 입력 업데이트 ─────────────────────────────────────────────────
st.text_input(
    "step 1: 검색어를 입력하고 Enter를 눌러주세요",
    key='temp_input',
    on_change=update_input
)
user_input = st.session_state.user_input

# ─── 8) 추천 교재 드롭다운 ────────────────────────────────────────────────────
title_list  = df['교재명'].dropna().tolist()
suggestions = [t for t in title_list if user_input.lower() in t.lower()]

if suggestions:
    options = ["── 선택 없음 ──"] + suggestions
    if st.session_state.select_title not in options:
        st.session_state.select_title = options[0]
    st.selectbox(
        "step 2: 교재를 선택하세요",
        options,
        key='select_title',
        on_change=update_select
    )
elif user_input:
    st.info("🔍 검색어에 해당하는 교재가 없습니다.")

# ─── 9) 현재 선택 상태 ─────────────────────────────────────────────────────────
selected_title = st.session_state.selected_title
selected_tag   = st.session_state.selected_tag

# ─── 10) 상세 / 태그 목록 또는 홈 화면 ──────────────────────────────────────────
if selected_title or selected_tag:
    # 홈 & 뒤로가기 버튼 (한 줄, 양 끝)
    col_home, _, col_back = st.columns([1, 20, 1])
    with col_home:
        if st.button("🏠홈", help="메인 목록으로 돌아가기"):
            clear_selection()
    with col_back:
        if st.button("◀️뒤로", help="이전 페이지로 이동"):
            go_back()

    if selected_title:
        # 상세 페이지
        row = df[df['교재명'] == selected_title].iloc[0]
        idx = df.index[df['교재명'] == selected_title][0]

        st.markdown(f"<h3>📖 {row['교재명']}</h3>", unsafe_allow_html=True)

        # — 라벨 2줄 구조 — 
        # 1행: 카테고리 · 난이도 · 에듀넷 키워드 라벨
        lbl1, lbl2, lbl3 = st.columns([2, 2, 4])
        with lbl1:
            st.markdown("<h4>🗂️ 카테고리</h4>", unsafe_allow_html=True)
        with lbl2:
            st.markdown("<h4>🧠 난이도</h4>", unsafe_allow_html=True)
        with lbl3:
            st.markdown("<h4>📚 에듀넷 키워드</h4>", unsafe_allow_html=True)

        # 2행: 실제 버튼
        col_cat, col_diff, col_edu = st.columns([2, 2, 4])
        with col_cat:
            if st.button(row['카테고리'], key=f"cat_{idx}", help="카테고리로 필터"):
                select_tag(row['카테고리'])
        with col_diff:
            if st.button(row['난이도'], key=f"diff_{idx}", help="난이도로 필터"):
                select_tag(row['난이도'])
        with col_edu:
            edu = row['에듀넷 키워드']
            if st.button(edu, key=f"edu_{idx}", help="에듀넷 키워드로 필터"):
                select_tag(edu)

        # 주요 키워드를 한 줄로
        major = row['주요 키워드']
        st.markdown(f"🏫 주요 키워드: {major}")

        # 교수 전략 & 추가 예시
        st.markdown("<h4>💡 교수 전략</h4>", unsafe_allow_html=True)
        st.info(row['교수 전략'])
        st.markdown("<h4>🧩 추가 예시</h4>", unsafe_allow_html=True)
        st.write(row['추가예시'])

    else:
        # 태그 기반 목록 페이지
        st.markdown("---")
        st.markdown(f"### 🔎 '{selected_tag}' 관련 교재 목록")
        mask = (
            (df['카테고리'] == selected_tag) |
            (df['난이도']   == selected_tag) |
            (df['에듀넷 키워드'].str.contains(selected_tag, na=False)) |
            (df['주요 키워드'].str.contains(selected_tag, na=False))
        )
        for title in df[mask]['교재명'].dropna():
            st.button(
                title,
                key=f"list_{title}",
                on_click=select_title_callback,
                args=(title,)
            )

else:
    # 홈 / 검색 결과 목록
    results = (
        df[df['교재명'].str.contains(user_input, case=False, na=False)]
        if user_input else df.copy()
    )
    if results.empty:
        st.info("🔍 검색 결과가 없습니다.")
    else:
        for idx, row in results.iterrows():
            st.markdown("---")
            st.button(
                f"📖 {row['교재명']}",
                key=f"home_{idx}",
                on_click=select_title_callback,
                args=(row['교재명'],)
            )
            st.caption(f"🗂️ {row['카테고리']}   🧠 {row['난이도']}")
            st.write(f"📚 {row['에듀넷 키워드']}")
            st.write(f"🏫 {row['주요 키워드']}")