# NWJNS Pixel Player (Python)

A cute 2D pixel-art styled desktop music player inspired by the soft blue NewJeans aesthetic.

## Features

- 💙 Pixel-art UI with animated cassette reels, sparkles, and equalizer bars
- 🎶 Plays audio from YouTube URLs or video IDs (streamed audio only)
- 📼 Built-in quick playlist with official music video links
- 🔊 Volume, seek bar, pause/play, next/previous controls
- ✨ Clean, lightweight desktop app using Tkinter

## Tech stack

- Python + Tkinter UI
- `yt-dlp` to resolve YouTube audio stream URLs
- `python-vlc` for audio playback engine

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> You need VLC installed on your system so `python-vlc` can find `libvlc`.

## Run

```bash
python app.py
```

## Notes

- Paste a YouTube URL (or video ID) in the input and click **Play URL**.
- This app uses a custom original pixel-art style and does not bundle official NewJeans assets.
