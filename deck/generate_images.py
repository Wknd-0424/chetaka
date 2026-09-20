"""Generate the slide images for the Chetaka pitch deck on VideoDB.

These are new images made only for the deck (none reuse the promo video scenes).
Uses the VideoDB key in ../video/.env. Saves JPEGs to assets/, skipping ones that exist.
"""

import io
import time
from pathlib import Path

import requests
import truststore

truststore.inject_into_ssl()

import videodb  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from PIL import Image  # noqa: E402

HERE = Path(__file__).parent
ASSETS = HERE / "assets"
load_dotenv(HERE.parent / "video" / ".env")

STYLE = " Photorealistic, cinematic lighting, shallow depth of field, no text, no watermark, no brand logos."

IMAGES = {
    "hero_shield": ("16:9", "Close-up of weathered elderly Indian hands gently holding a modern smartphone in a dark room, the phone screen glowing with a soft green protective light that spills over the fingers, warm diya lamp bokeh in the background."),
    "worried_couple": ("16:9", "Elderly Indian couple sitting at a dining table in a modest apartment in the evening, the husband holding a smartphone and the wife leaning in with a worried face, an open bank passbook and reading glasses on the table."),
    "upi_market": ("16:9", "A customer's hand scanning a payment QR code with a smartphone at a busy vegetable market stall in Hyderabad, colourful produce, warm afternoon light, the QR stand is plain and unbranded."),
    "npu_chip": ("16:9", "Extreme macro shot of a flagship smartphone circuit board with a central processor chip glowing with fine cyan and green light traces, dark background, high-tech atmosphere."),
    "family_safe": ("16:9", "Warm moment in an Indian living room: a young man in his thirties sits beside his elderly mother on a sofa, showing her something reassuring on her phone, she smiles with relief, golden evening light."),
    "rural_user": ("16:9", "Middle-aged Indian woman in a village in Telangana sitting outside her home using a smartphone, cotton saree, bright natural daylight, mud wall and green fields in the background."),
    "privacy_lock": ("16:9", "A smartphone lying face up on a dark wooden table, the screen showing a single glowing padlock icon, soft moody light, sense of privacy and security."),
    "helpline_desk": ("16:9", "Indian cyber-crime helpline office with a young female officer wearing a headset at a desk with monitors, calm professional atmosphere, cool daylight."),
    "students_building": ("16:9", "Three Indian engineering students building an Android app together at a hackathon at night, laptops and a phone on the table, energy drinks, focused and excited faces, warm desk lamps."),
}


def download(url: str, attempts: int = 4) -> bytes:
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, timeout=300)
            response.raise_for_status()
            return response.content
        except requests.RequestException as error:
            if attempt == attempts:
                raise
            print(f"  retry {attempt}: {error}", flush=True)
            time.sleep(3 * attempt)
    raise RuntimeError("unreachable")


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    coll = videodb.connect().get_collection()
    for name, (ratio, prompt) in IMAGES.items():
        target = ASSETS / f"{name}.jpg"
        if target.exists():
            continue
        print(f"generating {name} ...", flush=True)
        image = coll.generate_image(prompt=prompt + STYLE, aspect_ratio=ratio)
        picture = Image.open(io.BytesIO(download(image.generate_url()))).convert("RGB")
        picture.thumbnail((1600, 1600))
        picture.save(target, quality=86)
        print(f"  saved {target.name} {picture.size}", flush=True)
    print("ALL IMAGES DONE", flush=True)


if __name__ == "__main__":
    main()
