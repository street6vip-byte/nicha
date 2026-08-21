import os
import tweepy
from generate_content import (
    get_latest_telegram_image,
    generate_tweet,
    generate_tweet_with_image,
)
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
    if image_path and os.path.exists(image_path):
        api_v1 = _get_api_v1()
        media = api_v1.media_upload(image_path)
        media_ids = [media.media_id]
        print(f"이미지 업로드 완료 (media_id={media.media_id})")

    response = client.create_tweet(text=tweet_text, media_ids=media_ids)
    print(f"트윗 포스팅 성공! 응답: {response}")


def handle_pending() -> bool:
    """대기 중인 승인 요청을 처리합니다. 처리(또는 대기 유지)했으면 True, 대기 요청이 아예 없었으면 False."""
    pending = approval.load_pending()
    if pending is None:
        return False

    status = approval.check_response(pending)
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
            approval.notify_result(pending, reason=reason, success=False, error=str(e))
            # pending 파일을 지우지 않고 남겨둬서 다음 실행에서 재시도합니다.
    elif status == "rejected":
        print("거부됨 -> 게시하지 않습니다.")
        approval.notify_result(pending, reason="사용자 거부", success=None)
        approval.clear_pending()
    else:
        print("아직 승인/거부 응답이 없습니다. 이번 실행에서는 대기합니다.")

    return True


def request_new_post() -> None:
    image_path = get_latest_telegram_image()

    if image_path and os.path.exists(image_path):
        print(f"이미지({image_path})를 참고하여 트윗을 작성합니다.")
        tweet_text = generate_tweet_with_image(image_path)
    else:
        print("텍스트 전용 트윗을 작성합니다.")
        tweet_text = generate_tweet()

    print(f"생성된 트윗 내용:\n{tweet_text}")
    approval.send_approval_request(tweet_text, image_path)


def main() -> None:
    try:
        already_handled_or_waiting = handle_pending()
        if not already_handled_or_waiting:
            request_new_post()
    except Exception as e:
        print(f"처리 중 에러 발생: {e}")
        raise e


if __name__ == "__main__":
    main()
