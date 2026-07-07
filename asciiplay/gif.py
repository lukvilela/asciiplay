"""Gera um GIF animado do ASCII — ideal pra colocar no README do GitHub
(que não roda vídeo, mas mostra GIF)."""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .convert import RAMPS, Config, _adjust_gray

_FONTS = [
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/cour.ttf",
    "DejaVuSansMono.ttf",
    "consola.ttf",
]


def _load_font(size: int):
    for name in _FONTS:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _frame_to_image(frame: np.ndarray, cfg: Config, font, cw: int, ch: int) -> Image.Image:
    fh, fw = frame.shape[:2]
    rows = max(1, round(cfg.width * (fh / fw) * 0.5))
    small = cv2.resize(frame, (cfg.width, rows), interpolation=cv2.INTER_AREA)
    ramp = RAMPS.get(cfg.ramp, RAMPS["simple"])
    ramp_arr = np.array(list(ramp))
    gray = _adjust_gray(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), cfg)
    idx = (gray.astype(np.uint16) * (len(ramp) - 1) // 255).astype(np.int32)
    if cfg.invert:
        idx = (len(ramp) - 1) - idx
    chars = ramp_arr[idx]
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB) if cfg.color else None

    img = Image.new("RGB", (cfg.width * cw, rows * ch), (14, 16, 20))
    draw = ImageDraw.Draw(img)
    for y in range(rows):
        for x in range(cfg.width):
            c = chars[y, x]
            if c == " ":
                continue
            color = tuple(int(v) for v in rgb[y, x]) if rgb is not None else (208, 214, 226)
            draw.text((x * cw, y * ch), c, fill=color, font=font)
    return img


def to_gif(video: str, out: str, cfg: Config, gif_fps: int = 12, seconds: float = 6.0, font_size: int = 14) -> dict:
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        raise SystemExit(f"Não consegui abrir o vídeo: {video}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    if not src_fps or src_fps != src_fps:
        src_fps = 24.0
    step = max(1, round(src_fps / gif_fps))
    max_frames = int(seconds * gif_fps)

    font = _load_font(font_size)
    bbox = font.getbbox("Mg")
    ch = (bbox[3] - bbox[1]) + 3
    cw = max(1, round(font.getlength("M")))

    frames: list[Image.Image] = []
    i = 0
    while len(frames) < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            frames.append(_frame_to_image(frame, cfg, font, cw, ch))
        i += 1
    cap.release()
    if not frames:
        raise SystemExit("Nenhum frame gerado.")

    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / gif_fps),
        loop=0,
        optimize=True,
        disposal=2,
    )
    import os

    return {"frames": len(frames), "bytes": os.path.getsize(out)}
