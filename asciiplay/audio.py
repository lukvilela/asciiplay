"""Áudio para o modo play. Extrai a trilha do vídeo para WAV (via ffmpeg embutido do
imageio-ffmpeg) e toca em paralelo — o vídeo é temporizado em tempo real, então fica
sincronizado. No Windows usa winsound; em outros SOs tenta ffplay/aplay/afplay."""

from __future__ import annotations

import os
import subprocess
import tempfile

_DEVNULL = subprocess.DEVNULL


def _ffmpeg_exe() -> str | None:
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def extract_wav(video: str) -> str | None:
    """Extrai o áudio para um WAV temporário. Retorna None se não houver áudio/ffmpeg."""
    ff = _ffmpeg_exe()
    if not ff:
        return None
    tmpdir = tempfile.mkdtemp(prefix="asciiaud_")
    wav = os.path.join(tmpdir, "audio.wav")
    try:
        subprocess.run(
            [ff, "-y", "-i", video, "-vn", "-ac", "2", "-ar", "44100", wav],
            stdout=_DEVNULL,
            stderr=_DEVNULL,
            check=True,
        )
    except Exception:
        return None
    return wav if os.path.exists(wav) and os.path.getsize(wav) > 44 else None


class Audio:
    """Controla a reprodução do WAV. start() dispara sem bloquear; stop() interrompe."""

    def __init__(self, wav: str | None):
        self.wav = wav
        self._proc: subprocess.Popen | None = None

    @property
    def ok(self) -> bool:
        return bool(self.wav)

    def start(self) -> None:
        if not self.wav:
            return
        if os.name == "nt":
            try:
                import winsound

                winsound.PlaySound(self.wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass
        else:
            for cmd in (
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", self.wav],
                ["aplay", self.wav],
                ["afplay", self.wav],
            ):
                try:
                    self._proc = subprocess.Popen(cmd, stdout=_DEVNULL, stderr=_DEVNULL)
                    break
                except FileNotFoundError:
                    continue

    def stop(self) -> None:
        if os.name == "nt":
            try:
                import winsound

                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass
        elif self._proc:
            self._proc.terminate()
            self._proc = None

    def cleanup(self) -> None:
        self.stop()
        if self.wav:
            try:
                os.remove(self.wav)
                os.rmdir(os.path.dirname(self.wav))
            except OSError:
                pass
