"""
🎣 낚시 페이지 (가장 큰 모듈)
- 탭1: 출조 포털 & 물때 (선사 선택 + 해양관측 + 바다타임)
- 탭2: 선사 정보 리스트
- 탭3: 낚시 사진 (추후 구현)
"""

from datetime import date, datetime, timedelta
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

from utils.constants import REAL_SHEET_URL, KHOA_OBS_MAP, KHOA_DEFAULT_CODE


def render(df_fishing: pd.DataFrame, bada_id_map: dict):
    """낚시 페이지 렌더링 진입점"""
    st.markdown(
        "<h1 style='text-align: center;'>도시어부 라이프 🎣</h1>",
        unsafe_allow_html=True
    )

    tab1, tab2, tab3 = st.tabs(
        ["📅 출조 포털 & 물때", "🚢 선사정보", "📸 낚시사진"]
    )

    with tab1:
        _render_fishing_portal(df_fishing, bada_id_map)

    with tab2:
        _render_ship_list(df_fishing)

    with tab3:
        _render_photo_gallery()


# ============================================================
# 🎯 탭1: 출조 포털
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

    # 세션 상태 초기화
    _init_session_state()

    # 필터 UI
    today = date.today()
    t_date, sel_region1, sel_region2, sel_name = _render_filter_ui(
        df_fishing, today
    )
    st.divider()

    # 선택된 선사 카드
    if sel_name != "전체":
        df_filtered = df_fishing.copy()
        if sel_region1 != "전체":
            df_filtered = df_filtered[df_filtered["지역1"] == sel_region1]
        if sel_region2 != "전체":
            df_filtered = df_filtered[df_filtered["지역2"] == sel_region2]
        _render_ship_card(df_filtered, sel_name)

    # 상세 정보 (해양관측 + 계좌 + 물때)
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
        """선사 선택시 항구 자동 채우기"""
        ship = st.session_state.sel_ship
        if ship != "전체":
            port = df_fishing[df_fishing["선사명"] == ship]["지역2"].values
            if len(port) > 0:
                st.session_state.sel_reg2 = str(port[0])

    col1, col2, col3, col4 = st.columns([1, 1.2, 1.2, 1.5])

    # 출조 날짜
    with col1:
        t_date = st.date_input(
            "출조 예정일", value=today, format="YYYY/MM/DD"
        )

    # 지역1 (도/시)
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

    # 1차 필터링
    df_step1 = df_fishing.copy()
    if sel_region1 != "전체":
        df_step1 = df_step1[df_step1["지역1"] == sel_region1]

    # 지역2 (상세 항구)
    with col3:
        sel_region2 = _render_port_selectbox(df_step1)

    # 2차 필터링
    df_step2 = df_step1.copy()
    if sel_region2 != "전체":
        df_step2 = df_step2[df_step2["지역2"] == sel_region2]

    # 선사명
    with col4:
        sel_name = _render_ship_selectbox(df_step2, auto_fill_port)

    return t_date, sel_region1, sel_region2, sel_name


def _render_port_selectbox(df_step1: pd.DataFrame) -> str:
    """항구 선택박스 ([지역1] 지역2 형식)"""
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
    """선사 선택박스 (배지 포함)"""
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
    """관심/로구만 플래그 체크"""
    if col_name not in row:
        return False
    val = str(row[col_name]).strip()
    return bool(val) and val.upper() != "NAN"


# ============================================================
# 🏷️ 선사 스마트칩 카드
# ============================================================

def _render_ship_card(df_filtered: pd.DataFrame, sel_name: str):
    """선사 스마트 카드 렌더링"""
    target = df_filtered[df_filtered["선사명"] == sel_name]
    if target.empty:
        return

    res_url = str(target["예약사이트"].values[0])
    if not res_url.startswith("http"):
        return

    clean_domain = res_url.replace("https://", "") \
        .replace("http://", "").split("/")[0]

    # 배지
    fav_badge = _build_badge(target, "주요 관심 선사",
                              "⭐ 관심선사", "#fff3cd", "#856404", "#ffeeba")
    roguman_badge = _build_badge(target, "로구만 프렌즈 선사",
                                  "⚓ 로구만", "#cce5ff", "#004085", "#b8daff")

    # 버튼들
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


def _build_badge(target, col_name: str, label: str,
                 bg: str, color: str, border: str) -> str:
    """배지 HTML 생성"""
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


def _build_link_button(url: str, label: str, bg_color: str) -> str:
    """링크 버튼 HTML 생성"""
    return (
        f'<a href="{url}" target="_blank" '
        f'style="background-color: {bg_color}; color: white; '
        f'text-decoration: none; padding: 8px 0; border-radius: 6px; '
        f'font-weight: bold; font-size: 0.85rem; text-align: center; '
        f'border: none; cursor: pointer; display: block; width: 100%;">'
        f'{label}</a>'
    )


def _build_sunsang_button(target) -> str:
    """선상24 링크 버튼"""
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


def _build_thefishing_button(target) -> str:
    """더피싱 링크 버튼"""
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
# 🌊 해양 관측 + 계좌 정보
# ============================================================

def _render_observation_and_account(sel_region2: str,
                                      t_date: date, today: date):
    """해양 관측정보 + 계좌정보 (2:1 분할)"""
    col_obs, col_acc = st.columns([2.5, 1])

    with col_obs:
        _render_marine_observation(sel_region2, t_date, today)

    with col_acc:
        _render_account_info()


def _render_marine_observation(sel_region2: str,
                                t_date: date, today: date):
    """KHOA 해양 실시간 관측정보"""
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

        # 가장 최신 데이터 조회
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


def _display_observation_metrics(curr_data: dict):
    """관측 데이터 메트릭 표시"""
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
    """계좌 정보 카드"""
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

def _render_tide_info(sel_region2: str, bada_id_map: dict):
    """바다타임 물때 정보 임베딩"""
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
# 🚢 탭2: 선사 정보 리스트
# ============================================================

def _render_ship_list(df_fishing: pd.DataFrame):
    """선사 전체 정보 리스트"""
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
        st.write("로컬 환경 제한으로 데이터가 표출되지 않습니다. "
                 "(배포된 웹사이트에서 확인해주세요)")


# ============================================================
# 📸 탭3: 낚시 사진 (추후 구현)
# ============================================================

def _render_photo_gallery():
    """낚시 사진 갤러리 (미구현)"""
    st.subheader("📸 낚시의 추억")
    st.info("여기에 낚시 사진 갤러리 기능을 추가할 예정입니다!")
