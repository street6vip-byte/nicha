import os
import tweepy
from generate_content import (
    get_latest_telegram_image,
    generate_tweet,
    generate_tweet_with_image,
)

# 트위터(X) API 인증 정보
API_KEY = os.environ.get("X_API_KEY")
API_SECRET = os.environ.get("X_API_SECRET")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN")
ACCESS_SECRET = os.environ.get("X_ACCESS_SECRET")


def post_to_x():
    # 1. 텔레그램 또는 깃허브 방 사진 가져오기 시도
    image_path = get_latest_telegram_image()

    # 2. 글 내용 생성
    if image_path:
        print(f"이미지({image_path})를 기반으로 트윗을 작성합니다.")
        tweet_text = generate_tweet_with_image(image_path)
    else:
        print("이미지가 없어 텍스트 전용 트윗을 작성합니다.")
        tweet_text = generate_tweet()

    print(f"생성된 트윗 내용:\n{tweet_text}")

    # 3. 트위터(X) API v1 및 v2 클라이언트 설정 (오타 수정: access_secret -> access_token_secret)
    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
    api_v1 = tweepy.API(auth)

    client_v2 = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET,  # <-- 이 부분이 수정되었습니다!
    )

    # 4. 트위터에 업로드 실행
    try:
        if image_path and os.path.exists(image_path):
            # 사진이 있는 경우 사진 업로드 후 트윗 작성
            media = api_v1.media_upload(image_path)
            client_v2.create_tweet(
                text=tweet_text, media_ids=[media.media_id_string]
            )
            print("사진 + 트윗 포스팅 성공!")
        else:
            # 텍스트만 있는 경우
            client_v2.create_tweet(text=tweet_text)
            print("텍스트 전용 트윗 포스팅 성공!")

    except Exception as e:
        print(f"트위터 포스팅 중 에러 발생: {e}")
        raise e


if __name__ == "__main__":
    post_to_x()
