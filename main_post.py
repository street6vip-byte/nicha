import os
import glob
import random
from generate_content import generate_tweet_with_image
from post_to_x import post_tweet
from schedule_manager import get_due_slot_index, mark_posted

QUEUE_DIR = "images_queue"
POSTED_DIR = "images_posted"

if __name__ == "__main__":
    slot_index = get_due_slot_index()

    if slot_index is None:
        print("지금 올릴 예정된 슬롯 없음. 종료.")
    else:
        images = glob.glob(f"{QUEUE_DIR}/*.*")
        valid_images = [img for img in images if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]

        if valid_images:
            image_path = random.choice(valid_images)
            tweet_text = generate_tweet_with_image(image_path)
            tweet_id = post_tweet(tweet_text, image_path)
            mark_posted(slot_index)

            # 올린 사진은 posted 폴더로 이동
            filename = os.path.basename(image_path)
            os.rename(image_path, os.path.join(POSTED_DIR, filename))

            print(f"게시 완료 (slot {slot_index}): {tweet_text}")
        else:
            print("큐에 올려둔 사진이 없습니다.")
