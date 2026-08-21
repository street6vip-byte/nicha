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

    # 3. 트위터 v2 클라이언트 생성 (인증 정보를 명확하게 모두 전달)
    try:
        client = tweepy.Client(
            consumer_key=API_KEY,
            consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_SECRET,
        )

        # 4. 트윗 전송
        response = client.create_tweet(text=tweet_text)
        print(f"트윗 포스팅 성공! 응답: {response}")

    except Exception as e:
        print(f"트위터 포스팅 중 에러 발생: {e}")
        raise e


if __name__ == "__main__":
    post_to_x()
