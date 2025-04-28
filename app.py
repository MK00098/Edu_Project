# Streamlit 대쉬보드 (on_change 콜백으로 session_state 수정)

import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# --- Secret에서 구글 인증 불러오기 ---
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
)

# --- 구글시트 연결 ---
gc = gspread.authorize(credentials)
SPREADSHEET_ID = "1flo64cRwCCpI5B9dS3C2_4AdcI1alMZeD7D8GQKz32Y"
WORKSHEET_NAME = "students(for API)"
worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

# --- 데이터 불러오기 & 전처리 ---
data = worksheet.get_all_values()
df = pd.DataFrame(data)
header = df.iloc[0]
df = df[1:].reset_index(drop=True)
df.columns = header

# 필요한 컬럼만 추출 및 매핑
df = df[[
    '타이틀', '카테고리', '난이도',
    '키워드', '주요 키워드', '교수 전략'
]].rename(columns={
    '타이틀': '교재명',
    '카테고리': '카테고리',
    '난이도': '난이도',
    '키워드': '에듀넷 키워드',
    '주요 키워드': '주요 키워드',
    '교수 전략': '교수 전략'
})
df['추가예시'] = ''

# --- Streamlit UI 시작 ---
st.markdown("<h2 style='text-align:center;'>📚 초등 AI 교재 인사이트</h2>", unsafe_allow_html=True)
st.markdown("---")

# --- 세션 상태 초기화 ---
for key in ('temp_input', 'user_input', 'selected_title'):
    if key not in st.session_state:
        st.session_state[key] = ""

# --- 콜백 함수 정의 ---
def on_select():
    # selectbox on_change 콜백
    st.session_state['user_input'] = st.session_state['selected_title']
    st.session_state['temp_input'] = st.session_state['selected_title']

# --- 입력창 ---
st.text_input("초등학교 교재명을 검색하세요", key='temp_input')

temp_input = st.session_state['temp_input']
user_input = st.session_state['user_input']

# --- 추천 드랍다운 (입력만 있고 아직 선택 전) ---
title_list = df['교재명'].dropna().tolist()
if temp_input and not user_input:
    filtered = [t for t in title_list if temp_input.lower() in t.lower()]
    if filtered:
        st.selectbox(
            "🔎 검색 결과",
            filtered,
            key='selected_title',
            on_change=on_select
        )

# --- 검색 결과 필터링 (항상 포함 검색) ---
if user_input:
    results = df[df['교재명'].str.contains(user_input, case=False, na=False)]
else:
    results = pd.DataFrame()

# --- 결과 출력 ---
if not results.empty and user_input:
    for _, row in results.iterrows():
        with st.container():
            st.markdown("---")
            st.markdown(
                f"<h3 style='color:#4CAF50;'>📖 {row['교재명']}</h3>",
                unsafe_allow_html=True
            )

            st.markdown("<h4>📁 카테고리</h4>", unsafe_allow_html=True)
            st.write(row['카테고리'])

            st.markdown("<h4>🧠 난이도</h4>", unsafe_allow_html=True)
            st.success(row['난이도'])

            st.markdown("<h4>📚 에듀넷 키워드</h4>", unsafe_allow_html=True)
            st.write(row['에듀넷 키워드'])

            st.markdown("<h4>🏫 주요 키워드</h4>", unsafe_allow_html=True)
            st.write(row['주요 키워드'])

            st.markdown("<h4>💡 교수 전략</h4>", unsafe_allow_html=True)
            st.info(row['교수 전략'])

            st.markdown("<h4>🧩 추가 예시</h4>", unsafe_allow_html=True)
            st.write(row['추가예시'])
            st.markdown(" ")
elif temp_input:
    st.info("검색 결과가 없습니다. 다른 키워드를 입력해 주세요.")
