# Streamlit 대쉬보드 (모든 민감정보 Secrets에서 불러오는 최종 버전)

import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# --- Secret에서 불러오기 ---
SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
WORKSHEET_NAME = st.secrets["WORKSHEET_NAME"]

# --- 구글시트 연결 ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],  # 🔥 json.dumps 필요 없음
    scopes=scope
)

gc = gspread.authorize(credentials)
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
st.title("📚 초등 AI 교재 인사이트")

# 세션 상태로 입력값 관리
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ''

def update_input():
    st.session_state['user_input'] = st.session_state['temp_input']

# 입력창
st.text_input(
    "초등학교 교재명을 검색하세요",
    key='temp_input',
    on_change=update_input
)

# 교재명 리스트
title_list = df['교재명'].dropna().tolist()

selected_title = None
user_input = st.session_state['user_input']

if user_input:
    # 추천 검색어 리스트
    suggestions = [title for title in title_list if user_input.lower() in title.lower()]
    
    for suggestion in suggestions:
        if st.button(suggestion):
            selected_title = suggestion
            break

# 최종 검색 결과
if selected_title:
    results = df[df['교재명'] == selected_title]
else:
    results = df[df['교재명'].str.contains(user_input, case=False, na=False)] if user_input else df

# 결과 출력
if not results.empty:
    for idx, row in results.iterrows():
        st.markdown("---")
        st.header(f"📖 {row.get('교재명', '')}")

        st.caption(f"🗂️ 카테고리: {row.get('카테고리', '')}")

        st.subheader("🧠 난이도")
        st.success(row.get('난이도', ''))

        st.subheader("📚 에듀넷 키워드")
        st.write(row.get('에듀넷 키워드', ''))

        st.subheader("🏫 주요 키워드")
        st.write(row.get('주요 키워드', ''))

        st.subheader("💡 교수 전략")
        st.info(row.get('교수 전략', ''))

        st.subheader("🧩 추가 예시")
        st.write(row.get('추가예시', ''))
else:
    st.info("검색 결과가 없습니다. 다른 키워드를 입력해 주세요.")
