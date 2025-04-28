# --- (1) 검색어, 추천 버튼 로직 등 생략 …  
user_input = st.session_state['user_input']
selected_title = None

# (추천 버튼 클릭 시 selected_title 세팅 생략…)

# --- (2) results 할당
if selected_title:
    results = df[df['교재명'] == selected_title]
else:
    if user_input:
        results = df[df['교재명'].str.contains(user_input, case=False, na=False)]
    else:
        # 입력도 없고, 버튼도 안 눌렸으면 전체 보여주기
        results = df.copy()

# --- (3) UI 출력
if not results.empty:
    for idx, row in results.iterrows():
        st.markdown("---")
        st.markdown(f"<h3>📖 {row['교재명']}</h3>", unsafe_allow_html=True)

        st.markdown("<h4>🗂️ 카테고리</h4>", unsafe_allow_html=True)
        if st.button(row['카테고리'], key=f"cat_{idx}"):
            st.session_state['user_input'] = row['카테고리']

        st.markdown("<h4>🧠 난이도</h4>", unsafe_allow_html=True)
        if st.button(row['난이도'], key=f"diff_{idx}"):
            st.session_state['user_input'] = row['난이도']

        st.markdown("<h4>📚 에듀넷 키워드</h4>", unsafe_allow_html=True)
        for kw in str(row['에듀넷 키워드']).split('/'):
            if st.button(kw.strip(), key=f"edu_{idx}_{kw}"):
                st.session_state['user_input'] = kw.strip()

        st.markdown("<h4>🏫 주요 키워드</h4>", unsafe_allow_html=True)
        for kw in str(row['주요 키워드']).split('/'):
            if st.button(kw.strip(), key=f"major_{idx}_{kw}"):
                st.session_state['user_input'] = kw.strip()

        st.markdown("<h4>💡 교수 전략</h4>", unsafe_allow_html=True)
        st.info(row['교수 전략'])

        st.markdown("<h4>🧩 추가 예시</h4>", unsafe_allow_html=True)
        st.write(row['추가예시'])
else:
    st.info("검색 결과가 없습니다. 다른 키워드를 입력해 주세요.")
