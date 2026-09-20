"""Generate the light-theme slide images for the Chetaka deck with Gemini.

Reads GEMINI_API_KEY from deck/.env. Saves JPEGs into assets/, skipping files that exist.
"""

import io
import os
from pathlib import Path

import truststore

truststore.inject_into_ssl()

from dotenv import load_dotenv  # noqa: E402
from google import genai  # noqa: E402
from PIL import Image  # noqa: E402

HERE = Path(__file__).parent
ASSETS = HERE / "assets"
load_dotenv(HERE / ".env")

MODEL = "gemini-2.5-flash-image"
STYLE = (
    " Photorealistic editorial photograph, bright natural daylight, clean airy composition, "
    "soft shadows, light neutral background, plenty of negative space, shallow depth of field. "
    "No text, no watermark, no brand logos, no UI overlays."
)

IMAGES = {
    "hero_light": (
        "Close-up of the hands of an elderly Indian woman holding a modern smartphone, seen over her "
        "shoulder in a bright, airy living room with white walls and morning light through a window. "
        "The phone screen is blank and softly lit. Warm, calm and hopeful mood."
    ),
    "problem_light": (
        "An elderly Indian couple at a dining table in a bright apartment in the morning, the husband "
        "holding a phone to his ear with a concerned expression while his wife looks at him with worry. "
        "A bank passbook and reading glasses on the table. Documentary style, daylight."
    ),
    "users_light": (
        "A customer's hand holding a smartphone to pay at a small vegetable shop in Hyderabad, plain "
        "unbranded payment QR stand on the counter, colourful fresh produce, bright midday light, "
        "shopkeeper smiling in the background."
    ),
    "family_light": (
        "A man in his early thirties sitting beside his elderly mother on a sofa in a bright Indian "
        "living room, both looking at her phone together, she is relieved and smiling, he looks "
        "reassuring. Warm daylight, white walls, plants in the background."
    ),
}


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    for name, prompt in IMAGES.items():
        target = ASSETS / f"{name}.jpg"
        if target.exists():
            continue
        print(f"generating {name} ...", flush=True)
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt + STYLE,
            config={"image_config": {"aspect_ratio": "16:9"}},
        )
        saved = False
        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                picture = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
                picture.thumbnail((1600, 1600))
                picture.save(target, quality=88)
                print(f"  saved {target.name} {picture.size}", flush=True)
                saved = True
                break
        if not saved:
            raise RuntimeError(f"no image returned for {name}: {response.candidates[0].finish_reason}")
    print("ALL GEMINI IMAGES DONE", flush=True)


if __name__ == "__main__":
    main()
