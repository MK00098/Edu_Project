import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# ─── 1) 세션 상태 초기화 ──────────────────────────────────────────────────────
for key in (
    'temp_input',
    'user_input',
    'select_title',
    'selected_title',
    'selected_tag',
    'history'
):
    if key not in st.session_state:
        if key == 'history':
            st.session_state[key] = []
        elif 'input' in key or 'select' in key:
            st.session_state[key] = ''
        else:
            st.session_state[key] = None

# ─── 2) 내비게이션 헬퍼 ───────────────────────────────────────────────────────
def push_history():
    st.session_state.history.append({
        'selected_title': st.session_state.selected_title,
        'selected_tag':   st.session_state.selected_tag
    })

def go_back():
    if st.session_state.history:
        last = st.session_state.history.pop()
        st.session_state.selected_title = last['selected_title']
        st.session_state.selected_tag   = last['selected_tag']

def clear_selection():
    st.session_state.selected_title = None
    st.session_state.selected_tag   = None
    st.session_state.history        = []

# ─── 3) 콜백 정의 ─────────────────────────────────────────────────────────────
def update_input():
    st.session_state.user_input   = st.session_state.temp_input
    st.session_state.select_title = ''
    clear_selection()

def update_select():
    sel = st.session_state.select_title
    if sel and sel != "── 선택 없음 ──":
        push_history()
        st.session_state.selected_title = sel
        st.session_state.selected_tag   = None

def select_tag(tag):
    push_history()
    st.session_state.selected_tag   = tag
    st.session_state.selected_title = None

def select_title_callback(title):
    push_history()
    st.session_state.selected_title = title
    st.session_state.selected_tag   = None

# ─── 4) 구글 인증 & 시트 로드 ─────────────────────────────────────────────────
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ],
)
gc = gspread.authorize(credentials)
worksheet = gc.open_by_key("1flo64cRwCCpI5B9dS3C2_4AdcI1alMZeD7D8GQKz32Y") \
              .worksheet("students(for API)")

# ─── 5) 데이터 로딩 & 전처리 ─────────────────────────────────────────────────────
data = worksheet.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0]).rename(
    columns={'타이틀':'교재명','키워드':'에듀넷 키워드'}
)[['교재명','카테고리','난이도','에듀넷 키워드','주요 키워드','교수 전략']]

# ─── 6) 페이지 헤더 ───────────────────────────────────────────────────────────
st.markdown("<h2>📚 초등 AI/SW 교재 길라잡이</h2>", unsafe_allow_html=True)

# ─── 7) 검색창 & 입력 업데이트 ─────────────────────────────────────────────────
st.text_input(
    "step 1: 교재명을 입력하고 Enter를 눌러주세요",
    key='temp_input',
    on_change=update_input
)
user_input = st.session_state.user_input

# ─── 8) 추천 교재 드롭다운 ────────────────────────────────────────────────────
titles = df['교재명'].dropna().tolist()
sugs   = [t for t in titles if user_input.lower() in t.lower()]

if sugs:
    opts = ["── 선택 없음 ──"] + sugs
    if st.session_state.select_title not in opts:
        st.session_state.select_title = opts[0]
    st.selectbox(
        "step 2: 교재를 선택하세요",
        opts,
        key='select_title',
        on_change=update_select
    )
elif user_input:
    st.info("🔍 검색어에 해당하는 교재가 없습니다.")

# ─── 9) 현재 선택 상태 ─────────────────────────────────────────────────────────
sel_title = st.session_state.selected_title
sel_tag   = st.session_state.selected_tag

# ─── 10) 상세 / 태그 목록 또는 메인 목록 ────────────────────────────────────────
if sel_title or sel_tag:
    # 홈 & 뒤로가기 버튼 (한 줄, 양 끝)
    c1, _, c2 = st.columns([1, 18, 2])
    with c1:
        if st.button("🏠 홈"):
            clear_selection()
    with c2:
        if st.button("◀️ 뒤로가기"):
            go_back()

    if sel_title:
        # 상세 페이지
        row = df[df['교재명'] == sel_title].iloc[0]
        idx = df.index[df['교재명'] == sel_title][0]
        st.markdown(f"<h3>📖 {row['교재명']}</h3>", unsafe_allow_html=True)

        # 카테고리 · 난이도 · 에듀넷 키워드 (2줄)
        # 1행: 라벨
        lc, ld, le = st.columns([1,1,1])
        with lc: st.markdown("🗂️ **카테고리**", unsafe_allow_html=True)
        with ld: st.markdown("🧠 **난이도**", unsafe_allow_html=True)
        with le: st.markdown("📚 **에듀넷 키워드**", unsafe_allow_html=True)
        # 2행: 버튼
        bc, bd, be = st.columns([1,1,1])
        with bc:
            if st.button(row['카테고리'], key=f"cat_{idx}"):
                select_tag(row['카테고리'])
        with bd:
            if st.button(row['난이도'], key=f"diff_{idx}"):
                select_tag(row['난이도'])
        with be:
            if st.button(row['에듀넷 키워드'], key=f"edu_{idx}"):
                select_tag(row['에듀넷 키워드'])

        # 주요 키워드 2행 배치 (2개 + 3개)
        st.markdown("🏫 **주요 키워드**", unsafe_allow_html=True)
        kws = str(row['주요 키워드']).split('/')
        # 첫 줄 2개
        r1c1, r1c2 = st.columns([1,1])
        with r1c1: st.button(kws[0].strip(), key=f"maj_{idx}_0")
        with r1c2: st.button(kws[1].strip(), key=f"maj_{idx}_1")
        # 두 번째 줄 3개
        r2c1, r2c2, r2c3 = st.columns([1,1,1])
        with r2c1: st.button(kws[2].strip(), key=f"maj_{idx}_2")
        with r2c2: st.button(kws[3].strip(), key=f"maj_{idx}_3")
        with r2c3: st.button(kws[4].strip(), key=f"maj_{idx}_4")

        # 교수 전략: 회색 배경 박스
        st.markdown(
            f"<div style='background-color:#f5f5f5; padding:12px; border-radius:6px;'>"
            f"{row['교수 전략']}"
            "</div>",
            unsafe_allow_html=True
        )

    else:
        # 태그 기반 목록 페이지
        st.markdown("---")
        st.markdown(f"### 🔎 '{sel_tag}' 관련 교재 목록")
        mask = (
            (df['카테고리'] == sel_tag) |
            (df['난이도']   == sel_tag) |
            (df['에듀넷 키워드'].str.contains(sel_tag, na=False)) |
            (df['주요 키워드'].str.contains(sel_tag, na=False))
        )
        for t in df[mask]['교재명'].dropna():
            st.button(t, key=f"list_{t}", on_click=select_title_callback, args=(t,))

else:
    # 메인 / 검색 결과 목록
    results = df[df['교재명'].str.contains(user_input, case=False, na=False)] if user_input else df.copy()
    if results.empty:
        st.info("🔍 검색 결과가 없습니다.")
    else:
        for idx, row in results.iterrows():
            st.markdown("---")
            st.button(f"📖 {row['교재명']}", key=f"home_{idx}", on_click=select_title_callback, args=(row['교재명'],))
            st.caption(f"🗂️ {row['카테고리']}   🧠 {row['난이도']}")
            st.write(f"📚 {row['에듀넷 키워드']}")
            st.write(f"🏫 {row['주요 키워드']}")
