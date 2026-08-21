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


def post_tweet(tweet_text: str) -> None:
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET,
    )
    response = client.create_tweet(text=tweet_text)
    print(f"트윗 포스팅 성공! 응답: {response}")


def handle_pending() -> bool:
    """대기 중인 승인 요청을 처리합니다. 처리(또는 대기 유지)했으면 True, 대기 요청이 아예 없었으면 False."""
    pending = approval.load_pending()
    if pending is None:
        return False

    status = approval.check_response(pending)

    if status == "approved":
        print("승인됨 -> 게시를 진행합니다.")
        post_tweet(pending["text"])
        approval.clear_pending()
    elif status == "rejected":
        print("거부됨 -> 게시하지 않습니다.")
        approval.clear_pending()
    elif status == "timeout":
        print(f"{pending.get('timeout_minutes')}분 동안 응답 없음 -> 자동 게시로 진행합니다.")
        post_tweet(pending["text"])
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
