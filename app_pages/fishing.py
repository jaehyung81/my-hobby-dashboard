"""
🎣 낚시 페이지 (탭 3개)
- 탭1: 출조 포털 & 물때 (기존)
- 탭2: 선사 정보 리스트 (기존)
- 탭3: 낚시 기록 & 사진 (신규!)
"""

from datetime import date, datetime, timedelta
from collections import Counter
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

from utils.constants import REAL_SHEET_URL, KHOA_OBS_MAP, KHOA_DEFAULT_CODE


def render(df_fishing: pd.DataFrame, bada_id_map: dict,
           df_fishing_record: pd.DataFrame = None):
    """낚시 페이지 렌더링 진입점"""
    st.markdown(
        "<h1 style='text-align: center;'>도시어부 라이프 🎣</h1>",
        unsafe_allow_html=True
    )

    tab1, tab2, tab3 = st.tabs(
        ["📅 출조 포털 & 물때", "🚢 선사정보", "📸 낚시 기록 & 사진"]
    )

    with tab1:
        _render_fishing_portal(df_fishing, bada_id_map)

    with tab2:
        _render_ship_list(df_fishing)

    with tab3:
        _render_fishing_records(df_fishing_record)


# ============================================================
# 🎯 탭1: 출조 포털 (기존 코드 그대로 유지)
# ============================================================

def _render_fishing_portal(df_fishing: pd.DataFrame, bada_id_map: dict):
    """출조 포털 메인"""
    _render_portal_header()

    if df_fishing.empty:
        st.warning("⚠️ 구글 시트 데이터를 불러오지 못했습니다.")
        return

    required_cols = ["지역1", "지역2", "선사명"]
    if not all(c in df_fishing.columns for c in required_cols):
        st.error("🚨 구글 시트에 '지역1', '지역2', '선사명' 컬럼이 모두 있어야 합니다!")
        return

    _init_session_state()

    today = date.today()
    t_date, sel_region1, sel_region2, sel_name = _render_filter_ui(
        df_fishing, today
    )
    st.divider()

    if sel_name != "전체":
        df_filtered = df_fishing.copy()
        if sel_region1 != "전체":
            df_filtered = df_filtered[df_filtered["지역1"] == sel_region1]
        if sel_region2 != "전체":
            df_filtered = df_filtered[df_filtered["지역2"] == sel_region2]
        _render_ship_card(df_filtered, sel_name)

    if sel_region2 != "전체":
        _render_observation_and_account(sel_region2, t_date, today)
        st.divider()
        _render_tide_info(sel_region2, bada_id_map)
    else:
        st.info("💡 실시간 바다 날씨와 물때표를 보시려면 위에서 **상세 항구 ⚓**를 선택해주세요!")


def _render_portal_header():
    """포털 헤더"""
    col_hdr1, col_hdr2 = st.columns([1, 1])
    with col_hdr1:
        st.subheader("📅 원클릭 출조 및 실시간 정보")
    with col_hdr2:
        st.markdown(
            "<div style='text-align: right; margin-top: 15px; "
            "font-size: 0.9rem; color: #555; font-weight: bold;'>"
            "⭐ 주요 관심 선사 &nbsp;&nbsp;|&nbsp;&nbsp; "
            "⚓ 로구만 프렌즈 선사</div>",
            unsafe_allow_html=True
        )


def _init_session_state():
    """세션 상태 초기화"""
    defaults = {"sel_reg1": "전체", "sel_reg2": "전체", "sel_ship": "전체"}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _render_filter_ui(df_fishing: pd.DataFrame, today: date):
    """필터 UI (날짜 + 지역1 + 지역2 + 선사명)"""

    def auto_fill_port():
        ship = st.session_state.sel_ship
        if ship != "전체":
            port = df_fishing[df_fishing["선사명"] == ship]["지역2"].values
            if len(port) > 0:
                st.session_state.sel_reg2 = str(port[0])

    col1, col2, col3, col4 = st.columns([1, 1.2, 1.2, 1.5])

    with col1:
        t_date = st.date_input(
            "출조 예정일", value=today, format="YYYY/MM/DD"
        )

    with col2:
        region1_list = ["전체"] + sorted(
            [str(r) for r in df_fishing["지역1"].unique()
             if str(r).strip()]
        )
        if st.session_state.sel_reg1 not in region1_list:
            st.session_state.sel_reg1 = "전체"
        sel_region1 = st.selectbox(
            "지역 (도/시) 📍", region1_list, key="sel_reg1"
        )

    df_step1 = df_fishing.copy()
    if sel_region1 != "전체":
        df_step1 = df_step1[df_step1["지역1"] == sel_region1]

    with col3:
        sel_region2 = _render_port_selectbox(df_step1)

    df_step2 = df_step1.copy()
    if sel_region2 != "전체":
        df_step2 = df_step2[df_step2["지역2"] == sel_region2]

    with col4:
        sel_name = _render_ship_selectbox(df_step2, auto_fill_port)

    return t_date, sel_region1, sel_region2, sel_name


def _render_port_selectbox(df_step1: pd.DataFrame) -> str:
    """항구 선택박스"""
    temp_ports = df_step1[
        df_step1["지역2"].astype(str).str.strip() != ""
    ][["지역1", "지역2"]].drop_duplicates()
    temp_ports = temp_ports.sort_values(by=["지역1", "지역2"])

    region2_list = ["전체"] + temp_ports["지역2"].astype(str).tolist()

    port_format = {"전체": "전체"}
    for _, row in temp_ports.iterrows():
        port_format[str(row["지역2"])] = f"[{row['지역1']}] {row['지역2']}"

    if st.session_state.sel_reg2 not in region2_list:
        st.session_state.sel_reg2 = "전체"

    return st.selectbox(
        "상세 항구 ⚓", region2_list, key="sel_reg2",
        format_func=lambda x: port_format.get(x, x)
    )


def _render_ship_selectbox(df_step2: pd.DataFrame, on_change) -> str:
    """선사 선택박스"""
    fetch_cols = ["지역1", "지역2", "선사명"]
    if "주요 관심 선사" in df_step2.columns:
        fetch_cols.append("주요 관심 선사")
    if "로구만 프렌즈 선사" in df_step2.columns:
        fetch_cols.append("로구만 프렌즈 선사")

    temp_ships = df_step2[
        df_step2["선사명"].astype(str).str.strip() != ""
    ][fetch_cols].drop_duplicates()
    temp_ships = temp_ships.sort_values(by=["지역1", "지역2", "선사명"])

    name_list = ["전체"] + temp_ships["선사명"].astype(str).tolist()

    ship_format = {"전체": "전체"}
    for _, row in temp_ships.iterrows():
        s_name = str(row["선사명"])
        display = f"[{row['지역2']}] {s_name}"

        if _has_flag(row, "주요 관심 선사"):
            display += " ⭐"
        if _has_flag(row, "로구만 프렌즈 선사"):
            display += " ⚓"
        ship_format[s_name] = display

    if st.session_state.sel_ship not in name_list:
        st.session_state.sel_ship = "전체"

    return st.selectbox(
        "선사 선택 🚢", name_list, key="sel_ship",
        on_change=on_change,
        format_func=lambda x: ship_format.get(x, x)
    )


def _has_flag(row, col_name: str) -> bool:
    if col_name not in row:
        return False
    val = str(row[col_name]).strip()
    return bool(val) and val.upper() != "NAN"


# ============================================================
# 🏷️ 선사 스마트칩 카드
# ============================================================

def _render_ship_card(df_filtered: pd.DataFrame, sel_name: str):
    target = df_filtered[df_filtered["선사명"] == sel_name]
    if target.empty:
        return

    res_url = str(target["예약사이트"].values[0])
    if not res_url.startswith("http"):
        return

    clean_domain = res_url.replace("https://", "") \
        .replace("http://", "").split("/")[0]

    fav_badge = _build_badge(target, "주요 관심 선사",
                              "⭐ 관심선사", "#fff3cd", "#856404", "#ffeeba")
    roguman_badge = _build_badge(target, "로구만 프렌즈 선사",
                                  "⚓ 로구만", "#cce5ff", "#004085", "#b8daff")

    main_btn = _build_link_button(res_url, "선사 메인 홈페이지 가기", "#ff4b4b")
    sunsang_btn = _build_sunsang_button(target)
    thefishing_btn = _build_thefishing_button(target)

    buttons_html = (
        f'<div style="display: flex; flex-direction: column; gap: 8px; '
        f'width: 220px; flex-shrink: 0;">'
        f'{main_btn}{sunsang_btn}{thefishing_btn}</div>'
    )

    chip_html = f'''
    <div style="display: flex; align-items: center;
                justify-content: space-between;
                background-color: #f8f9fa; border: 1px solid #dadce0;
                border-radius: 12px; padding: 12px 20px;
                margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center;">
            <div style="background-color: #1a73e8; color: white;
                        border-radius: 8px; width: 40px; height: 40px;
                        display: flex; align-items: center;
                        justify-content: center; font-size: 1.2rem;
                        margin-right: 15px;">🚢</div>
            <div>
                <div style="font-weight: bold; font-size: 1.1rem;
                            color: #202124; margin-bottom: 2px;
                            display: flex; align-items: center;">
                    {sel_name}{fav_badge}{roguman_badge}
                </div>
                <div style="font-size: 0.85rem; color: #5f6368;">
                    {clean_domain}
                </div>
            </div>
        </div>
        {buttons_html}
    </div>
    '''
    st.markdown(chip_html, unsafe_allow_html=True)


def _build_badge(target, col_name, label, bg, color, border):
    if col_name not in target.columns:
        return ""
    val = str(target[col_name].values[0]).strip()
    if not val or val.upper() == "NAN":
        return ""

    return (
        f'<span style="background-color: {bg}; color: {color}; '
        f'padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; '
        f'border: 1px solid {border}; margin-left: 8px;">{label}</span>'
    )


def _build_link_button(url, label, bg_color):
    return (
        f'<a href="{url}" target="_blank" '
        f'style="background-color: {bg_color}; color: white; '
        f'text-decoration: none; padding: 8px 0; border-radius: 6px; '
        f'font-weight: bold; font-size: 0.85rem; text-align: center; '
        f'border: none; cursor: pointer; display: block; width: 100%;">'
        f'{label}</a>'
    )


def _build_sunsang_button(target):
    if "선상24_Ship_No" not in target.columns:
        return ""
    s_no = target["선상24_Ship_No"].values[0]
    if pd.isna(s_no) or not str(s_no).strip():
        return ""

    try:
        clean_no = str(int(float(s_no)))
    except Exception:
        clean_no = str(s_no).strip()

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    url = (f"https://www.sunsang24.com/ship/schedule/"
           f"?sdate={tomorrow}&ship_no={clean_no}")
    return _build_link_button(url, "🔗 선상24 바로가기 (내일 날짜)", "#0068c9")


def _build_thefishing_button(target):
    if "더피싱_Ship_No" not in target.columns:
        return ""
    tf_no = target["더피싱_Ship_No"].values[0]
    if pd.isna(tf_no) or not str(tf_no).strip():
        return ""

    try:
        clean_no = str(int(float(tf_no)))
    except Exception:
        clean_no = str(tf_no).strip()

    url = f"https://thefishing.kr/reservation/list.php?uid={clean_no}"
    return _build_link_button(url, "🔗 더피싱 예약 바로가기", "#d11820")


# ============================================================
# 🌊 해양 관측 + 계좌 정보 (기존 코드 유지)
# ============================================================

def _render_observation_and_account(sel_region2, t_date, today):
    col_obs, col_acc = st.columns([2.5, 1])
    with col_obs:
        _render_marine_observation(sel_region2, t_date, today)
    with col_acc:
        _render_account_info()


def _render_marine_observation(sel_region2, t_date, today):
    obs_code = next(
        (v for k, v in KHOA_OBS_MAP.items() if k in sel_region2),
        KHOA_DEFAULT_CODE
    )

    try:
        if not (hasattr(st, "secrets") and "KHOA_API_KEY" in st.secrets):
            return

        api_key = st.secrets["KHOA_API_KEY"].strip()
        req_date = t_date.strftime("%Y%m%d")

        url_1 = (
            f"https://apis.data.go.kr/1192136/dtRecent/GetDTRecentApiService"
            f"?serviceKey={api_key}&obsCode={obs_code}"
            f"&reqDate={req_date}&pageNo=1&numOfRows=1&type=json"
        )
        res_1 = requests.get(url_1, timeout=10)

        if res_1.status_code != 200:
            st.error(f"🚨 서버 통신 실패! {res_1.status_code}")
            return

        try:
            data1 = res_1.json()
        except ValueError:
            st.warning("🚨 공공데이터포털 서버 점검 중")
            return

        if "OpenAPI_ServiceResponse" in data1:
            msg = (data1["OpenAPI_ServiceResponse"]
                   .get("cmmMsgHeader", {})
                   .get("returnAuthMsg", ""))
            st.error(f"🚨 공공데이터포털 접속 거절: {msg}")
            return

        response_node = data1.get("response", {})
        header1 = response_node.get("header", data1.get("header", {}))
        body1 = response_node.get("body", data1.get("body", {}))

        if header1.get("resultCode") != "00" or body1.get("totalCount", 0) == 0:
            if t_date > today:
                st.info("🔮 미래 날짜는 아직 실시간 데이터가 없습니다.")
            else:
                st.warning("🚨 현재 해당 지역 근처 관측소 데이터 점검 중")
            return

        total = body1.get("totalCount")
        url_2 = (
            f"https://apis.data.go.kr/1192136/dtRecent/GetDTRecentApiService"
            f"?serviceKey={api_key}&obsCode={obs_code}"
            f"&reqDate={req_date}&pageNo={total}&numOfRows=1&type=json"
        )
        res_2 = requests.get(url_2, timeout=10)
        data2 = res_2.json()

        body2 = data2.get("response", {}).get("body", data2.get("body", {}))
        raw_items = body2.get("items", {})
        items = (raw_items.get("item", [])
                 if isinstance(raw_items, dict) else raw_items)
        if not isinstance(items, list):
            items = [items]

        if not items:
            st.warning("⚠️ 공공데이터포털 서버 통신 오류")
            return

        _display_observation_metrics(items[-1])

    except Exception as e:
        st.error(f"🚨 통신 에러: {e}")


def _display_observation_metrics(curr_data):
    st.markdown("##### 📡 근해 실시간 관측 정보")
    w1, w2, w3 = st.columns(3)

    wind = curr_data.get("wspd", curr_data.get("wind_speed", "-"))
    temp = curr_data.get("wtem", curr_data.get("water_temp", "-"))
    tide = curr_data.get("bscTdlvHgt", curr_data.get("tide_level", "-"))

    w1.metric("💨 실시간 풍속", f"{wind} m/s")
    w2.metric("🌡️ 현재 수온", f"{temp} ℃")
    w3.metric("📏 실시간 조위", f"{tide} cm")

    obs_time = curr_data.get("obsrvnDt", "알수없음")
    obs_name = curr_data.get("obsvtrNm", "알수없음")
    st.caption(f"🕒 실시간 관측 시간: {obs_time} (관측소: {obs_name})")


def _render_account_info():
    html = """
    <div style="background-color: #ffffff; border: 1px solid #dadce0;
                border-radius: 12px; padding: 16px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.04);
                height: 100%; display: flex; flex-direction: column;
                justify-content: center;">
        <div style="font-weight: bold; font-size: 0.95rem;
                    color: #202124; margin-bottom: 12px;
                    display: flex; align-items: center;">
            💳 예약/환불 계좌
        </div>
        <div style="font-size: 0.85rem; color: #333;">
            <div style="display: flex; justify-content: space-between;
                        align-items: center; margin-bottom: 8px;">
                <span style="background-color:#e8f0fe; color:#1a73e8;
                             padding:3px 6px; border-radius:4px;
                             font-weight:bold; font-size:0.75rem;">토스</span>
                <span style="font-family: monospace; font-weight: 600;
                             font-size: 0.9rem;">1001-2501-0108</span>
            </div>
            <div style="display: flex; justify-content: space-between;
                        align-items: center; margin-bottom: 8px;">
                <span style="background-color:#fae100; color:#371d1e;
                             padding:3px 6px; border-radius:4px;
                             font-weight:bold; font-size:0.75rem;">카카오</span>
                <span style="font-family: monospace; font-weight: 600;
                             font-size: 0.9rem;">3333058783320</span>
            </div>
            <div style="border-top: 1px dashed #eee; padding-top: 8px;
                        text-align: right; font-size: 0.8rem; color: #5f6368;">
                예금주: <strong style="color:#202124;">이재형</strong>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# 🌊 바다타임 물때표
# ============================================================

def _render_tide_info(sel_region2, bada_id_map):
    region_words = str(sel_region2).split()
    target_port = region_words[-1]
    target_city = region_words[0]

    clean_port = (target_port
                  .replace("항", "")
                  .replace("포구", "")
                  .replace("방파제", ""))

    b_id = (bada_id_map.get(target_port)
            or bada_id_map.get(clean_port)
            or bada_id_map.get(target_city, "118"))

    tide_url = f"https://www.badatime.com/{b_id}/tide"
    mobile_url = f"https://m.badatime.com/{b_id}.html"

    st.link_button(
        f"📱 {target_port} 모바일 물때 달력 (새 창 열기)",
        mobile_url, use_container_width=True
    )

    st.subheader("📊 통합 해양정보 대시보드 (바다타임 제공)")
    st.caption(
        f"※ 완벽 매핑된 **[{target_port}]** (또는 인근 지역) 데이터입니다! "
        "아래 화면에서 탭을 클릭해서 확인하세요!"
    )
    components.iframe(tide_url, height=1000, scrolling=True)


# ============================================================
# 🚢 탭2: 선사 정보 리스트 (기존)
# ============================================================

def _render_ship_list(df_fishing):
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.subheader("🚢 등록된 전체 선사 정보")
    with col_t2:
        st.write("")
        st.link_button("📊 구글 시트 직접 편집", REAL_SHEET_URL,
                       use_container_width=True)

    if not df_fishing.empty and "지역1" in df_fishing.columns:
        st.dataframe(df_fishing, use_container_width=True, hide_index=True)
    else:
        st.write("로컬 환경 제한으로 데이터가 표출되지 않습니다.")


# ============================================================
# 📸 탭3: 낚시 기록 & 사진 (🆕 신규!)
# ============================================================

def _render_fishing_records(df_record: pd.DataFrame):
    """낚시 기록 메인 페이지"""

    # 헤더
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.subheader("📸 도시어부의 추억")
    with col_t2:
        st.write("")
        st.link_button("📝 기록 추가하기 (구글시트)",
                       REAL_SHEET_URL,
                       use_container_width=True)

    # 데이터 검증
    if df_record is None or df_record.empty:
        st.warning("⚠️ 낚시 기록 데이터를 불러오지 못했습니다.")
        st.info("💡 구글 시트의 **`낚시기록`** 탭에 데이터를 입력하고, "
                "**파일 → 공유 → 웹에 게시**로 CSV URL을 받아 "
                "**`utils/constants.py`** 의 **`FISHING_RECORD_CSV`** 에 추가해주세요!")
        return

    # 데이터 전처리
    df = _preprocess_record(df_record)
    if df.empty:
        st.warning("⚠️ 유효한 출조 기록이 없습니다.")
        return

    # 1️⃣ 요약 대시보드
    _render_summary_dashboard(df)
    st.divider()

    # 2️⃣ 필터 + 출조 기록 테이블
    df_filtered = _render_filter_and_table(df)
    st.divider()

    # 3️⃣ 통계 차트
    _render_statistics(df)
    st.divider()

    # 4️⃣ BEST 출조 TOP 5
    _render_best_records(df)
    st.divider()

    # 5️⃣ 출조 상세 보기 + 사진
    _render_record_detail(df_filtered if not df_filtered.empty else df)


def _preprocess_record(df: pd.DataFrame) -> pd.DataFrame:
    """낚시 기록 데이터 전처리"""
    df = df.copy()

    # 일자 컬럼 처리
    if "일자" not in df.columns:
        return pd.DataFrame()

    df["일자_dt"] = pd.to_datetime(df["일자"], errors="coerce")
    df = df[df["일자_dt"].notna()].copy()

    # 연도 추출
    df["연도"] = df["일자_dt"].dt.year

    # 평점 숫자 변환
    if "평점(1~10)" in df.columns:
        df["평점숫자"] = pd.to_numeric(df["평점(1~10)"], errors="coerce")
    elif "평점" in df.columns:
        df["평점숫자"] = pd.to_numeric(df["평점"], errors="coerce")
    else:
        df["평점숫자"] = None

    # 최대사이즈 숫자 변환
    if "최대사이즈" in df.columns:
        df["사이즈숫자"] = pd.to_numeric(df["최대사이즈"], errors="coerce")
    else:
        df["사이즈숫자"] = None

    # 최신순 정렬
    df = df.sort_values("일자_dt", ascending=False)

    return df


def _render_summary_dashboard(df: pd.DataFrame):
    """요약 대시보드"""
    st.markdown("### 📊 한눈에 보는 낚시 라이프")

    # 출조 횟수 (행 수가 아닌, 일자별 unique 카운트)
    total_trips = df["일자"].nunique()

    # 연도별 출조 수
    current_year = date.today().year
    this_year_trips = df[df["연도"] == current_year]["일자"].nunique()

    # 어종 종류 수
    if "어종" in df.columns:
        all_fish = []
        for f in df["어종"].dropna():
            if str(f).strip():
                # 슬래시나 쉼표로 분리된 어종 분해
                for fish in str(f).replace("/", ",").split(","):
                    fish = fish.strip()
                    if fish:
                        all_fish.append(fish)
        unique_fish = len(set(all_fish))
    else:
        unique_fish = 0

    # 평균 평점
    avg_rating = df["평점숫자"].mean() if df["평점숫자"].notna().any() else 0

    # 최고 사이즈
    max_size = df["사이즈숫자"].max() if df["사이즈숫자"].notna().any() else 0

    # 메트릭 표시
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🎯 총 출조", f"{total_trips}회")
    c2.metric(f"📅 {current_year}년 출조", f"{this_year_trips}회")
    c3.metric("🐟 어종 종류", f"{unique_fish}종")
    c4.metric("⭐ 평균 평점",
              f"{avg_rating:.1f}점" if avg_rating > 0 else "-")
    c5.metric("🏆 최고 사이즈",
              f"{int(max_size)}cm" if max_size > 0 else "-")


def _render_filter_and_table(df: pd.DataFrame) -> pd.DataFrame:
    """필터 + 출조 기록 테이블"""
    st.markdown("### 📋 출조 기록 리스트")

    # 필터 4개
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        years = ["전체"] + sorted(
            [int(y) for y in df["연도"].unique()], reverse=True
        )
        sel_year = st.selectbox("📅 연도", years, key="record_year")

    with col_f2:
        regions = ["전체"]
        if "지역1" in df.columns:
            regions += sorted([str(r) for r in df["지역1"].unique()
                               if str(r).strip()])
        sel_region = st.selectbox("📍 지역", regions, key="record_region")

    with col_f3:
        ships = ["전체"]
        if "선사명" in df.columns:
            ships += sorted([str(s) for s in df["선사명"].unique()
                             if str(s).strip()])
        sel_ship = st.selectbox("🚢 선사", ships, key="record_ship")

    with col_f4:
        fishes = ["전체"]
        if "어종" in df.columns:
            fish_set = set()
            for f in df["어종"].dropna():
                if str(f).strip():
                    for fish in str(f).replace("/", ",").split(","):
                        fish = fish.strip()
                        if fish:
                            fish_set.add(fish)
            fishes += sorted(fish_set)
        sel_fish = st.selectbox("🐟 어종", fishes, key="record_fish")

    # 필터 적용
    df_f = df.copy()
    if sel_year != "전체":
        df_f = df_f[df_f["연도"] == sel_year]
    if sel_region != "전체" and "지역1" in df_f.columns:
        df_f = df_f[df_f["지역1"] == sel_region]
    if sel_ship != "전체" and "선사명" in df_f.columns:
        df_f = df_f[df_f["선사명"] == sel_ship]
    if sel_fish != "전체" and "어종" in df_f.columns:
        df_f = df_f[df_f["어종"].astype(str).str.contains(
            sel_fish, na=False, regex=False)]

    # 결과 표시
    st.caption(f"🔍 검색 결과: **{len(df_f)}건**")

    if df_f.empty:
        st.info("조건에 맞는 기록이 없습니다.")
        return df_f

    # 표시할 컬럼만 선택
    display_cols = []
    col_order = ["일자", "요일", "시간대", "지역1", "지역2", "선사명",
                 "어종", "낚시방법", "재형결과", "최대사이즈",
                 "평점(1~10)", "동행자"]
    for c in col_order:
        if c in df_f.columns:
            display_cols.append(c)

    st.dataframe(
        df_f[display_cols],
        use_container_width=True,
        hide_index=True,
        height=350,
    )

    return df_f


def _render_statistics(df: pd.DataFrame):
    """통계 차트"""
    st.markdown("### 📈 출조 통계 분석")

    col_s1, col_s2 = st.columns(2)

    # 1) 연도별 출조 횟수
    with col_s1:
        st.markdown("##### 📅 연도별 출조 횟수")
        year_counts = df.groupby("연도")["일자"].nunique().reset_index()
        year_counts.columns = ["연도", "출조횟수"]
        year_counts = year_counts.sort_values("연도")
        st.bar_chart(year_counts.set_index("연도"), height=250)

    # 2) 어종별 빈도
    with col_s2:
        st.markdown("##### 🐟 어종별 출조 빈도")
        if "어종" in df.columns:
            all_fish = []
            for f in df["어종"].dropna():
                if str(f).strip():
                    for fish in str(f).replace("/", ",").split(","):
                        fish = fish.strip()
                        if fish:
                            all_fish.append(fish)

            if all_fish:
                fish_counts = pd.Series(Counter(all_fish)).sort_values(
                    ascending=False).head(10)
                fish_df = pd.DataFrame({
                    "어종": fish_counts.index,
                    "횟수": fish_counts.values
                })
                st.bar_chart(fish_df.set_index("어종"), height=250)
            else:
                st.info("어종 데이터가 없습니다.")

    col_s3, col_s4 = st.columns(2)

    # 3) 선사 TOP 10
    with col_s3:
        st.markdown("##### 🚢 자주 가는 선사 TOP 10")
        if "선사명" in df.columns:
            ship_data = df[df["선사명"].astype(str).str.strip() != ""]
            if not ship_data.empty:
                ship_counts = ship_data["선사명"].value_counts().head(10)
                ship_df = pd.DataFrame({
                    "선사명": ship_counts.index,
                    "방문횟수": ship_counts.values
                })
                st.bar_chart(ship_df.set_index("선사명"), height=250)
            else:
                st.info("선사 데이터가 없습니다.")

    # 4) 지역별 분포
    with col_s4:
        st.markdown("##### 📍 지역별 출조 분포")
        if "지역1" in df.columns:
            region_data = df[df["지역1"].astype(str).str.strip() != ""]
            if not region_data.empty:
                region_counts = region_data["지역1"].value_counts()
                region_df = pd.DataFrame({
                    "지역": region_counts.index,
                    "출조횟수": region_counts.values
                })
                st.bar_chart(region_df.set_index("지역"), height=250)
            else:
                st.info("지역 데이터가 없습니다.")


def _render_best_records(df: pd.DataFrame):
    """BEST 출조 TOP 5"""
    st.markdown("### 🏆 BEST 출조 TOP 5")

    # 평점이 있는 기록만
    df_rated = df[df["평점숫자"].notna()].copy()

    if df_rated.empty:
        st.info("💡 평점이 입력된 기록이 아직 없습니다. 시트에 평점을 입력해보세요!")
        return

    # 평점 + 사이즈 종합 정렬
    df_rated["종합점수"] = df_rated["평점숫자"].fillna(0) + \
                          (df_rated["사이즈숫자"].fillna(0) / 100)
    top5 = df_rated.nlargest(5, "종합점수")

    cols = st.columns(min(5, len(top5)))
    for i, (_, row) in enumerate(top5.iterrows()):
        with cols[i]:
            rating = row.get("평점숫자", 0)
            size = row.get("사이즈숫자", 0)
            date_str = row["일자_dt"].strftime("%Y-%m-%d")
            region = row.get("지역2", row.get("지역1", "?"))
            ship = row.get("선사명", "-")
            fish = row.get("어종", "-")

            rank_emoji = ["🥇", "🥈", "🥉", "🏅", "🏅"][i]

            card_html = f"""
            <div style="border: 2px solid #ffc107; border-radius: 12px;
                        padding: 12px; background-color: #fffdf5;
                        height: 100%; text-align: center;
                        box-shadow: 0 2px 8px rgba(255,193,7,0.2);">
                <div style="font-size: 1.8rem; margin-bottom: 4px;">
                    {rank_emoji}
                </div>
                <div style="font-weight: bold; color: #ff6b35;
                            font-size: 1.1rem; margin-bottom: 6px;">
                    ⭐ {rating:.0f}점
                </div>
                <div style="font-size: 0.85rem; color: #555;
                            margin-bottom: 4px;">
                    📅 {date_str}
                </div>
                <div style="font-size: 0.85rem; color: #333;
                            margin-bottom: 4px;">
                    📍 {region}
                </div>
                <div style="font-size: 0.85rem; color: #333;
                            margin-bottom: 4px;">
                    🚢 {ship}
                </div>
                <div style="font-size: 0.85rem; color: #333;">
                    🐟 {fish}
                </div>
                {f'<div style="font-size: 0.8rem; color: #d11820; margin-top: 4px; font-weight: bold;">📏 {int(size)}cm</div>' if size > 0 else ''}
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)


def _render_record_detail(df: pd.DataFrame):
    """출조 상세 보기 + 사진 폴더 링크"""
    st.markdown("### 🔍 출조 상세 보기")

    if df.empty:
        st.info("표시할 기록이 없습니다.")
        return

    # 출조 선택 옵션 생성
    options = []
    for _, row in df.iterrows():
        date_str = row["일자_dt"].strftime("%Y-%m-%d")
        region = row.get("지역2", row.get("지역1", "?"))
        ship = row.get("선사명", "-")
        time_slot = row.get("시간대", "")
        time_str = f" [{time_slot}]" if time_slot and str(time_slot).strip() else ""
        options.append(f"{date_str}{time_str} | {region} | {ship}")

    sel_idx = st.selectbox(
        "출조 선택", range(len(options)),
        format_func=lambda i: options[i],
        key="record_detail_select"
    )

    sel_row = df.iloc[sel_idx]

    # 상세 정보 표시
    col_d1, col_d2 = st.columns([1, 1])

    with col_d1:
        st.markdown("##### 📅 기본 정보")
        _show_info_row("일자",
                       sel_row["일자_dt"].strftime("%Y-%m-%d (%a)"))
        _show_info_row("시간대", sel_row.get("시간대", ""))
        _show_info_row("지역",
                       f"{sel_row.get('지역1', '')} {sel_row.get('지역2', '')}")
        _show_info_row("선사명", sel_row.get("선사명", ""))
        _show_info_row("출조형태", sel_row.get("출조형태", ""))
        _show_info_row("탑승현황", sel_row.get("탑승현황", ""))
        _show_info_row("동행자", sel_row.get("동행자", ""))

        st.markdown("##### 🎣 낚시 정보")
        _show_info_row("어종", sel_row.get("어종", ""))
        _show_info_row("낚시방법", sel_row.get("낚시방법", ""))
        _show_info_row("사용채비", sel_row.get("사용채비", ""))
        _show_info_row("사용미끼", sel_row.get("사용미끼", ""))
        _show_info_row("히트미끼", sel_row.get("히트미끼", ""))

    with col_d2:
        st.markdown("##### 🏆 결과 & 환경")
        _show_info_row("배전체조황", sel_row.get("배전체조황", ""))
        _show_info_row("재형결과", sel_row.get("재형결과", ""))
        _show_info_row("최대사이즈",
                       f"{int(sel_row['사이즈숫자'])}cm"
                       if pd.notna(sel_row.get("사이즈숫자")) else "")
        _show_info_row("방생", sel_row.get("방생", ""))
        _show_info_row("날씨", sel_row.get("날씨", ""))
        _show_info_row("파도", sel_row.get("파도", ""))
        _show_info_row("바람", sel_row.get("바람", ""))
        _show_info_row("물때", sel_row.get("물때", ""))

        st.markdown("##### ⭐ 평가")
        rating = sel_row.get("평점숫자", None)
        if pd.notna(rating):
            stars = "⭐" * int(rating) + "☆" * (10 - int(rating))
            _show_info_row("평점", f"{int(rating)}/10 {stars}")
        _show_info_row("배평가", sel_row.get("배평가", ""))
        _show_info_row("사무장여부", sel_row.get("사무장여부", ""))
        _show_info_row("재이용의사", sel_row.get("재이용의사", ""))

    # 비고
    bigo = sel_row.get("비고", "")
    if bigo and str(bigo).strip():
        st.markdown("##### 📝 비고")
        st.info(bigo)

    # 사진 폴더 + 조황 링크 버튼
    col_b1, col_b2 = st.columns(2)

    with col_b1:
        photo_url = sel_row.get("사진폴더", "")
        if photo_url and str(photo_url).startswith("http"):
            st.link_button("📸 사진 폴더 열기 (구글 드라이브)",
                           photo_url, use_container_width=True,
                           type="primary")
        else:
            st.button("📸 사진 폴더 없음", disabled=True,
                      use_container_width=True)

    with col_b2:
        catch_url = sel_row.get("조황링크", "")
        if catch_url and str(catch_url).startswith("http"):
            st.link_button("🔗 선사 조황 보기",
                           catch_url, use_container_width=True,
                           type="secondary")
        else:
            st.button("🔗 조황 링크 없음", disabled=True,
                      use_container_width=True)


def _show_info_row(label, value):
    """정보 한 줄 표시"""
    val = str(value).strip() if value is not None else ""
    if not val or val == "nan":
        val = "-"
    st.markdown(
        f"<div style='display: flex; padding: 4px 0; "
        f"border-bottom: 1px dashed #eee;'>"
        f"<div style='width: 90px; color: #5f6368; font-size: 0.9rem;'>"
        f"{label}</div>"
        f"<div style='flex: 1; color: #202124; font-size: 0.9rem; "
        f"font-weight: 500;'>{val}</div></div>",
        unsafe_allow_html=True
    )