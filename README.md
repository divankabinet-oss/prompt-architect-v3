
# Prompt Architect AI — Telegram Bot

A Telegram bot that builds photorealistic interior prompt strings for Midjourney / Seedream / RealRender / Nanobanana using modular styles (photographers, lighting, camera angle) and optional "lived-in" clutter.

## Quick Start (Local)
1. Python 3.10+
2. `pip install -r requirements.txt`
3. Set environment variable TOKEN to your bot token (from @BotFather).
4. `python main.py`

## Deploy on Render
- Add `TOKEN` as Environment Variable.
- This repo already contains `Procfile` and `requirements.txt`.
- Use a Worker service: `worker: python main.py`.

## Data files
- `data/photographers.json`
- `data/lighting.json`
- `data/interiors.json`
- `data/clutter.json`
Modify these to extend the library.
