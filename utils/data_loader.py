"""
📥 데이터 로더 모듈
- 구글 시트에서 CSV 데이터 불러오기
- 바다타임 지역 매핑 정보 불러오기
- 모든 데이터 로딩은 여기서 처리!
"""

import os
import re
import io
import requests
import urllib.request
import pandas as pd
import streamlit as st

from utils.constants import (
    CACHE_TTL,
    REQUEST_TIMEOUT,
    BACKUP_TIMEOUT,
    BADA_DEFAULT_MAP,
)


@st.cache_data(ttl=CACHE_TTL)
def load_csv_from_url(url: str, skip_first_row: bool = False) -> pd.DataFrame:
    """
    구글 시트 CSV URL에서 데이터 로드
    - 기본: requests 로 시도
    - 실패시: urllib 로 백업 시도
    - 둘 다 실패: 빈 DataFrame 반환

    Args:
        url: 구글시트 CSV 퍼블리시 URL
        skip_first_row: 첫 줄을 건너뛸지 여부 (그룹헤더용)
    Returns:
        pd.DataFrame (실패시 빈 DataFrame)
    """
    # 1차 시도: requests
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        res.encoding = "utf-8"
        
        # 🆕 skip_first_row=True면 첫 줄(그룹헤더) 건너뛰기
        skip_rows = 1 if skip_first_row else 0
        return pd.read_csv(
            io.StringIO(res.text), skiprows=skip_rows
        ).fillna("")
    except Exception as e:
        print(f"[load_csv_from_url] requests 실패, urllib로 재시도: {e}")

    # 2차 시도: urllib (백업)
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=BACKUP_TIMEOUT) as response:
            skip_rows = 1 if skip_first_row else 0
            return pd.read_csv(
                response, encoding="utf-8", skiprows=skip_rows
            ).fillna("")
    except Exception as e:
        print(f"[load_csv_from_url] urllib도 실패: {e}")
        return pd.DataFrame()


@st.cache_data
def load_bada_map(mapping_file: str = "assets/bada_mapping.txt") -> dict:
    """
    바다타임 지역-ID 매핑 로드
    - assets/bada_mapping.txt 에서 추가 데이터 읽어옴
    - 파일 없어도 기본 매핑(BADA_DEFAULT_MAP)은 동작

    Args:
        mapping_file: 매핑 파일 경로
    Returns:
        dict: {"지역명": "바다타임ID"}
    """
    # 기본 매핑으로 시작
    bada_map = dict(BADA_DEFAULT_MAP)

    if not os.path.exists(mapping_file):
        return bada_map

    try:
        with open(mapping_file, "r", encoding="utf-8") as f:
            html_text = f.read()
            matches = re.findall(
                r'badatime\.com/(\d+)/[^>]*>([^<]+)</a>', html_text
            )

            for b_id, name in matches:
                clean_name = name.strip()
                bada_map[clean_name] = b_id

                # "○○항" → "○○" 도 자동 등록
                if clean_name.endswith("항"):
                    bada_map[clean_name[:-1]] = b_id
                # "○○포구" → "○○" 도 자동 등록
                if clean_name.endswith("포구"):
                    bada_map[clean_name[:-2]] = b_id
    except Exception as e:
        print(f"[load_bada_map] 매핑 파일 읽기 실패: {e}")

    return bada_map
