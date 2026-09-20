"""Generate and download all media for the Chetaka 30-second concept video.

VideoDB free plan allows one AI video clip, so shot 1 is video and shots 2-6 are AI images
that build_video.py animates locally. Asset IDs are cached in assets.json and files are saved
to media/, so a re-run skips finished items.
"""

import json
import time
from pathlib import Path

import requests
import truststore

truststore.inject_into_ssl()

import videodb  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

HERE = Path(__file__).parent
CACHE = HERE / "assets.json"
MEDIA = HERE / "media"
load_dotenv(HERE / ".env")

STYLE = " Photorealistic, cinematic, 16:9, no text, no watermark, no real brand logos."

SHOT1_VIDEO_ID = "m-z-01a0b012-7937-7670-80ae-92d2f618b8e8"

IMAGES = {
    "shot2": (
        "Dark cinematic shot of a man in silhouette speaking into a phone, face hidden in shadow, "
        "collared shirt with a fake police-style ID card clipped on, in a cramped room. Cold blue "
        "monitor glow, several phones on a desk behind him, hard rim light, thin haze, menacing."
        + STYLE
    ),
    "shot3": (
        "Close-up of a modern Android smartphone held in an elderly Indian woman's hand, screen "
        "facing camera, the whole screen glowing bright red with a large white shield icon in "
        "the centre, faint vibration motion lines around the phone edges, warm room light, "
        "shallow depth of field." + STYLE
    ),
    "shot4": (
        "Over-the-shoulder close-up of an elderly Indian woman's thumb hovering above a phone "
        "screen, the screen covered by a deep red overlay with a large white pause icon and a "
        "circular countdown ring, soft background blur, warm living-room light." + STYLE
    ),
    "shot5": (
        "Medium shot of a 30-year-old Indian man in a formal shirt at a modern office desk in the "
        "evening, city lights through glass behind him, looking at his glowing phone with an "
        "urgent worried expression, cool office light with warm screen glow on his face, 50mm lens."
        + STYLE
    ),
    "shot6": (
        "Minimal dark background with a soft green glow, a simple glowing shield outline made of "
        "light in the upper centre of the frame, subtle floating particles, premium tech brand "
        "reveal, large empty dark space in the lower half." + STYLE
    ),
}

VOICE = {
    "vo1": "Every day, parents like Amma get a call from the police.",
    "vo2": "Digital arrest. Pay now, or be jailed.",
    "vo3": "Until now. Chetaka listens on the phone, in Telugu, Hindi and English, and warns mid-call.",
    "vo4": "And if she opens a payment app after the call, Chetaka stops the payment first.",
    "vo5": "Her son knows in seconds.",
    "vo6": "Chetaka. The scam shield that follows the call into the payment app. Nothing leaves the phone.",
}

MUSIC_PROMPT = (
    "30 second cinematic trailer score: first 12 seconds a low tense pulsing synth with a slow "
    "heartbeat rhythm, then a short silence, then a soft hopeful warm synth pad with gentle piano "
    "that resolves calmly at the end. No vocals."
)


def load_cache() -> dict:
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def save_cache(cache: dict) -> None:
    CACHE.write_text(json.dumps(cache, indent=2))


def download(url: str, target: Path, attempts: int = 4) -> None:
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, timeout=300)
            response.raise_for_status()
            break
        except requests.RequestException as error:
            if attempt == attempts:
                raise
            print(f"  download retry {attempt} after: {error}", flush=True)
            time.sleep(3 * attempt)
    target.write_bytes(response.content)
    print(f"  saved {target.name} ({len(response.content) // 1024} KB)", flush=True)


def main() -> None:
    MEDIA.mkdir(exist_ok=True)
    coll = videodb.connect().get_collection()
    cache = load_cache()

    shot1_file = MEDIA / "shot1.mp4"
    if not shot1_file.exists():
        print("downloading shot1 ...", flush=True)
        info = coll.get_video(SHOT1_VIDEO_ID).download()
        url = info.get("download_url") or info.get("url") if isinstance(info, dict) else None
        if not url:
            raise RuntimeError(f"no download URL in response: {info}")
        download(url, shot1_file)

    for name, prompt in IMAGES.items():
        target = MEDIA / f"{name}.png"
        if target.exists():
            continue
        if name in cache:
            image = coll.get_image(cache[name])
        else:
            print(f"generating {name} ...", flush=True)
            image = coll.generate_image(prompt=prompt, aspect_ratio="16:9")
            cache[name] = image.id
            save_cache(cache)
        download(image.generate_url(), target)

    for name, text in VOICE.items():
        target = MEDIA / f"{name}.mp3"
        if target.exists():
            continue
        if name in cache:
            audio = coll.get_audio(cache[name])
        else:
            print(f"generating {name} ...", flush=True)
            audio = coll.generate_voice(text=text)
            cache[name] = audio.id
            save_cache(cache)
        download(audio.generate_url(), target)

    music_file = MEDIA / "music.mp3"
    if not music_file.exists():
        if "music" in cache:
            music = coll.get_audio(cache["music"])
        else:
            print("generating music ...", flush=True)
            music = coll.generate_music(prompt=MUSIC_PROMPT, duration=30)
            cache["music"] = music.id
            save_cache(cache)
        download(music.generate_url(), music_file)

    print("ALL ASSETS DONE", flush=True)


if __name__ == "__main__":
    main()
