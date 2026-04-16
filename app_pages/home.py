"""
🏠 홈 페이지
- D-Day 카드 (가장 가까운 5일치 일정)
- 검색박스 (구글/네이버)
- 바로가기 링크
"""

from collections import defaultdict
from datetime import date
import pandas as pd
import streamlit as st

from utils.date_utils import get_fixed_events, calculate_dday


def render(df_events: pd.DataFrame):
    """홈 페이지 렌더링 진입점"""
    st.title("환영합니다! 재형님 👋")

    _render_dday_cards(df_events)
    st.divider()

    _render_search_box()
    st.divider()

    _render_quick_links()


def _render_dday_cards(df_events: pd.DataFrame):
    """D-Day 카드 영역"""
    st.subheader("🗓️ 주요 일정 (D-Day)")

    today = date.today()
    all_events = _collect_all_events(df_events, today)

    # 날짜별로 묶기
    grouped = defaultdict(list)
    for ev in all_events:
        if ev["name"] not in grouped[ev["date"]]:
            grouped[ev["date"]].append(ev["name"])

    # 가장 가까운 5개 날짜
    sorted_dates = sorted(grouped.keys())[:5]
    if not sorted_dates:
        st.info("예정된 일정이 없습니다.")
        return

    cols = st.columns(len(sorted_dates))
    for i, d in enumerate(sorted_dates):
        dday_info = calculate_dday(d, today)
        card_html = _build_dday_card_html(d, dday_info, grouped[d])
        with cols[i]:
            st.markdown(card_html, unsafe_allow_html=True)


def _collect_all_events(df_events: pd.DataFrame, today: date) -> list:
    """고정 일정 + 엑셀 일정 모두 수집"""
    all_events = []

    # 1) 고정 일정 (가족 생일, 로또)
    for name, d_obj in get_fixed_events(today).items():
        if d_obj >= today:
            all_events.append({"date": d_obj, "name": name})

    # 2) 구글시트 엑셀 일정
    if (not df_events.empty
            and "일자" in df_events.columns
            and "내용" in df_events.columns):
        for _, row in df_events.iterrows():
            try:
                ev_date = pd.to_datetime(row["일자"]).date()
                if ev_date >= today:
                    v_type = str(row.get("연차구분", "")).strip()
                    v_str = f"[{v_type}] " if v_type else ""
                    all_events.append({
                        "date": ev_date,
                        "name": f"📂 {v_str}{row['내용']}"
                    })
            except Exception:
                continue

    return all_events


def _build_dday_card_html(d: date, dday_info: dict, events: list) -> str:
    """D-Day 카드 HTML 생성"""
    date_str = d.strftime("%m.%d")
    events_html = "".join([
        f"<div style='font-size:0.9rem; margin-bottom:6px; "
        f"color:#333; line-height:1.3; word-break:keep-all;'>{ev}</div>"
        for ev in events
    ])

    return f"""
    <div style="border: 1px solid #e6e6e6; border-radius: 10px;
                padding: 15px; background-color: #ffffff; text-align: center;
                height: 100%; box-shadow: 2px 2px 8px rgba(0,0,0,0.04);">
        <h3 style="margin: 0; color: {dday_info['color']};
                   font-size: 1.6rem; padding-bottom: 5px;">
            {dday_info['label']}
        </h3>
        <div style="color: #888888; font-size: 0.95rem;
                    margin-bottom: 12px; font-weight: 500;">
            {date_str}
        </div>
        <hr style="margin: 0 0 12px 0; border: 0;
                   border-top: 1px dashed #ddd;">
        <div style="text-align: left;">{events_html}</div>
    </div>
    """


def _render_search_box():
    """구글/네이버 검색박스"""
    st.subheader("🔎 빠른 검색")

    # 구글
    g1, g2, g3, g4 = st.columns([0.5, 6, 1.5, 1.5])
    with g1:
        st.image("https://www.google.com/favicon.ico", width=28)
    with g2:
        google_q = st.text_input(
            "Google", label_visibility="collapsed",
            placeholder="Google 검색어 입력", key="g_in"
        )
    with g3:
        google_url = (
            f"https://www.google.com/search?q={google_q}"
            if google_q else "https://www.google.com/"
        )
        st.link_button("🔍 Go", google_url, use_container_width=True)
    with g4:
        st.link_button("📧 Gmail", "https://mail.google.com/",
                       use_container_width=True)

    # 네이버
    n1, n2, n3, n4 = st.columns([0.5, 6, 1.5, 1.5])
    with n1:
        st.image("https://www.naver.com/favicon.ico", width=28)
    with n2:
        naver_q = st.text_input(
            "Naver", label_visibility="collapsed",
            placeholder="Naver 검색어 입력", key="n_in"
        )
    with n3:
        naver_url = (
            f"https://search.naver.com/search.naver?query={naver_q}"
            if naver_q else "https://www.naver.com/"
        )
        st.link_button("🔍 Go", naver_url, use_container_width=True)
    with n4:
        st.link_button("📧 N메일", "https://mail.naver.com/",
                       use_container_width=True)


def _render_quick_links():
    """바로가기 링크"""
    st.subheader("🚀 바로가기")
    l1, l2, l3 = st.columns(3)
    l1.link_button("🎣 로구만 카페",
                   "https://cafe.naver.com/blackoxxxq",
                   use_container_width=True)
    l2.link_button("✨ Gemini 메인",
                   "https://gemini.google.com/",
                   use_container_width=True)
    l3.link_button("📂 구글 드라이브",
                   "https://drive.google.com/",
                   use_container_width=True)
