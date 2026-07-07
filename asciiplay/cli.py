"""Interface de linha de comando: play / export."""

from __future__ import annotations

import argparse

from .convert import RAMPS, Config


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("video", help="caminho do .mp4 OU um link (YouTube etc.)")
    p.add_argument("-q", "--quality", type=int, default=720, help="qualidade máx. ao baixar de link (altura em px)")
    p.add_argument("-w", "--width", type=int, default=0, help="largura em colunas (0 = largura do terminal)")
    p.add_argument("-m", "--mode", choices=["ascii", "half"], default="ascii", help="ascii (texto) ou half (meio-bloco colorido)")
    p.add_argument("-r", "--ramp", choices=list(RAMPS.keys()), default="simple", help="conjunto de caracteres (modo ascii)")
    p.add_argument("-c", "--color", action="store_true", help="colorir os caracteres (modo ascii)")
    p.add_argument("--invert", action="store_true", help="inverte claro/escuro")
    p.add_argument("--fps", type=float, default=None, help="força um FPS (padrão: o do vídeo)")
    p.add_argument("-e", "--edges", action="store_true", help="realça os contornos (formas mais nítidas)")
    p.add_argument("--gamma", type=float, default=1.0, help="clareia/escurece os médios (ex.: 1.4)")
    p.add_argument("--contrast", type=float, default=1.0, help="contraste extra (ex.: 1.3)")
    p.add_argument("--no-normalize", dest="normalize", action="store_false", help="desliga o auto-contraste por frame")


def _cfg(a: argparse.Namespace) -> Config:
    return Config(
        width=a.width,
        mode=a.mode,
        ramp=a.ramp,
        color=a.color,
        invert=a.invert,
        normalize=a.normalize,
        gamma=a.gamma,
        contrast=a.contrast,
        edges=a.edges,
    )


def main(argv: list[str] | None = None) -> None:
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(prog="asciiplay", description="Toca vídeos como ASCII no terminal.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_play = sub.add_parser("play", help="toca o vídeo ao vivo no terminal")
    _add_common(p_play)
    p_play.add_argument("--loop", action="store_true", help="repete em loop")
    p_play.add_argument("-a", "--audio", action="store_true", help="toca o áudio do vídeo junto")

    p_exp = sub.add_parser("export", help="gera um script .py autônomo que se reproduz sozinho")
    _add_common(p_exp)
    p_exp.add_argument("-o", "--output", default="video_ascii.py", help="arquivo de saída (.py)")
    p_exp.add_argument("--max-frames", type=int, default=None, help="limite de frames (controla o tamanho do arquivo)")

    p_gif = sub.add_parser("gif", help="gera um GIF animado do ASCII (bom pra README)")
    _add_common(p_gif)
    p_gif.add_argument("-o", "--output", default="demo.gif", help="arquivo de saída (.gif)")
    p_gif.add_argument("--gif-fps", type=int, default=12, help="fps do GIF (padrão 12)")
    p_gif.add_argument("--seconds", type=float, default=6.0, help="duração aproximada em segundos")

    a = parser.parse_args(argv)

    import os as _os

    from . import source

    path, is_tmp = source.resolve(a.video, a.quality)
    try:
        if a.cmd == "play":
            from .player import play

            play(path, _cfg(a), fps_override=a.fps, loop=a.loop, audio=a.audio)
        elif a.cmd == "export":
            from .export import export

            info = export(path, a.output, _cfg(a), fps_override=a.fps, max_frames=a.max_frames)
            mb = info["bytes"] / 1_048_576
            print(f"✓ Gerado {a.output} — {info['frames']} frames @ {info['fps']:.1f} fps ({mb:.1f} MB).")
            print(f"  Rode com:  python {a.output}   (ou  python {a.output} --loop)")
            if mb > 5:
                print("  Dica: arquivo grande. Use --width menor, --max-frames ou --fps p/ reduzir.")
        elif a.cmd == "gif":
            from .gif import to_gif

            info = to_gif(path, a.output, _cfg(a), gif_fps=a.gif_fps, seconds=a.seconds)
            print(f"✓ Gerado {a.output} — {info['frames']} frames ({info['bytes'] / 1_048_576:.1f} MB).")
    finally:
        if is_tmp:
            try:
                _os.remove(path)
            except OSError:
                pass
