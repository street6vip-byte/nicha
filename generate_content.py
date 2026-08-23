import os
import random
import time
import requests
from google import genai
from google.genai import types
from PIL import Image

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

PRIMARY_MODEL = "gemini-3-flash-preview"
BACKUP_MODEL = "gemini-2.5-flash"
# 방 사진의 인테리어를 유지하면서 구도만 다른 변형 사진을 생성할 때 쓰는 모델.
# Gemini 이미지 생성 모델명은 자주 바뀌니, 실제 사용 전 Google AI 스튜디오/문서에서
# 최신 이미지 생성 지원 모델명을 확인해서 필요하면 이 값을 바꿔주세요.
IMAGE_GEN_MODEL = "gemini-2.5-flash-image"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# ---------------------------------------------------------------------------
# 니차 페르소나 정의 (파타야 거주 + ISFP + 퐁뎅 + 한국어 섞어쓰기)
# ---------------------------------------------------------------------------
PERSONA_SYSTEM_PROMPT = """\
You are ghostwriting tweets for a fictional X (Twitter) account featuring
a character named Nicha (นิชา).

Character:
- Nicha is a 20-year-old Thai woman living in Pattaya, Thailand.
- She is a university student living near the beach.
- Personality: ISFP (chill, quiet, flexible, art/nature loving, comfortable at home).
- Hobbies & Interests: Relaxing at beach cafes, watching sea sunsets, watching anime, listening to music, K-pop, and occasionally playing Pokdeng (ป๊อกเด้ง) card game with close friends.
- Language style: 
  * Writes every tweet in natural, casual Thai (ภาษาไทย).
  * Uses natural Thai expressions, casual wording, slang, and sentence endings.
  * She is learning Korean at a beginner level, so she naturally sprinkles simple Korean words written in Hangul (e.g., 대박, 진짜, 귀여워, 오빠, 가자) into her Thai sentences when appropriate.
- Formatting:
  * Add 1 to 5 relevant hashtags at the end of every tweet.
  * Under 260 characters total, INCLUDING hashtags.
  * Output ONLY the tweet text, nothing else.
"""

TOPIC_SEEDS = [
    "listening to a favorite K-pop song and saying '진짜 좋아'",
    "watching anime late at night in her cozy room",
    "getting iced coffee at a chill beach cafe in Pattaya",
    "watching the sunset over Pattaya beach with '대박' mood",
    "complaining about humid weather near the sea",
    "being a total ISFP homebody wanting to stay in bed all day",
    "playing Pokdeng (ป๊อกเด้ง) with friends",
    "practicing simple Korean words while studying",
    "a small everyday moment at university",
]


def pick_topic() -> str:
    return random.choice(TOPIC_SEEDS)


ROOM_PHOTOS = [
    "room_bed.jpg",
    "room_desk.jpg",
    "room_vanity.jpg",
    "room_tv.jpg",
    "room_bathroom.jpg",
]


def get_random_room_photo() -> str | None:
    """자동 스케줄 게시용: 깃허브에 올려둔 방 사진 중 랜덤으로 하나 선택."""
    available_photos = [p for p in ROOM_PHOTOS if os.path.exists(p)]
    if not available_photos:
        print("사용 가능한 방 사진이 없습니다.")
        return None
    chosen_photo = random.choice(available_photos)
    print(f"[자동 스케줄] 방 사진 랜덤 선택: {chosen_photo}")
    return chosen_photo


ROOM_VARIANT_PROMPT = """\
Using the attached photo as a strict visual reference, generate a new photorealistic
photo of the EXACT SAME room interior: same furniture, same wall decor/art, same
lighting fixtures, same color scheme, same layout and same objects on surfaces.
Do NOT invent new furniture or change the decor. Only vary the camera angle,
composition, framing, or exact moment captured — as if someone took another casual
phone photo of the same room a little later. Keep the photorealistic, unstaged,
everyday phone-photo look (not a professional real-estate photo, not overly polished).
Output only the image."""


def generate_room_variant(reference_photo_path: str) -> str | None:
    """레퍼런스 방 사진을 기반으로, 같은 인테리어를 유지하면서 구도만 다른
    새 사진을 생성합니다. 실패하면 None을 반환하고, 호출부에서 원본 사진으로
    대체해서 쓰면 됩니다."""
    try:
        ref_img = Image.open(reference_photo_path)
    except Exception as e:
        print(f"[방 사진 변형] 레퍼런스 사진 로드 실패: {e}")
        return None

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=IMAGE_GEN_MODEL,
                contents=[ref_img, ROOM_VARIANT_PROMPT],
            )
            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None) is not None:
                    save_path = "generated_room.jpg"
                    with open(save_path, "wb") as f:
                        f.write(part.inline_data.data)
                    print(f"[방 사진 변형] 생성 완료: {save_path}")
                    return save_path
            print("[방 사진 변형] 응답에 이미지 데이터가 없습니다.")
        except Exception as e:
            print(f"[방 사진 변형] 시도 {attempt + 1} 실패: {e}")
            time.sleep(3)

    return None


def get_latest_telegram_image() -> str | None:
    """텔레그램 봇으로 전송된 가장 최근 사진을 다운로드. 없으면 깃허브에 올린 방 사진 중 랜덤 선택!"""
    # 1. 텔레그램 확인 시도
    if TELEGRAM_BOT_TOKEN:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?limit=100"
            res = requests.get(url, timeout=10).json()

            if res.get("ok") and res.get("result"):
                photos = []
                for update in res["result"]:
                    msg = update.get("message") or update.get("channel_post") or {}
                    if "photo" in msg:
                        photo_info = msg["photo"][-1]
                        photos.append(photo_info["file_id"])

                if photos:
                    latest_file_id = photos[-1]
                    file_info = requests.get(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={latest_file_id}",
                        timeout=10,
                    ).json()

                    if file_info.get("ok"):
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
            print(f"텔레그램 이미지 확인 중 예외 발생 (기본 방 사진으로 대체): {e}")

    # 2. 텔레그램에 사진이 없거나 오류가 나면 -> 깃허브에 올려둔 방 사진 중 하나를 랜덤으로 사용!
    room_photos = [
        "room_bed.jpg",
        "room_desk.jpg",
        "room_vanity.jpg",
        "room_tv.jpg",
        "room_bathroom.jpg",
    ]
    
    # 실제로 존재하는 파일만 골라냄
    available_photos = [p for p in room_photos if os.path.exists(p)]

    if available_photos:
        chosen_photo = random.choice(available_photos)
        print(f"텔레그램 사진 없음 -> 깃허브의 방 사진 사용: {chosen_photo}")
        return chosen_photo

    print("사용 가능한 사진이 전혀 없습니다.")
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
    """이미지 분석 기반 트윗 생성 (방 사진이나 텔레그램 사진을 보고 글 작성)"""
    img = Image.open(image_path)
    models_to_try = [PRIMARY_MODEL, BACKUP_MODEL]

    for model_name in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        img,
                        "Write today's tweet based on this room/daily life image from Nicha's perspective, acting like she is in this space.",
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
