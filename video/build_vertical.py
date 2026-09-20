"""Build the vertical (9:16) Chetaka concept video with a warm, unhurried pace.

Inputs: media/ (generate_assets.py, screen_text.py, indian_voice.py, shot6_relief.png,
music_warm.mp3). Output: chetaka_concept_vertical.mp4 (1080x1920).

Each landscape image is cropped around its subject. Shots that show a phone screen use a wider
crop placed over a blurred copy of itself, so the whole phone stays visible and the caption sits
in the blurred band below it. Shots join with soft crossfades.
"""

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = Path(__file__).parent
MEDIA = HERE / "media"
BUILD = HERE / "build_vertical"
OUTPUT = HERE / "chetaka_concept_vertical.mp4"

W, H, FPS = 1080, 1920, 30
FONT_FILE = "C\\:/Windows/Fonts/arialbd.ttf"
BOLD = "C:/Windows/Fonts/arialbd.ttf"
REGULAR = "C:/Windows/Fonts/arial.ttf"
CROSSFADE = 0.7
VOICE_LEAD = 0.8      # seconds after a shot starts before its line begins
TAIL = 1.4            # breathing room after each line
END_TAIL = 3.2
MUSIC_VOLUME = 0.20

# name, source, crop centre x, crop width, voice, caption, zoom
SHOTS = [
    ("amma_call", "shot1.mp4", 580, 405, "vo1", "Every day, parents like Amma\nget a call from 'the police'.", None),
    ("caller", "shot2.png", 675, 576, "vo2", "\"This is a digital arrest.\nPay now, or go to jail.\"", "in"),
    ("alert", "shot3_ui.png", 570, 760, "vo3", "Chetaka listens on her phone\nand warns her mid-call.", "in"),
    ("pause", "shot4_ui.png", 1030, 760, "vo4", "Payment app opened after the call?\nChetaka pauses first.", "out"),
    ("son", "shot5.png", 780, 576, "vo5", "Her son gets an alert\nat the same moment.", "in"),
    ("relief", "shot6_relief.png", 540, 864, "vo6", "He calls her right away.\nAmma is safe.", "in"),
    ("end", "shot6.png", 768, 576, "vo7", None, "in"),
]

END_CARD = [
    ("Chetaka", 124, "1180", 0.8),
    ("The scam shield that follows\nthe call into the payment app", 50, "1360", 1.6),
    ("On-device AI  |  Nothing leaves the phone", 36, "1600", 2.6),
]


def ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


def duration_of(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def text_file(name: str, text: str) -> str:
    path = BUILD / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path).replace("\\", "/").replace(":", "\\:")


def drawtext(file: str, size: int, y: str, start: float = 0.0, box_alpha: float = 0.5, x: str = "(w-text_w)/2") -> str:
    return (
        f"drawtext=fontfile='{FONT_FILE}':textfile='{file}':fontsize={size}:fontcolor=white:"
        f"line_spacing=10:text_align=C:x={x}:y={y}:box=1:boxcolor=black@{box_alpha}:boxborderw=24:"
        f"shadowcolor=black@0.6:shadowx=2:shadowy=2:enable='gte(t,{start})'"
    )


def crop_box(image: Image.Image, cx: int, width: int) -> tuple[int, int, int, int]:
    height = min(image.height, round(width * H / W))
    left = max(0, min(image.width - width, cx - width // 2))
    top = (image.height - height) // 2
    return left, top, left + width, top + height


def vertical_still(name: str, source: str, cx: int, width: int) -> Path:
    """Crop around the subject; if the crop is wider than 9:16, float it over a blurred fill."""
    image = Image.open(MEDIA / source).convert("RGB")
    crop = image.crop(crop_box(image, cx, width))
    foreground = crop.resize((W, round(crop.height * W / crop.width)), Image.LANCZOS)

    if foreground.height >= H:
        top = (foreground.height - H) // 2
        frame = foreground.crop((0, top, W, top + H))
    else:
        scale = H / crop.height
        background = crop.resize((round(crop.width * scale), H), Image.LANCZOS)
        left = (background.width - W) // 2
        background = background.crop((left, 0, left + W, H)).filter(ImageFilter.GaussianBlur(40))
        frame = ImageEnhance.Brightness(background).enhance(0.55)
        frame.paste(foreground, (0, (H - foreground.height) // 2 - 60))

    if name == "son":
        add_family_alert_card(frame)

    target = BUILD / f"{name}.png"
    frame.save(target)
    return target


def add_family_alert_card(frame: Image.Image) -> None:
    """Phone-style notification card showing the message the son receives."""
    card = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    left, top, right, bottom = 60, 190, W - 60, 470
    d.rounded_rectangle([left, top, right, bottom], radius=36, fill=(255, 255, 255, 236))
    d.rounded_rectangle([left + 34, top + 34, left + 104, top + 104], radius=18, fill=(22, 150, 90, 255))
    d.text((left + 52, top + 44), "C", font=ImageFont.truetype(BOLD, 44), fill="white")
    d.text((left + 130, top + 40), "Chetaka Family Alert", font=ImageFont.truetype(BOLD, 38), fill=(20, 20, 20))
    d.text((right - 120, top + 46), "now", font=ImageFont.truetype(REGULAR, 32), fill=(110, 110, 110))
    body = ImageFont.truetype(REGULAR, 34)
    d.text((left + 34, top + 135), "Amma spoke to an unknown caller for", font=body, fill=(40, 40, 40))
    d.text((left + 34, top + 180), "12 min and just opened a payment app.", font=body, fill=(40, 40, 40))
    d.text((left + 34, top + 225), "Tap to call her.", font=ImageFont.truetype(BOLD, 34), fill=(22, 130, 80))
    frame.paste(Image.alpha_composite(frame.convert("RGBA"), card).convert("RGB"))


def render_segment(index: int, shot: tuple, seconds: float) -> Path:
    name, source, cx, width, _, caption, zoom = shot
    frames = round(seconds * FPS)
    target = BUILD / f"seg{index}.mp4"
    filters = []

    if zoom is None:
        crop_h = round(width * H / W)
        left = max(0, cx - width // 2)
        filters.append(
            f"crop={width}:{min(crop_h, 720)}:{left}:0,scale={W}:{H},"
            f"tpad=stop_mode=clone:stop_duration={seconds},fps={FPS}"
        )
        inputs = ["-i", str(MEDIA / source)]
    else:
        still = vertical_still(name, source, cx, width)
        zoom_expr = f"1+0.06*on/{frames}" if zoom == "in" else f"1.06-0.06*on/{frames}"
        filters.append(
            f"scale={W * 2}:{H * 2},zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={W}x{H}:fps={FPS}"
        )
        inputs = ["-loop", "1", "-i", str(still)]

    if caption:
        filters.append(drawtext(text_file(f"caption{index}", caption), 50, "h-text_h-230", start=0.4))
    if name == "end":
        for n, (text, size, y, start) in enumerate(END_CARD):
            filters.append(drawtext(text_file(f"end{n}", text), size, y, start, box_alpha=0.0))
    filters.append(drawtext(text_file("concept", "CONCEPT VIDEO"), 26, "70", box_alpha=0.4, x="w-text_w-50"))
    filters.append("format=yuv420p")

    ffmpeg([
        *inputs, "-t", f"{seconds}", "-vf", ",".join(filters), "-frames:v", str(frames), "-an",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-r", str(FPS), str(target),
    ])
    print(f"rendered {name} ({seconds:.1f}s)", flush=True)
    return target


def main() -> None:
    BUILD.mkdir(exist_ok=True)

    voice_files = [MEDIA / f"{shot[4]}_warm_trim.wav" for shot in SHOTS]
    durations = []
    for i, voice in enumerate(voice_files):
        tail = END_TAIL if i == len(SHOTS) - 1 else TAIL
        durations.append(round(VOICE_LEAD + duration_of(voice) + tail, 2))

    segments = [render_segment(i, shot, durations[i]) for i, shot in enumerate(SHOTS)]
    starts = [sum(durations[:i]) - i * CROSSFADE for i in range(len(SHOTS))]
    total = starts[-1] + durations[-1]

    inputs: list[str] = []
    for segment in segments:
        inputs += ["-i", str(segment)]
    video_chain, previous = [], "[0:v]"
    for i in range(1, len(segments)):
        label = f"[x{i}]"
        video_chain.append(
            f"{previous}[{i}:v]xfade=transition=fade:duration={CROSSFADE}:offset={starts[i]:.3f}{label}"
        )
        previous = label
    video_chain.append(f"{previous}fade=t=in:st=0:d=0.8,fade=t=out:st={total - 1.2:.3f}:d=1.2[vout]")

    music_index = len(segments)
    inputs += ["-i", str(MEDIA / "music_warm.mp3"), "-i", str(MEDIA / "music_warm.mp3")]
    audio_chain = [
        f"[{music_index}:a][{music_index + 1}:a]acrossfade=d=4:c1=tri:c2=tri,"
        f"atrim=0:{total:.3f},volume={MUSIC_VOLUME},afade=t=in:st=0:d=2,"
        f"afade=t=out:st={total - 4:.3f}:d=4[music]"
    ]
    labels = ["[music]"]
    for i, voice in enumerate(voice_files):
        index = music_index + 2 + i
        inputs += ["-i", str(voice)]
        delay = round((starts[i] + VOICE_LEAD) * 1000)
        audio_chain.append(f"[{index}:a]adelay={delay}|{delay},volume=1.5[v{i}]")
        labels.append(f"[v{i}]")
    audio_chain.append(
        f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0,"
        f"atrim=0:{total:.3f},alimiter=limit=0.95[aout]"
    )

    ffmpeg([
        *inputs, "-filter_complex", ";".join(video_chain + audio_chain),
        "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart", str(OUTPUT),
    ])
    print(f"done: {OUTPUT} ({total:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
