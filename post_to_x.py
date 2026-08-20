import os
import tweepy

def get_twitter_conn_v1() -> tweepy.API:
    """v1.1 API (이미지 업로드용)"""
    auth = tweepy.OAuth1UserHandler(
        os.environ.get("X_API_KEY"),
        os.environ.get("X_API_SECRET"),
        os.environ.get("X_ACCESS_TOKEN"),
        os.environ.get("X_ACCESS_TOKEN_SECRET") or os.environ.get("X_ACCESS_SECRET")
    )
    return tweepy.API(auth)

def get_twitter_conn_v2() -> tweepy.Client:
    """v2 API (트윗 작성용)"""
    return tweepy.Client(
        consumer_key=os.environ.get("X_API_KEY"),
        consumer_secret=os.environ.get("X_API_SECRET"),
        access_token=os.environ.get("X_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("X_ACCESS_TOKEN_SECRET") or os.environ.get("X_ACCESS_SECRET")
    )

def post_tweet(text: str, image_path: str = None) -> str:
    """트윗 게시 (텍스트 또는 이미지 포함)"""
    client_v2 = get_twitter_conn_v2()
    
    if image_path and os.path.exists(image_path):
        api_v1 = get_twitter_conn_v1()
        media = api_v1.media_upload(image_path)
        response = client_v2.create_tweet(text=text, media_ids=[media.media_id])
    else:
        response = client_v2.create_tweet(text=text)
        
    return response.data["id"]
