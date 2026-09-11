# SentinelCrypto — Hybrid Image Encryption

A web application that encrypts and decrypts images using a dual-layer hybrid approach combining **Logistic Map chaos sequences** and **deep learning feature extraction** via a Keras Autoencoder.

## Features

- 🔒 **Encrypt** any PNG/JPG/WEBP image using chaos + CNN fusion
- 🔓 **Decrypt** using a session key shared between sender and receiver
- 📊 Real-time metrics: Entropy, NPCR, UACI
- 🎨 Modern dark glassmorphism UI with animated video background

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Encryption | Logistic Map (r=3.99) × Keras Autoencoder |
| CV | OpenCV |
| Frontend | Vanilla HTML/CSS/JS |

## Setup & Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/your-username/Encryption-Project.git
cd Encryption-Project

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Flask server
python app.py
```

Then open `http://localhost:5000` in your browser.

## How It Works

```
Plaintext Image (P)
        │
        ├─── Keras Autoencoder ──► CNN Feature Map
        │                                │
        └─── Session ID ──► Logistic Map ► Chaos Key
                                         │
                              CNN Features XOR Chaos Key = Final Key
                                         │
                                P XOR Final Key = C (Cipher)
```

## Deployment

> ⚠️ **Vercel note:** This app uses TensorFlow + OpenCV which may exceed Vercel's 250MB bundle limit. Recommended alternatives:
> - [Render](https://render.com) — free tier, no size limit issues
> - [Railway](https://railway.app)
> - [Hugging Face Spaces](https://huggingface.co/spaces)

For Vercel: a `vercel.json` is included in the repo.

## Project Structure

```
Encryption-Project/
├── app.py              # Flask routes + API
├── encryption.py       # Chaos + CNN encryption logic
├── decryption.py       # Reverse XOR decryption
├── chaos.py            # Logistic Map implementation
├── metrics.py          # Entropy, NPCR, UACI
├── models/
│   └── autoencoder.h5  # Pre-trained Keras Autoencoder
├── static/
│   ├── css/style.css
│   ├── js/sender.js
│   ├── js/receiver.js
│   ├── video/bg_loop.mp4
│   └── uploads/        # Runtime session files (gitignored)
└── templates/
    ├── sender.html
    └── receiver.html
```

## Encryption Metrics

| Metric | Ideal Value | Description |
|---|---|---|
| Entropy | ≈ 8.0 | Maximum randomness/unpredictability |
| NPCR | ≈ 99.61% | Number of Pixel Change Rate |
| UACI | ≈ 33.46% | Unified Average Change Intensity |
