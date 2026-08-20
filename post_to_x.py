"""
생성된 트윗 텍스트와 이미지(선택)를 X(트위터)에 실제로 게시하는 모듈.

환경 변수 (X Developer Portal > Project > App > Keys and tokens 에서 발급):
  X_API_KEY
  X_API_SECRET
  X_ACCESS_TOKEN
  X_ACCESS_SECRET

주의: 앱 권한이 "Read and Write"로 설정되어 있어야 합니다.
권한을 바꾼 뒤에는 Access Token/Secret을 재발급받아야 반영됩니다.
"""

import os
import tweepy


def post_tweet(text: str, image_path: str | None = None) -> str:
    """
    텍스트와 (선택적) 이미지를 받아 X(트위터)에 게시하고 tweet_id를 반환합니다.
    """
    # 1. API v1.1 클라이언트 (이미지/미디어 업로드용)
    auth = tweepy.OAuth1UserHandler(
        os.environ["X_API_KEY"],
        os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"],
        os.environ["X_ACCESS_SECRET"],
    )
    api_v1 = tweepy.API(auth)

    # 2. API v2 클라이언트 (트윗 게시용)
    client_v2 = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )

    media_ids = []

    # 이미지가 존재하면 X 서버에 먼저 업로드 후 media_id 획득
    if image_path and os.path.exists(image_path):
        print(f"이미지 업로드 중: {image_path}")
        media = api_v1.media_upload(filename=image_path)
        media_ids.append(media.media_id)

    # 트윗 발행 (이미지가 있으면 media_ids 전달, 없으면 None)
    response = client_v2.create_tweet(
        text=text,
        media_ids=media_ids if media_ids else None
    )

    tweet_id = response.data["id"]
    return tweet_id


if __name__ == "__main__":
    # 로컬 테스트용
    test_text = "Testing image post from Nicha bot! 555 #test"
    # test_image = "images_queue/sample.jpg"  # 테스트할 이미지 경로
    
    # tid = post_tweet(test_text, image_path=test_image)
    # print(f"Posted! https://x.com/i/web/status/{tid}")
