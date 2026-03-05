import streamlit as st
import pandas as pd
import os
import requests
import urllib.request
import io
from datetime import date, datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar

# 1. 페이지 설정
st.set_page_config(page_title="재형의 대시보드", page_icon="🏠", layout="wide")

# ✨ [UI 간격 조정] 상단 여백 싹 제거
st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem !important; }
        header { height: 2rem !important; background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# --- 🔄 [구글 시트 연동 설정] ---
FISHING_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR0bfr1sGxo99WWEmDw7Q1SEQo9a9DkloWt2pgIFwoIGCTi0SmD1lQRp_GsyTIbqBm3pn9SRCVwxpi_/pub?gid=1169225155&single=true&output=csv"
CALENDAR_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR0bfr1sGxo99WWEmDw7Q1SEQo9a9DkloWt2pgIFwoIGCTi0SmD1lQRp_GsyTIbqBm3pn9SRCVwxpi_/pub?gid=1183615157&single=true&output=csv"

REAL_SHEET_URL = "https://docs.google.com/spreadsheets/d/1g9nOdErm8O8isOykEXyjDwlQqKaBtjk_3vGnsXEhaE0/edit"

@st.cache_data(ttl=600)
def load_data(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status() 
        res.encoding = 'utf-8'
        return pd.read_csv(io.StringIO(res.text)).fillna("")
    except Exception:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                return pd.read_csv(response, encoding='utf-8').fillna("")
        except Exception:
            return pd.DataFrame()

# 데이터 로딩
df_fishing = load_data(FISHING_CSV)
df_events = load_data(CALENDAR_CSV)

# 2. 사이드바 및 가족 트리
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

# --- 🔄 공통 데이터 처리 ---
today = date.today()

def get_next_date(m, d):
    try: target = date(today.year, m, d)
    except ValueError: target = date(today.year, m + 1, 1) 
    if target < today: target = date(today.year + 1, m, d)
    return target

def get_next_lunar_date(m, d):
    calendar = KoreanLunarCalendar()
    calendar.setLunarDate(today.year, m, d, False)
    target = date(calendar.solarYear, calendar.solarMonth, calendar.solarDay)
    if target < today:
        calendar.setLunarDate(today.year + 1, m, d, False)
        target = date(calendar.solarYear, calendar.solarMonth, calendar.solarDay)
    return target

fixed_events = {
    "💰 로또 사는 날": (today + timedelta(days=(3 - today.weekday()) % 7)),
    "👦 은호 생일": get_next_date(7, 10),
    "👶 수호 생일": get_next_date(5, 19),
    "🎂 연정 생일": get_next_lunar_date(10, 24),
    "🎂 재형 생일": get_next_date(10, 18),
    "💍 결혼기념일": get_next_date(4, 22),
}

# --- 🏠 홈 메뉴 ---
if menu == "🏠 홈":
    st.title("환영합니다! 재형님 👋")
    st.subheader("🗓️ 주요 일정 (D-Day)")
    
    combined_all = fixed_events.copy()
    
    if not df_events.empty and "일자" in df_events.columns and "내용" in df_events.columns:
        for _, row in df_events.iterrows():
            try:
                ev_date = pd.to_datetime(row['일자']).date()
                if ev_date >= today:
                    combined_all[f"📂 {row['내용']}"] = ev_date
            except: pass

    sorted_top6 = sorted(combined_all.items(), key=lambda x: x[1])[:6]
    
    if sorted_top6:
        cols = st.columns(len(sorted_top6))
        for i, (name, target_date) in enumerate(sorted_top6):
            d_day = (target_date - today).days
            with cols[i]:
                if d_day == 0:
                    st.metric(label=name, value="Today", delta="오늘!", delta_color="inverse")
                elif d_day == 1:
                    st.metric(label=name, value="D-1", delta="내일!")
                else:
                    st.metric(label=name, value=f"D-{d_day}", delta=target_date.strftime("%m.%d"))

    st.divider()
    
    st.subheader("🔎 빠른 검색")
    g1, g2, g3, g4 = st.columns([0.5, 6, 1.5, 1.5])
    with g1: st.image("https://www.google.com/favicon.ico", width=28)
    with g2: google_q = st.text_input("Google", label_visibility="collapsed", placeholder="Google 검색어 입력", key="g_in")
    with g3: st.link_button("🔍 Go", f"https://www.google.com/search?q={google_q}" if google_q else "https://www.google.com/", use_container_width=True)
    with g4: st.link_button("📧 Gmail", "https://mail.google.com/", use_container_width=True)
    
    n1, n2, n3, n4 = st.columns([0.5, 6, 1.5, 1.5])
    with n1: st.image("https://www.naver.com/favicon.ico", width=28)
    with n2: naver_q = st.text_input("Naver", label_visibility="collapsed", placeholder="Naver 검색어 입력", key="n_in")
    with n3: st.link_button("🔍 Go", f"https://search.naver.com/search.naver?query={naver_q}" if naver_q else "https://www.naver.com/", use_container_width=True)
    with n4: st.link_button("📧 N메일", "https://mail.naver.com/", use_container_width=True)

    st.divider()
    st.subheader("🚀 바로가기")
    l1, l2, l3 = st.columns(3)
    l1.link_button("🎣 로구만 카페", "https://cafe.naver.com/blackoxxxq", use_container_width=True)
    l2.link_button("✨ Gemini 메인", "https://gemini.google.com/", use_container_width=True)
    l3.link_button("📂 구글 드라이브", "https://drive.google.com/", use_container_width=True)

# --- 🗓️ 일정 메뉴 ---
elif menu == "🗓️ 일정":
    st.title("상세 일정 및 메모 관리 🗓️")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("📅 날짜 선택")
        sel_date = st.date_input("조회할 날짜", value=today, key="sel_date_picker")
        
        st.info("💡 일정과 메모는 아래 구글 시트에서 관리하세요.")
        st.link_button("📊 구글 시트 직접 편집하기", REAL_SHEET_URL, use_container_width=True, type="primary")

        st.divider()

        st.subheader("🔢 날짜 계산기")
        calc_mode = st.radio("계산 선택", ["날짜 더하기 (+일)", "D-Day 계산"], horizontal=True)
        
        if calc_mode == "날짜 더하기 (+일)":
            plus_days = st.number_input("며칠 뒤를 계산할까요?", min_value=1, value=100)
            target_calc_date = today + timedelta(days=plus_days)
            st.success(f"{plus_days}일 뒤: **{target_calc_date.strftime('%Y-%m-%d')}**")
        else:
            target_d = st.date_input("기준 날짜 선택", value=date(2026, 12, 25))
            diff = (target_d - today).days
            if diff > 0:
                st.info(f"**{diff}일** 남았습니다.")
            elif diff == 0:
                st.success("오늘입니다! 🎉")
            else:
                st.warning(f"**{abs(diff)}일** 지났습니다.")

    with c2:
        st.subheader(f"📢 {sel_date.strftime('%m월 %d일')} 일정 및 메모")
        
        found_on_date = False
        for name, d_obj in fixed_events.items():
            if d_obj == sel_date:
                st.success(f"📌 **[고정] {name}**")
                found_on_date = True
        
        if not df_events.empty and "일자" in df_events.columns and "내용" in df_events.columns:
            for _, row in df_events.iterrows():
                try:
                    ev_date = pd.to_datetime(row['일자']).date()
                    if ev_date == sel_date:
                        st.success(f"📂 **[엑셀] {row['내용']}**")
                        memo_val = row.get('메모', "")
                        if memo_val and str(memo_val).strip() != "":
                            st.warning(f"📝 **메모:** {memo_val}")
                        found_on_date = True
                except:
                    continue
        
        if not found_on_date:
            st.info("해당 날짜에 등록된 일정이 없습니다.")

        st.divider()
        st.subheader("📋 전체 일정 리스트 (D-Day 순)")
        
        all_combined_list = []
        for n, d in fixed_events.items():
            all_combined_list.append({"날짜": d, "내용": n, "출처": "고정"})
        
        if not df_events.empty and "일자" in df_events.columns and "내용" in df_events.columns:
            for _, row in df_events.iterrows():
                try:
                    all_combined_list.append({
                        "날짜": pd.to_datetime(row['일자']).date(),
                        "내용": row['내용'],
                        "출처": "엑셀"
                    })
                except:
                    continue
        
        if all_combined_list:
            future_events = [item for item in all_combined_list if item["날짜"] >= today]
            
            if future_events:
                display_df = pd.DataFrame(future_events).sort_values(by="날짜")
                display_df['D-Day'] = display_df['날짜'].apply(
                    lambda x: f"D-{(x-today).days}" if x > today else "Today"
                )
                st.dataframe(display_df[['날짜', 'D-Day', '내용', '출처']], use_container_width=True, hide_index=True)
            else:
                st.info("예정된 일정이 없습니다.")
        
elif menu == "👨‍👩‍👦‍👦 가족":
    st.title("사랑하는 우리 가족 ❤️")
    st.write("가족 구성원 정보를 확인하고 주요 일정을 공유하는 공간입니다.")
    
    if not df_events.empty:
        if "일자" in df_events.columns:
            st.subheader("📅 엑셀 연동 가족 일정 (Jaehyung_Home_Data)")
            df_events['일자'] = pd.to_datetime(df_events['일자']).dt.date
            st.dataframe(df_events.sort_values('일자'), use_container_width=True, hide_index=True)
        else:
            st.error("🚨 엑셀 데이터 형식을 불러오는 중 오류가 발생했습니다.")
    else:
        st.info("💡 구글 드라이브의 엑셀 파일에 일정을 입력하면 여기에 나타납니다.")

    st.divider()
    st.image("https://cdn-icons-png.flaticon.com/512/3093/3093835.png", width=200)

elif menu == "📈 자산 관리":
    st.title("미국 주식 수익률 계산기 💵")
    
    c1, c2 = st.columns([1, 1.5])
    with c1:
        price = st.number_input("단가 ($)", value=29.50)
        qty = st.number_input("수량", value=100)
        curr = st.number_input("현재가 ($)", value=31.30)
    with c2:
        profit = (curr - price) * qty
        rate = ((curr - price) / price) * 100
        st.metric("수익률", f"{rate:.2f}%", delta=f"{profit:.2f}$")
        st.write("---")
        st.caption("💸 실시간 환율을 적용한 원화 환산 기능은 추후 업데이트 예정입니다.")

elif menu == "🎣 낚시":
    st.markdown("<h1 style='text-align: center;'>도시어부 라이프 🎣</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📅 출조 포털 & 물때", "🚢 선사정보", "📸 낚시사진"])
    
    with tab1:
        st.subheader("📅 원클릭 출조 및 실시간 정보")
        
        if not df_fishing.empty:
            if "지역" in df_fishing.columns and "선사명" in df_fishing.columns:
                col1, col2, col3 = st.columns(3)
                with col1:
                    t_date = st.date_input("출조 예정일", value=today, format="YYYY/MM/DD")
                with col2:
                    region_list = ["선택하세요"] + sorted([str(r) for r in df_fishing["지역"].unique() if str(r).strip() != ""])
                    sel_region = st.selectbox("출조 지역 선택 📍", region_list)
                with col3:
                    if sel_region != "선택하세요":
                        filtered_names = df_fishing[df_fishing["지역"] == sel_region]["선사명"].unique()
                        name_list = ["선택하세요"] + sorted([str(n) for n in filtered_names])
                        sel_name = st.selectbox("선사 선택 🚢", name_list)
                    else:
                        sel_name = st.selectbox("선사 선택 🚢", ["지역을 먼저 선택하세요"])

                st.divider()

                if sel_region != "선택하세요":
                    obs_map = {"군산": "DT_0026", "비응항": "DT_0026", "보령": "DT_0031", "대천": "DT_0031", "안흥": "DT_0035", "시화": "DT_0041", "오이도": "DT_0041", "인천": "DT_0001", "연안부두": "DT_0001", "영종도": "DT_0001", "백사장항": "DT_0035", "안면도": "DT_0035", "장고항": "DT_0033", "홍원항": "DT_0028"}
                    obs_code = next((v for k, v in obs_map.items() if k in sel_region), "DT_0026")
                    
                    try:
                        if hasattr(st, "secrets") and "KHOA_API_KEY" in st.secrets:
                            api_key = st.secrets["KHOA_API_KEY"].strip()
                            
                            today_str = date.today().strftime("%Y%m%d")
                            obs_url = f"https://apis.data.go.kr/1192136/dtRecent/GetDTRecentApiService?serviceKey={api_key}&pageNo=1&numOfRows=10&type=json&obsCode={obs_code}&reqDate={today_str}"
                            
                            res = requests.get(obs_url, timeout=10)
                            
                            if res.status_code == 200:
                                try:
                                    data = res.json()
                                    items = []
                                    
                                    # ✨ [업그레이드] 어떤 모양의 박스로 오든 다 뜯어냅니다!
                                    if "response" in data and "body" in data.get("response", {}):
                                        body = data["response"]["body"]
                                        if body.get("items"):
                                            raw_item = body["items"].get("item", [])
                                            if isinstance(raw_item, list):
                                                items = raw_item
                                            elif isinstance(raw_item, dict):
                                                items = [raw_item]
                                    
                                    # 데이터가 존재할 경우 화면에 뿌리기
                                    if items:
                                        curr_data = items[-1]
                                        w1, w2, w3 = st.columns(3)
                                        wind_val = curr_data.get('wind_speed', curr_data.get('wind_spd', '-'))
                                        w1.metric("💨 실시간 풍속", f"{wind_val} m/s")
                                        w2.metric("🌡️ 현재 수온", f"{curr_data.get('water_temp', '-')} ℃")
                                        w3.metric("📏 실시간 조위", f"{curr_data.get('tide_level', '-')} cm")
                                        
                                        obs_time = curr_data.get('record_time', curr_data.get('obs_time', '알수없음'))
                                        st.caption(f"🕒 관측 시간: {obs_time}")
                                    else:
                                        # ✨ [엑스레이 장착] 진짜 데이터가 비어있다면 서버가 준 편지(JSON) 원본을 그대로 노출!
                                        st.warning("⚠️ API 통신은 성공했으나, 공공데이터포털에서 받은 상자(데이터)가 비어있습니다!")
                                        with st.expander("🔍 공공데이터포털 서버 응답 원본(JSON) 보기", expanded=True):
                                            st.json(data)
                                        
                                except ValueError:
                                    st.error("🚨 API 인증 에러! (공공데이터포털 서버 지연)")
                                    with st.expander("🔍 에러 메시지 원본 보기"):
                                        st.text(res.text[:500])
                            else:
                                st.error(f"🚨 공공데이터포털 서버 통신 실패! 상태코드: {res.status_code}")
                        else:
                            st.info("💡 실시간 물때를 보려면 Streamlit Cloud에 API 키(Secrets)를 등록해주세요.")
                    except Exception as e:
                        st.error(f"🚨 기상 API 통신 에러 발생: {e}")

                    b1, b2 = st.columns(2)
                    with b1:
                        st.link_button(f"🌊 {sel_region} 상세 물때표 (바다타임)", f"https://www.badatime.com/search.jsp?q={sel_region}", use_container_width=True)
                    with b2:
                        if sel_name not in ["선택하세요", "지역을 먼저 선택하세요"]:
                            target_row = df_fishing[(df_fishing["지역"] == sel_region) & (df_fishing["선사명"] == sel_name)]
                            if not target_row.empty:
                                res_url = str(target_row["예약사이트"].values[0])
                                if res_url.startswith("http"):
                                    st.link_button(f"🚢 {sel_name} 예약 사이트 바로가기", res_url, use_container_width=True, type="primary")
            
            else:
                st.error("🚨 한글 인코딩 또는 컬럼 누락 에러!")

        else:
            st.warning("⚠️ 구글 시트 데이터를 불러오지 못했습니다.")

    with tab2:
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            st.subheader("🚢 등록된 전체 선사 정보")
        with col_t2:
            st.write("") 
            st.link_button("📊 구글 시트 직접 편집", REAL_SHEET_URL, use_container_width=True)
            
        if not df_fishing.empty and "지역" in df_fishing.columns:
            st.dataframe(df_fishing, use_container_width=True, hide_index=True)
        else:
            st.write("로컬 환경 제한으로 데이터가 표출되지 않습니다. (배포된 웹사이트에서 확인해주세요)")

    with tab3:
        st.subheader("📸 낚시의 추억")
        st.info("여기에 낚시 사진 갤러리 기능을 추가할 예정입니다!")