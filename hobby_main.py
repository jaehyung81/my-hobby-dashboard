import streamlit as st
import pandas as pd
import os
import requests
import urllib.request
import io
import re
from collections import defaultdict # ✨ 같은 날짜 묶어주는 마법 도구 추가
from datetime import date, datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar
import streamlit.components.v1 as components

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

# ✨ [바다타임 1400개 매핑 자동화] 
@st.cache_data
def load_bada_map():
    bada_map = {
        "비응": "118", "군산": "118", "오이도": "380", "보령": "126", "무창포": "126", "오천": "126",
        "홍원": "523", "마량": "523", "태안": "128", "안흥": "128", "신진도": "128", "백사장": "175",
        "당진": "131", "장고항": "131", "영종도": "159", "인천": "159", "고성": "528", "대진": "528", "속초": "192"
    }
    try:
        if os.path.exists("bada_mapping.txt"):
            with open("bada_mapping.txt", "r", encoding="utf-8") as f:
                html_text = f.read()
                matches = re.findall(r'badatime\.com/(\d+)/[^>]*>([^<]+)</a>', html_text)
                for b_id, name in matches:
                    clean_name = name.strip()
                    bada_map[clean_name] = b_id
                    if clean_name.endswith("항"):
                        bada_map[clean_name[:-1]] = b_id
                    if clean_name.endswith("포구"):
                        bada_map[clean_name[:-2]] = b_id
    except Exception:
        pass
    return bada_map

df_fishing = load_data(FISHING_CSV)
df_events = load_data(CALENDAR_CSV)
bada_id_map = load_bada_map() 

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
    "👩 어머니 생신": get_next_date(2, 1),
    "👨 아버지 생신": get_next_lunar_date(8, 12),
    "👵 어머님 생신": get_next_lunar_date(1, 20),
    "👴 아버님 생신": get_next_lunar_date(9, 4),
}

# --- 🏠 홈 메뉴 ---
if menu == "🏠 홈":
    st.title("환영합니다! 재형님 👋")
    st.subheader("🗓️ 주요 일정 (D-Day)")
    
    # ✨ [D-Day 카드 UI 적용] 모든 일정을 모아서 '날짜별'로 완벽하게 그룹핑!
    all_future_events = []
    
    # 1. 고정 일정 담기
    for name, d_obj in fixed_events.items():
        if d_obj >= today:
            all_future_events.append({"date": d_obj, "name": name})
            
    # 2. 엑셀 일정 담기
    if not df_events.empty and "일자" in df_events.columns and "내용" in df_events.columns:
        for _, row in df_events.iterrows():
            try:
                ev_date = pd.to_datetime(row['일자']).date()
                if ev_date >= today:
                    v_type = str(row.get('연차구분', "")).strip()
                    v_str = f"[{v_type}] " if v_type else ""
                    all_future_events.append({"date": ev_date, "name": f"📂 {v_str}{row['내용']}"})
            except: pass

    # 3. 날짜별로 묶어주기 (3월 12일에 2개가 있으면 하나로 통합!)
    grouped_events = defaultdict(list)
    for ev in all_future_events:
        if ev["name"] not in grouped_events[ev["date"]]:
            grouped_events[ev["date"]].append(ev["name"])
            
    # 가장 가까운 5일치 날짜만 추출
    sorted_dates = sorted(grouped_events.keys())[:5]
    
    if sorted_dates:
        cols = st.columns(len(sorted_dates))
        for i, d in enumerate(sorted_dates):
            diff = (d - today).days
            # 날짜에 따라 포인트 컬러 변경
            if diff == 0:
                d_str = "Today!"
                d_color = "#FF4B4B" # 빨강
            elif diff == 1:
                d_str = "D-1"
                d_color = "#FF8C00" # 주황
            else:
                d_str = f"D-{diff}"
                d_color = "#0068C9" # 파랑
                
            date_str = d.strftime("%m.%d")
            
            # 카드 안에 들어갈 세부 일정들 (여러 개면 밑으로 추가됨)
            events_html = "".join([f"<div style='font-size:0.9rem; margin-bottom:6px; color:#333; line-height:1.3; word-break:keep-all;'>{ev}</div>" for ev in grouped_events[d]])
            
            # 예쁜 카드 모양 HTML
            card_html = f"""
            <div style="border: 1px solid #e6e6e6; border-radius: 10px; padding: 15px; background-color: #ffffff; text-align: center; height: 100%; box-shadow: 2px 2px 8px rgba(0,0,0,0.04);">
                <h3 style="margin: 0; color: {d_color}; font-size: 1.6rem; padding-bottom: 5px;">{d_str}</h3>
                <div style="color: #888888; font-size: 0.95rem; margin-bottom: 12px; font-weight: 500;">{date_str}</div>
                <hr style="margin: 0 0 12px 0; border: 0; border-top: 1px dashed #ddd;">
                <div style="text-align: left;">
                    {events_html}
                </div>
            </div>
            """
            with cols[i]:
                st.markdown(card_html, unsafe_allow_html=True)

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
                st.success(f"📌 **{name}**")
                found_on_date = True
        
        if not df_events.empty and "일자" in df_events.columns and "내용" in df_events.columns:
            for _, row in df_events.iterrows():
                try:
                    ev_date = pd.to_datetime(row['일자']).date()
                    if ev_date == sel_date:
                        v_type = str(row.get('연차구분', "")).strip()
                        v_str = f"[{v_type}] " if v_type else ""
                        
                        st.success(f"📂 **{v_str}{row['내용']}**")
                        
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
            all_combined_list.append({"날짜": d, "내용": n, "연차구분": "-"})
        
        if not df_events.empty and "일자" in df_events.columns and "내용" in df_events.columns:
            for _, row in df_events.iterrows():
                try:
                    v_type = str(row.get('연차구분', "")).strip()
                    all_combined_list.append({
                        "날짜": pd.to_datetime(row['일자']).date(),
                        "내용": row['내용'],
                        "연차구분": v_type if v_type else "-"
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
                
                st.dataframe(
                    display_df[['날짜', 'D-Day', '내용', '연차구분']], 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "연차구분": st.column_config.TextColumn("연차구분", width="small")
                    }
                )
            else:
                st.info("예정된 일정이 없습니다.")
        
elif menu == "👨‍👩‍👦‍👦 가족":
    st.title("사랑하는 우리 가족 ❤️")
    st.write("가족 구성원 정보를 확인하고 주요 일정을 공유하는 공간입니다.")
    
    if not df_events.empty:
        if "일자" in df_events.columns:
            st.subheader("📅 엑셀 연동 가족 일정")
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
            if "지역1" in df_fishing.columns and "지역2" in df_fishing.columns and "선사명" in df_fishing.columns:
                
                # ✨ [역방향 선택 마법!] 선사를 고르면 항구를 찾아냅니다.
                if "sel_reg1" not in st.session_state: st.session_state.sel_reg1 = "전체"
                if "sel_reg2" not in st.session_state: st.session_state.sel_reg2 = "전체"
                if "sel_ship" not in st.session_state: st.session_state.sel_ship = "전체"

                def auto_fill_port():
                    ship = st.session_state.sel_ship
                    if ship != "전체":
                        # 선택한 배의 항구를 구글 시트에서 찾아서 강제로 채워줍니다!
                        port = df_fishing[df_fishing["선사명"] == ship]["지역2"].values
                        if len(port) > 0:
                            st.session_state.sel_reg2 = str(port[0])

                col1, col2, col3, col4 = st.columns([1, 1.2, 1.2, 1.5])
                with col1:
                    t_date = st.date_input("출조 예정일", value=today, format="YYYY/MM/DD")
                
                with col2:
                    region1_list = ["전체"] + sorted([str(r) for r in df_fishing["지역1"].unique() if str(r).strip() != ""])
                    if st.session_state.sel_reg1 not in region1_list: st.session_state.sel_reg1 = "전체"
                    sel_region1 = st.selectbox("지역 (도/시) 📍", region1_list, key="sel_reg1")
                
                df_step1 = df_fishing.copy()
                if sel_region1 != "전체": 
                    df_step1 = df_step1[df_step1["지역1"] == sel_region1]
                    
                with col3:
                    region2_list = ["전체"] + sorted([str(r) for r in df_step1["지역2"].unique() if str(r).strip() != ""])
                    if st.session_state.sel_reg2 not in region2_list: st.session_state.sel_reg2 = "전체"
                    sel_region2 = st.selectbox("상세 항구 ⚓", region2_list, key="sel_reg2")
                
                df_step2 = df_step1.copy()
                if sel_region2 != "전체": 
                    df_step2 = df_step2[df_step2["지역2"] == sel_region2]
                    
                with col4:
                    # 💡 on_change 속성을 걸어서, 선사를 고르는 순간 auto_fill_port 함수가 작동합니다!
                    name_list = ["전체"] + sorted([str(n) for n in df_step2["선사명"].unique() if str(n).strip() != ""])
                    if st.session_state.sel_ship not in name_list: st.session_state.sel_ship = "전체"
                    sel_name = st.selectbox("선사 선택 🚢", name_list, key="sel_ship", on_change=auto_fill_port)

                st.divider()

                # ✨ [UI 개조 1] 선사를 선택했을 때 '스마트 칩 카드'를 물때표보다 위에 예쁘게 띄웁니다!
                if sel_name != "전체":
                    target_row = df_step2[df_step2["선사명"] == sel_name]
                    if not target_row.empty:
                        res_url = str(target_row["예약사이트"].values[0])
                        if res_url.startswith("http"):
                            clean_domain = res_url.replace("https://", "").replace("http://", "").split("/")[0]
                            
                            smart_chip_html = f"""
                            <div style="
                                display: flex; align-items: center; justify-content: space-between;
                                background-color: #f8f9fa; border: 1px solid #dadce0;
                                border-radius: 12px; padding: 12px 20px; margin-bottom: 20px;
                                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                            ">
                                <div style="display: flex; align-items: center;">
                                    <div style="background-color: #1a73e8; color: white; border-radius: 8px; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; margin-right: 15px;">
                                        🚢
                                    </div>
                                    <div>
                                        <div style="font-weight: bold; font-size: 1.1rem; color: #202124; margin-bottom: 2px;">{sel_name}</div>
                                        <div style="font-size: 0.85rem; color: #5f6368;">{clean_domain}</div>
                                    </div>
                                </div>
                                <a href="{res_url}" target="_blank" style="
                                    background-color: #ff4b4b; color: white; text-decoration: none;
                                    padding: 8px 20px; border-radius: 6px; font-weight: bold; font-size: 0.9rem;
                                    transition: all 0.2s; border: none; cursor: pointer;
                                ">
                                    예약 사이트 바로가기
                                </a>
                            </div>
                            """
                            st.markdown(smart_chip_html, unsafe_allow_html=True)
                            
                # 기존 실시간 관측소 로직 (스마트 칩 아래에 표시됨)
                if sel_region2 != "전체":
                    khoa_obs_map = {
                        "군산": "DT_0018", "비응": "DT_0018", "야미도": "DT_0018", "선유도": "DT_0018", "새만금": "DT_0018",
                        "보령": "DT_0025", "대천": "DT_0025", "무창포": "DT_0025", "오천": "DT_0025", "회변": "DT_0025",
                        "태안": "DT_0050", "안흥": "DT_0067", "신진도": "DT_0067", "백사장": "DT_0067", "안면도": "DT_0067", "영목": "DT_0067",
                        "서천": "DT_0051", "홍원": "DT_0051", "마량": "DT_0051", "장항": "DT_0024",
                        "당진": "DT_0017", "장고항": "DT_0017", "도비도": "DT_0017", "대산": "DT_0017",
                        "시흥": "DT_0008", "오이도": "DT_0008", "시화": "DT_0008", "안산": "DT_0008",
                        "인천": "DT_0001", "연안부두": "DT_0001", "영종도": "DT_0001", "남항": "DT_0001",
                        "고성": "DT_0012", "대진": "DT_0012", "공현진": "DT_0012", "속초": "DT_0012", "아야진": "DT_0012",
                    }
                    obs_code = next((v for k, v in khoa_obs_map.items() if k in sel_region2), "DT_0018")
                    
                    try:
                        if hasattr(st, "secrets") and "KHOA_API_KEY" in st.secrets:
                            api_key = st.secrets["KHOA_API_KEY"].strip()
                            req_date_str = t_date.strftime("%Y%m%d")
                            
                            url_1 = f"https://apis.data.go.kr/1192136/dtRecent/GetDTRecentApiService?serviceKey={api_key}&obsCode={obs_code}&reqDate={req_date_str}&pageNo=1&numOfRows=1&type=json"
                            res_1 = requests.get(url_1, timeout=10)
                            
                            if res_1.status_code == 200:
                                try:
                                    data1 = res_1.json()
                                    if "OpenAPI_ServiceResponse" in data1:
                                        st.error(f"🚨 공공데이터포털 접속 거절: {data1['OpenAPI_ServiceResponse'].get('cmmMsgHeader', {}).get('returnAuthMsg', '')}")
                                    else:
                                        response_node = data1.get("response", {})
                                        header1 = response_node.get("header", data1.get("header", {}))
                                        body1 = response_node.get("body", data1.get("body", {}))
                                        
                                        result_code = header1.get("resultCode")
                                        if result_code == "00" and body1.get("totalCount", 0) > 0:
                                            total_count = body1.get("totalCount")
                                            url_2 = f"https://apis.data.go.kr/1192136/dtRecent/GetDTRecentApiService?serviceKey={api_key}&obsCode={obs_code}&reqDate={req_date_str}&pageNo={total_count}&numOfRows=1&type=json"
                                            res_2 = requests.get(url_2, timeout=10)
                                            data2 = res_2.json()
                                            
                                            body2 = data2.get("response", {}).get("body", data2.get("body", {}))
                                            raw_items = body2.get("items", {})
                                            items = raw_items.get("item", []) if isinstance(raw_items, dict) else raw_items
                                            if not isinstance(items, list): items = [items]
                                                
                                            if items:
                                                curr_data = items[-1]
                                                # ✨ [UI 개조 2] 실시간 풍속, 수온 타이틀을 넣어 더 전문적으로 보이게!
                                                st.markdown("##### 📡 근해 실시간 관측 정보")
                                                w1, w2, w3 = st.columns(3)
                                                wind_val = curr_data.get('wspd', curr_data.get('wind_speed', '-'))
                                                w1.metric("💨 실시간 풍속", f"{wind_val} m/s")
                                                w2.metric("🌡️ 현재 수온", f"{curr_data.get('wtem', curr_data.get('water_temp', '-'))} ℃")
                                                w3.metric("📏 실시간 조위", f"{curr_data.get('bscTdlvHgt', curr_data.get('tide_level', '-'))} cm")
                                                
                                                st.caption(f"🕒 실시간 관측 시간: {curr_data.get('obsrvnDt', '알수없음')} (관측소: {curr_data.get('obsvtrNm', '알수없음')})")
                                            else: st.warning(f"⚠️ 공공데이터포털 서버 통신 오류")
                                        else:
                                            if t_date > today: st.info("🔮 미래 날짜는 아직 실시간 데이터가 없습니다.")
                                            else: st.warning(f"🚨 현재 해당 지역 근처 관측소 데이터 점검 중")
                                except ValueError: st.warning("🚨 공공데이터포털 서버 점검 중")
                            else: st.error(f"🚨 서버 통신 실패! {res_1.status_code}")
                    except Exception as e: st.error(f"🚨 통신 에러: {e}")

                    st.divider()
                    
                    # ✨ [스마트 대체 검색]
                    region_words = str(sel_region2).split()
                    target_port = region_words[-1] 
                    target_city = region_words[0]  
                    
                    clean_port = target_port.replace("항", "").replace("포구", "").replace("방파제", "") 
                    b_id = bada_id_map.get(target_port) or bada_id_map.get(clean_port)
                    if not b_id:
                        b_id = bada_id_map.get(target_city, "118") 
                    
                    badatime_url = f"https://www.badatime.com/{b_id}/tide"
                    badatime_mobile_url = f"https://m.badatime.com/{b_id}.html"
                    
                    # ✨ [UI 개조 3] 버튼이 카드 안으로 흡수됐으므로 모바일 물때표 버튼만 시원하게 꽉 채워줍니다!
                    st.link_button(f"📱 {target_port} 모바일 물때 달력 (새 창 열기)", badatime_mobile_url, use_container_width=True)

                    st.subheader("📊 통합 해양정보 대시보드 (바다타임 제공)")
                    st.caption(f"※ 완벽 매핑된 **[{target_port}]** (또는 인근 지역) 데이터입니다! 아래 화면에서 탭을 클릭해서 확인하세요!")
                    components.iframe(badatime_url, height=1000, scrolling=True)
                else:
                    st.info("💡 실시간 바다 날씨와 물때표를 보시려면 위에서 **상세 항구 ⚓**를 선택해주세요!")
            else:
                st.error("🚨 구글 시트에 '지역1', '지역2', '선사명' 컬럼이 모두 있어야 합니다! 헤더 이름을 확인해주세요.")
        else:
            st.warning("⚠️ 구글 시트 데이터를 불러오지 못했습니다.")

    with tab2:
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1: st.subheader("🚢 등록된 전체 선사 정보")
        with col_t2: st.write(""); st.link_button("📊 구글 시트 직접 편집", REAL_SHEET_URL, use_container_width=True)
        if not df_fishing.empty and "지역1" in df_fishing.columns:
            st.dataframe(df_fishing, use_container_width=True, hide_index=True)
        else:
            st.write("로컬 환경 제한으로 데이터가 표출되지 않습니다. (배포된 웹사이트에서 확인해주세요)")

    with tab3:
        st.subheader("📸 낚시의 추억")
        st.info("여기에 낚시 사진 갤러리 기능을 추가할 예정입니다!")