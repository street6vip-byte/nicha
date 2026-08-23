import os
import tweepy
from generate_content import (
    generate_tweet,
    generate_tweet_with_image,
    get_random_room_photo,
)
from telegram_trigger import get_new_telegram_photo
from schedule_manager import get_due_slot_index, mark_posted
from webhook_payload import load_webhook_update
import telegram_approval as approval

API_KEY = os.environ.get("X_API_KEY")
API_SECRET = os.environ.get("X_API_SECRET")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
ACCESS_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET") or os.environ.get("X_ACCESS_SECRET")


def _get_api_v1() -> tweepy.API:
    """이미지 업로드는 v1.1 API(OAuth1)로만 가능해서 별도 클라이언트가 필요합니다."""
    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
    return tweepy.API(auth)


def post_tweet(tweet_text: str, image_path: str | None = None) -> None:
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET,
    )

    media_ids = None
    if image_path:
        if os.path.exists(image_path):
            api_v1 = _get_api_v1()
            media = api_v1.media_upload(image_path)
            media_ids = [media.media_id]
            print(f"이미지 업로드 완료 (media_id={media.media_id}, path={image_path})")
        else:
            print(f"⚠️ 이미지 경로는 있지만 파일이 실제로 존재하지 않습니다: {image_path} -> 텍스트만 게시됩니다.")
    else:
        print("이미지 경로가 없어서(image_path=None) 텍스트만 게시합니다.")

    response = client.create_tweet(text=tweet_text, media_ids=media_ids)
    print(f"트윗 포스팅 성공! 응답: {response}")


def handle_pending(webhook_update: dict | None) -> bool:
    """대기 중인 승인 요청을 처리합니다. 처리(또는 대기 유지)했으면 True, 대기 요청이 아예 없었으면 False."""
    pending = approval.load_pending()
    if pending is None:
        return False

    status = approval.check_response(pending, webhook_update)
    image_path = pending.get("image_path")
    print(f"[디버그] pending image_path={image_path}, 실제 존재함={os.path.exists(image_path) if image_path else 'N/A'}")

    if status in ("approved", "timeout"):
        reason = (
            "사용자 승인"
            if status == "approved"
            else f"{pending.get('timeout_minutes')}분 무응답 타임아웃 자동 게시"
        )
        try:
            post_tweet(pending["text"], image_path)
            approval.notify_result(pending, reason=reason, success=True)
            if pending.get("source") == "auto_schedule" and pending.get("slot_index") is not None:
                mark_posted(pending["slot_index"])
            approval.clear_pending()
        except Exception as e:
            print(f"게시 실패: {e}")
            if "duplicate content" in str(e).lower():
                print("중복 문구 감지 -> 같은 이미지로 새 문구를 재생성해서 한 번 더 시도합니다.")
                try:
                    if image_path and os.path.exists(image_path):
                        retry_text = generate_tweet_with_image(image_path)
                    else:
                        retry_text = generate_tweet()
                    post_tweet(retry_text, image_path)
                    approval.notify_result(
                        pending,
                        reason=f"{reason} (중복 문구 감지 -> 새 문구로 재생성 후 게시 성공)",
                        success=True,
                    )
                    if pending.get("source") == "auto_schedule" and pending.get("slot_index") is not None:
                        mark_posted(pending["slot_index"])
                    approval.clear_pending()
                except Exception as e2:
                    print(f"재생성 후에도 게시 실패: {e2}")
                    approval.notify_result(
                        pending,
                        reason=f"{reason} (재생성까지 시도했지만 실패 -> 이 건은 건너뜁니다)",
                        success=False,
                        error=str(e2),
                    )
                    if pending.get("source") == "auto_schedule" and pending.get("slot_index") is not None:
                        mark_posted(pending["slot_index"])
                    approval.clear_pending()
            else:
                approval.notify_result(pending, reason=reason, success=False, error=str(e))
                # 그 외 오류는 pending 파일을 지우지 않고 남겨둬서 다음 실행에서 재시도합니다.
    elif status == "rejected":
        print("거부됨 -> 게시하지 않습니다.")
        approval.notify_result(pending, reason="사용자 거부", success=None)
        approval.clear_pending()
    else:
        print("아직 승인/거부 응답이 없습니다. 이번 실행에서는 대기합니다.")

    return True


def try_telegram_trigger(webhook_update: dict | None) -> bool:
    """① 웹훅으로 새 텔레그램 사진이 전달됐으면 그걸로 승인 요청을 보냅니다."""
    image_path = get_new_telegram_photo(webhook_update)
    if not image_path:
        return False

    tweet_text = generate_tweet_with_image(image_path)
    print(f"[텔레그램 트리거] 생성된 트윗 내용:\n{tweet_text}")
    approval.send_approval_request(tweet_text, image_path, source="telegram_trigger")
    return True


def try_scheduled_auto_post() -> bool:
    """② 오늘 스케줄 중 예정 시각이 지난 슬롯이 있으면 자동으로 트윗을 생성해 승인 요청을 보냅니다."""
    slot_index = get_due_slot_index()
    if slot_index is None:
        return False

    image_path = get_random_room_photo()
    if image_path:
        tweet_text = generate_tweet_with_image(image_path)
    else:
        tweet_text = generate_tweet()

    print(f"[자동 스케줄 #{slot_index}] 생성된 트윗 내용:\n{tweet_text}")
    approval.send_approval_request(
        tweet_text, image_path, source="auto_schedule", slot_index=slot_index
    )
    return True


def main() -> None:
    webhook_update = load_webhook_update()
    print(f"[디버그] webhook_update 존재함={webhook_update is not None}")

    try:
        if handle_pending(webhook_update):
            return
        if try_telegram_trigger(webhook_update):
            return
        if try_scheduled_auto_post():
            return
        print("이번 실행에서는 처리할 게 없습니다 (대기 요청 없음, 새 사진 없음, 예정 슬롯 없음).")
    except Exception as e:
        print(f"처리 중 에러 발생: {e}")
        raise e


if __name__ == "__main__":
    main()
