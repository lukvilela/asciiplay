"""Renderiza o vídeo inteiro e gera um script Python AUTÔNOMO que se reproduz sozinho
no terminal (sem dependências além da stdlib). É o "vídeo virado código"."""

from __future__ import annotations

import base64
import pickle
import zlib

import cv2

from .convert import Config, render
from .player import open_video

# Template do player embutido. {DATA} e {FPS} são preenchidos.
_TEMPLATE = '''#!/usr/bin/env python3
# Gerado por asciiplay — este arquivo É o vídeo. Rode: python {name}
import base64, zlib, pickle, sys, time, os

_FPS = {fps}
_DATA = "{data}"

def _enable_ansi():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if os.name == "nt":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
        except Exception:
            pass

def main():
    frames = pickle.loads(zlib.decompress(base64.b85decode(_DATA)))
    loop = "--loop" in sys.argv
    _enable_ansi()
    sys.stdout.write("\\x1b[2J\\x1b[?25l")
    try:
        while True:
            start = time.perf_counter()
            for i, f in enumerate(frames):
                sys.stdout.write("\\x1b[H" + f)
                sys.stdout.flush()
                dt = (i + 1) / _FPS - (time.perf_counter() - start)
                if dt > 0:
                    time.sleep(dt)
            if not loop:
                break
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\\x1b[?25h\\x1b[0m\\n")

if __name__ == "__main__":
    main()
'''


def export(path: str, out: str, cfg: Config, fps_override: float | None = None, max_frames: int | None = None) -> dict:
    cap = open_video(path)
    fps = fps_override or cap.get(cv2.CAP_PROP_FPS) or 24.0
    if not fps or fps != fps:
        fps = 24.0
    # o script gerado roda em outro terminal depois, então usamos largura fixa
    if cfg.width <= 0:
        cfg.width = 100

    frames: list[str] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(render(frame, cfg))
        if max_frames and len(frames) >= max_frames:
            break
    cap.release()

    blob = zlib.compress(pickle.dumps(frames), 9)
    data = base64.b85encode(blob).decode("ascii")
    script = _TEMPLATE.format(name=out.replace("\\", "/").split("/")[-1], fps=round(fps, 3), data=data)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(script)

    return {"frames": len(frames), "fps": fps, "bytes": len(script)}
