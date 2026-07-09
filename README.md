# US Macro Dashboard

미국 거시경제 (국채 금리, 실질 GDP, 인플레이션, 연준 유동성) 데이터를 FRED API에서 가져와
NBER 경기침체 음영 overlay와 함께 시각화하는 단일 HTML 대시보드.

## 데이터 소스

- **FRED — Federal Reserve Economic Data, St. Louis Fed** (단일 통합 게이트웨이)
- 기초 1차 출처:
  - 국채 금리 → U.S. Treasury (DGS, T10Y2Y, T10Y3M)
  - GDP → Bureau of Economic Analysis (BEA): GDPC1, A191RL1Q225SBEA
  - 물가 → Bureau of Labor Statistics (BLS) for CPI / BEA for PCE
  - 연준 유동성 → Federal Reserve Board (WALCL, WRESBAL, RRPONTSYD, WTREGEN, M2SL, FEDFUNDS)
  - 경기침체 음영 → NBER (USREC indicator)

## 첫 사용 가이드

### 1. FRED API 키 발급 (1회, 무료, 1분)

1. <https://fredaccount.stlouisfed.org/apikey> 접속
2. St. Louis Fed 계정으로 로그인 (구글 OAuth 가능)
3. "Request API Key" 버튼 → 용도("Personal use") 입력 → 발급
4. 32자리 API 키 복사

공식 안내: <https://fred.stlouisfed.org/docs/api/api_key.html>

### 2. 데이터 가져오기

터미널을 열고 이 폴더로 이동한 다음:

```bash
# 방법 A — 환경변수 (권장, 키가 명령 이력에 남지 않음)
export FRED_API_KEY=발급받은_32자리_키
python3 update.py

# 방법 B — 인자로 직접 전달
python3 update.py 발급받은_32자리_키
```

`dashboard.html` 파일이 같은 폴더에 생성됩니다.

### 3. 대시보드 열기

`dashboard.html`을 더블클릭 → 기본 브라우저에서 열립니다.
오프라인에서도 동작합니다 (모든 데이터가 HTML에 임베드되어 있음).

## 정기 업데이트

주간 / 월간으로 데이터를 새로 받고 싶을 때마다 `python3 update.py` 한 줄만 다시 실행하면
`dashboard.html`이 최신 데이터로 덮어써집니다.

## 대시보드 구성

### 상단 스냅샷 (8개 카드)
- 10Y Treasury · 10Y-2Y Spread (bps) · Fed Funds Rate
- Headline CPI YoY · Core PCE YoY (Fed의 선호 지표)
- Real GDP YoY · M2 YoY · Fed Balance Sheet ($T)

각 카드 적용 가능 시 30일/1년 전 대비 변화 표시.

### 기간 selector
1Y / 3Y / 5Y / 10Y / 20Y / MAX. 모든 시계열 차트에 일괄 적용 (yield curve 제외).

### 탭 4개

**Treasuries**
- Yield Curve (오늘 vs 3개월 전 vs 12개월 전) — 만기별 비교
- 2Y / 5Y / 10Y / 30Y 시계열
- 10Y-2Y / 10Y-3M 스프레드 (역전 여부)

**GDP**
- 실질 GDP 레벨
- QoQ 연율 성장 (양/음 색상 막대)
- YoY 성장 (GDPC1에서 계산)

**Inflation**
- CPI YoY (Headline vs Core) — Fed 2% target 점선
- PCE YoY (Headline vs Core) — Fed 2% target 점선
- 10Y Breakeven (시장 내재 기대 인플레이션)

**Fed Liquidity**
- Fed 총자산 ($T)
- Reserves / RRP / TGA ($T)
- M2 YoY
- Fed Funds Effective Rate

### NBER 경기침체 overlay
모든 시계열 차트에 NBER 공식 경기침체 구간이 옅은 빨강 음영으로 자동 표시됩니다.

## 파일 구성

```
거시경제 분석 툴/
├── update.py                 # FRED fetcher (stdlib only, 외부 패키지 불필요)
├── dashboard_template.html   # UI 템플릿 (수정 시 update.py 재실행)
├── dashboard.html            # ★ update.py 실행 후 생성 — 이걸 열면 됨
└── README.md                 # 이 파일
```

## 기술 노트

- **Python 의존성 없음**: stdlib (`urllib`)만 사용. Python 3.8+면 동작.
- **JavaScript**: Chart.js 4 + Luxon time adapter (CDN). 인터넷 없이도 한번 로드된 캐시로 동작 가능.
- **CORS 제약**: FRED API는 브라우저 직접 fetch를 차단하므로 Python으로 데이터를 미리 가져와 HTML에 임베드하는 구조.
- **단위 변환**: WALCL / WRESBAL / WTREGEN은 Millions of USD, RRPONTSYD는 Billions of USD → 모두 Trillions로 환산.
- **YoY 계산**: 월별 시리즈는 t/(t-12)-1, 분기 시리즈는 t/(t-4)-1.

## 시리즈 카탈로그

| 카테고리 | FRED ID | 설명 | 단위 | 주기 |
|---|---|---|---|---|
| Treasury | DGS1MO~DGS30 | Constant-maturity yields | % | Daily |
| Treasury | T10Y2Y, T10Y3M | Yield curve spreads | % | Daily |
| GDP | GDPC1 | Real GDP (chained 2017$) | Bn$ | Quarterly |
| GDP | A191RL1Q225SBEA | Real GDP QoQ annualized growth | % | Quarterly |
| Inflation | CPIAUCSL | Headline CPI | Index | Monthly |
| Inflation | CPILFESL | Core CPI (ex food/energy) | Index | Monthly |
| Inflation | PCEPI | PCE Price Index | Index | Monthly |
| Inflation | PCEPILFE | Core PCE | Index | Monthly |
| Inflation | T10YIE | 10Y Breakeven Inflation | % | Daily |
| Liquidity | WALCL | Fed Total Assets | Mn$ | Weekly (Wed) |
| Liquidity | WRESBAL | Reserve Balances | Mn$ | Weekly |
| Liquidity | RRPONTSYD | Overnight RRP | Bn$ | Daily |
| Liquidity | WTREGEN | Treasury General Account | Mn$ | Weekly |
| Liquidity | M2SL | M2 Money Supply | Bn$ | Monthly |
| Liquidity | FEDFUNDS | Fed Funds Effective Rate | % | Monthly |
| Recession | USREC | NBER Recession Indicator | 0/1 | Monthly |

새 지표를 추가하려면 `update.py`의 `SERIES` dict와 `dashboard_template.html`의 차트 정의에 함께 추가하면 됩니다.
