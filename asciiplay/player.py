"""Reproduz um vídeo como ASCII/half-block ao vivo no terminal."""

from __future__ import annotations

import sys
import time

import cv2

from . import term
from .convert import Config, render


def open_video(path: str):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f"Não consegui abrir o vídeo: {path}")
    return cap


def fit_width(cfg: Config, fw: int, fh: int) -> None:
    """Escolhe a largura pra caber no terminal em LARGURA e ALTURA (sem rolar a tela)."""
    cols, rows = term.size()
    avail_rows = max(4, rows - 1)
    # linhas de texto ≈ width * (fh/fw) * 0.5  → largura máxima que cabe na altura
    w_by_rows = int(avail_rows * 2.0 * fw / max(1, fh))
    want = cfg.width if cfg.width > 0 else cols
    cfg.width = max(10, min(want, cols, w_by_rows))


# Sequências de "synchronized output" (o terminal desenha o frame de uma vez → sem flicker).
_SYNC_ON = "\x1b[?2026h"
_SYNC_OFF = "\x1b[?2026l"


def play(path: str, cfg: Config, fps_override: float | None = None, loop: bool = False, audio: bool = False) -> None:
    cap = open_video(path)
    fps = fps_override or cap.get(cv2.CAP_PROP_FPS) or 24.0
    if not fps or fps != fps:  # NaN
        fps = 24.0
    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 16
    fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 9
    fit_width(cfg, fw, fh)

    aud = None
    if audio:
        from .audio import Audio, extract_wav

        print("Preparando áudio…")
        aud = Audio(extract_wav(path))

    term.enable_ansi()
    term.begin()
    try:
        while True:
            start = time.perf_counter()
            if aud:
                aud.stop()
                aud.start()
            frame_no = 0
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                target = frame_no / fps
                elapsed = time.perf_counter() - start
                frame_no += 1
                # se estiver muito atrasado, pula o desenho deste frame (mantém o ritmo)
                if elapsed > target + 1.5 / fps:
                    continue
                # frame desenhado de forma atômica → sem flicker/tearing
                sys.stdout.write(_SYNC_ON + "\x1b[H" + render(frame, cfg) + _SYNC_OFF)
                sys.stdout.flush()
                sleep = frame_no / fps - (time.perf_counter() - start)
                if sleep > 0:
                    time.sleep(sleep)
            if not loop:
                break
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    except KeyboardInterrupt:
        pass
    finally:
        if aud:
            aud.cleanup()
        cap.release()
        term.end()
