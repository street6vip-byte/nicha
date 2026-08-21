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
ACCESS_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET") or os.environ.get("X_ACCESS_SECRET")


def _debug_creds():
    """실제 값은 절대 출력하지 않고, 존재 여부/길이/앞뒤 공백 여부만 로그로 확인."""
    creds = {
        "X_API_KEY": API_KEY,
        "X_API_SECRET": API_SECRET,
        "X_ACCESS_TOKEN": ACCESS_TOKEN,
        "X_ACCESS_TOKEN_SECRET(or X_ACCESS_SECRET)": ACCESS_SECRET,
    }
    print("=== 자격증명 디버그 (값은 출력 안 함) ===")
    for name, value in creds.items():
        if value is None:
            print(f"{name}: 없음(None) <- 시크릿이 아예 안 들어옴")
            continue
        has_leading_or_trailing_space = value != value.strip()
        print(
            f"{name}: 존재함, 길이={len(value)}, "
            f"앞뒤공백포함={has_leading_or_trailing_space}"
        )
    print("=======================================")


_debug_creds()


def post_to_x():
    # 1. 사진 가져오기
    image_path = get_latest_telegram_image()

    # 2. 트윗 내용 생성 (이미지 참고)
    if image_path and os.path.exists(image_path):
        print(f"이미지({image_path})를 참고하여 트윗을 작성합니다.")
        tweet_text = generate_tweet_with_image(image_path)
    else:
        print("텍스트 전용 트윗을 작성합니다.")
        tweet_text = generate_tweet()

    print(f"생성된 트윗 내용:\n{tweet_text}")

    # 3. Tweepy v2 클라이언트를 통한 트윗 전송
    try:
        client = tweepy.Client(
            consumer_key=API_KEY,
            consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_SECRET,
        )

        response = client.create_tweet(text=tweet_text)
        print(f"트윗 포스팅 성공! 응답: {response}")

    except Exception as e:
        print(f"트위터 포스팅 중 에러 발생: {e}")
        raise e


if __name__ == "__main__":
    post_to_x()
