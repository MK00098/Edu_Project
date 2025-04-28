import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh

# --- 자동 새로고침 (선택, 안 넣어도 무방) ---
st_autorefresh(interval=60000, limit=None, key="refresh")  # 60초마다 새로고침

# --- 설정 부분 ---
# Google Cloud 서비스 계정 정보는 Streamlit Secrets에서 가져오기
SHEET_JSON = st.secrets["gcp_service_account"]

# 구글 스프레드시트 ID는 코드에 직접 작성
SPREADSHEET_ID = "1flo64cRwCCpI5B9dS3C2_4AdcI1alMZeD7D8GQKz32Y"
WORKSHEET_NAME = "students(for API)"

# --- 구글시트 연결 ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
credentials = Credentials.from_service_account_info(SHEET_JSON, scopes=scope)
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

# 교재명 자동 추천 기능
search = st.text_input("초등학교 교재명을 검색하세요", placeholder="교재명을 입력하세요...")

# 필터링
if search:
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
