"""
📈 자산 관리 페이지
- 미국 주식 수익률 계산기
"""

import streamlit as st


def render():
    """자산 관리 페이지 렌더링 진입점"""
    st.title("미국 주식 수익률 계산기 💵")

    c1, c2 = st.columns([1, 1.5])

    with c1:
        price = st.number_input("단가 ($)", value=29.50)
        qty = st.number_input("수량", value=100)
        curr = st.number_input("현재가 ($)", value=31.30)

    with c2:
        profit = (curr - price) * qty
        rate = ((curr - price) / price) * 100 if price else 0

        st.metric("수익률", f"{rate:.2f}%", delta=f"{profit:.2f}$")
        st.write("---")
        st.caption("💸 실시간 환율을 적용한 원화 환산 기능은 추후 업데이트 예정입니다.")
