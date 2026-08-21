"""
게시 전 텔레그램으로 승인/거부를 받는 모듈.

흐름:
  1. send_approval_request(): 트윗 초안(텍스트+이미지)을 텔레그램으로 보내고,
     '승인'/'거부' 인라인 버튼을 붙입니다. 상태는 pending_post.json에 저장.
  2. check_response(): 다음 실행 때 호출되어, 사용자가 버튼을 눌렀는지 확인합니다.
     - 승인 버튼 클릭 -> "approved"
     - 거부 버튼 클릭 -> "rejected"
     - timeout_minutes 안에 응답이 없으면 -> "timeout" (호출부에서 자동 게시 처리)
     - 그 외 -> "waiting" (다음 실행에서 다시 확인)

pending_post.json 과 pending/ 이미지 파일은 GitHub Actions 실행이 끝날 때
워크플로우에서 git commit 해줘야 다음 실행에서도 이어집니다 (check_and_post.yml 참고).
"""

import json
import os
import time
import uuid

import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

PENDING_FILE = "pending_post.json"
PENDING_IMAGE_DIR = "pending"

# 승인/거부 응답이 이 시간(분) 안에 안 오면 자동으로 '승인'으로 간주하고 게시합니다.
TIMEOUT_MINUTES = 60


def _api(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"


def send_approval_request(tweet_text: str, image_path: str | None) -> dict:
    """승인/거부 버튼이 달린 미리보기 메시지를 텔레그램으로 전송하고 상태를 저장합니다."""
    if not TELEGRAM_CHAT_ID:
        raise Exception("TELEGRAM_CHAT_ID 환경변수가 설정되어 있지 않습니다.")

    callback_id = uuid.uuid4().hex[:8]
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ 승인 (게시)", "callback_data": f"approve:{callback_id}"},
            {"text": "❌ 거부 (취소)", "callback_data": f"reject:{callback_id}"},
        ]]
    }
    caption = (
        f"게시 예정 트윗이에요, 확인해주세요! (미응답 시 {TIMEOUT_MINUTES}분 후 자동 게시)\n\n"
        f"{tweet_text}"
    )

    saved_image_path = None

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            resp = requests.post(
                _api("sendPhoto"),
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption,
                    "reply_markup": json.dumps(keyboard),
                },
                files={"photo": f},
                timeout=20,
            ).json()

        # 다음 워크플로우 실행에서도 같은 이미지를 쓸 수 있도록 레포 안에 보관
        os.makedirs(PENDING_IMAGE_DIR, exist_ok=True)
        saved_image_path = os.path.join(PENDING_IMAGE_DIR, os.path.basename(image_path))
        with open(image_path, "rb") as src, open(saved_image_path, "wb") as dst:
            dst.write(src.read())
    else:
        resp = requests.post(
            _api("sendMessage"),
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": caption,
                "reply_markup": json.dumps(keyboard),
            },
            timeout=20,
        ).json()

    if not resp.get("ok"):
        raise Exception(f"텔레그램 승인 요청 전송 실패: {resp}")

    pending = {
        "callback_id": callback_id,
        "message_id": resp["result"]["message_id"],
        "chat_id": TELEGRAM_CHAT_ID,
        "text": tweet_text,
        "image_path": saved_image_path,
        "requested_at": time.time(),
        "timeout_minutes": TIMEOUT_MINUTES,
    }
    _save_pending(pending)
    print(f"텔레그램으로 승인 요청 전송 완료 (callback_id={callback_id})")
    return pending


def _save_pending(pending: dict) -> None:
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f, indent=2, ensure_ascii=False)


def load_pending() -> dict | None:
    if not os.path.exists(PENDING_FILE):
        return None
    with open(PENDING_FILE) as f:
        return json.load(f)


def clear_pending() -> None:
    pending = load_pending()
    if pending and pending.get("image_path") and os.path.exists(pending["image_path"]):
        os.remove(pending["image_path"])
    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)


def check_response(pending: dict) -> str:
    """
    텔레그램에서 승인/거부 버튼 응답이 왔는지 확인합니다.
    반환값: "approved" | "rejected" | "timeout" | "waiting"
    """
    callback_id = pending["callback_id"]
    message_id = pending["message_id"]

    try:
        updates = requests.get(_api("getUpdates"), params={"limit": 100}, timeout=15).json()
    except Exception as e:
        print(f"텔레그램 응답 확인 중 오류(다음 실행에서 재시도): {e}")
        updates = {"ok": False}

    if updates.get("ok"):
        for update in updates["result"]:
            cq = update.get("callback_query")
            if not cq:
                continue
            if cq.get("message", {}).get("message_id") != message_id:
                continue

            data = cq.get("data", "")
            if data == f"approve:{callback_id}":
                _answer_callback(cq["id"], "승인되었습니다. 게시를 진행합니다.")
                return "approved"
            if data == f"reject:{callback_id}":
                _answer_callback(cq["id"], "거부되었습니다. 게시하지 않습니다.")
                return "rejected"

    elapsed_minutes = (time.time() - pending["requested_at"]) / 60
    if elapsed_minutes >= pending.get("timeout_minutes", TIMEOUT_MINUTES):
        return "timeout"

    return "waiting"


def _answer_callback(callback_query_id: str, text: str) -> None:
    try:
        requests.post(
            _api("answerCallbackQuery"),
            data={"callback_query_id": callback_query_id, "text": text},
            timeout=10,
        )
    except Exception:
        pass
