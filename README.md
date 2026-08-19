# X(트위터) 자동 포스팅 봇 (텍스트 전용)

태국 파타야에 거주하는 여성 페르소나로, 하루 4~5건의 트윗(텍스트만)을
불특정 시간에 자동 생성/게시하는 시스템입니다. 서버 없이 GitHub Actions로만
동작합니다.

> **중요 — 공개 표기 안내**
> 이 계정이 AI로 생성된 가상 캐릭터라면, X 프로필/소개글에 그 사실을
> 명시하는 것을 권장합니다 (예: "AI-generated persona / virtual character").

## 동작 방식

1. **매일 새벽** `schedule_daily.yml` 워크플로우가 실행되어 오늘 올릴
   랜덤 시각(4~5개, 08:00~23:00 방콕 시간 사이, 최소 90분 간격)을
   `schedule.json`에 저장합니다.
2. **15분마다** `check_and_post.yml` 워크플로우가 실행되어, 예정 시각이
   지났고 아직 안 올린 슬롯이 있으면:
   - 오늘의 주제를 하나 뽑고
   - Claude API로 그 주제에 맞는 트윗 텍스트를 생성하고
   - 텍스트만 X에 게시합니다.

이미지 생성/첨부 기능은 포함되어 있지 않습니다.

## 설정 방법

### 1) 이 폴더를 새 GitHub 레포에 올리기

```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

`.github/workflows/` 안의 두 yml 파일이 그 경로 그대로 올라가야
GitHub Actions가 인식합니다 (레포 루트에 두면 인식하지 못합니다).

### 2) X Developer 계정 준비

1. https://developer.x.com 에서 새 계정으로 Project + App 생성
2. App 권한을 **Read and Write**로 설정 (기본값은 Read only라 반드시 바꿔야 함)
3. Keys and tokens 탭에서 아래 4개 발급:
   - API Key / API Key Secret
   - Access Token / Access Token Secret
     (권한을 바꾼 뒤라면 재발급 필요)

### 3) Anthropic API 키 준비

https://console.anthropic.com 에서 API 키 발급.

### 4) GitHub Secrets 등록

레포 → Settings → Secrets and variables → Actions → New repository secret
으로 아래 5개를 등록하세요.

| Secret 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic 콘솔에서 발급받은 키 |
| `X_API_KEY` | X Developer Portal API Key |
| `X_API_SECRET` | X Developer Portal API Key Secret |
| `X_ACCESS_TOKEN` | X Developer Portal Access Token |
| `X_ACCESS_SECRET` | X Developer Portal Access Token Secret |

워크플로우 yml 파일의 `env` 블록에도 각 시크릿이 선언되어 있는지 함께
확인하세요 — 레포 Secrets에만 등록하고 `env` 블록에 빠지면 런타임에
인식되지 않습니다. (이 레포의 `check_and_post.yml`에는 이미 반영되어
있습니다.)

### 5) 동작 확인

Actions 탭에서 두 워크플로우를 각각 "Run workflow"로 수동 실행해보세요.

- `schedule_daily.yml` 실행 → `schedule.json` 파일이 새로 생성/커밋되는지 확인
  (새 계정이므로 이전 게시 이력이 없는 깨끗한 상태로 시작합니다)
- `check_and_post.yml` 실행 → (스케줄 시각이 지나 있다면) 실제로 텍스트가
  게시되는지 확인

이후로는 cron이 자동으로 돌아갑니다.

## 커스터마이징

- **페르소나/문체**: `generate_content.py` 의 `PERSONA_SYSTEM_PROMPT`
- **주제 로테이션**: `generate_content.py` 의 `TOPIC_SEEDS`
- **포스팅 시간대**: `schedule_manager.py` 의 `WINDOW_START_HOUR`,
  `WINDOW_END_HOUR`
- **하루 포스팅 개수**: `schedule_manager.py` 의 `MIN_POSTS_PER_DAY`,
  `MAX_POSTS_PER_DAY`
- **슬롯 간 최소 간격**: `schedule_manager.py` 의 `MIN_GAP_MINUTES`
- **타임존**: `POST_TIMEZONE` 환경변수 (기본 `Asia/Bangkok`)

## 로컬 테스트

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY=...
python generate_content.py   # 트윗 문구만 생성해서 출력 (게시 안 함)

export X_API_KEY=... X_API_SECRET=... X_ACCESS_TOKEN=... X_ACCESS_SECRET=...
python post_to_x.py          # 테스트 문구를 실제로 게시함 (주의)
```
