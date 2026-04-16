# 🏠 재형의 대시보드

개인 생활관리 Streamlit 앱 (홈 / 일정 / 가족 / 자산 / 낚시)

## 📁 프로젝트 구조

```
hobby_app/
├── 🚀 main.py                  # 진입점 (실행 시작점)
├── 📄 requirements.txt         # 의존성 패키지
├── 📄 README.md                # 이 파일
│
├── 📁 app_pages/               # 메뉴별 페이지 (※ pages 아님!)
│   ├── __init__.py
│   ├── home.py                 # 🏠 홈 (D-Day, 검색, 바로가기)
│   ├── calendar.py             # 🗓️ 일정 관리
│   ├── family.py               # 👨‍👩‍👦‍👦 가족
│   ├── asset.py                # 📈 자산관리
│   └── fishing.py              # 🎣 낚시 (가장 큰 모듈)
│
├── 📁 utils/                   # 공통 유틸리티
│   ├── __init__.py
│   ├── constants.py            # URL, 상수, 가족정보
│   ├── data_loader.py          # 구글시트 로딩
│   └── date_utils.py           # 날짜/음력 계산
│
└── 📁 assets/                  # 정적 파일
    └── bada_mapping.txt        # (선택) 바다타임 매핑 데이터
```

## ⚠️ 왜 `app_pages` 인가?

Streamlit이 **`pages/` 폴더를 자동으로 멀티페이지 메뉴로 인식**하는 기능이 있어요.
그래서 사이드바 상단에 `home`, `asset`, `calendar`... 같은 메뉴가 자동으로 생겨버립니다.

이를 방지하기 위해 폴더명을 `app_pages` 로 변경했습니다! 🎯

## 🚀 실행 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 실행
streamlit run main.py
```

## ✏️ 수정 가이드

| 바꾸고 싶은 것 | 어떤 파일 열면 돼요? |
|----------------|----------------------|
| 구글시트 URL | `utils/constants.py` |
| 가족 생일 | `utils/constants.py` |
| 홈 화면 디자인 | `app_pages/home.py` |
| 일정 기능 | `app_pages/calendar.py` |
| 낚시 기능 | `app_pages/fishing.py` |
| 메뉴 추가 | `main.py` + `app_pages/새파일.py` |

## 🎯 새 기능 추가 방법 (예: 로또)

1. `app_pages/lotto.py` 새로 만들고 `render()` 함수 작성
2. `main.py` 상단에 `from app_pages import lotto` 추가
3. `main.py` 메뉴 리스트에 `"🎰 로또"` 추가
4. 라우팅에 `elif menu == "🎰 로또": lotto.render()` 추가

끝! 🎉

## 🔐 Streamlit Secrets 설정

`.streamlit/secrets.toml` 파일에 KHOA API 키 등록:
```toml
KHOA_API_KEY = "YOUR_API_KEY_HERE"
```
