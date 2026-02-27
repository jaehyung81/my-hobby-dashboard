import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar

# 1. 페이지 설정
st.set_page_config(page_title="재형의 대시보드", page_icon="🏠", layout="wide")

# 2. 사이드바 메뉴 및 가족 트리
st.sidebar.title("재형의 개인비서 🤖")

menu = st.sidebar.radio(
    "메뉴를 선택하세요:",
    ["🏠 홈", "🗓️ 일정", "👨‍👩‍👦‍👦 가족", "📈 자산 관리(주식)", "🎣 낚시"]
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
    try:
        target = date(today.year, m, d)
    except ValueError: 
        target = date(today.year, m + 1, 1) 
    if target < today:
        target = date(today.year + 1, m, d)
    return target

def get_next_lunar_date(m, d):
    calendar = KoreanLunarCalendar()
    calendar.setLunarDate(today.year, m, d, False)
    target = date(calendar.solarYear, calendar.solarMonth, calendar.solarDay)
    if target < today:
        calendar.setLunarDate(today.year + 1, m, d, False)
        target = date(calendar.solarYear, calendar.solarMonth, calendar.solarDay)
    return target

# 💡 절대 경로 설정 (구글 드라이브 에러 방지용!)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_EVENTS_FILE = os.path.join(BASE_DIR, "custom_events.json")
MEMOS_FILE = os.path.join(BASE_DIR, "memos.json")

# --- 💾 내가 직접 등록한 일정 저장/불러오기 ---
def load_custom_events():
    if os.path.exists(CUSTOM_EVENTS_FILE):
        with open(CUSTOM_EVENTS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return {k: datetime.strptime(v, "%Y-%m-%d").date() for k, v in data.items()}
            except:
                return {}
    return {}

def save_custom_events(events_dict):
    data_to_save = {k: v.strftime("%Y-%m-%d") for k, v in events_dict.items()}
    with open(CUSTOM_EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

# 📋 기본 일정 데이터 세팅 (매년/매주 반복되는 고정 일정만!)
days_until_thursday = (3 - today.weekday()) % 7
next_lotto_date = today + timedelta(days=days_until_thursday)

all_events = {
    "💰 로또 사는 날": next_lotto_date, 
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

# 직접 등록한 일정을 기본 일정에 합치기
custom_events = load_custom_events()
all_events.update(custom_events)

# 날짜순 정렬
sorted_events = dict(sorted(all_events.items(), key=lambda item: item[1]))

# --- 💾 날짜별 메모 저장/불러오기 ---
def load_memos():
    if os.path.exists(MEMOS_FILE):
        with open(MEMOS_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_memos(memos):
    with open(MEMOS_FILE, "w", encoding="utf-8") as f:
        json.dump(memos, f, ensure_ascii=False, indent=4)

# 3. 메뉴별 화면 구성
if menu == "🏠 홈":
    st.title("환영합니다! 재형님 👋")

    st.subheader("🗓️ 주요 일정 (D-Day)")
    upcoming_events = {name: date_obj for name, date_obj in sorted_events.items() if date_obj >= today}
    top_6_events = list(upcoming_events.items())[:6]
    
    cols = st.columns(len(top_6_events)) if top_6_events else []
    for i, (name, target_date) in enumerate(top_6_events):
        d_day_num = (target_date - today).days
        with cols[i]:
            if d_day_num == 0:
                st.metric(label=name, value="Today", delta="오늘!", delta_color="inverse")
            elif d_day_num == 1:
                st.metric(label=name, value="D-1", delta="내일!")
            else:
                st.metric(label=name, value=f"D-{d_day_num}", delta=target_date.strftime("%m.%d"))

    st.divider()
    
    st.subheader("🔎 빠른 검색")
    c1, c2, c3, c4 = st.columns([0.5, 6, 1.5, 1.5])
    with c1: st.image("https://www.google.com/favicon.ico", width=28)
    with c2: google_q = st.text_input("Google", label_visibility="collapsed", placeholder="Google 검색어 입력", key="g_input")
    with c3:
        if google_q: st.link_button("🔍 Go", f"https://www.google.com/search?q={google_q}", use_container_width=True)
        else: st.link_button("🔍 Go", "https://www.google.com/", use_container_width=True)
    with c4: st.link_button("📧 Gmail", "https://mail.google.com/", use_container_width=True)

    n1, n2, n3, n4 = st.columns([0.5, 6, 1.5, 1.5])
    with n1: st.image("https://www.naver.com/favicon.ico", width=28)
    with n2: naver_q = st.text_input("Naver", label_visibility="collapsed", placeholder="Naver 검색어 입력", key="n_input")
    with n3:
        if naver_q: st.link_button("🔍 Go", f"https://search.naver.com/search.naver?query={naver_q}", use_container_width=True)
        else: st.link_button("🔍 Go", "https://www.naver.com/", use_container_width=True)
    with n4: st.link_button("📧 N메일", "https://mail.naver.com/", use_container_width=True)

    st.divider()

    st.subheader("💬 자주 찾는 Gemini 채팅방")
    chat_rooms = {
        "이동할 채팅방을 선택하세요": "",
        "🚀 재형 홈페이지 만들기 시작": "https://gemini.google.com/app/b2e4c40598df523a", 
        "⭐ 일상": "https://gemini.google.com/app/842a9777e87fb44b",
        "💰 로또 당첨": "https://gemini.google.com/app/b44cd477209867d1",
        "🎣 선상낚시 선사정보": "https://gemini.google.com/app/e084cd21c6fa3d64",
        "👻 Gemini 기능": "https://gemini.google.com/app/93ff95315133628b"
    }
    selected_chat = st.selectbox("채팅방 목록", list(chat_rooms.keys()))
    if selected_chat != "이동할 채팅방을 선택하세요":
        st.link_button(f"👉 {selected_chat} 바로가기", chat_rooms[selected_chat])

    st.divider()
    
    st.subheader("🚀 바로가기")
    l1, l2, l3 = st.columns(3)
    with l1: st.link_button("🎣 로구만 카페", "https://cafe.naver.com/blackoxxxq", use_container_width=True)
    with l2: st.link_button("✨ Gemini 메인", "https://gemini.google.com/", use_container_width=True)
    with l3: st.link_button("📂 구글 드라이브", "https://drive.google.com/", use_container_width=True)

elif menu == "🗓️ 일정":
    st.title("일정 상세 관리 🗓️")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("📅 달력 확인")
        sel_date = st.date_input("날짜를 선택하세요", value=today, format="YYYY/MM/DD")
        
        st.divider() 

        # 💡 기존 일정 등록 UI
        with st.expander("➕ 나만의 새 일정 등록하기", expanded=False):
            with st.form("add_event_form", clear_on_submit=True):
                new_event_name = st.text_input("일정 이름 (예: 가족 캠핑 🏕️)")
                new_event_date = st.date_input("날짜 선택", value=today, format="YYYY/MM/DD")
                submit_btn = st.form_submit_button("일정 추가", use_container_width=True)
                
                if submit_btn:
                    if new_event_name:
                        custom_events[new_event_name] = new_event_date
                        save_custom_events(custom_events)
                        st.success(f"'{new_event_name}' 일정이 성공적으로 등록되었습니다!")
                        st.rerun() # 화면 새로고침해서 즉시 반영
                    else:
                        st.warning("일정 이름을 입력해주세요!")

        # 💡 새로 추가된 일정 수정/삭제 UI (여기가 추가되었습니다!)
        with st.expander("✏️ 등록한 일정 수정/삭제", expanded=False):
            if custom_events:
                event_to_edit = st.selectbox("수정하거나 삭제할 일정을 선택하세요", list(custom_events.keys()))
                
                edit_name = st.text_input("새로운 일정 이름", value=event_to_edit)
                edit_date = st.date_input("새로운 날짜", value=custom_events[event_to_edit], format="YYYY/MM/DD")
                
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("💾 수정", use_container_width=True):
                        # 이름이 바뀌었으면 기존 키를 지우고 새 이름으로 저장
                        if edit_name != event_to_edit:
                            del custom_events[event_to_edit]
                        custom_events[edit_name] = edit_date
                        save_custom_events(custom_events)
                        st.success("일정이 성공적으로 수정되었습니다!")
                        st.rerun()
                with btn_col2:
                    if st.button("🗑️ 삭제", type="primary", use_container_width=True): # type="primary"를 넣으면 버튼이 빨간색/강조색으로 바뀝니다!
                        del custom_events[event_to_edit]
                        save_custom_events(custom_events)
                        st.success("일정이 삭제되었습니다!")
                        st.rerun()
            else:
                st.info("직접 등록하신 일정이 아직 없습니다.")

        st.divider()

        st.subheader("🔢 날짜 계산기")
        calc_mode = st.radio("계산 선택", ["날짜 더하기 (+일)", "D-Day 계산"], horizontal=True)
        if calc_mode == "날짜 더하기 (+일)":
            plus_days = st.number_input("몇 일 뒤를 계산할까요?", min_value=1, value=100)
            result_date = today + timedelta(days=plus_days)
            st.success(f"{plus_days}일 뒤: **{result_date.strftime('%Y-%m-%d')}**")
        else:
            target_d = st.date_input("기준 날짜 선택", value=date(2026, 12, 25), format="YYYY/MM/DD")
            diff = (target_d - today).days
            if diff > 0: st.info(f"**{diff}일** 남았습니다.")
            elif diff == 0: st.success("오늘입니다! 🎉")
            else: st.warning(f"**{abs(diff)}일** 지났습니다.")

        st.divider()

        st.subheader(f"📝 {sel_date.strftime('%m/%d')} 메모")
        memos = load_memos()
        date_key = sel_date.strftime("%Y-%m-%d")
        
        current_memo_text = memos.get(date_key, "")
        new_memo_text = st.text_area(
            "일정이나 할 일을 적어두세요 (자동 저장)",
            value=current_memo_text,
            height=150,
            key=f"memo_{date_key}"
        )
        
        if new_memo_text != current_memo_text:
            memos[date_key] = new_memo_text
            save_memos(memos)

    with c2:
        st.subheader(f"📢 {sel_date.strftime('%m월 %d일')} 일정")
        found_on_date = False
        
        for name, date_obj in sorted_events.items():
            if date_obj == sel_date:
                st.success(f"📌 **{name}**") 
                found_on_date = True
        
        if not found_on_date:
            st.info("선택하신 날짜에는 등록된 주요 일정이 없습니다.")

        if date_key in memos and memos[date_key].strip():
            st.warning(f"📝 **작성된 메모:**\n{memos[date_key]}")

        st.write("---")
        st.caption("🔜 이어서 다가오는 일정:")
        
        cnt = 0
        for name, date_obj in sorted_events.items():
            if date_obj > sel_date:
                d_day_val = (date_obj - today).days
                d_str = f"D-{d_day_val}" if d_day_val > 0 else "Today"
                st.write(f"- **{name}** ({date_obj.strftime('%m/%d')}, {d_str})")
                cnt += 1
                if cnt >= 2: break

        st.divider()

        st.subheader("📋 전체 일정 리스트")
        schedule_data = []
        weekday_map = ["(월)", "(화)", "(수)", "(목)", "(금)", "(토)", "(일)"]
        
        for name, date_obj in sorted_events.items():
            list_date = date_obj
            if date_obj.year == today.year + 1 and date_obj.month >= 3:
                list_date = date(today.year, date_obj.month, date_obj.day)
                
            if list_date.year == today.year or (list_date.year == today.year + 1 and list_date.month <= 2):
                d_day = (list_date - today).days
                d_day_str = "D-Day" if d_day == 0 else (f"D-{d_day}" if d_day > 0 else f"D+{abs(d_day)}")
                formatted_date = f"{list_date.strftime('%Y-%m-%d')} {weekday_map[list_date.weekday()]}"
                schedule_data.append({ "날짜": formatted_date, "D-Day": d_day_str, "일정명": name, "Highlight": list_date == sel_date })
        
        schedule_data = sorted(schedule_data, key=lambda x: x["날짜"])
        df = pd.DataFrame(schedule_data)
        
        def highlight_selected_row(row):
            return ['background-color: #ffffcc; color: black; font-weight: bold'] * len(row) if row['Highlight'] else [''] * len(row)

        st.dataframe(
            df.style.apply(highlight_selected_row, axis=1),
            column_order=("날짜", "D-Day", "일정명"),
            use_container_width=True,
            hide_index=True
        )

elif menu == "👨‍👩‍👦‍👦 가족":
    st.title("사랑하는 우리 가족 ❤️")
    st.write("가족 구성원 정보를 확인하는 공간입니다.")
    st.image("https://cdn-icons-png.flaticon.com/512/3093/3093835.png", width=200)

elif menu == "📈 자산 관리(주식)":
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

elif menu == "🎣 낚시":
    st.markdown("<h1 style='text-align: center;'>도시어부 라이프 🎣</h1>", unsafe_allow_html=True)
    
    # 1. 데이터 로드 (구글 시트 연동)
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS5oMJ3Lo3azFRkQnIrJAtBGOrX2S8WUIlSCI2Qf4ylmDsAddx9aRDP6hgzqyDCfQ/pub?output=csv"
    if 'df_fishing' not in st.session_state:
        try:
            st.session_state.df_fishing = pd.read_csv(csv_url).fillna("")
        except:
            st.session_state.df_fishing = pd.DataFrame()
    df_fishing = st.session_state.df_fishing

    tab1, tab2, tab3 = st.tabs(["📅 출조 포털 & 물때", "🚢 선사정보", "📸 낚시사진"])
    
    with tab1:
        st.subheader("📅 원클릭 출조 & 실시간 물때")
        if not df_fishing.empty:
            c1, c2, c3 = st.columns(3)
            with c1: target_date = st.date_input("출조 희망 일자 🗓️", value=today, format="YYYY/MM/DD", key="d1")
            with c2:
                t2_regions = ["선택하세요"] + sorted([str(x) for x in df_fishing["지역"].unique() if str(x).strip() != ""])
                selected_region = st.selectbox("출조 지역 📍", t2_regions, key="r1")
            with c3:
                if selected_region != "선택하세요":
                    r_filtered = df_fishing[df_fishing["지역"] == selected_region]
                    t2_names = ["선택하세요"] + sorted([str(x) for x in r_filtered["선사명"].unique()])
                else: t2_names = ["지역을 먼저 선택하세요"]
                selected_name = st.selectbox("선사명 🚢", t2_names, key="n1")

            st.divider()

            if selected_region != "선택하세요":
                # --- 🚩 공통 정보 설정 ---
                obs_map = {"군산": "DT_0026", "비응항": "DT_0026", "보령": "DT_0031", "대천": "DT_0031", "안흥": "DT_0035"}
                obs_code = "DT_0026"
                for k, v in obs_map.items():
                    if k in selected_region: obs_code = v; break

                # 🔐 보안 설정된 API 키 가져오기
                API_KEY = st.secrets["KHOA_API_KEY"] #
                import requests

                # --- 💨 1. 실시간 해상 관측 정보 (풍속, 수온 등) ---
                obs_url = f"https://www.khoa.go.kr/oceangrid/grid/api/tideObs/search.do?ServiceKey={API_KEY}&ObsCode={obs_code}&ResultType=json"
                try:
                    obs_res = requests.get(obs_url, timeout=5).json()
                    if "result" in obs_res and "data" in obs_res["result"]:
                        curr = obs_res["result"]["data"][0]
                        st.markdown(f"#### 🚩 {selected_region} 실시간 해상 현황")
                        w1, w2, w3 = st.columns(3)
                        w1.metric("💨 풍속", f"{curr.get('wind_speed', '-')} m/s") #
                        w2.metric("🌡️ 수온", f"{curr.get('water_temp', '-')} ℃") #
                        w3.metric("📏 조위", f"{curr.get('tide_level', '-')} cm") #
                        st.caption(f"🕒 관측시각: {curr.get('record_time', '-')}")
                except:
                    st.info("실시간 해상 관측 정보를 불러오는 중입니다...")

                # --- 🚢 2. 예약 버튼 영역 ---
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    st.link_button(f"🌊 {selected_region} 상세 물때 (바다타임)", f"https://www.badatime.com/search.jsp?q={selected_region}", use_container_width=True)
                with btn_col2:
                    if selected_name not in ["선택하세요", "지역을 먼저 선택하세요"]:
                        boat_row = df_fishing[(df_fishing["지역"]==selected_region) & (df_fishing["선사명"]==selected_name)]
                        if not boat_row.empty:
                            res_url = boat_row["예약사이트"].values[0]
                            if res_url and str(res_url).startswith("http"):
                                st.link_button(f"🚢 {selected_name} 예약하기", str(res_url), use_container_width=True, type="primary")
                
                # --- 📊 3. 물때 예보 정보 ---
                t_date_str = target_date.strftime("%Y%m%d")
                tide_url = f"https://www.khoa.go.kr/oceangrid/grid/api/tideObsPre/search.do?ServiceKey={API_KEY}&ObsCode={obs_code}&Date={t_date_str}&ResultType=json"
                try:
                    t_res = requests.get(tide_url, timeout=5).json()
                    if "result" in t_res and "data" in t_res["result"]:
                        t_df = pd.DataFrame(t_res["result"]["data"]).rename(columns={'tph_time':'시각', 'tph_level':'조위(cm)', 'hl_code':'구분'})
                        t_df['구분'] = t_df['구분'].replace({'H':'▲ 만조', 'L':'▼ 간조'})
                        st.write(f"📊 **{target_date.strftime('%m/%d')} 상세 물때표**")
                        st.table(t_df[['시각', '구분', '조위(cm)']])
                except:
                    st.warning("물때 예보 데이터를 불러올 수 없습니다. (키 활성화 대기 중)")
            else:
                st.info("💡 위에서 **출조 지역**을 선택해 주세요.")

    # --- [탭 2] 선사 정보 ---
    with tab2:
        st.subheader("🚢 자주 찾는 선사 정보")
        if not df_fishing.empty:
            st.dataframe(df_fishing, use_container_width=True, hide_index=True)

    # --- [탭 3] 📸 낚시 사진 ---
    with tab3:
        st.subheader("📸 낚시의 추억")
        st.write("멋진 조과 사진을 기다립니다!")