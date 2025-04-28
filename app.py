import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# 1) 세션 상태 초기화
for key in ('temp_input', 'user_input', 'selected_title', 'selected_tag'):
    if key not in st.session_state:
        # input/tag 키워드는 빈 문자열, 나머지는 None 으로 초기화
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
worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

# 3) 데이터 로딩 및 전처리
data = worksheet.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])
df = df[['타이틀', '카테고리', '난이도', '키워드', '주요 키워드', '교수 전략']].rename(
    columns={'타이틀': '교재명', '키워드': '에듀넷 키워드'}
)
df['추가예시'] = ''

# 4) 페이지 헤더
st.markdown("<h2>📚 초등 AI 교재 인사이트</h2>", unsafe_allow_html=True)

# 5) 검색창 & 입력 업데이트
def update_input():
    st.session_state['user_input'] = st.session_state['temp_input']
    st.session_state['selected_title'] = None
    st.session_state['selected_tag'] = None

st.text_input(
    "초등학교 교재명을 검색하세요",
    key='temp_input',
    on_change=update_input
)

user_input = st.session_state['user_input']
title_list = df['교재명'].dropna().tolist()

# 6) 추천 교재 드롭다운
suggestions = [t for t in title_list if user_input.lower() in t.lower()]
if suggestions:
    sel = st.selectbox(
        "추천 교재를 선택하세요",
        ["── 선택 없음 ──"] + suggestions,
        key='select_title'
    )
    if sel != "── 선택 없음 ──":
        st.session_state['selected_title'] = sel
else:
    st.write("🔍 검색어에 해당하는 교재가 없습니다.")

# 7) 필터링 로직
selected_title = st.session_state['selected_title']
selected_tag   = st.session_state['selected_tag']

if selected_title:
    results = df[df['교재명'] == selected_title]
elif selected_tag:
    mask = (
        (df['카테고리'] == selected_tag) |
        (df['난이도'] == selected_tag) |
        (df['에듀넷 키워드'].str.contains(selected_tag, na=False)) |
        (df['주요 키워드'].str.contains(selected_tag, na=False))
    )
    results = df[mask]
elif user_input:
    results = df[df['교재명'].str.contains(user_input, case=False, na=False)]
else:
    results = df.copy()

# 8) 결과 출력
if not results.empty:
    for idx, row in results.iterrows():
        st.markdown("---")
        st.markdown(f"<h3>📖 {row['교재명']}</h3>", unsafe_allow_html=True)

        # 클릭 가능한 태그들
        for label, col, sep in [
            ("🗂️ 카테고리", '카테고리', None),
            ("🧠 난이도",   '난이도',   None),
            ("📚 에듀넷 키워드", '에듀넷 키워드', '/'),
            ("🏫 주요 키워드",   '주요 키워드',   '/'),
        ]:
            st.markdown(f"<h4>{label}</h4>", unsafe_allow_html=True)
            items = [row[col]] if sep is None else str(row[col]).split(sep)
            for it in items:
                it = it.strip()
                if not it:
                    continue
                if st.button(it, key=f"{col}_{idx}_{it}"):
                    st.session_state['selected_tag']   = it
                    st.session_state['selected_title'] = None
                    st.session_state['user_input']     = ''

        # 교수 전략 & 추가 예시
        st.markdown("<h4>💡 교수 전략</h4>", unsafe_allow_html=True)
        st.info(row['교수 전략'])

        st.markdown("<h4>🧩 추가 예시</h4>", unsafe_allow_html=True)
        st.write(row['추가예시'])
else:
    st.info("🔍 검색 결과가 없습니다. 다른 키워드를 입력해 주세요.")
