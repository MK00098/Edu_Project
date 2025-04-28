import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# ─── 1) 세션 상태 초기화 ──────────────────────────────────────────────────────
for key in ('temp_input', 'user_input', 'select_title', 'selected_title', 'selected_tag'):
    if key not in st.session_state:
        st.session_state[key] = '' if 'input' in key or 'select' in key else None

# ─── 콜백 함수 정의 ───────────────────────────────────────────────────────────
def update_input():
    st.session_state['user_input']       = st.session_state['temp_input']
    st.session_state['select_title']     = ''   # 드롭다운 초기화
    st.session_state['selected_title']   = None
    st.session_state['selected_tag']     = None

def update_select():
    sel = st.session_state['select_title']
    # 드롭다운에서 실제 선택된 값이 "선택 없음"이 아니면 상세페이지로
    if sel and sel != "── 선택 없음 ──":
        st.session_state['selected_title'] = sel
        st.session_state['selected_tag']   = None

def select_tag(tag):
    st.session_state['selected_tag']   = tag
    st.session_state['selected_title'] = None

def select_title_callback(title):
    st.session_state['selected_title'] = title
    st.session_state['selected_tag']   = None

def clear_selection():
    st.session_state['selected_title'] = None
    st.session_state['selected_tag']   = None

# ─── 2) 구글 인증 & 시트 로드 ─────────────────────────────────────────────────
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ],
)
gc        = gspread.authorize(credentials)
SPREADSHEET_ID  = "1flo64cRwCCpI5B9dS3C2_4AdcI1alMZeD7D8GQKz32Y"
WORKSHEET_NAME  = "students(for API)"
worksheet       = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

# ─── 3) 데이터 로딩 & 전처리 ─────────────────────────────────────────────────────
data = worksheet.get_all_values()
df   = pd.DataFrame(data[1:], columns=data[0])
df   = df[['타이틀','카테고리','난이도','키워드','주요 키워드','교수 전략']].rename(
           columns={'타이틀':'교재명','키워드':'에듀넷 키워드'}
       )
df['추가예시'] = ''

# ─── 4) 페이지 헤더 ───────────────────────────────────────────────────────────
st.markdown("<h2>📚 초등 AI 교재 인사이트</h2>", unsafe_allow_html=True)

# ─── 5) 검색창 & 입력 업데이트 ─────────────────────────────────────────────────
st.text_input(
    "초등학교 교재명을 검색하세요",
    key='temp_input',
    on_change=update_input
)
user_input = st.session_state['user_input']

# ─── 6) 추천 교재 드롭다운 (수정) ───────────────────────────────────────────────
title_list  = df['교재명'].dropna().tolist()
suggestions = [t for t in title_list if user_input.lower() in t.lower()]

if suggestions:
    options = ["── 선택 없음 ──"] + suggestions

    # 세션 상태 값이 options 에 없으면 기본을 "── 선택 없음 ──" 으로
    curr = st.session_state['select_title']
    if curr not in options:
        curr = options[0]
        st.session_state['select_title'] = curr

    st.selectbox(
        "추천 교재를 선택하세요",
        options,
        index=options.index(curr),
        key='select_title',
        on_change=update_select
    )
else:
    if user_input:
        st.info("🔍 검색어에 해당하는 교재가 없습니다.")

# ─── 7) 현재 선택값 가져오기 ───────────────────────────────────────────────────
selected_title = st.session_state['selected_title']
selected_tag   = st.session_state['selected_tag']

# ─── 8) 상세 페이지 ─────────────────────────────────────────────────────────
if selected_title:
    st.button("🔙 뒤로", on_click=clear_selection)
    row = df[df['교재명']==selected_title].iloc[0]

    st.markdown(f"<h3>📖 {row['교재명']}</h3>", unsafe_allow_html=True)
    # (중략) 동일한 태그·교수전략·추가예시 블록

# ─── 9) 태그 기반 목록 페이지 ─────────────────────────────────────────────────
elif selected_tag:
    st.button("🔙 뒤로", on_click=clear_selection)
    st.markdown("---")
    st.markdown(f"### 🔎 '{selected_tag}' 관련 교재 목록")

    mask     = (
        (df['카테고리']==selected_tag) |
        (df['난이도']==selected_tag)     |
        (df['에듀넷 키워드'].str.contains(selected_tag, na=False)) |
        (df['주요 키워드'].str.contains(selected_tag, na=False))
    )
    filtered = df[mask]['교재명'].dropna().tolist()
    for title in filtered:
        st.button(title, key=f"list_{title}",
                  on_click=select_title_callback, args=(title,))

# ─── 10) 기본 리스트 또는 이름 검색 결과 ───────────────────────────────────────
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
