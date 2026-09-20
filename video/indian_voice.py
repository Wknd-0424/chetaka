"""Generate a warm, unhurried voiceover with Indian English neural voices (Microsoft Edge TTS).

Narrator: en-IN-NeerjaExpressiveNeural (female). Caller line: en-IN-PrabhatNeural (male).
Each line is saved as media/<name>_warm.mp3 and a silence-trimmed media/<name>_warm_trim.wav.
"""

import asyncio
import subprocess
from pathlib import Path

import truststore

truststore.inject_into_ssl()

import edge_tts  # noqa: E402

MEDIA = Path(__file__).parent / "media"
NARRATOR = "en-IN-NeerjaExpressiveNeural"
CALLER = "en-IN-PrabhatNeural"
TRIM_SILENCE = (
    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
    "silenceremove=start_periods=1:start_threshold=-45dB,areverse"
)

# name: (voice, rate, pitch, text) — slower rates and gentle pitch for a warm, natural tone
LINES = {
    "vo1": (NARRATOR, "-10%", "-2Hz", "Every day, parents like our Amma get a call… from someone who says they are the police."),
    "vo2": (CALLER, "-8%", "-4Hz", "Madam, this is a digital arrest. You must pay now, or you will be jailed."),
    "vo3": (NARRATOR, "-10%", "-2Hz", "But this time, Chetaka is listening, right on her phone, in Telugu, Hindi and English. And it warns her, gently, while the call is still on."),
    "vo4": (NARRATOR, "-10%", "-2Hz", "And if she still opens a payment app after the call, Chetaka pauses, and asks her to take a breath first."),
    "vo5": (NARRATOR, "-10%", "-2Hz", "At the same moment, her son receives an alert."),
    "vo6": (NARRATOR, "-12%", "-2Hz", "He calls her right away. Amma is safe, and her savings stay where they belong."),
    "vo7": (NARRATOR, "-12%", "-2Hz", "Chetaka. The scam shield that follows the call, into the payment app. And nothing ever leaves the phone."),
}


async def main() -> None:
    for name, (voice, rate, pitch, text) in LINES.items():
        mp3 = MEDIA / f"{name}_warm.mp3"
        wav = MEDIA / f"{name}_warm_trim.wav"
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(mp3))
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-af", TRIM_SILENCE, str(wav)],
            check=True,
        )
        print(f"saved {wav.name} ({voice})", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
