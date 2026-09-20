"""Draw readable Chetaka alert text onto the phone screens in shot 3 and shot 4.

AI images cannot render reliable text, so the UI text is drawn here and warped onto each
phone screen with a perspective transform. Output: media/shot3_ui.png, media/shot4_ui.png.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
MEDIA = HERE / "media"
BOLD = "C:/Windows/Fonts/arialbd.ttf"
REGULAR = "C:/Windows/Fonts/arial.ttf"
SCALE = 2  # draw the layer at 2x, then warp, for smooth edges


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size * SCALE)


def perspective_coefficients(screen_quad, canvas_size):
    """Coefficients that map output (image) points back to canvas points for Image.transform."""
    width, height = canvas_size
    canvas_quad = [(0, 0), (width, 0), (width, height), (0, height)]
    rows, rhs = [], []
    for (x, y), (u, v) in zip(screen_quad, canvas_quad):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        rhs += [u, v]
    return np.linalg.solve(np.array(rows, float), np.array(rhs, float)).tolist()


def centered(draw, text, font_obj, cx, y, fill):
    box = draw.textbbox((0, 0), text, font=font_obj)
    draw.text((cx - (box[2] - box[0]) / 2, y), text, font=font_obj, fill=fill)
    return y + (box[3] - box[1])


def pill(draw, cx, cy, w, h, label, font_obj, fill, text_fill):
    s = SCALE
    draw.rounded_rectangle(
        [cx - w * s / 2, cy - h * s / 2, cx + w * s / 2, cy + h * s / 2], radius=h * s / 2, fill=fill
    )
    box = draw.textbbox((0, 0), label, font=font_obj)
    draw.text(
        (cx - (box[2] - box[0]) / 2, cy - (box[3] - box[1]) / 2 - box[1]), label, font=font_obj, fill=text_fill
    )


def warp_onto(base: Image.Image, layer: Image.Image, screen_quad) -> Image.Image:
    coeffs = perspective_coefficients(screen_quad, layer.size)
    warped = layer.transform(base.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    return Image.alpha_composite(base.convert("RGBA"), warped).convert("RGB")


def shot3() -> None:
    """Portrait phone, full red screen with a shield in the middle."""
    base = Image.open(MEDIA / "shot3.png")
    screen_quad = [(352, 106), (694, 106), (784, 908), (436, 934)]
    w, h = 400 * SCALE, 900 * SCALE
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    white = (255, 255, 255, 255)
    cx = w / 2

    y = 95 * SCALE
    y = centered(d, "SCAM", font(BOLD, 66), cx, y, white) + 18 * SCALE
    centered(d, "DETECTED", font(BOLD, 58), cx, y, white)

    y = 625 * SCALE
    y = centered(d, "Police never ask", font(BOLD, 30), cx, y, white) + 12 * SCALE
    y = centered(d, "for OTP.", font(BOLD, 30), cx, y, white) + 26 * SCALE
    pill(d, cx, y + 38 * SCALE, 250, 66, "HANG UP", font(BOLD, 30), white, (215, 0, 0, 255))

    warp_onto(base, layer, screen_quad).save(MEDIA / "shot3_ui.png")


def shot4() -> None:
    """Tilted landscape phone with a pause icon; text goes left and right of the pause ring."""
    base = Image.open(MEDIA / "shot4.png")
    screen_quad = [(722, 252), (1352, 362), (1292, 598), (706, 480)]
    w, h = 800 * SCALE, 380 * SCALE
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    white = (255, 255, 255, 255)
    soft = (255, 225, 225, 255)

    left_cx = 190 * SCALE
    y = 95 * SCALE
    y = centered(d, "WAIT.", font(BOLD, 46), left_cx, y, white) + 18 * SCALE
    y = centered(d, "Are they asking", font(BOLD, 22), left_cx, y, white) + 8 * SCALE
    centered(d, "you to pay?", font(BOLD, 22), left_cx, y, white)

    right_cx = 640 * SCALE
    y = 60 * SCALE
    y = centered(d, "Unknown caller", font(REGULAR, 20), right_cx, y, soft) + 8 * SCALE
    y = centered(d, "12 min call", font(REGULAR, 20), right_cx, y, soft) + 16 * SCALE
    y = centered(d, "Real police never", font(BOLD, 20), right_cx, y, white) + 8 * SCALE
    centered(d, "ask for money.", font(BOLD, 20), right_cx, y, white)

    warp_onto(base, layer, screen_quad).save(MEDIA / "shot4_ui.png")


if __name__ == "__main__":
    shot3()
    shot4()
    print("saved media/shot3_ui.png and media/shot4_ui.png")
