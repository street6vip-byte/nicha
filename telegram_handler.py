"""
텔레그램 트리거 + 승인 흐름 전용 진입점.
telegram_webhook.yml 워크플로우에서 실행됩니다.

이 스크립트는 자동 스케줄 게시(auto_post.py)와 완전히 분리되어 있고,
pending_post.json / pending/ / telegram_state.json 상태만 다룹니다.
"""

from generate_content import generate_tweet_with_image
from telegram_trigger import get_new_telegram_photo
from webhook_payload import load_webhook_update
from x_poster import post_tweet
import telegram_approval as approval


def handle_pending(webhook_update: dict | None) -> bool:
    """대기 중인 승인 요청을 처리합니다. 처리(또는 대기 유지)했으면 True, 대기 요청이 아예 없었으면 False."""
    pending = approval.load_pending()
    if pending is None:
        return False

    status = approval.check_response(pending, webhook_update)
    image_path = pending.get("image_path")

    if status in ("approved", "timeout"):
        reason = (
            "사용자 승인"
            if status == "approved"
            else f"{pending.get('timeout_minutes')}분 무응답 타임아웃 자동 게시"
        )
        try:
            post_tweet(pending["text"], image_path)
            approval.notify_result(pending, reason=reason, success=True)
            approval.clear_pending()
        except Exception as e:
            print(f"게시 실패: {e}")
            if "duplicate content" in str(e).lower():
                approval.notify_result(
                    pending,
                    reason=f"{reason} (중복 문구로 X가 거부함 -> 이 건은 건너뜁니다)",
                    success=False,
                    error=str(e),
                )
                approval.clear_pending()
            else:
                approval.notify_result(pending, reason=reason, success=False, error=str(e))
                # pending 파일을 지우지 않고 남겨둬서 다음 실행에서 재시도합니다.
    elif status == "rejected":
        print("거부됨 -> 게시하지 않습니다.")
        approval.notify_result(pending, reason="사용자 거부", success=None)
        approval.clear_pending()
    else:
        print("아직 승인/거부 응답이 없습니다. 이번 실행에서는 대기합니다.")

    return True


def try_telegram_trigger(webhook_update: dict | None) -> bool:
    """웹훅으로 새 텔레그램 사진이 전달됐으면 그걸로 승인 요청을 보냅니다."""
    image_path = get_new_telegram_photo(webhook_update)
    if not image_path:
        return False

    tweet_text = generate_tweet_with_image(image_path)
    print(f"[텔레그램 트리거] 생성된 트윗 내용:\n{tweet_text}")
    approval.send_approval_request(tweet_text, image_path, source="telegram_trigger")
    return True


def main() -> None:
    webhook_update = load_webhook_update()
    print(f"[디버그] webhook_update 존재함={webhook_update is not None}")

    try:
        if handle_pending(webhook_update):
            return
        if try_telegram_trigger(webhook_update):
            return
        print("[텔레그램 핸들러] 이번 실행에서는 처리할 게 없습니다.")
    except Exception as e:
        print(f"처리 중 에러 발생: {e}")
        raise e


if __name__ == "__main__":
    main()
