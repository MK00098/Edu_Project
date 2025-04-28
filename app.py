import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh

# --- 자동 새로고침 (선택 사항) ---
st_autorefresh(interval=60000, limit=None, key="refresh")  # 60초마다 새로고침

# --- 설정 부분 ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# 서비스 계정 키를 Streamlit Secrets에서 가져옴
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

gc = gspread.authorize(credentials)

SPREADSHEET_ID = "1flo64cRwCCpI5B9dS3C2_4AdcI1alMZeD7D8GQKz32Y"
WORKSHEET_NAME = "students(for API)"

# 구글시트 연결
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
    '주요 개념 5개: 맵핑용', 
    '교수 전략'
]
df = df[columns_to_keep]

# 컬럼명 매핑
df = df.rename(columns={
    '타이틀': '교재명',
    '카테고리': '카테고리',
    '난이도': '난이도',
    '키워드': '일반 키워드',
    '주요 개념 5개: 맵핑용': '산업연계 키워드',
    '교수 전략': '교수 전략'
})

# 추가예시 컬럼 생성
df['추가예시'] = ''

# --- Streamlit UI ---
st.title("📚 초등 AI 교재 인사이트")

# 교재명 리스트 준비
title_list = df['교재명'].dropna().unique().tolist()

# 검색창 + 추천 리스트
search = st.text_input("초등학교 교재명을 입력하세요", placeholder="예: 소프트웨어")

# 자동 추천 드롭다운
if search:
    matching_titles = [title for title in title_list if search.lower() in title.lower()]
    if matching_titles:
        selected_title = st.selectbox("추천 교재명", matching_titles)
    else:
        selected_title = None
else:
    selected_title = None

# 결과 필터링
if selected_title:
    filtered = df[df['교재명'] == selected_title]
elif search:
    filtered = df[df['교재명'].str.contains(search, case=False, na=False)]
else:
    filtered = df.copy()

# 검색 결과 출력
if not filtered.empty:
    for idx, row in filtered.iterrows():
        st.markdown("---")
        st.header(f"📖 {row['교재명']}")
        st.caption(f"🗂️ 카테고리: {row.get('카테고리', '')}")

        st.subheader("🧠 난이도")
        st.success(row.get('난이도', ''))

        st.subheader("📝 일반 키워드")
        st.write(row.get('일반 키워드', ''))

        st.subheader("🏫 산업연계 키워드")
        st.write(row.get('산업연계 키워드', ''))

        st.subheader("💡 교수 전략")
        st.info(row.get('교수 전략', ''))

        st.subheader("🧩 추가 예시")
        st.write(row.get('추가예시', ''))
else:
    st.info("검색 결과가 없습니다. 다른 키워드를 입력해 주세요.")
