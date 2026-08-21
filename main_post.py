import os
import tweepy
from generate_content import (
    get_latest_telegram_image,
    generate_tweet,
    generate_tweet_with_image,
)

API_KEY = os.environ.get("X_API_KEY")
API_SECRET = os.environ.get("X_API_SECRET")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
ACCESS_SECRET = os.environ.get("X_ACCESS_SECRET")


def post_to_x():
    # 1. 사진 가져오기 시도 (글 작성 참고용)
    image_path = get_latest_telegram_image()

    # 2. 글 내용 생성
    if image_path and os.path.exists(image_path):
        print(f"이미지({image_path})를 참고하여 트윗을 작성합니다.")
        tweet_text = generate_tweet_with_image(image_path)
    else:
        print("텍스트 전용 트윗을 작성합니다.")
        tweet_text = generate_tweet()

    print(f"생성된 트윗 내용:\n{tweet_text}")

    # 3. OAuth 1.0a 방식으로 인증 (v1 API 사용)
    try:
        auth = tweepy.OAuth1UserHandler(
            API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET
        )
        api = tweepy.API(auth)

        # 4. 텍스트 트윗 전송 (v1.1 update_status 사용)
        response = api.update_status(status=tweet_text)
        print(f"트윗 포스팅 성공! 응답 ID: {response.id}")

    except Exception as e:
        print(f"트위터 포스팅 중 에러 발생: {e}")
        raise e


if __name__ == "__main__":
    post_to_x()
