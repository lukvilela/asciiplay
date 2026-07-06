"""Resolve a origem do vídeo: caminho local ou link (YouTube etc. via yt-dlp).

Baixa em alta resolução juntando os streams de vídeo e áudio com o ffmpeg embutido
(imageio-ffmpeg). Sem ffmpeg, cai num formato progressivo (arquivo único)."""

from __future__ import annotations

import os
import shutil
import tempfile


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def _ffmpeg_dir() -> str | None:
    """Deixa o ffmpeg embutido numa pasta com o nome 'ffmpeg(.exe)' que o yt-dlp acha."""
    try:
        import imageio_ffmpeg  # type: ignore

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        d = os.path.join(tempfile.gettempdir(), "asciiplay_ffmpeg")
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if not os.path.exists(dst):
            shutil.copy2(exe, dst)
        return d
    except Exception:
        return None


def download(url: str, quality: int = 720) -> str:
    """Baixa o vídeo do link para um arquivo temporário e devolve o caminho."""
    try:
        import yt_dlp  # type: ignore
    except ImportError as e:
        raise SystemExit("Para baixar de links, instale o yt-dlp:  pip install yt-dlp") from e

    tmpdir = tempfile.mkdtemp(prefix="asciiplay_")
    ffdir = _ffmpeg_dir()

    opts: dict = {
        "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "merge_output_format": "mp4",
    }
    if ffdir:
        # alta resolução: melhor vídeo + melhor áudio, juntados pelo ffmpeg
        opts["format"] = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best"
        opts["ffmpeg_location"] = ffdir
    else:
        # sem ffmpeg: um único arquivo progressivo
        opts["format"] = f"best[height<={quality}][ext=mp4]/best[height<={quality}]/best"

    print("Baixando o vídeo do link…")
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir)]
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        raise SystemExit("Não consegui baixar o vídeo desse link.")
    path = max(files, key=os.path.getsize)  # o arquivo final (mesclado) é o maior
    print(f"Baixado: {info.get('title', 'vídeo')}")
    return path


def resolve(arg: str, quality: int = 720) -> tuple[str, bool]:
    """Retorna (caminho_local, é_temporário)."""
    if is_url(arg):
        return download(arg, quality), True
    return arg, False
