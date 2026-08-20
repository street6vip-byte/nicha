import os
import random
import time
import requests
from google import genai
from google.genai import types
from PIL import Image

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-3.6-flash"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

PERSONA_SYSTEM_PROMPT = """\
You are ghostwriting tweets for a fictional X (Twitter) account featuring
a character named Nicha (นิชา).
- Nicha is a 20-year-old Thai woman living in Bangkok, Thailand.
- Write every tweet in natural, casual Thai (ภาษาไทย).
- Add 1 to 3 relevant hashtags at the end.
- Output ONLY the tweet text, under 260 characters total.
"""

def get_latest_telegram_image() -> str | None:
    """텔레그램 봇으로 전송된 가장 최근 사진을 가져옴"""
    if not TELEGRAM_BOT_TOKEN:
        return None
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    res = requests.get(url).json()
    
    if not res.get("ok") or not res.get("result"):
        return None

    photos = []
    for update in res["result"]:
        message = update.get("message", {})
        if "photo" in message:
            # 가장 해상도가 높은 사진 선택
            photo_info = message["photo"][-1]
            photos.append(photo_info["file_id"])
            
    if not photos:
        return None

    # 가장 최근 사진 다운로드
    latest_file_id = photos[-1]
    file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={latest_file_id}").json()
    file_path = file_info["result"]["file_path"]
    
    img_data = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}").content
    save_path = "telegram_image.jpg"
    with open(save_path, "wb") as f:
        f.write(img_data)
        
    return save_path

def generate_tweet_with_image(image_path: str) -> str:
    img = Image.open(image_path)
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=[img, "Write today's tweet based on this image from Nicha's perspective."],
                config=types.GenerateContentConfig(
                    system_instruction=PERSONA_SYSTEM_PROMPT,
                    temperature=0.7,
                ),
            )
            return response.text.strip().strip('"').strip("'").strip()
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
            else:
                raise e
