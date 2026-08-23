"""
텔레그램 트리거 흐름(telegram_handler.py)과 자동 스케줄 흐름(auto_post.py)이
공통으로 쓰는 X(트위터) 게시 로직.
"""

import os

import tweepy

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
