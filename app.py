# app.py
import streamlit as st

# 게임 상태 초기화 함수
def initialize_game():
    """
    게임 상태를 초기화합니다.
    """
    st.session_state.word_history = []
    st.session_state.current_turn = 1
    st.session_state.last_word = ""
    st.session_state.game_over = False
    st.session_state.message = "게임을 시작합니다! 첫 단어를 입력해주세요."

# Streamlit 앱의 메인 함수
def main():
    st.set_page_config(
        page_title="단어 말 끝 이어가기 게임",
        layout="centered",
        initial_sidebar_state="auto"
    )

    st.title("단어 말 끝 이어가기 게임")
    st.write("마지막 글자로 시작하는 단어를 이어가세요!")

    # 게임 상태가 없으면 초기화
    if "word_history" not in st.session_state:
        initialize_game()

    # 게임 오버 상태일 경우 메시지 표시 및 재시작 버튼
    if st.session_state.game_over:
        st.error(st.session_state.message)
        if st.button("새 게임 시작"):
            initialize_game()
            st.experimental_rerun() # 상태 초기화 후 페이지 새로고침
        return # 게임 오버 시 더 이상 진행하지 않음

    # 현재 턴 및 마지막 단어 표시
    st.subheader(f"현재 턴: {st.session_state.current_turn}")
    if st.session_state.last_word:
        st.write(f"이전 단어: **{st.session_state.last_word}** (마지막 글자: `{st.session_state.last_word[-1]}`)")
    else:
        st.write("첫 단어를 입력해주세요.")

    # 사용자 입력 필드
    user_input = st.text_input(
        "단어를 입력하세요:",
        key="word_input",
        placeholder=f"'{st.session_state.last_word[-1]}'로 시작하는 단어" if st.session_state.last_word else "단어를 입력하세요"
    )

    # 메시지 출력 영역
    message_placeholder = st.empty()
    message_placeholder.info(st.session_state.message)

    # 단어 제출 버튼
    if st.button("제출"):
        if not user_input:
            st.session_state.message = "단어를 입력해주세요!"
            message_placeholder.warning(st.session_state.message)
            return

        new_word = user_input.strip()

        # 1. 빈 문자열 검사
        if not new_word:
            st.session_state.message = "단어를 입력해주세요!"
            message_placeholder.warning(st.session_state.message)
            return

        # 2. 이미 사용된 단어인지 검사
        if new_word in st.session_state.word_history:
            st.session_state.game_over = True
            st.session_state.message = f"게임 오버! '{new_word}'는 이미 사용된 단어입니다."
            message_placeholder.error(st.session_state.message)
            return

        # 3. 첫 단어가 아니면서, 이전 단어의 마지막 글자와 일치하는지 검사
        if st.session_state.last_word:
            if new_word[0] != st.session_state.last_word[-1]:
                st.session_state.game_over = True
                st.session_state.message = f"게임 오버! '{new_word}'는 '{st.session_state.last_word[-1]}'로 시작하지 않습니다."
                message_placeholder.error(st.session_state.message)
                return
        
        # 모든 검사 통과 시
        st.session_state.word_history.append(new_word)
        st.session_state.last_word = new_word
        st.session_state.current_turn += 1
        st.session_state.message = f"'{new_word}'가 성공적으로 추가되었습니다."
        message_placeholder.success(st.session_state.message)
        
        # 입력 필드 초기화 (Streamlit의 text_input은 자동으로 초기화되지 않으므로, key를 사용하여 강제 초기화)
        st.session_state.word_input = "" 
        st.experimental_rerun() # 상태 업데이트 후 페이지 새로고침하여 UI 반영

    st.markdown("---")
    st.subheader("사용된 단어 목록")
    if st.session_state.word_history:
        # 최신 단어가 위로 오도록 역순으로 출력
        for i, word in enumerate(reversed(st.session_state.word_history)):
            st.write(f"{len(st.session_state.word_history) - i}. {word}")
    else:
        st.write("아직 사용된 단어가 없습니다.")

    st.markdown("---")
    if st.button("게임 재시작", key="reset_button_bottom"):
        initialize_game()
        st.experimental_rerun() # 상태 초기화 후 페이지 새로고침

if __name__ == "__main__":
    main()
