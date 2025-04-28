# … (생략) …

# 결과 출력
if not results.empty:
    for idx, row in results.iterrows():
        st.markdown("---")
        st.markdown(f"<h3>📖 {row['교재명']}</h3>", unsafe_allow_html=True)

        # 1) 카테고리를 난이도와 같은 레벨로
        st.markdown("<h4>🗂️ 카테고리</h4>", unsafe_allow_html=True)
        # 2) 버튼으로 렌더링
        if st.button(row['카테고리'], key=f"cat_{idx}"):
            st.session_state['user_input'] = row['카테고리']

        st.markdown("<h4>🧠 난이도</h4>", unsafe_allow_html=True)
        if st.button(row['난이도'], key=f"diff_{idx}"):
            st.session_state['user_input'] = row['난이도']

        st.markdown("<h4>📚 에듀넷 키워드</h4>", unsafe_allow_html=True)
        # “/”로 구분된 키워드 분할해서 각각 버튼으로 출력
        for kw in row['에듀넷 키워드'].split('/'):
            if st.button(kw.strip(), key=f"edu_{idx}_{kw}"):
                st.session_state['user_input'] = kw.strip()

        st.markdown("<h4>🏫 주요 키워드</h4>", unsafe_allow_html=True)
        for kw in row['주요 키워드'].split('/'):
            if st.button(kw.strip(), key=f"major_{idx}_{kw}"):
                st.session_state['user_input'] = kw.strip()

        st.markdown("<h4>💡 교수 전략</h4>", unsafe_allow_html=True)
        st.info(row['교수 전략'])

        st.markdown("<h4>🧩 추가 예시</h4>", unsafe_allow_html=True)
        st.write(row['추가예시'])
else:
    st.info("검색 결과가 없습니다. 다른 키워드를 입력해 주세요.")
