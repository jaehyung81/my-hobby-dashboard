"""
🏠 재형의 대시보드 - 메인 진입점
- 페이지 설정
- 사이드바 메뉴 (라우터)
- 가족 트리 표시
- 데이터 로딩 후 각 페이지로 전달

실행: streamlit run main.py
"""

import streamlit as st

from utils.constants import FISHING_CSV, CALENDAR_CSV, FISHING_RECORD_CSV
from utils.data_loader import load_csv_from_url, load_bada_map
from app_pages import home, calendar, family, asset, fishing


# ============================================================
# 1️⃣ 페이지 설정 (가장 먼저!)
# ============================================================
st.set_page_config(
    page_title="재형의 대시보드",
    page_icon="🏠",
    layout="wide"
)

# ============================================================
# 2️⃣ 전역 CSS (상단 여백 조정)
# ============================================================
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.5rem !important;
        }
        header {
            height: 2rem !important;
            background-color: transparent !important;
        }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# 3️⃣ 데이터 로드 (캐시됨)
# ============================================================
df_fishing = load_csv_from_url(FISHING_CSV)
df_events = load_csv_from_url(CALENDAR_CSV)
df_fishing_record = load_csv_from_url(FISHING_RECORD_CSV, skip_first_row=True)  # 🆕 그룹헤더 건너뛰기!
bada_id_map = load_bada_map()


# ============================================================
# 4️⃣ 사이드바: 메뉴 + 가족 트리
# ============================================================
st.sidebar.title("재형의 개인비서 🤖")
menu = st.sidebar.radio(
    "메뉴를 선택하세요:",
    ["🏠 홈", "🗓️ 일정", "👨‍👩‍👦‍👦 가족", "📈 자산 관리", "🎣 낚시"]
)

st.sidebar.divider()
with st.sidebar.expander("👨‍👩‍👦‍👦 우리 가족 트리", expanded=True):
    st.write("📂 **LJH Family**")
    st.write("├── 🤵 **재형 (10.18)**")
    st.write("├── 👰 **연정 (음력 10.24)**")
    st.write("├── 👦 **은호 (07.10)**")
    st.write("└── 👶 **수호 (05.19)**")


# ============================================================
# 5️⃣ 라우팅: 선택된 메뉴에 맞는 페이지 렌더링
# ============================================================
if menu == "🏠 홈":
    home.render(df_events)

elif menu == "🗓️ 일정":
    calendar.render(df_events)

elif menu == "👨‍👩‍👦‍👦 가족":
    family.render(df_events)

elif menu == "📈 자산 관리":
    asset.render()

elif menu == "🎣 낚시":
    fishing.render(df_fishing, bada_id_map, df_fishing_record)
