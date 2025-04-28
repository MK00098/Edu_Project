import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# 1) 세션 상태 초기화
for key in ('temp_input', 'user_input', 'selected_title', 'selected_tag'):
    if key not in st.session_state:
        st.session_state[key] = '' if 'input' in key or 'tag' in key else None

# 2) 구글 인증 & 시트 로드
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ],
)
gc = gspread.authorize(credentials)

SPREADSHEET_ID = "1flo64cRwCCpI5B9dS3C2_4AdcI1alMZeD7D8GQKz32Y"
WORKSHEET_NAME = "students(for API)"
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

# 3) 데이터 읽어서 DataFrame 만들기
data = worksheet.get_all_values()
df = pd.DataFrame(data)
header = df.iloc[0]
df = df[1:].reset_index(drop=True)
df.columns = header

# 필요한 컬럼만 추출 & 이름 매핑
cols = ['타이틀','카테고리','난이도','키워드','주요 키워드','교수 전략']
df = df[cols].rename(columns={
    '타이틀': '교재명',
    '키워드': '에듀넷 키워드'
})
df['추가예시'] = ''

# 4) UI 헤더
st.markdown("<h2>📚 초등 AI 교재 인사이트</h2>", unsafe_allow_html=True)

# 5) 검색어 입력 및 상태 업데이트
def update_input():
    st.session_state['user_input'] = st.session_state['temp_input']
    st.session_state['selected_title'] = None
    st.session_state['selected_tag'] = None

st.text_input(
    "초등학교 교재명을 검색하세요",
    key='temp_input',
    on_change=update_input
)

# 6) 제목 추천 버튼
user_input = st.session_state['user_input']
title_list = df['교재명'].dropna().tolist()
for title in title_list:
    if user_input and user_input.lower() in title.lower():
        if st.button(title, key=f"sugg_{title}"):
            st.session_state['selected_title'] = title
            st.session_state['selected_tag'] = None
            break

selected_title = st.session_state['selected_title']
selected_tag   = st.session_state['selected_tag']

# 7) 결과 필터링 로직
if selected_title:
    results = df[df['교재명'] == selected_title]
elif selected_tag:
    results = df[
        (df['카테고리']          == selected_tag) |
        (df['난이도']            == selected_tag) |
        (df['에듀넷 키워드'].str.contains(selected_tag, na=False)) |
        (df['주요 키워드'].str.contains(selected_tag, na=False))
    ]
elif user_input:
    results = df[df['교재명'].str.contains(user_input, case=False, na=False)]
else:
    results = df.copy()

# 8) 결과 출력
if not results.empty:
    for idx, row in results.iterrows():
        st.markdown("---")
        st.markdown(f"<h3>📖 {row['교재명']}</h3>", unsafe_allow_html=True)

        # 카테고리
        st.markdown("<h4>🗂️ 카테고리</h4>", unsafe_allow_html=True)
        if st.button(row['카테고리'], key=f"cat_{idx}"):
            st.session_state['selected_tag'] = row['카테고리']
            st.session_state['selected_title'] = None
            st.session_state['user_input'] = ''

        # 난이도
        st.markdown("<h4>🧠 난이도</h4>", unsafe_allow_html=True)
        if st.button(row['난이도'], key=f"diff_{idx}"):
            st.session_state['selected_tag'] = row['난이도']
            st.session_state['selected_title'] = None
            st.session_state['user_input'] = ''

        # 에듀넷 키워드
        st.markdown("<h4>📚 에듀넷 키워드</h4>", unsafe_allow_html=True)
        for kw in str(row['에듀넷 키워드']).split('/'):
            kw = kw.strip()
            if not kw:
                continue
            if st.button(kw, key=f"edu_{idx}_{kw}"):
                st.session_state['selected_tag'] = kw
                st.session_state['selected_title'] = None
                st.session_state['user_input'] = ''

        # 주요 키워드
        st.markdown("<h4>🏫 주요 키워드</h4>", unsafe_allow_html=True)
        for kw in str(row['주요 키워드']).split('/'):
            kw = kw.strip()
            if not kw:
                continue
            if st.button(kw, key=f"major_{idx}_{kw}"):
                st.session_state['selected_tag'] = kw
                st.session_state['selected_title'] = None
                st.session_state['user_input'] = ''

        # 교수 전략
        st.markdown("<h4>💡 교수 전략</h4>", unsafe_allow_html=True)
        st.info(row['교수 전략'])

        # 추가 예시
        st.markdown("<h4>🧩 추가 예시</h4>", unsafe_allow_html=True)
        st.write(row['추가예시'])
else:
    st.info("검색 결과가 없습니다. 다른 키워드를 입력해 주세요.")
