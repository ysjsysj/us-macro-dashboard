# 배포 가이드 — GitHub Pages (Private repo) 자동 갱신

이 문서 그대로 따라가면 데스크탑 상태와 무관하게 매일 07:00 UTC (16:00 KST)에
자동으로 최신 FRED 데이터로 대시보드가 갱신되고, `https://<계정>.github.io/<리포지토리>/`
링크로 어디서든 접속 가능해집니다.

---

## 사전 조건 — GitHub Student Pack (Private repo에 Pages 쓰려면 필요)

Private 리포지토리에서 GitHub Pages를 사용하려면 Pro 계정이 필요하고,
Yonsei 학생은 무료로 발급 가능합니다.

1. <https://education.github.com/pack> 접속 → "Get student benefits"
2. 학교 이메일: `ysj010429@o365.yonsei.ac.kr` 입력
3. 학교 소속 증빙 (학생증 사진, 등록금 영수증 등) 업로드
4. 승인까지 보통 몇 시간 ~ 며칠. 승인되면 GitHub Pro 자동 부여.

*이미 Pro거나 Public 리포로 진행할 계획이라면 이 단계는 건너뛰세요.*

---

## 1. 새 리포지토리 만들기

1. GitHub 로그인 → 우상단 `+` → **New repository**
2. Repository name: 예) `us-macro-dashboard`
3. Visibility: **Private**
4. `Add a README file` **체크 해제** (이미 로컬에 있음)
5. `Create repository`

---

## 2. 로컬 폴더를 리포지토리에 push

터미널을 열고 이 폴더에서:

```bash
cd "/Users/yuseungjun/Documents/Claude/Projects/거시경제 분석 툴"

# git 초기화 (한 번만)
git init
git branch -M main

# 원격 등록 (URL은 방금 만든 리포에서 복사, 예시:)
git remote add origin https://github.com/<계정명>/us-macro-dashboard.git

# 첫 커밋
git add .
git commit -m "Initial commit: US macro dashboard"
git push -u origin main
```

`update.py`, `dashboard_template.html`, `dashboard.html`, `README.md`,
`.github/workflows/update.yml`, `.gitignore` 모두 push 됩니다.

---

## 3. FRED API 키를 GitHub Secret으로 등록

**절대 코드에 API 키를 커밋하지 마세요.** 대신:

1. 리포지토리 페이지 → **Settings** 탭
2. 좌측 사이드바 → **Secrets and variables** → **Actions**
3. `New repository secret` 버튼
4. Name: `FRED_API_KEY`
5. Secret: `13f284de9241e089dbb39585f27ac223`
6. `Add secret`

이 값은 워크플로 실행 시에만 환경변수로 주입되며, 로그에도 마스킹됩니다.

---

## 4. GitHub Pages 활성화

1. 리포지토리 → **Settings** → **Pages**
2. **Source**: `GitHub Actions` 선택 (Deploy from branch 아님)
3. 저장할 필요 없이 자동 설정됨

---

## 5. 첫 워크플로 실행 (수동 트리거)

1. 리포지토리 → **Actions** 탭
2. 좌측에서 `Update US Macro Dashboard` 워크플로 선택
3. 우측 `Run workflow` → `Run workflow` 클릭
4. 초록 체크 뜰 때까지 대기 (약 1~2분)

성공하면:
- `dashboard.html`이 최신 FRED 데이터로 자동 커밋됨
- Pages에 배포되어 URL 준비됨

**Pages URL 확인:** Settings → Pages 페이지 상단에
`Your site is live at https://<계정명>.github.io/<리포지토리명>/` 표시됨.
이 URL을 브라우저 즐겨찾기 / 아이폰 홈화면 추가하면 어디서든 클릭 한 번으로 접속.

---

## 6. 이후는 완전 자동

- 매일 07:00 UTC (한국 오후 4시)에 GitHub 서버에서 자동 실행
- 새 데이터가 있으면 자동 커밋 + Pages 재배포
- 변경 이력은 리포 커밋 로그에 남아 언제든 되돌리기 가능
- 수동 갱신: Actions 탭에서 `Run workflow` 언제든 클릭

## 트러블슈팅

**Actions 실행이 실패해요**
→ Actions 탭에서 실패한 run 클릭 → 에러 로그 확인.
`FRED_API_KEY secret is not set` 메시지면 3단계 다시 확인.

**Pages 사이트가 404**
→ Actions run이 초록색인지 먼저 확인.
Settings → Pages에서 Source가 "GitHub Actions"인지 재확인.
첫 배포는 몇 분 지연될 수 있음.

**주기를 바꾸고 싶어요**
→ `.github/workflows/update.yml`의 `cron: "0 7 * * *"` 부분 수정.
[crontab.guru](https://crontab.guru)에서 표현식 만들 수 있음.
매주 월요일 → `0 7 * * 1`, 매주 월/목 → `0 7 * * 1,4`.
GitHub Actions cron은 항상 **UTC 기준**.

**리포지토리를 나중에 Public으로 바꿔도 되나?**
→ 가능. Public이면 무료 계정에서도 Pages 무제한. FRED 데이터는 공개 자료라
공개해도 컴플라이언스 문제 없음. 다만 리포 안에는 워크플로 파일이 남으니,
Secret 이름만 그대로 두고 값은 유지되어 있으면 계속 잘 돌아감.
