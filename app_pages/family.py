"""
👨‍👩‍👦‍👦 가족 페이지
- 엑셀 연동 가족 일정 표시
"""

import pandas as pd
import streamlit as st


def render(df_events: pd.DataFrame):
    """가족 페이지 렌더링 진입점"""
    st.title("사랑하는 우리 가족 ❤️")
    st.write("가족 구성원 정보를 확인하고 주요 일정을 공유하는 공간입니다.")

    if df_events.empty:
        st.info("💡 구글 드라이브의 엑셀 파일에 일정을 입력하면 여기에 나타납니다.")
    elif "일자" in df_events.columns:
        st.subheader("📅 엑셀 연동 가족 일정")
        df = df_events.copy()
        df["일자"] = pd.to_datetime(df["일자"]).dt.date
        st.dataframe(df.sort_values("일자"),
                     use_container_width=True, hide_index=True)
    else:
        st.error("🚨 엑셀 데이터 형식을 불러오는 중 오류가 발생했습니다.")

    st.divider()
    st.image(
        "https://cdn-icons-png.flaticon.com/512/3093/3093835.png",
        width=200
    )
