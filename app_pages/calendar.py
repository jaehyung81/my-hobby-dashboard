"""
🗓️ 일정 페이지
- 날짜 선택 및 날짜 계산기
- 해당 날짜 일정 조회
- 전체 일정 리스트 (D-Day 순)
"""

from datetime import date, timedelta
import pandas as pd
import streamlit as st

from utils.date_utils import get_fixed_events
from utils.constants import REAL_SHEET_URL


def render(df_events: pd.DataFrame):
    """일정 페이지 렌더링 진입점"""
    st.title("상세 일정 및 메모 관리 🗓️")

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
    st.info("💡 일정과 메모는 아래 구글 시트에서 관리하세요.")
    st.link_button("📊 구글 시트 직접 편집하기",
                   REAL_SHEET_URL,
                   use_container_width=True, type="primary")
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

    # 엑셀 일정
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
            "날짜": d, "내용": n, "연차구분": "-", "메모": "-"
        })

    # 엑셀 일정
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
                    "연차구분": v_type if v_type else "-",
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
        display_df[["날짜", "D-Day", "내용", "연차구분", "메모"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "연차구분": st.column_config.TextColumn("연차구분", width="small"),
            "메모": st.column_config.TextColumn("메모", width="medium"),
        }
    )
