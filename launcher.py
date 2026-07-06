#!/usr/bin/env python3
"""Launcher interativo — feito pra virar um .exe. Ao rodar, pergunta o link e as
opções (estilo, som, preencher tela) e toca o vídeo em ASCII no terminal."""

import sys

from asciiplay import source
from asciiplay.convert import Config
from asciiplay.player import play

BANNER = r"""
   __ _  ___  ___(_)(_)  _ __  | | __ _ _   _
  / _` |/ __|/ __| || | | '_ \ | |/ _` | | | |
 | (_| |\__ \ (__| || | | |_) || | (_| | |_| |
  \__,_||___/\___|_||_| | .__/ |_|\__,_|\__, |
                        |_|             |___/
       vídeo do YouTube  ->  ASCII no terminal
"""


def ask(prompt: str, default: str) -> str:
    v = input(prompt).strip()
    return v or default


def main() -> None:
    print(BANNER)
    link = input("Cole o link do YouTube (ou o caminho de um .mp4): ").strip()
    if not link:
        print("Nada informado. Saindo.")
        return

    print("\nEstilo:")
    print("  [1] ASCII (preto e branco)")
    print("  [2] ASCII colorido            (recomendado — leve e fluido)")
    print("  [3] Vídeo em blocos coloridos (mais bonito, porém mais pesado)")
    print("  [4] Bad Apple                 (preto e branco, alto contraste)")
    estilo = ask("Escolha [Enter = 2]: ", "2")

    som = ask("Tocar com som? [S/n]: ", "s").lower() != "n"
    loop = ask("Repetir em loop? [s/N]: ", "n").lower() == "s"

    if estilo == "4":
        cfg = Config(mode="ascii", color=False, ramp="blocks", contrast=1.4)
    elif estilo == "3":
        cfg = Config(mode="half")
    elif estilo == "1":
        cfg = Config(mode="ascii", color=False)
    else:
        cfg = Config(mode="ascii", color=True)

    quality = 480
    if source.is_url(link):
        print("\nQualidade do download:")
        print("  [1] 360p  (mais rápido, menos chance de falhar)")
        print("  [2] 480p  (equilíbrio — recomendado)")
        print("  [3] 720p  (melhor detalhe, download maior)")
        q = ask("Escolha [Enter = 2]: ", "2")
        quality = {"1": 360, "2": 480, "3": 720}.get(q, 480)

    print("\nPreparando… (o download pode levar alguns segundos)\n")
    path, is_tmp = source.resolve(link, quality)
    try:
        play(path, cfg, loop=loop, audio=som)
    finally:
        if is_tmp:
            import os

            try:
                os.remove(path)
            except OSError:
                pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:  # noqa: BLE001
        print(f"\nOps, algo deu errado: {e}")
    # mantém a janela aberta quando aberto por duplo-clique (.exe)
    try:
        input("\nAcabou. Pressione Enter para fechar…")
    except EOFError:
        pass
