@echo off
REM Gera o executavel AsciiVideo.exe (launcher interativo)
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --onefile --name AsciiVideo --icon icon.ico --collect-all cv2 --collect-all imageio_ffmpeg --collect-all yt_dlp --noconfirm launcher.py
echo.
echo Pronto! O executavel esta em:  dist\AsciiVideo.exe
pause
