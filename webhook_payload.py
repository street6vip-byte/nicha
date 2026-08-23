"""
GitHub Actions 워크플로우가 repository_dispatch(웹훅)로 트리거됐을 때,
Cloudflare Worker가 넘겨준 텔레그램 update 원본 JSON을 읽어옵니다.

check_and_post.yml에서 repository_dispatch 이벤트일 때만
client_payload를 telegram_update.json 파일로 저장해두고,
main_post.py가 이 모듈을 통해 그 내용을 읽습니다.

schedule/workflow_dispatch로 트리거된 실행(백업용 cron, 수동 실행)에는
이 파일이 없으므로 load_webhook_update()는 None을 반환합니다 -> 그 경우
기존처럼 승인 대기 타임아웃 체크와 자동 스케줄 게시만 동작합니다.
"""

import json
import os

WEBHOOK_UPDATE_FILE = "telegram_update.json"


def load_webhook_update() -> dict | None:
    if not os.path.exists(WEBHOOK_UPDATE_FILE):
        return None
    try:
        with open(WEBHOOK_UPDATE_FILE) as f:
            data = json.load(f)
        return data if data else None
    except Exception as e:
        print(f"[웹훅] telegram_update.json 파싱 실패: {e}")
        return None
