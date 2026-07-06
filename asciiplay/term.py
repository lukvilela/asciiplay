"""Utilitários de terminal (ANSI, tamanho, cursor)."""

from __future__ import annotations

import os
import shutil
import sys


def enable_ansi() -> None:
    """Liga ANSI (VT) no Windows e garante saída em UTF-8 (▀, cores, ramps unicode)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass


def size() -> tuple[int, int]:
    s = shutil.get_terminal_size(fallback=(100, 30))
    return s.columns, s.lines


def begin() -> None:
    sys.stdout.write("\x1b[2J\x1b[?25l")  # limpa tela, esconde cursor
    sys.stdout.flush()


def end() -> None:
    sys.stdout.write("\x1b[?25h\x1b[0m\n")  # mostra cursor, reseta cor
    sys.stdout.flush()
