"""GitHub Actions에서 주기적으로(예: 15분마다) 실행되는 진입점.

오늘 예정된 포스팅 시각이 지났고 아직 안 올린 슬롯이 있으면
트윗 텍스트를 생성해서 게시하고, 스케줄 파일에 posted=true로 표시합니다.

(텍스트 전용 파이프라인입니다. 이미지 첨부 기능은 사용하지 않습니다.)
"""

from generate_content import generate_tweet, pick_topic
from post_to_x import post_tweet
from schedule_manager import get_due_slot_index, mark_posted

if __name__ == "__main__":
    slot_index = get_due_slot_index()

    if slot_index is None:
        print("지금 올릴 예정된 슬롯 없음. 종료.")
    else:
        topic_text = pick_topic()
        tweet_text = generate_tweet(topic_text)

        tweet_id = post_tweet(tweet_text)
        mark_posted(slot_index)

        print(f"게시 완료 (slot {slot_index}): {tweet_text}")
        print(f"https://x.com/i/web/status/{tweet_id}")
