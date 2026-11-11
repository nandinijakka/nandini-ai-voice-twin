# Nandini AI Voice Twin

A responsive voice-first personal interview assistant. Visitors can ask questions by voice (Chrome Web Speech API) or text. Answers are spoken using browser speech synthesis. The backend uses Groq's OpenAI-compatible chat completion API when `GROQ_API_KEY` is configured; without a key it runs a small built-in demo response mode.

## Features
- Mobile-friendly single-page web app
- Voice input in supported browsers (Chrome recommended)
- Text input fallback for every browser
- Spoken answers, conversation context, suggested questions, mute and clear controls
- Server-side API key only; never exposed to the browser
- Demo mode works without an API key

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Optional: create `.env` (copy `.env.example`) and set your private `GROQ_API_KEY`. The app loads `.env` automatically for local development. Without the key, demo mode still works.

```bash
# Windows PowerShell
$env:GROQ_API_KEY="your_key_here"
# macOS/Linux
export GROQ_API_KEY="your_key_here"

uvicorn main:app --reload
```

Open http://127.0.0.1:8000. Microphone access requires localhost or HTTPS and browser permission.

## Deploy on Render (public URL)

1. Create a GitHub repository and upload the contents of this folder (not the parent folder).
2. In Render, choose **New → Web Service**, connect that repository, and select the free plan if available.
3. Render reads `render.yaml`. Build command: `pip install -r requirements.txt`; start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. In the Render service's **Environment** settings, add `GROQ_API_KEY` with your private key from https://console.groq.com/keys. Keep it secret; never add it to GitHub or frontend code.
5. Deploy. Render will provide an `https://...onrender.com` URL. Share that URL as your submission.
6. Test `/health`, text chat, microphone permission, and spoken output on a phone and laptop.

If you skip the key, the deployed site still opens and uses the built-in demo responses, but it will not generate fully dynamic answers. A key is required for the full AI experience. Render free services may sleep when idle and take a little time to wake up.

## Customize the personality
Edit `PROFILE` in `main.py`. Keep it factual and only add personal details Nandini has confirmed. The model is instructed not to invent unknown facts.

## API
- `GET /` — web app
- `GET /health` — service health and whether AI is configured (does not expose the key)
- `POST /api/chat` — `{ "message": "...", "history": [{"role":"user|assistant", "content":"..."}] }`
