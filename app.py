import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# ─── 1) 세션 상태 초기화 ──────────────────────────────────────────────────────
for key in ('temp_input', 'user_input', 'select_title', 'selected_title', 'selected_tag'):
    if key not in st.session_state:
        st.session_state[key] = '' if 'input' in key or 'select' in key else None
# history: 뒤로가기용 스택
if 'history' not in st.session_state:
    st.session_state['history'] = []

# ─── 2) 내비게이션 헬퍼 ────────────────────────────────────────────────────────
def add_history():
    # 현재 선택된 상태를 스택에 저장
    st.session_state['history'].append((
        st.session_state['selected_title'],
        st.session_state['selected_tag']
    ))

def go_back():
    if st.session_state['history']:
        prev_title, prev_tag = st.session_state['history'].pop()
        st.session_state['selected_title'] = prev_title
        st.session_state['selected_tag']   = prev_tag

# ─── 3) 콜백 함수 정의 ─────────────────────────────────────────────────────────
def update_input():
    st.session_state['user_input']      = st.session_state['temp_input']
    st.session_state['select_title']    = ''
    st.session_state['selected_title']  = None
    st.session_state['selected_tag']    = None
    st.session_state['history'].clear()  # 새 검색이면 뒤로가기 초기화

def update_select():
    sel = st.session_state['select_title']
    if sel and sel != "── 선택 없음 ──":
        add_history()
        st.session_state['selected_title'] = sel
        st.session_state['selected_tag']   = None

def select_tag(tag):
    add_history()
    st.session_state['selected_tag']   = tag
    st.session_state['selected_title'] = None

def select_title_callback(title):
    add_history()
    st.session_state['selected_title'] = title
    st.session_state['selected_tag']   = None

# ─── 4) 구글 인증 & 시트 로드 ─────────────────────────────────────────────────
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ],
)
gc = gspread.authorize(credentials)
SPREADSHEET_ID = "1flo64cRwCCpI5B9dS3C2_4AdcI1alMZeD7D8GQKz32Y"
WORKSHEET_NAME  = "students(for API)"
ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

# ─── 5) 데이터 로딩 & 전처리 ─────────────────────────────────────────────────────
data = ws.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])
df = df[['타이틀','카테고리','난이도','키워드','주요 키워드','교수 전략']].rename(
    columns={'타이틀':'교재명','키워드':'에듀넷 키워드'}
)
df['추가예시'] = ''

# ─── 6) 페이지 헤더 & 검색창 ───────────────────────────────────────────────────
st.markdown("<h2>📚 초등 AI 교재 인사이트</h2>", unsafe_allow_html=True)
st.text_input("초등학교 교재명을 검색하세요", key='temp_input', on_change=update_input)
user_input = st.session_state['user_input']

# ─── 7) 추천 교재 드롭다운 ────────────────────────────────────────────────────
title_list  = df['교재명'].dropna().tolist()
suggestions = [t for t in title_list if user_input.lower() in t.lower()]

if suggestions:
    st.selectbox(
        "추천 교재를 선택하세요",
        ["── 선택 없음 ──"] + suggestions,
        key='select_title',
        on_change=update_select
    )
elif user_input:
    st.info("🔍 검색어에 해당하는 교재가 없습니다.")

# ─── 8) 현재 상태 가져오기 ─────────────────────────────────────────────────────
selected_title = st.session_state['selected_title']
selected_tag   = st.session_state['selected_tag']

# ─── 9) 상세 페이지 ───────────────────────────────────────────────────────────
if selected_title:
    st.button("🔙 뒤로", on_click=go_back)
    st.markdown("---")
    row = df[df['교재명'] == selected_title].iloc[0]

    st.markdown(f"<h3>📖 {row['교재명']}</h3>", unsafe_allow_html=True)
    # 태그 버튼
    for label, col, sep in [
        ("🗂️ 카테고리",    '카테고리',        None),
        ("🧠 난이도",      '난이도',          None),
        ("📚 에듀넷 키워드",'에듀넷 키워드',  '/'),
        ("🏫 주요 키워드",  '주요 키워드',    '/'),
    ]:
        st.markdown(f"<h4>{label}</h4>", unsafe_allow_html=True)
        items = [row[col]] if sep is None else str(row[col]).split(sep)
        for it in items:
            it = it.strip()
            if it:
                st.button(it, key=f"tag_{col}_{it}", on_click=select_tag, args=(it,))

    st.markdown("<h4>💡 교수 전략</h4>", unsafe_allow_html=True)
    st.info(row['교수 전략'])
    st.markdown("<h4>🧩 추가 예시</h4>", unsafe_allow_html=True)
    st.write(row['추가예시'])

# ─── 10) 태그 기반 목록 페이지 ─────────────────────────────────────────────────
elif selected_tag:
    st.button("🔙 뒤로", on_click=go_back)
    st.markdown("---")
    st.markdown(f"### 🔎 '{selected_tag}' 관련 교재 목록")

    mask = (
        (df['카테고리'] == selected_tag) |
        (df['난이도']   == selected_tag) |
        (df['에듀넷 키워드'].str.contains(selected_tag, na=False)) |
        (df['주요 키워드'].str.contains(selected_tag, na=False))
    )
    for title in df[mask]['교재명'].dropna().tolist():
        st.button(title, key=f"list_{title}", on_click=select_title_callback, args=(title,))

# ─── 11) 기본 리스트 또는 검색 결과 ─────────────────────────────────────────────
else:
    if user_input:
        results = df[df['교재명'].str.contains(user_input, case=False, na=False)]
    else:
        results = df.copy()

    if results.empty:
        st.info("🔍 검색 결과가 없습니다.")
    else:
        for idx, row in results.iterrows():
            st.markdown("---")
            st.markdown(f"<h3>📖 {row['교재명']}</h3>", unsafe_allow_html=True)
            st.caption(f"🗂️ {row['카테고리']}   🧠 {row['난이도']}")
            st.write(f"📚 {row['에듀넷 키워드']}")
            st.write(f"🏫 {row['주요 키워드']}")
