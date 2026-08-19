"""
'불특정 시간에 하루 4~5건' 스케줄링을 담당하는 모듈.

방식:
  1) 매일 새벽 한 번 main_schedule.py 가 실행되어, 오늘 올릴 랜덤 시각
     (4~5개)을 정해서 schedule.json 에 저장합니다.
  2) 이후 main_post.py 가 짧은 주기(예: 15분)로 계속 실행되며,
     "지금 이 시각이 오늘 예정된 포스팅 시각을 지났고 아직 안 올렸는가?"를
     확인해서, 맞으면 트윗을 생성/게시하고 posted=true 로 표시합니다.

schedule.json 은 매 실행 후 깃 저장소에 커밋되어 상태가 유지됩니다.
"""

import json
import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

SCHEDULE_FILE = "schedule.json"

# 페르소나가 태국에 살고 있으니 방콕 시간 기준. 필요하면 바꾸세요.
TIMEZONE = ZoneInfo(os.environ.get("POST_TIMEZONE", "Asia/Bangkok"))

# 하루 중 포스팅이 가능한 시간대 (활동 시간대에 자연스럽게 올라오도록)
WINDOW_START_HOUR = 8
WINDOW_END_HOUR = 23

MIN_POSTS_PER_DAY = 4
MAX_POSTS_PER_DAY = 5
MIN_GAP_MINUTES = 90  # 슬롯끼리 너무 붙어서 올라오지 않도록 최소 간격


def _now() -> datetime:
    return datetime.now(TIMEZONE)


def _random_times_for_today(n: int) -> list[str]:
    """오늘 날짜의 랜덤 HH:MM 문자열 n개를 최소 간격을 지켜서 생성."""
    start_minutes = WINDOW_START_HOUR * 60
    end_minutes = WINDOW_END_HOUR * 60

    for _ in range(200):  # 간격 조건을 만족할 때까지 재시도
        candidates = sorted(
            random.randint(start_minutes, end_minutes) for _ in range(n)
        )
        if n == 1 or all(
            b - a >= MIN_GAP_MINUTES for a, b in zip(candidates, candidates[1:])
        ):
            break

    times = []
    for minutes in candidates:
        h, m = divmod(minutes, 60)
        times.append(f"{h:02d}:{m:02d}")
    return times


def generate_today_schedule() -> dict:
    """오늘자 스케줄을 새로 만들어 파일에 저장하고 반환합니다."""
    today = _now().strftime("%Y-%m-%d")
    n_posts = random.randint(MIN_POSTS_PER_DAY, MAX_POSTS_PER_DAY)
    times = _random_times_for_today(n_posts)

    schedule = {
        "date": today,
        "slots": [{"time": t, "posted": False} for t in times],
    }
    _save(schedule)
    return schedule


def _save(schedule: dict) -> None:
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)


def _load() -> dict | None:
    if not os.path.exists(SCHEDULE_FILE):
        return None
    with open(SCHEDULE_FILE) as f:
        return json.load(f)


def get_due_slot_index() -> int | None:
    """
    오늘 스케줄 중, 아직 안 올렸고 예정 시각이 지난 슬롯의 인덱스를 반환.
    없으면 None. 날짜가 바뀌었는데 스케줄이 없으면 None (스케줄 생성 워크플로우가
    먼저 돌아야 함).
    """
    schedule = _load()
    if schedule is None:
        return None

    today = _now().strftime("%Y-%m-%d")
    if schedule.get("date") != today:
        return None  # 오늘자 스케줄이 아직 안 만들어짐

    now_time = _now().strftime("%H:%M")
    for i, slot in enumerate(schedule["slots"]):
        if not slot["posted"] and slot["time"] <= now_time:
            return i
    return None


def mark_posted(index: int) -> None:
    schedule = _load()
    schedule["slots"][index]["posted"] = True
    _save(schedule)


if __name__ == "__main__":
    print(generate_today_schedule())
