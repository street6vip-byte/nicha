"""
'텔레그램 트리거' 전용 모듈: 아직 게시에 쓰지 않은 새 사진이 있는지 감지합니다.

generate_content.get_latest_telegram_image()는 매번 '가장 최근 사진'을 그대로
다시 돌려주기 때문에(sticky), 같은 사진으로 계속 트리거가 걸리는 문제가 있었습니다.
이 모듈은 telegram_state.json에 이미 처리한 file_id 목록을 기록해두고,
정말 '새로' 온 사진일 때만 감지되도록 합니다.

telegram_state.json은 다른 상태 파일과 마찬가지로 워크플로우 실행 후 git commit 되어야
다음 실행에서도 이어집니다 (check_and_post.yml 참고).
"""

import json
import os

import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
STATE_FILE = "telegram_state.json"
MAX_HISTORY = 50  # 파일이 무한정 커지지 않도록 최근 N개 file_id만 보관


def _load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {"processed_file_ids": []}
    with open(STATE_FILE) as f:
        return json.load(f)


def _save_state(state: dict) -> None:
    state["processed_file_ids"] = state["processed_file_ids"][-MAX_HISTORY:]
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_new_telegram_photo() -> str | None:
    """아직 처리한 적 없는 새 텔레그램 사진이 있으면 다운로드해서 로컬 경로를 반환하고,
    처리 완료로 기록합니다. 새 사진이 없으면 None을 반환합니다."""
    if not TELEGRAM_BOT_TOKEN:
        return None

    state = _load_state()
    processed = set(state["processed_file_ids"])

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?limit=100"
        res = requests.get(url, timeout=10).json()
    except Exception as e:
        print(f"[텔레그램 트리거] 업데이트 확인 중 오류: {e}")
        return None

    if not res.get("ok"):
        return None

    new_file_id = None
    for update in res["result"]:
        msg = update.get("message") or update.get("channel_post") or {}
        if "photo" in msg:
            file_id = msg["photo"][-1]["file_id"]
            if file_id not in processed:
                new_file_id = file_id  # 여러 개면 가장 마지막(최신) 것으로 계속 갱신

    if not new_file_id:
        return None

    try:
        file_info = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={new_file_id}",
            timeout=10,
        ).json()
        file_path = file_info["result"]["file_path"]
        img_data = requests.get(
            f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}",
            timeout=10,
        ).content

        save_path = "telegram_image.jpg"
        with open(save_path, "wb") as f:
            f.write(img_data)
    except Exception as e:
        print(f"[텔레그램 트리거] 사진 다운로드 실패: {e}")
        return None

    state["processed_file_ids"].append(new_file_id)
    _save_state(state)
    print(f"[텔레그램 트리거] 새 사진 감지 및 다운로드 완료: {save_path}")
    return save_path
