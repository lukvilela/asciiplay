# 🎞️ asciiplay — vídeo em ASCII no terminal

<p align="center"><img src="demo.gif" alt="asciiplay — demonstração" width="640"></p>

Pega um `.mp4` e reproduz como **arte ASCII no próprio terminal**. Também consegue **exportar o vídeo como um script Python autônomo** que se reproduz sozinho — ou seja, o vídeo vira código.

## Como funciona

Cada frame do vídeo é redimensionado para a largura do terminal e convertido em texto: o **brilho de cada pixel** vira um caractere (dos mais "vazios" aos mais "cheios"). No modo colorido usa cores ANSI de verdade; no modo *half* usa meio-bloco (`▀`) com duas cores por célula, o que dá cara de vídeo mesmo.

Usa **OpenCV** para ler o vídeo (não precisa de ffmpeg para a imagem) e **numpy** para converter rápido.

## Instalar

```bash
pip install -r requirements.txt
```

## Usar

Tocar ao vivo:

```bash
python -m asciiplay play video.mp4                 # ASCII, largura do terminal
python -m asciiplay play video.mp4 -c              # ASCII colorido
python -m asciiplay play video.mp4 -m half         # meio-bloco (cara de vídeo)
python -m asciiplay play video.mp4 -w 120 --loop   # largura fixa, em loop
python -m asciiplay play video.mp4 -a              # com áudio
python -m asciiplay play "https://youtu.be/XXXX"   # direto de um link (YouTube etc.)
```

Gerar um GIF (bom pra README/redes):

```bash
python -m asciiplay gif video.mp4 -c -o demo.gif
python -m asciiplay gif "https://youtu.be/XXXX" -c --seconds 6
```

Exportar como script autônomo (o vídeo "vira código"):

```bash
python -m asciiplay export video.mp4 -o meuvideo.py
python meuvideo.py            # roda a animação, sem dependências (só stdlib)
python meuvideo.py --loop
```

## Modo fácil (executável)

Pra quem não quer mexer no terminal: um launcher que pergunta o link e as opções.

```bash
python launcher.py          # roda o assistente interativo
```

Para gerar um **`.exe`** (Windows) que abre sozinho e é só colar o link:

```bash
build_exe.bat               # gera dist\AsciiVideo.exe
```

O `.exe` é grande (~100 MB, traz Python + libs) e na primeira vez baixa o ffmpeg embutido (uma vez). Dá pra enviar o arquivo pronto para outra pessoa usar sem instalar nada.

## Opções

| Opção | O que faz |
|---|---|
| `-w, --width` | Largura em colunas (0 = largura do terminal) |
| `-m, --mode`  | `ascii` (texto) ou `half` (meio-bloco colorido) |
| `-r, --ramp`  | Conjunto de caracteres: `simple`, `blocks`, `detailed` |
| `-c, --color` | Coloriza os caracteres (modo ascii) |
| `--invert`    | Inverte claro/escuro |
| `--fps`       | Força um FPS (padrão: o do vídeo) |
| `--loop`      | (play) repete em loop |
| `--max-frames`| (export) limita frames p/ controlar o tamanho do arquivo |

## Notas

- Terminais modernos (Windows Terminal, iTerm, etc.) mostram as cores de 24 bits. Quanto maior a janela, mais nítido.
- Áudio ainda não é reproduzido (só imagem). Um próximo passo é sincronizar o som via `ffplay`.
- O modo `half` colorido gera arquivos de export bem maiores que o `ascii`.
