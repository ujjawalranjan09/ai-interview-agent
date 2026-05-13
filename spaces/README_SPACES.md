# 🚀 Deploy to HuggingFace Spaces

This directory contains everything needed to deploy the AI Interview Agent
as a public demo on HuggingFace Spaces (free tier).

## Step-by-Step Guide

### 1. Create a new Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Space name: `ai-interview-agent`
3. License: Apache 2.0
4. SDK: **Docker**
5. Hardware: CPU Basic (free) or T4 Small (for Whisper/SpeechBrain)

### 2. Push this repo to your Space

```bash
# Clone the Space repo
git clone https://huggingface.co/spaces/ujjawalranjan09/ai-interview-agent

# Copy your project files into it
cp -r /path/to/ai-interview-agent/* ai-interview-agent/

# Push
cd ai-interview-agent
git add . && git commit -m "Initial deploy" && git push
```

### 3. Set Space Secrets

In your Space Settings → Repository Secrets, add:

| Secret | Value |
|--------|-------|
| `HF_TOKEN` | Your HuggingFace token (for Mistral inference) |
| `MONGODB_URI` | Your MongoDB Atlas connection string |
| `OPENAI_API_KEY` | Optional — GPT fallback |

### 4. Space will auto-build

HuggingFace will pick up `spaces/Dockerfile.spaces` and start the app.
Your demo will be live at:

```
https://huggingface.co/spaces/ujjawalranjan09/ai-interview-agent
```

## 📦 What HF Spaces Provides (Free)

- Public demo URL (great for resume / LinkedIn)
- 16 GB RAM CPU instance
- Persistent storage (optional)
- Auto-restart on crash

## 💡 Pro Tips

- Add a `README.md` with `title`, `emoji`, `colorFrom`, `colorTo`,
  `sdk: docker`, `app_port: 7860` YAML front matter for the Spaces preview card
- Pin the Space to your HF profile for discoverability
- Share the Space URL in your GitHub README badge:
  `[![Open in Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/ujjawalranjan09/ai-interview-agent)`
