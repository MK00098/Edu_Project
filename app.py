# Streamlit 대쉬보드 (최적화 버전)

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

# --- 스프레드시트 ID와 워크시트 이름 설정 ---
SPREADSHEET_ID = "1flo64cRwCCpI5B9dS3C2_4AdcI1alMZeD7D8GQKz32Y"
WORKSHEET_NAME = "students(for API)"

spreadsheet = gc.open_by_key(SPREADSHEET_ID)
worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

# --- 데이터 불러오기 ---
data = worksheet.get_all_values()
df = pd.DataFrame(data)

# 첫 행을 헤더로 설정
header = df.iloc[0]
df = df[1:].reset_index(drop=True)
df.columns = header

# 필요한 컬럼만 추출
columns_to_keep = [
    '타이틀', 
    '카테고리', 
    '난이도', 
    '키워드', 
    '주요 키워드',    
    '교수 전략'
]
df = df[columns_to_keep]

# 컬럼명 매핑
df = df.rename(columns={
    '타이틀': '교재명',
    '카테고리': '카테고리',
    '난이도': '난이도',
    '키워드': '에듀넷 키워드',
    '주요 키워드': '주요 키워드',
    '교수 전략': '교수 전략'
})

# 추가예시 컬럼 생성
df['추가예시'] = ''

# --- Streamlit UI 시작 ---
st.markdown("<h2 style='text-align:center;'>📚 초등 AI 교재 인사이트</h2>", unsafe_allow_html=True)
st.markdown("---")

# --- 세션 상태 초기화 ---
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ''
if 'temp_input' not in st.session_state:
    st.session_state['temp_input'] = ''

# --- 입력창 ---
st.text_input(
    "초등학교 교재명을 검색하세요",
    key='temp_input'
)

user_input = st.session_state['user_input']
temp_input = st.session_state['temp_input']

# --- 추천 드랍다운 (temp_input 있을 때만) ---
title_list = df['교재명'].dropna().tolist()

if temp_input and not user_input:
    filtered_suggestions = [title for title in title_list if temp_input.lower() in title.lower()]
    if filtered_suggestions:
        selected_title = st.selectbox("🔎 검색 결과", filtered_suggestions)
        if selected_title:
            st.session_state['user_input'] = selected_title
            st.session_state['temp_input'] = selected_title
            st.rerun()

# --- 검색 결과 필터링 ---
if user_input:
    results = df[df['교재명'].str.contains(user_input, case=False, na=False)]
else:
    results = pd.DataFrame()  # 아무것도 입력 안 하면 빈 결과

# --- 결과 출력 ---
if not results.empty and user_input:
    for idx, row in results.iterrows():
        with st.container():
            st.markdown("---")
            st.markdown(f"<h3 style='color:#4CAF50;'>📖 {row.get('교재명', '')}</h3>", unsafe_allow_html=True)
            
            st.markdown(" ")
            st.markdown("<h4>📁 카테고리</h4>", unsafe_allow_html=True)
            st.write(row.get('카테고리', ''))

            st.markdown("<h4>🧠 난이도</h4>", unsafe_allow_html=True)
            st.success(row.get('난이도', ''))

            st.markdown("<h4>📚 에듀넷 키워드</h4>", unsafe_allow_html=True)
            st.write(row.get('에듀넷 키워드', ''))

            st.markdown("<h4>🏫 주요 키워드</h4>", unsafe_allow_html=True)
            st.write(row.get('주요 키워드', ''))

            st.markdown("<h4>💡 교수 전략</h4>", unsafe_allow_html=True)
            st.info(row.get('교수 전략', ''))

            st.markdown("<h4>🧩 추가 예시</h4>", unsafe_allow_html=True)
            st.write(row.get('추가예시', ''))
            
            st.markdown(" ")
elif temp_input:
    st.info("검색 결과가 없습니다. 다른 키워드를 입력해 주세요.")
