import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# 1) 세션 상태 초기화: 반드시 가장 위에!
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ''
if 'selected_title' not in st.session_state:
    st.session_state['selected_title'] = None

# 2) 구글 인증, 시트 로드 (생략) …

# 3) 입력 업데이트 콜백
def update_input():
    st.session_state['user_input'] = st.session_state['temp_input']
    st.session_state['selected_title'] = None  # 새 검색어 입력 시 이전 선택 초기화

# 4) 입력창
st.text_input(
    "초등학교 교재명을 검색하세요",
    key='temp_input',
    on_change=update_input
)

# 5) 세션에서 안전하게 꺼내 쓰기
user_input     = st.session_state['user_input']
selected_title = st.session_state['selected_title']

# 6) 추천 버튼 로직 (예시)
title_list = df['교재명'].tolist()
for t in title_list:
    if user_input.lower() in t.lower() and st.button(t, key=t):
        st.session_state['selected_title'] = t
        selected_title = t
        break

# 7) results 정의
if selected_title:
    results = df[df['교재명'] == selected_title]
elif user_input:
    results = df[df['교재명'].str.contains(user_input, case=False, na=False)]
else:
    results = df.copy()

# 8) 결과 출력
if not results.empty:
    # … 앞서 드린 버튼·마크다운 출력 코드 …
else:
    st.info("검색 결과가 없습니다. 다른 키워드를 입력해 주세요.")
