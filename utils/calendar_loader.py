"""
📅 구글 캘린더 API 로더 모듈
- 서비스 계정을 통해 구글 캘린더에서 일정 로드
- Streamlit 캐시 적용으로 성능 최적화
- 캘린더 연동 실패시 빈 리스트 반환 (앱 크래시 방지)
"""

import json
from datetime import date, datetime, timedelta

import streamlit as st

from utils.constants import CACHE_TTL

# 구글 API 관련 임포트 (설치 필요: google-auth, google-api-python-client)
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


# 캘린더 API 접근에 필요한 권한 범위
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _get_calendar_service():
    """
    서비스 계정 인증 → Calendar API 서비스 객체 반환
    secrets.toml에서 서비스 계정 키를 읽어옴

    Returns:
        googleapiclient.discovery.Resource 또는 None
    """
    if not GOOGLE_API_AVAILABLE:
        return None

    try:
        if "GOOGLE_SERVICE_ACCOUNT" not in st.secrets:
            return None

        # secrets.toml에서 서비스 계정 정보 읽기
        sa_info = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])

        # private_key 줄바꿈 복원 (toml에서 \\n → \n)
        if "private_key" in sa_info:
            sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")

        credentials = service_account.Credentials.from_service_account_info(
            sa_info, scopes=SCOPES
        )
        service = build("calendar", "v3", credentials=credentials)
        return service

    except Exception as e:
        print(f"[calendar_loader] 서비스 계정 인증 실패: {e}")
        return None


@st.cache_data(ttl=CACHE_TTL)
def load_calendar_events(calendar_id: str, days_ahead: int = 180) -> list:
    """
    구글 캘린더에서 일정 로드 (오늘부터 days_ahead일 후까지)

    Args:
        calendar_id: 구글 캘린더 ID (보통 이메일 주소)
        days_ahead: 며칠 앞까지 조회할지 (기본 180일 = 약 6개월)
    Returns:
        list: [{"date": date, "summary": str, "description": str}, ...]
    """
    service = _get_calendar_service()
    if service is None:
        return []

    try:
        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=100,
        ).execute()

        items = events_result.get("items", [])
        parsed = []

        for item in items:
            # 종일 일정 vs 시간 지정 일정
            start = item.get("start", {})
            if "date" in start:
                # 종일 일정: "2026-05-10"
                ev_date = datetime.strptime(start["date"], "%Y-%m-%d").date()
            elif "dateTime" in start:
                # 시간 지정 일정: "2026-05-10T14:00:00+09:00"
                dt_str = start["dateTime"]
                ev_date = datetime.fromisoformat(dt_str).date()
            else:
                continue

            parsed.append({
                "date": ev_date,
                "summary": item.get("summary", "(제목 없음)"),
                "description": item.get("description", ""),
            })

        return parsed

    except Exception as e:
        print(f"[calendar_loader] 캘린더 일정 로드 실패: {e}")
        return []


def is_calendar_available() -> bool:
    """캘린더 API 사용 가능 여부 확인"""
    if not GOOGLE_API_AVAILABLE:
        return False
    if "GOOGLE_SERVICE_ACCOUNT" not in st.secrets:
        return False
    return True
