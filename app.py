# Streamlit 대쉬보드 (카테고리/난이도/키워드/타이틀 네비게이션 통합 버전)

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

# 🔥 스프레드시트 ID와 워크시트 이름
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

# 추가 예시 컬럼 생성
df['추가예시'] = ''

# --- Streamlit UI 시작 ---
st.markdown("<h2>📚 초등 AI 교재 인사이트</h2>", unsafe_allow_html=True)

# 세션 상태 초기화
if 'selected_title' not in st.session_state:
    st.session_state['selected_title'] = None
if 'selected_level' not in st.session_state:
    st.session_state['selected_level'] = None
if 'selected_keyword' not in st.session_state:
    st.session_state['selected_keyword'] = None
if 'selected_category' not in st.session_state:
    st.session_state['selected_category'] = None
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ''

# 입력창
def update_input():
    st.session_state['user_input'] = st.session_state['temp_input']
    st.session_state['selected_title'] = None
    st.session_state['selected_level'] = None
    st.session_state['selected_keyword'] = None
    st.session_state['selected_category'] = None

st.text_input(
    "초등학교 교재명을 검색하세요",
    key='temp_input',
    on_change=update_input
)

# 검색 조건 설정
user_input = st.session_state['user_input']
selected_title = st.session_state['selected_title']
selected_level = st.session_state['selected_level']
selected_keyword = st.session_state['selected_keyword']
selected_category = st.session_state['selected_category']

# 필터링
if selected_title:
    results = df[df['교재명'] == selected_title]
elif selected_category:
    results = df[df['카테고리'] == selected_category]
elif selected_level:
    results = df[df['난이도'] == selected_level]
elif selected_keyword:
    results = df[df['주요 키워드'].str.contains(selected_keyword, na=False)]
elif user_input:
    results = df[df['교재명'].str.contains(user_input, case=False, na=False)]
else:
    results = df.copy()

# 결과 출력
if not results.empty:
    for idx, row in results.iterrows():
        st.markdown("---")
        st.markdown(f"<h3>📖 {row.get('교재명', '')}</h3>", unsafe_allow_html=True)

        # 카테고리
        st.markdown("<h4>📁 카테고리</h4>", unsafe_allow_html=True)
        if st.button(f"{row.get('카테고리', '')}", key=f"category_{idx}"):
            st.session_state['selected_category'] = row.get('카테고리')
            st.session_state['selected_title'] = None
            st.session_state['selected_level'] = None
            st.session_state['selected_keyword'] = None
            st.experimental_rerun()

        # 난이도
        st.markdown("<h4>🧠 난이도</h4>", unsafe_allow_html=True)
        if st.button(f"{row.get('난이도', '')}", key=f"level_{idx}"):
            st.session_state['selected_level'] = row.get('난이도')
            st.session_state['selected_title'] = None
            st.session_state['selected_keyword'] = None
            st.session_state['selected_category'] = None
            st.experimental_rerun()

        # 에듀넷 키워드
        st.markdown("<h4>📚 에듀넷 키워드</h4>", unsafe_allow_html=True)
        st.write(row.get('에듀넷 키워드', ''))

        # 주요 키워드
        st.markdown("<h4>🏫 주요 키워드</h4>", unsafe_allow_html=True)
        keywords = str(row.get('주요 키워드', '')).split('/')
        for keyword in keywords:
            if keyword.strip() != "":
                if st.button(keyword.strip(), key=f"keyword_{idx}_{keyword}"):
                    st.session_state['selected_keyword'] = keyword.strip()
                    st.session_state['selected_title'] = None
                    st.session_state['selected_level'] = None
                    st.session_state['selected_category'] = None
                    st.experimental_rerun()

        # 교수 전략
        st.markdown("<h4>💡 교수 전략</h4>", unsafe_allow_html=True)
        st.info(row.get('교수 전략', ''))

        # 추가 예시
        st.markdown("<h4>🧩 추가 예시</h4>", unsafe_allow_html=True)
        st.write(row.get('추가예시', ''))

        # 교재명 다시 버튼으로
        if st.button(f"👉 {row.get('교재명', '')} 상세보기", key=f"title_{idx}"):
            st.session_state['selected_title'] = row.get('교재명')
            st.session_state['selected_level'] = None
            st.session_state['selected_keyword'] = None
            st.session_state['selected_category'] = None
            st.experimental_rerun()

else:
    st.info("검색 결과가 없습니다. 다른 키워드를 입력해 주세요.")
