# VTT2SRT-Tool

VTT2SRT-Tool is a simple Windows GUI application that converts WebVTT (.vtt) transcript files into SRT subtitle files. Supports batch conversion, folder processing, optional ffmpeg integration, and an easy-to-use interface. The translation takes a long time, so don't think that nothing is happening. This tool can now translate into 6 languages.

## Functies:

Convert .vtt subtitles to .srt
Batch subtitle conversion
TXT transcript export
Subtitle translation
Multiple language support
Folder processing
Optional ffmpeg support
Simple GUI interface
Windows friendly

## Screenshot

![VTT2SRT-Tool Screenshot](screenshots/main-window.png)

Supported Translation Languages:
English
Dutch
German
French
Spanish
Japanese

Requirements
Python 3.11+
ffmpeg (optional but recommended)

Install dependencies:

pip install -r requirements.txt

Install ffmpeg (Optional)

Download ffmpeg here:

https://ffmpeg.org/download.html

Recommended Windows builds:

https://www.gyan.dev/ffmpeg/builds/

Add ffmpeg to your Windows PATH for full functionality.

requirements.txt
ffmpeg-python
deep-translator

## Installatie

### Python installeren

Download Python:
https://www.python.org/downloads/

Run
python VTT2SRT-Tool.py

Future Features:
Whisper AI support
AI transcript cleanup
Batch subtitle sync
MKV subtitle embedding
Subtitle timing adjustment
Multi-language AI translation
License

## Translation Notes

Subtitle translation uses the Python package `deep-translator`, which relies on Google Translate.

Sometimes Google may temporarily block:
- German translations
- French translations
- Multiple fast translation requests

If this happens, subtitle translation may silently stop or skip some lines.  
The app already includes small delays between requests to reduce this problem.

---

## Subtitle Compatibility Notes

Some media players do not fully support Unicode subtitles or use incorrect subtitle encoding detection.

Possible issues:
- Spanish or Japanese subtitles not displaying
- Broken special characters
- Empty subtitles in MKV players
- Incorrect ANSI encoding detection

To improve compatibility, all generated `.srt` subtitle files are saved as:

```text
UTF-8 with BOM (utf-8-sig)

This improves compatibility with:

VLC
Kodi
Plex
MPC-HC
Smart TVs
MKV players

MIT License

GitHub

Created by UtCollector
