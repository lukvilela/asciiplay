"""Resolve a origem do vídeo: caminho local ou link (YouTube etc. via yt-dlp)."""

from __future__ import annotations

import os
import tempfile


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def download(url: str, quality: int = 480) -> str:
    """Baixa o vídeo do link para um arquivo temporário e devolve o caminho.

    Usa um formato progressivo (áudio+vídeo num arquivo só) pra não depender de ffmpeg.
    """
    try:
        import yt_dlp  # type: ignore
    except ImportError as e:
        raise SystemExit("Para baixar de links, instale o yt-dlp:  pip install yt-dlp") from e

    tmpdir = tempfile.mkdtemp(prefix="asciiplay_")
    opts = {
        # <=quality e um único arquivo (sem merge → sem ffmpeg)
        "format": f"best[height<={quality}][ext=mp4]/best[height<={quality}]/best[ext=mp4]/best",
        "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    print("Baixando o vídeo do link…")
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
    if not os.path.exists(path):
        raise SystemExit("Não consegui baixar o vídeo desse link.")
    print(f"Baixado: {info.get('title', 'vídeo')}")
    return path


def resolve(arg: str, quality: int = 480) -> tuple[str, bool]:
    """Retorna (caminho_local, é_temporário)."""
    if is_url(arg):
        return download(arg, quality), True
    return arg, False
