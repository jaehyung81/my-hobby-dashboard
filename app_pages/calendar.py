"""
🗓️ 일정 페이지
- 날짜 선택 및 날짜 계산기
- 해당 날짜 일정 조회 (구글 캘린더 + 구글시트 백업)
- 전체 일정 리스트 (D-Day 순)
"""

from datetime import date, timedelta
import pandas as pd
import streamlit as st

from utils.date_utils import get_fixed_events
from utils.constants import REAL_SHEET_URL, GOOGLE_CALENDAR_ID, CALENDAR_DAYS_AHEAD
from utils.calendar_loader import load_calendar_events, is_calendar_available


def render(df_events: pd.DataFrame):
    """일정 페이지 렌더링 진입점"""
    st.title("상세 일정 및 메모 관리 🗓️")

    # 일정 소스 표시
    if is_calendar_available():
        st.caption("📅 일정 소스: **구글 캘린더** 연동 중")
    else:
        st.caption("📂 일정 소스: **구글 시트** (캘린더 미연동)")

    c1, c2 = st.columns([1, 2])
    today = date.today()

    with c1:
        sel_date = _render_date_picker(today)
        st.divider()
        _render_date_calculator(today)

    with c2:
        _render_daily_events(df_events, sel_date, today)
        st.divider()
        _render_all_events_list(df_events, today)


def _render_date_picker(today: date) -> date:
    """날짜 선택 위젯"""
    st.subheader("📅 날짜 선택")
    sel_date = st.date_input("조회할 날짜", value=today,
                             key="sel_date_picker")
    st.info("💡 일정 등록/수정은 클로드 채팅에서 구글 캘린더로 관리하세요!")
    btn1, btn2 = st.columns(2)
    with btn1:
        st.link_button("🤖 Claude.ai",
                       "https://claude.ai/",
                       use_container_width=True, type="primary")
    with btn2:
        st.link_button("📅 Google Calendar",
                       "https://calendar.google.com/",
                       use_container_width=True, type="secondary")
    return sel_date


def _render_date_calculator(today: date):
    """날짜 계산기"""
    st.subheader("🔢 날짜 계산기")
    calc_mode = st.radio(
        "계산 선택", ["날짜 더하기 (+일)", "D-Day 계산"],
        horizontal=True
    )

    if calc_mode == "날짜 더하기 (+일)":
        plus_days = st.number_input(
            "며칠 뒤를 계산할까요?", min_value=1, value=100
        )
        target = today + timedelta(days=plus_days)
        st.success(f"{plus_days}일 뒤: **{target.strftime('%Y-%m-%d')}**")
    else:
        target_d = st.date_input("기준 날짜 선택", value=date(2026, 12, 25))
        diff = (target_d - today).days
        if diff > 0:
            st.info(f"**{diff}일** 남았습니다.")
        elif diff == 0:
            st.success("오늘입니다! 🎉")
        else:
            st.warning(f"**{abs(diff)}일** 지났습니다.")


def _render_daily_events(df_events: pd.DataFrame,
                          sel_date: date, today: date):
    """선택한 날짜의 일정 표시"""
    st.subheader(f"📢 {sel_date.strftime('%m월 %d일')} 일정 및 메모")
    found = False

    # 고정 일정
    for name, d_obj in get_fixed_events(today).items():
        if d_obj == sel_date:
            st.success(f"📌 **{name}**")
            found = True

    # 구글 캘린더 일정
    calendar_loaded = False
    if is_calendar_available():
        cal_events = load_calendar_events(
            GOOGLE_CALENDAR_ID, CALENDAR_DAYS_AHEAD
        )
        if cal_events:
            calendar_loaded = True
            for ev in cal_events:
                if ev["date"] == sel_date:
                    st.success(f"📅 **{ev['summary']}**")
                    if ev["description"]:
                        st.warning(f"📝 **메모:** {ev['description']}")
                    found = True

    # 구글시트 일정 (캘린더 미연동시 백업)
    if not calendar_loaded:
        if (not df_events.empty
                and "일자" in df_events.columns
                and "내용" in df_events.columns):
            for _, row in df_events.iterrows():
                try:
                    ev_date = pd.to_datetime(row["일자"]).date()
                    if ev_date == sel_date:
                        v_type = str(row.get("연차구분", "")).strip()
                        v_str = f"[{v_type}] " if v_type else ""
                        st.success(f"📂 **{v_str}{row['내용']}**")

                        memo = row.get("메모", "")
                        if memo and str(memo).strip():
                            st.warning(f"📝 **메모:** {memo}")
                        found = True
                except Exception:
                    continue

    if not found:
        st.info("해당 날짜에 등록된 일정이 없습니다.")


def _render_all_events_list(df_events: pd.DataFrame, today: date):
    """전체 일정 리스트 (D-Day 순)"""
    st.subheader("📋 전체 일정 리스트 (D-Day 순)")

    all_events = []

    # 고정 일정
    for n, d in get_fixed_events(today).items():
        all_events.append({
            "날짜": d, "내용": n, "소스": "고정", "메모": "-"
        })

    # 구글 캘린더 일정
    calendar_loaded = False
    if is_calendar_available():
        cal_events = load_calendar_events(
            GOOGLE_CALENDAR_ID, CALENDAR_DAYS_AHEAD
        )
        if cal_events:
            calendar_loaded = True
            for ev in cal_events:
                all_events.append({
                    "날짜": ev["date"],
                    "내용": ev["summary"],
                    "소스": "📅 캘린더",
                    "메모": ev["description"] if ev["description"] else "-"
                })

    # 구글시트 일정 (백업)
    if not calendar_loaded:
        if (not df_events.empty
                and "일자" in df_events.columns
                and "내용" in df_events.columns):
            for _, row in df_events.iterrows():
                try:
                    v_type = str(row.get("연차구분", "")).strip()
                    v_memo = str(row.get("메모", "")).strip()
                    all_events.append({
                        "날짜": pd.to_datetime(row["일자"]).date(),
                        "내용": row["내용"],
                        "소스": f"📂 시트{f' [{v_type}]' if v_type else ''}",
                        "메모": v_memo if v_memo else "-"
                    })
                except Exception:
                    continue

    future = [e for e in all_events if e["날짜"] >= today]

    if not future:
        st.info("예정된 일정이 없습니다.")
        return

    display_df = pd.DataFrame(future).sort_values(by="날짜")
    display_df["D-Day"] = display_df["날짜"].apply(
        lambda x: f"D-{(x - today).days}" if x > today else "Today"
    )

    st.dataframe(
        display_df[["날짜", "D-Day", "내용", "소스", "메모"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "소스": st.column_config.TextColumn("소스", width="small"),
            "메모": st.column_config.TextColumn("메모", width="medium"),
        }
    )
