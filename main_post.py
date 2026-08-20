import os
from generate_content import (
    generate_tweet,
    generate_tweet_with_image,
    get_latest_telegram_image,
)
from post_to_x import post_tweet


def main():
    print("텔레그램 이미지 확인 중...")
    # 텔레그램에서 전송된 최신 이미지 다운로드
    image_path = get_latest_telegram_image()

    if image_path and os.path.exists(image_path):
        print(f"텔레그램 이미지 감지됨: {image_path}")
        # Gemini로 이미지 분석 및 트윗 생성
        tweet_text = generate_tweet_with_image(image_path)
        print(f"생성된 트윗: {tweet_text}")

        # X(트위터)에 이미지와 함께 업로드
        tweet_id = post_tweet(tweet_text, image_path)
        print(f"트윗 게시 성공! Tweet ID: {tweet_id}")

        # 사용한 임시 이미지 삭제
        os.remove(image_path)
    else:
        print("텔레그램 이미지가 없습니다. 텍스트 전용 트윗을 생성합니다...")
        tweet_text = generate_tweet()
        print(f"생성된 트윗: {tweet_text}")

        # X(트위터)에 텍스트만 업로드
        tweet_id = post_tweet(tweet_text)
        print(f"트윗 게시 성공! Tweet ID: {tweet_id}")


if __name__ == "__main__":
    main()
