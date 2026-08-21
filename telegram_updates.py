"""
텔레그램 getUpdates를 오프셋(offset) 기반으로 가져오는 공용 모듈.

문제: getUpdates를 offset 없이 호출하면 텔레그램 서버는 '아직 확인 안 한'
업데이트를 오래된 것부터 순서대로 돌려준다. 지금까지 이 프로젝트 코드가
offset을 한 번도 넘겨준 적이 없어서, 예전에 봇이 있었던 다른 그룹의 메시지
수백 개가 계속 '미확인' 상태로 쌓여 있었고, limit=100 안에 최근 메시지
(승인 버튼 클릭 등)가 들어오지 못하는 문제가 있었다.

해결: 마지막으로 확인한 update_id를 telegram_offset.json에 저장해두고,
다음 조회부터는 그 이후 것만 받아오도록 offset을 넘긴다. 이러면 텔레그램
서버도 그 이전 업데이트를 확인 완료로 처리해서 큐에서 정리한다.

telegram_offset.json은 다른 상태 파일과 마찬가지로 워크플로우 실행 후
git commit 되어야 다음 실행에서도 이어집니다 (check_and_post.yml 참고).
"""

import json
import os

import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OFFSET_FILE = "telegram_offset.json"


def _api(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"


def _load_offset() -> int | None:
    if not os.path.exists(OFFSET_FILE):
        return None
    with open(OFFSET_FILE) as f:
        return json.load(f).get("offset")


def _save_offset(offset: int) -> None:
    with open(OFFSET_FILE, "w") as f:
        json.dump({"offset": offset}, f)


def fetch_updates(limit: int = 100, max_batches: int = 20) -> list:
    """아직 확인 안 한 업데이트를 전부 가져오고, 확인 완료로 표시(offset 전진)합니다.
    쌓여있는 백로그가 많아도 한 번의 실행에서 최대 max_batches*limit개까지 밀린 걸
    한꺼번에 소진합니다."""
    if not TELEGRAM_BOT_TOKEN:
        return []

    offset = _load_offset()
    all_results = []

    for _ in range(max_batches):
        params = {"limit": limit}
        if offset is not None:
            params["offset"] = offset

        try:
            res = requests.get(_api("getUpdates"), params=params, timeout=15).json()
        except Exception as e:
            print(f"[텔레그램] 업데이트 조회 실패: {e}")
            break

        if not res.get("ok"):
            break

        results = res["result"]
        if not results:
            break

        all_results.extend(results)
        max_id = max(u["update_id"] for u in results)
        offset = max_id + 1
        _save_offset(offset)

        if len(results) < limit:
            break  # 더 이상 남은 업데이트가 없음

    return all_results
