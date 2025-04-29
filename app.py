# Streamlit 대쉬보드

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
    columns={
        '타이틀': '교재명',
        '키워드': '에듀넷 키워드'
    }
)[[
    '교재명',
    '카테고리',
    '난이도',
    '추천 학년',        # N열에서 불러온 '추천 학년'
    '에듀넷 키워드',
    '주요 키워드',
    '교수 전략'
]]

# ─── 6) 페이지 헤더 ───────────────────────────────────────────────────────────
st.markdown("<h2>📚 초등 AI/SW 교재 길라잡이</h2>", unsafe_allow_html=True)

# ─── 7) 검색창 & 입력 업데이트 ─────────────────────────────────────────────────
st.text_input(
    "step 1: 교재명을 입력하고 enter를 눌러주세요",
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
    col_home, col_spacer, col_back = st.columns([3, 15, 4])
    with col_home:
        if st.button("🏠 홈", help="메인 목록으로 돌아가기"):
            clear_selection()
    with col_back:
        if st.button("◀️ 뒤로가기", help="이전 페이지로 이동"):
            go_back()

    if selected_title:
        # 상세 페이지
        row = df[df['교재명'] == selected_title].iloc[0]
        idx = df.index[df['교재명'] == selected_title][0]

        st.markdown(f"<h3>📖 {row['교재명']}</h3>", unsafe_allow_html=True)

        # ── 카테고리 · 난이도 · 추천 학년 · 에듀넷 키워드 · 주요 키워드 (한 줄씩) ──────────
        for label, col_name, sep in [
            ("🗂️ 카테고리",     '카테고리',     None),
            ("🧠 난이도",       '난이도',       None),
            ("🎓 추천 학년",    '추천 학년',    None),
            ("📚 에듀넷 키워드",'에듀넷 키워드','/'),
            ("🏫 주요 키워드",   '주요 키워드',  '/'),
        ]:
            st.markdown(f"<h4>{label}</h4>", unsafe_allow_html=True)
            items = [row[col_name]] if sep is None else str(row[col_name]).split(sep)
            for it in items:
                it = it.strip()
                if it:
                    st.button(it, key=f"{col_name}_{idx}_{it}", on_click=select_tag, args=(it,))

        # 교수 전략
        st.markdown("<h4>💡 교수 전략</h4>", unsafe_allow_html=True)
        st.write(row['교수 전략'])  # 기본 배경으로 출력

    else:
        # 태그 기반 목록 페이지
        st.markdown("---")
        st.markdown(f"### 🔎 '{selected_tag}' 관련 교재 목록")
        mask = (
            (df['카테고리'] == selected_tag) |
            (df['난이도']   == selected_tag) |
            (df['추천 학년'] == selected_tag)   |  # 추천 학년도 태그 필터에 포함
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
                f"📖  {row['교재명']}",
                key=f"home_{idx}",
                on_click=select_title_callback,
                args=(row['교재명'],)
            )
            st.caption(f"🗂️ {row['카테고리']}   🧠 {row['난이도']}   🎓 {row['추천 학년']}")
            st.write(f"📚 {row['에듀넷 키워드']}")
            st.write(f"🏫 {row['주요 키워드']}")
