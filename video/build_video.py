"""Build the Chetaka 30-second concept video locally with ffmpeg.

Inputs come from media/ (created by generate_assets.py). Output: chetaka_concept_30s.mp4.
Shot 1 is an AI video clip; shots 2-6 are AI images animated with a slow zoom.
"""

import subprocess
from pathlib import Path

HERE = Path(__file__).parent
MEDIA = HERE / "media"
BUILD = HERE / "build"
OUTPUT = HERE / "chetaka_concept_30s.mp4"

FPS = 30
WIDTH, HEIGHT = 1920, 1080
FONT = "C\\:/Windows/Fonts/arialbd.ttf"
VOICE_DELAY = 0.25
MUSIC_VOLUME = 0.22

# (source file, voice file, seconds, caption lines, zoom direction)
# Voices: Indian English (indian_voice.py), silence-trimmed to *_in_trim.wav.
# Shots 3 and 4 use the *_ui.png images with alert text drawn by screen_text.py.
SHOTS = [
    ("shot1.mp4", "vo1_in_trim.wav", 3.8, "Every day, parents like Amma\nget a call from 'the police'.", None),
    ("shot2.png", "vo2_in_trim.wav", 3.8, "\"Digital arrest! Pay now, or you will be jailed.\"", "in"),
    ("shot3_ui.png", "vo3_in_trim.wav", 7.3, "Chetaka warns mid-call\nin Telugu, Hindi and English.", "in"),
    ("shot4_ui.png", "vo4_in_trim.wav", 5.3, "Payment app opened after the call?\nChetaka pauses the payment first.", "out"),
    ("shot5.png", "vo5_in_trim.wav", 2.0, "Her son knows in seconds.", "in"),
    ("shot6.png", "vo6_in_trim.wav", 7.8, None, "in"),
]

# Captions moved right so they do not cover the phone screen text.
RIGHT_ALIGNED_CAPTIONS = {"shot3_ui.png"}

END_CARD = [
    ("Chetaka", 110, "(h-text_h)/2+170", 0.6),
    ("The scam shield that follows the call into the payment app", 44, "(h-text_h)/2+300", 1.2),
    ("On-device AI  |  Nothing leaves the phone", 34, "h-text_h-70", 1.8),
]


def run(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


def text_file(name: str, text: str) -> str:
    path = BUILD / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path).replace("\\", "/").replace(":", "\\:")


def drawtext(file: str, size: int, y: str, start: float = 0.0, box_alpha: float = 0.55) -> str:
    return (
        f"drawtext=fontfile='{FONT}':textfile='{file}':fontsize={size}:fontcolor=white:"
        f"line_spacing=4:text_align=C:x=(w-text_w)/2:y={y}:box=1:boxcolor=black@{box_alpha}:boxborderw=22:"
        f"enable='gte(t,{start})'"
    )


def render_shot(index: int, source: str, seconds: float, caption: str | None, zoom: str | None) -> Path:
    frames = round(seconds * FPS)
    target = BUILD / f"seg{index}.mp4"
    filters = []

    if zoom is None:
        filters.append(f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},fps={FPS}")
    else:
        zoom_expr = "1+0.10*on/{n}" if zoom == "in" else "1.10-0.10*on/{n}"
        filters.append(
            f"scale={WIDTH * 2}:{HEIGHT * 2}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH * 2}:{HEIGHT * 2},"
            f"zoompan=z='{zoom_expr.format(n=frames)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )

    if caption:
        caption_filter = drawtext(text_file(f"caption{index}", caption), 52, "h-text_h-90")
        if source in RIGHT_ALIGNED_CAPTIONS:
            caption_filter = caption_filter.replace("x=(w-text_w)/2", "x=w-text_w-90")
        filters.append(caption_filter)
    if index == len(SHOTS) - 1:
        for n, (text, size, y, start) in enumerate(END_CARD):
            filters.append(drawtext(text_file(f"end{n}", text), size, y, start, box_alpha=0.0))

    filters.append(drawtext(text_file("concept", "CONCEPT VIDEO"), 26, "40", box_alpha=0.45).replace(
        "x=(w-text_w)/2", "x=w-text_w-50"
    ))
    fade_out = max(seconds - 0.3, 0)
    filters.append(f"fade=t=in:st=0:d=0.3,fade=t=out:st={fade_out}:d=0.3,format=yuv420p")

    input_args = ["-i", str(MEDIA / source)] if zoom is None else ["-loop", "1", "-i", str(MEDIA / source)]
    run([
        *input_args, "-t", f"{seconds}", "-vf", ",".join(filters), "-frames:v", str(frames),
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS), str(target),
    ])
    print(f"rendered shot {index + 1} ({seconds}s)", flush=True)
    return target


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    segments = [
        render_shot(i, source, seconds, caption, zoom)
        for i, (source, _, seconds, caption, zoom) in enumerate(SHOTS)
    ]

    concat_list = BUILD / "segments.txt"
    concat_list.write_text("".join(f"file '{s.as_posix()}'\n" for s in segments), encoding="utf-8")
    silent = BUILD / "video_silent.mp4"
    run(["-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(silent)])

    total = sum(shot[2] for shot in SHOTS)
    inputs = ["-i", str(silent), "-i", str(MEDIA / "music.mp3")]
    audio_filters = [
        f"[1:a]atrim=0:{total},volume={MUSIC_VOLUME},afade=t=in:st=0:d=1,"
        f"afade=t=out:st={total - 3}:d=3[music]"
    ]
    labels = ["[music]"]
    offset = 0.0
    for i, (_, voice, seconds, _, _) in enumerate(SHOTS):
        inputs += ["-i", str(MEDIA / voice)]
        delay_ms = round((offset + VOICE_DELAY) * 1000)
        audio_filters.append(f"[{i + 2}:a]adelay={delay_ms}|{delay_ms},volume=1.6[v{i}]")
        labels.append(f"[v{i}]")
        offset += seconds
    audio_filters.append(
        f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0,"
        f"atrim=0:{total},alimiter=limit=0.95[aout]"
    )

    run([
        *inputs, "-filter_complex", ";".join(audio_filters), "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total}", "-movflags", "+faststart",
        str(OUTPUT),
    ])
    print(f"done: {OUTPUT} ({total}s)", flush=True)


if __name__ == "__main__":
    main()
