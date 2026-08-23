"""
'텔레그램 트리거' 전용 모듈: 웹훅으로 전달받은 사진 메시지를 처리합니다.

웹훅 방식으로 전환하면서 더 이상 getUpdates(폴링)를 쓰지 않습니다. 대신
check_and_post.yml이 repository_dispatch(웹훅)로 트리거될 때마다, 그 실행이
받은 telegram_update 하나를 그대로 넘겨받아서 "이게 내 사진 메시지인가?"만
판단합니다.

telegram_state.json에는 이미 처리한 file_id를 기록해서, 혹시 텔레그램이
같은 업데이트를 중복 전송하더라도(웹훅은 드물게 재전송될 수 있음) 같은
사진으로 중복 트리거되지 않도록 방지합니다.
"""

import json
import os

import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
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


def get_new_telegram_photo(webhook_update: dict | None) -> str | None:
    """웹훅으로 전달받은 update가 나의 채팅에서 온 사진 메시지면 다운로드해서
    로컬 경로를 반환합니다. 아니면(사진 아님/다른 채팅/이미 처리함/웹훅 데이터 없음) None."""
    if not webhook_update or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return None

    msg = webhook_update.get("message") or webhook_update.get("channel_post") or {}

    # 지정된 나의 채팅(TELEGRAM_CHAT_ID)에서 온 메시지만 인식 (다른 그룹/채팅 유입 방지)
    if str(msg.get("chat", {}).get("id")) != str(TELEGRAM_CHAT_ID):
        return None

    if "photo" not in msg:
        return None

    file_id = msg["photo"][-1]["file_id"]

    state = _load_state()
    if file_id in state["processed_file_ids"]:
        return None  # 이미 처리한 사진(웹훅 중복 전송 등)

    try:
        file_info = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}",
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

    state["processed_file_ids"].append(file_id)
    _save_state(state)
    print(f"[텔레그램 트리거] 새 사진 감지 및 다운로드 완료: {save_path}")
    return save_path
