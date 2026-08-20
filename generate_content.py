import os
import random
import time
import requests
from google import genai
from google.genai import types
from PIL import Image

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

# 백업 모델 지정 (503 에러 발생 시 자동 전환)
PRIMARY_MODEL = "gemini-3.6-flash"
BACKUP_MODEL = "gemini-2.5-flash"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# ---------------------------------------------------------------------------
# 니차 페르소나 정의
# ---------------------------------------------------------------------------
PERSONA_SYSTEM_PROMPT = """\
You are ghostwriting tweets for a fictional X (Twitter) account featuring
a character named Nicha (นิชา).

Character:
- Nicha is a 20-year-old Thai woman living in Bangkok, Thailand.
- She is a university student.
- She spends a lot of time at home, enjoys anime, listening to music, and K-pop.
- Writes every tweet in natural, casual Thai (ภาษาไทย).
- Use natural Thai expressions, casual wording, slang, and sentence endings.
- Add 1 to 3 relevant hashtags at the end of every tweet.
- Under 260 characters total, INCLUDING hashtags.
- Output ONLY the tweet text, nothing else.
"""

TOPIC_SEEDS = [
    "listening to a favorite K-pop song",
    "watching anime late at night",
    "getting iced coffee or a sweet drink",
    "complaining about Bangkok's hot weather",
    "being lazy and wanting to stay in bed",
    "a small everyday moment at university",
    "a snack eaten today",
    "doing laundry while listening to music",
]


def pick_topic() -> str:
    return random.choice(TOPIC_SEEDS)


def get_latest_telegram_image() -> str | None:
    """텔레그램 봇으로 전송된 가장 최근 사진을 다운로드"""
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        return None

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?limit=100"
        res = requests.get(url, timeout=10).json()

        if not res.get("ok") or not res.get("result"):
            print(f"텔레그램 응답 없음 또는 결과 비어있음: {res}")
            return None

        photos = []
        for update in res["result"]:
            msg = update.get("message") or update.get("channel_post") or {}
            if "photo" in msg:
                photo_info = msg["photo"][-1]
                photos.append(photo_info["file_id"])

        if not photos:
            print("텔레그램 최근 메시지 중 사진을 찾지 못했습니다.")
            return None

        latest_file_id = photos[-1]
        file_info = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={latest_file_id}",
            timeout=10,
        ).json()

        if not file_info.get("ok"):
            return None

        file_path = file_info["result"]["file_path"]
        img_data = requests.get(
            f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}",
            timeout=10,
        ).content

        save_path = "telegram_image.jpg"
        with open(save_path, "wb") as f:
            f.write(img_data)

        print(f"텔레그램 사진 다운로드 성공: {save_path}")
        return save_path
    except Exception as e:
        print(f"텔레그램 이미지 로드 실패: {e}")
        return None


def generate_tweet(topic_text: str | None = None) -> str:
    """텍스트 전용 트윗 생성"""
    if topic_text is None:
        topic_text = pick_topic()

    models_to_try = [PRIMARY_MODEL, BACKUP_MODEL]

    for model_name in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"Write today's tweet for Nicha. Topic angle: {topic_text}",
                    config=types.GenerateContentConfig(
                        system_instruction=PERSONA_SYSTEM_PROMPT,
                        temperature=0.7,
                    ),
                )
                return response.text.strip().strip('"').strip("'").strip()
            except Exception as e:
                print(f"[{model_name}] 시도 {attempt + 1} 실패: {e}")
                time.sleep(5)

    raise Exception("모든 Gemini 모델 및 재시도 실패")


def generate_tweet_with_image(image_path: str) -> str:
    """이미지 분석 기반 트윗 생성"""
    img = Image.open(image_path)
    models_to_try = [PRIMARY_MODEL, BACKUP_MODEL]

    for model_name in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        img,
                        "Write today's tweet based on this image from Nicha's perspective.",
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=PERSONA_SYSTEM_PROMPT,
                        temperature=0.7,
                    ),
                )
                return response.text.strip().strip('"').strip("'").strip()
            except Exception as e:
                print(f"[{model_name}] 시도 {attempt + 1} 실패: {e}")
                time.sleep(5)

    raise Exception("모든 Gemini 모델 및 재시도 실패")
