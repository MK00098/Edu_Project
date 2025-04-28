import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Secret에서 구글 인증 불러오기 ---
credentials = Credentials.from_service_account_info(
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

spreadsheet = gc.open_by_key(SPREADSHEET_ID)
worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

# --- 데이터 불러오기 ---
data = worksheet.get_all_values()
df = pd.DataFrame(data)

header = df.iloc[0]
df = df[1:].reset_index(drop=True)
df.columns = header

columns_to_keep = ['타이틀', '카테고리', '난이도', '키워드', '주요 키워드', '교수 전략']
df = df[columns_to_keep]

df = df.rename(columns={
    '타이틀': '교재명',
    '카테고리': '카테고리',
    '난이도': '난이도',
    '키워드': '에듀넷 키워드',
    '주요 키워드': '주요 키워드',
    '교수 전략': '교수 전략'
})

df['추가예시'] = ''

# --- Streamlit UI 시작 ---
st.markdown("<h2>📚 초등 AI 교재 인사이트</h2>", unsafe_allow_html=True)

# 세션 상태 초기화
for key in ['selected_title', 'selected_level', 'selected_keyword', 'selected_category', 'user_input', 'history', 'forward_history']:
    if key not in st.session_state:
        st.session_state[key] = None if key in ['selected_title', 'selected_level', 'selected_keyword', 'selected_category'] else [] if key in ['history', 'forward_history'] else ''

# --- 버튼 3개 가로 배치 ---
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("🏠 홈으로"):
        st.session_state['selected_title'] = None
        st.session_state['selected_level'] = None
        st.session_state['selected_keyword'] = None
        st.session_state['selected_category'] = None
        st.session_state['user_input'] = ''
        st.session_state['history'] = []
        st.session_state['forward_history'] = []
        st.rerun()

with col2:
    if st.session_state['history']:
        if st.button("🔙 뒤로가기"):
            current = {
                'selected_title': st.session_state['selected_title'],
                'selected_level': st.session_state['selected_level'],
                'selected_keyword': st.session_state['selected_keyword'],
                'selected_category': st.session_state['selected_category'],
                'user_input': st.session_state['user_input']
            }
            st.session_state['forward_history'].append(current)
            last_state = st.session_state['history'].pop()
            st.session_state.update(last_state)
            st.rerun()

with col3:
    if st.session_state['forward_history']:
        if st.button("🔜 앞으로가기"):
            st.session_state['history'].append({
                'selected_title': st.session_state['selected_title'],
                'selected_level': st.session_state['selected_level'],
                'selected_keyword': st.session_state['selected_keyword'],
                'selected_category': st.session_state['selected_category'],
                'user_input': st.session_state['user_input']
            })
            next_state = st.session_state['forward_history'].pop()
            st.session_state.update(next_state)
            st.rerun()

# --- 검색창 ---
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

# 추천 검색어
title_list = df['교재명'].dropna().tolist()
user_input = st.session_state['user_input']

selected_title = st.session_state['selected_title']
selected_level = st.session_state['selected_level']
selected_keyword = st.session_state['selected_keyword']
selected_category = st.session_state['selected_category']

if user_input and not (selected_title or selected_level or selected_keyword or selected_category):
    suggestions = [title for title in title_list if user_input.lower() in title.lower()]
    for suggestion in suggestions:
        if st.button(f"🔎 {suggestion}", key=f"suggestion_{suggestion}"):
            st.session_state['selected_title'] = suggestion
            st.session_state['selected_level'] = None
            st.session_state['selected_keyword'] = None
            st.session_state['selected_category'] = None
            st.session_state['history'] = []
            st.session_state['forward_history'] = []
            st.rerun()

# --- 필터링
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

# --- 결과 출력
if not results.empty:
    for idx, row in results.iterrows():
        st.markdown("---")
        st.markdown(f"<h3>📖 {row.get('교재명', '')}</h3>", unsafe_allow_html=True)

        # 카테고리
        st.markdown("<h4>📁 카테고리</h4>", unsafe_allow_html=True)
        if st.button(f"{row.get('카테고리', '')}", key=f"category_{idx}"):
            st.session_state['history'].append({
                'selected_title': st.session_state['selected_title'],
                'selected_level': st.session_state['selected_level'],
                'selected_keyword': st.session_state['selected_keyword'],
                'selected_category': st.session_state['selected_category'],
                'user_input': st.session_state['user_input']
            })
            st.session_state['selected_category'] = row.get('카테고리')
            st.session_state['selected_title'] = None
            st.session_state['selected_level'] = None
            st.session_state['selected_keyword'] = None
            st.rerun()

        # 난이도
        st.markdown("<h4>🧠 난이도</h4>", unsafe_allow_html=True)
        if st.button(f"{row.get('난이도', '')}", key=f"level_{idx}"):
            st.session_state['history'].append({
                'selected_title': st.session_state['selected_title'],
                'selected_level': st.session_state['selected_level'],
                'selected_keyword': st.session_state['selected_keyword'],
                'selected_category': st.session_state['selected_category'],
                'user_input': st.session_state['user_input']
            })
            st.session_state['selected_level'] = row.get('난이도')
            st.session_state['selected_title'] = None
            st.session_state['selected_keyword'] = None
            st.session_state['selected_category'] = None
            st.rerun()

        # 에듀넷 키워드
        st.markdown("<h4>📚 에듀넷 키워드</h4>", unsafe_allow_html=True)
        st.write(row.get('에듀넷 키워드', ''))

        # 주요 키워드 (2+3개 고정, 줄바꿈 없음)
        st.markdown("<h4>🏫 주요 키워드</h4>", unsafe_allow_html=True)
        keywords = str(row.get('주요 키워드', '')).split('/')

        if keywords:
            # 위에 2개
            top_cols = st.columns(2)
            for i in range(min(2, len(keywords))):
                keyword = keywords[i].strip()
                if keyword:
                    with top_cols[i]:
                        if st.button(keyword, key=f"keyword_top_{idx}_{i}"):
                            st.session_state['history'].append({
                                'selected_title': st.session_state['selected_title'],
                                'selected_level': st.session_state['selected_level'],
                                'selected_keyword': st.session_state['selected_keyword'],
                                'selected_category': st.session_state['selected_category'],
                                'user_input': st.session_state['user_input']
                            })
                            st.session_state['selected_keyword'] = keyword
                            st.session_state['selected_title'] = None
                            st.session_state['selected_level'] = None
                            st.session_state['selected_category'] = None
                            st.rerun()

            # 아래에 3개
            bottom_cols = st.columns(3)
            for j in range(2, min(5, len(keywords))):
                keyword = keywords[j].strip()
                if keyword:
                    with bottom_cols[(j-2) % 3]:
                        if st.button(keyword, key=f"keyword_bottom_{idx}_{j}"):
                            st.session_state['history'].append({
                                'selected_title': st.session_state['selected_title'],
                                'selected_level': st.session_state['selected_level'],
                                'selected_keyword': st.session_state['selected_keyword'],
                                'selected_category': st.session_state['selected_category'],
                                'user_input': st.session_state['user_input']
                            })
                            st.session_state['selected_keyword'] = keyword
                            st.session_state['selected_title'] = None
                            st.session_state['selected_level'] = None
                            st.session_state['selected_category'] = None
                            st.rerun()

        # 교수 전략
        st.markdown("<h4>💡 교수 전략</h4>", unsafe_allow_html=True)
        st.info(row.get('교수 전략', ''))

        # 추가 예시
        st.markdown("<h4>🧩 추가 예시</h4>", unsafe_allow_html=True)
        st.write(row.get('추가예시', ''))

else:
    st.info("검색 결과가 없습니다. 다른 키워드를 입력해 주세요.")
