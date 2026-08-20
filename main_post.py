import os
import sys
from generate_content import (
    generate_tweet,
    generate_tweet_with_image,
    get_latest_telegram_image,
)
from post_to_x import post_tweet


def main():
    print("텔레그램 이미지 확인 중...")
    image_path = get_latest_telegram_image()

    if image_path and os.path.exists(image_path):
        print(f"텔레그램 이미지 감지됨: {image_path}")
        print("Gemini 태국어 트윗 생성 중...")
        tweet_text = generate_tweet_with_image(image_path)
        print(f"생성된 트윗: {tweet_text}")

        print("X(트위터) 업로드 시작...")
        tweet_id = post_tweet(tweet_text, image_path)
        print(f"🎉 게시 완료! Tweet ID: {tweet_id}")

        # 임시 이미지 파일 삭제
        os.remove(image_path)
    else:
        print("텔레그램에서 전송된 이미지가 없습니다.")
        print("텍스트 전용 트윗 생성 중...")
        tweet_text = generate_tweet()
        print(f"생성된 트윗: {tweet_text}")

        print("X(트위터) 업로드 시작...")
        tweet_id = post_tweet(tweet_text)
        print(f"🎉 게시 완료! Tweet ID: {tweet_id}")


if __name__ == "__main__":
    main()
