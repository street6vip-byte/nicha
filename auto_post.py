"""
자동 스케줄 게시 전용 진입점 (승인 절차 없음).
auto_schedule_post.yml 워크플로우에서 실행됩니다.

이 스크립트는 텔레그램 트리거/승인 흐름(telegram_handler.py)과 완전히
분리되어 있고, schedule.json 상태만 다룹니다. pending_post.json은 건드리지
않습니다.
"""

from generate_content import (
    generate_tweet,
    generate_tweet_with_image,
    get_random_room_photo,
    generate_room_variant,
)
from schedule_manager import get_due_slot_index, mark_posted
from x_poster import post_tweet
import telegram_approval as approval


def try_scheduled_auto_post() -> bool:
    """오늘 스케줄 중 예정 시각이 지난 슬롯이 있으면, 승인 절차 없이 즉시 게시합니다."""
    slot_index = get_due_slot_index()
    if slot_index is None:
        print("[자동 스케줄] 지금 처리할 예정 슬롯이 없습니다.")
        return False

    reference_photo = get_random_room_photo()
    image_path = None
    if reference_photo:
        image_path = generate_room_variant(reference_photo)
        if not image_path:
            print("[자동 스케줄] 방 사진 변형 생성 실패 -> 원본 방 사진을 그대로 사용합니다.")
            image_path = reference_photo

    if image_path:
        tweet_text = generate_tweet_with_image(image_path)
    else:
        tweet_text = generate_tweet()

    print(f"[자동 스케줄 #{slot_index}] 생성된 트윗 내용:\n{tweet_text}")

    try:
        post_tweet(tweet_text, image_path)
        mark_posted(slot_index)
        approval.notify_direct_post(tweet_text, success=True)
    except Exception as e:
        print(f"[자동 스케줄] 게시 실패: {e}")
        if "duplicate content" in str(e).lower():
            # 재시도해도 계속 실패하는 종류라서, 이 슬롯은 포기하고 넘어갑니다.
            mark_posted(slot_index)
        approval.notify_direct_post(tweet_text, success=False, error=str(e))

    return True


def main() -> None:
    try:
        try_scheduled_auto_post()
    except Exception as e:
        print(f"처리 중 에러 발생: {e}")
        raise e


if __name__ == "__main__":
    main()
