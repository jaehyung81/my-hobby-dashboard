"""
📅 날짜 관련 유틸리티 모듈
- 양력 / 음력 날짜 계산
- D-Day 계산
- 가족 생일 자동 계산
"""

from datetime import date, timedelta
from korean_lunar_calendar import KoreanLunarCalendar

from utils.constants import FAMILY_BIRTHDAYS


def get_next_solar_date(month: int, day: int, base_date: date = None) -> date:
    """
    양력 기준 다음 기념일 날짜 반환
    - 올해 날짜가 지났으면 → 내년 날짜
    - 2월 29일처럼 없는 날은 다음달 1일로 보정

    Args:
        month: 월 (1~12)
        day: 일 (1~31)
        base_date: 기준일 (기본값: 오늘)
    Returns:
        다음 해당 날짜 (date 객체)
    """
    if base_date is None:
        base_date = date.today()

    try:
        target = date(base_date.year, month, day)
    except ValueError:
        # 예: 2월 30일 → 3월 1일로 보정
        target = date(base_date.year, month + 1, 1)

    if target < base_date:
        target = date(base_date.year + 1, month, day)

    return target


def get_next_lunar_date(month: int, day: int, base_date: date = None) -> date:
    """
    음력 기준 다음 기념일을 양력 날짜로 변환

    Args:
        month: 음력 월
        day: 음력 일
        base_date: 기준일 (기본값: 오늘)
    Returns:
        다음 해당 음력 날짜의 양력 환산 date
    """
    if base_date is None:
        base_date = date.today()

    calendar = KoreanLunarCalendar()
    calendar.setLunarDate(base_date.year, month, day, False)
    target = date(calendar.solarYear, calendar.solarMonth, calendar.solarDay)

    # 올해 날짜가 이미 지났으면 내년으로
    if target < base_date:
        calendar.setLunarDate(base_date.year + 1, month, day, False)
        target = date(calendar.solarYear, calendar.solarMonth, calendar.solarDay)

    return target


def get_next_lotto_date(base_date: date = None) -> date:
    """
    다음 로또 추첨일 (매주 토요일) 반환

    Args:
        base_date: 기준일 (기본값: 오늘)
    Returns:
        다음 토요일 date
    """
    if base_date is None:
        base_date = date.today()
    # 토요일 = weekday 5
    days_ahead = (5 - base_date.weekday()) % 7
    return base_date + timedelta(days=days_ahead)


def get_fixed_events(base_date: date = None) -> dict:
    """
    고정 일정(가족 생일, 기념일, 로또) 계산해서 반환

    Args:
        base_date: 기준일 (기본값: 오늘)
    Returns:
        dict: {"일정명": date 객체}
    """
    if base_date is None:
        base_date = date.today()

    events = {
        "💰 로또 사는 날": get_next_lotto_date(base_date),
    }

    # 가족 생일/기념일 자동 계산
    for name, info in FAMILY_BIRTHDAYS.items():
        if info["lunar"]:
            events[name] = get_next_lunar_date(
                info["month"], info["day"], base_date
            )
        else:
            events[name] = get_next_solar_date(
                info["month"], info["day"], base_date
            )

    return events


def calculate_dday(target_date: date, base_date: date = None) -> dict:
    """
    D-Day 계산 및 라벨/색상 반환

    Args:
        target_date: 목표 날짜
        base_date: 기준일 (기본값: 오늘)
    Returns:
        dict: {
            "diff": 남은 일수 (int),
            "label": "D-10" 같은 표시 문자열,
            "color": 색상 헥스코드
        }
    """
    from utils.constants import COLOR_TODAY, COLOR_TOMORROW, COLOR_FUTURE

    if base_date is None:
        base_date = date.today()

    diff = (target_date - base_date).days

    if diff == 0:
        return {"diff": 0, "label": "Today!", "color": COLOR_TODAY}
    elif diff == 1:
        return {"diff": 1, "label": "D-1", "color": COLOR_TOMORROW}
    elif diff > 0:
        return {"diff": diff, "label": f"D-{diff}", "color": COLOR_FUTURE}
    else:
        return {"diff": diff, "label": f"D+{abs(diff)}", "color": "#999999"}
