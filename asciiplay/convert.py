"""Conversão de um frame (imagem BGR do OpenCV) em texto para o terminal.

Melhorias de legibilidade:
- auto-contraste por frame (estica os tons pra revelar detalhe)
- gamma e contraste ajustáveis
- modo "edges": realça os contornos com - / | \\ (deixa as formas nítidas)

Modos: "ascii" (brilho→caractere, opc. colorido) e "half" (meio-bloco ▀ truecolor).
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

RAMPS = {
    "simple": " .:-=+*#%@",
    "blocks": " ░▒▓█",
    "detailed": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
}

RESET = "\x1b[0m"
_EDGE_LUT = np.array(["-", "/", "|", "\\", "-"])  # bins de orientação da borda


@dataclass
class Config:
    width: int = 100
    mode: str = "ascii"       # "ascii" | "half"
    ramp: str = "simple"
    color: bool = False
    invert: bool = False
    normalize: bool = True    # auto-contraste por frame
    gamma: float = 1.0        # >1 clareia os médios
    contrast: float = 1.0     # 1 = neutro
    edges: bool = False       # realça contornos (modo ascii)
    fill: bool = False        # estica pra preencher a tela toda (ignora proporção)
    height: int = 0           # linhas de texto alvo (0 = deriva da proporção)


def _target_size(fw: int, fh: int, cfg: "Config") -> tuple[int, int]:
    # altura explícita (modo fill / height): amostra exatamente esse tanto de linhas
    if cfg.height > 0:
        rows_px = cfg.height * 2 if cfg.mode == "half" else cfg.height
        return cfg.width, rows_px
    if cfg.mode == "half":
        rows = max(2, round(cfg.width * (fh / fw)))
        return cfg.width, rows + (rows % 2)
    rows = max(1, round(cfg.width * (fh / fw) * 0.5))
    return cfg.width, rows


def _adjust_gray(gray: np.ndarray, cfg: Config) -> np.ndarray:
    """Auto-contraste + contraste + gamma sobre a imagem de brilho."""
    g = gray.astype(np.float32)
    if cfg.normalize:
        lo, hi = np.percentile(g, 2), np.percentile(g, 98)
        if hi > lo:
            g = (g - lo) * (255.0 / (hi - lo))
    if cfg.contrast != 1.0:
        g = (g - 128.0) * cfg.contrast + 128.0
    g = np.clip(g, 0, 255)
    if cfg.gamma != 1.0:
        g = 255.0 * np.power(g / 255.0, 1.0 / cfg.gamma)
    return np.clip(g, 0, 255).astype(np.uint8)


def _edge_chars(gray_u8: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Máscara de bordas (Canny) + caractere de orientação por pixel."""
    v = float(np.median(gray_u8))
    lo = int(max(0, 0.66 * v))
    hi = int(min(255, 1.33 * v))
    mask = cv2.Canny(gray_u8, lo, hi) > 0
    gx = cv2.Sobel(gray_u8, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_u8, cv2.CV_32F, 0, 1, ksize=3)
    orient = (np.degrees(np.arctan2(gy, gx)) + 90.0) % 180.0
    bins = np.digitize(orient, [22.5, 67.5, 112.5, 157.5])
    return mask, _EDGE_LUT[bins]


def _normalize_color(bgr: np.ndarray) -> np.ndarray:
    """Estica o contraste preservando a cor (canal L do LAB)."""
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0].astype(np.float32)
    lo, hi = np.percentile(L, 2), np.percentile(L, 98)
    if hi > lo:
        lab[:, :, 0] = np.clip((L - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return bgr


def _render_ascii(frame: np.ndarray, cfg: Config) -> str:
    ramp = RAMPS.get(cfg.ramp, RAMPS["simple"])
    ramp_arr = np.array(list(ramp))
    gray = _adjust_gray(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cfg)
    idx = (gray.astype(np.uint16) * (len(ramp) - 1) // 255).astype(np.int32)
    if cfg.invert:
        idx = (len(ramp) - 1) - idx
    chars = ramp_arr[idx]

    if cfg.edges:
        mask, echars = _edge_chars(gray)
        chars = np.where(mask, echars, chars)

    if not cfg.color:
        return "\n".join("".join(row) for row in chars)

    # tolist() dá ints nativos (bem mais rápido) e a quantização (&0xF8) aumenta os
    # trechos de mesma cor → menos escapes ANSI → mais rápido e estável entre frames.
    rgb = (cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) & 0xF8).tolist()
    charlist = chars.tolist()
    h, w = chars.shape
    lines = []
    for y in range(h):
        row, cr = rgb[y], charlist[y]
        parts, last = [], None
        for x in range(w):
            r, g, b = row[x]
            key = (r, g, b)
            if key != last:
                parts.append("\x1b[38;2;%d;%d;%dm" % key)
                last = key
            parts.append(cr[x])
        parts.append(RESET)
        lines.append("".join(parts))
    return "\n".join(lines)


def _render_half(frame: np.ndarray, cfg: Config) -> str:
    rgb = (cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) & 0xF8)
    h, w, _ = rgb.shape
    rows = rgb.tolist()
    lines = []
    for y in range(0, h - 1, 2):
        top, bot = rows[y], rows[y + 1]
        parts, last = [], None
        for x in range(w):
            tr, tg, tb = top[x]
            br, bg, bb = bot[x]
            key = (tr, tg, tb, br, bg, bb)
            if key != last:
                parts.append("\x1b[38;2;%d;%d;%d;48;2;%d;%d;%dm" % key)
                last = key
            parts.append("▀")
        parts.append(RESET)
        lines.append("".join(parts))
    return "\n".join(lines)


def render(frame: np.ndarray, cfg: Config) -> str:
    fh, fw = frame.shape[:2]
    cols, rows = _target_size(fw, fh, cfg)
    resized = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA)
    if cfg.mode == "half":
        if cfg.normalize:
            resized = _normalize_color(resized)
        return _render_half(resized, cfg)
    return _render_ascii(resized, cfg)
