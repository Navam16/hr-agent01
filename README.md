# 🎙️ HR Voice Recruiting Agent — MVP Demo

An AI-powered HR recruiting agent with **voice input and output**.  
Screens candidate resumes against a job description using a **4-agent pipeline** — powered by **Groq**.

---

## 🗂️ Project Structure

```
hr_voice_mvp/
├── app.py                        ← Main Streamlit app (single file)
├── requirements.txt              ← Python dependencies
├── .env.example                  ← Copy this to .env and add your key
├── .gitignore                    ← Keeps secrets out of GitHub
├── .streamlit/
│   └── secrets.toml.example      ← For Streamlit Cloud deployment
└── sample_resumes/               ← ⭐ PUT YOUR RESUME PDFs HERE
    ├── john_doe.pdf
    ├── jane_smith.pdf
    └── ... (any number of PDFs)
```

---

## ⭐ Where to Put Resumes

> **Put all candidate PDF resumes inside the `sample_resumes/` folder.**

- Only `.pdf` files are supported
- File name = candidate display name (e.g. `john_doe.pdf` → "John Doe")
- Add as many resumes as needed — the agent processes all of them
- The folder is already created. Just drop PDFs in.

---

## 🔑 API Keys Required

| Service | Key Name | Used For | Cost | Get It |
|---|---|---|---|---|
| **Groq** | `GROQ_API_KEY` | LLM (llama-3.3-70b) + Whisper STT | **Free** | [console.groq.com](https://console.groq.com) |

**That's the only key you need.** Everything else is free and keyless:
- `gTTS` — text-to-speech (free, no key)
- `PyPDF2` — PDF parsing (local, no key)
- `Streamlit` — UI framework (free, no key)

---

## 🚀 Local Setup (Run on Your Machine)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/hr-voice-agent.git
cd hr-voice-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your API key
cp .env.example .env
# Open .env and replace: GROQ_API_KEY=gsk_your_key_here

# 4. Add resume PDFs
# Drop candidate PDFs into the sample_resumes/ folder

# 5. Run
streamlit run app.py
```

App opens at: **http://localhost:8501**

---

## ☁️ Deploy on Streamlit Community Cloud (Free Hosting)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New App** → select your repo → set `app.py` as main file
4. Go to **App Settings → Secrets** and paste:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Click **Deploy** — your app gets a public URL

---

## 🤖 How the Agent Works

```
User speaks / types JD
        ↓
[Agent 1] JD Analyzer       → extracts required skills, experience, must-haves
        ↓
[Agent 2] Resume Parser      → extracts candidate profile from each PDF
        ↓
[Agent 3] RedFlag Detector   → finds job hopping, gaps, inconsistencies
        ↓
[Agent 4] Recruiter Agent    → scores 0-100, verdict, interview questions
        ↓
Ranked results + Voice summary
```

---

## 🎙️ Voice Features

| Feature | How it works |
|---|---|
| **Voice Input** | Record your JD verbally — Groq Whisper transcribes it |
| **Voice Output** | Top candidate summary is spoken aloud using gTTS |
| **Per-candidate audio** | Click 🔊 button on any candidate card to hear their summary |
| **Toggle** | Turn voice on/off from the sidebar |

---

## 📦 Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| LLM | Groq — llama-3.3-70b-versatile |
| Speech-to-Text | Groq — whisper-large-v3-turbo |
| Text-to-Speech | gTTS (Google TTS, free) |
| PDF Parsing | PyPDF2 |
| Agent Pipeline | Pure Python (no LangGraph for MVP) |

---

## ❓ Troubleshooting

**No resumes found?**
→ Make sure PDFs are in `sample_resumes/` and the filename ends in `.pdf`

**API key error?**
→ Check `.env` has `GROQ_API_KEY=gsk_...` with no extra spaces

**Voice not playing?**
→ Ensure browser allows audio autoplay, or click the play button manually

**Transcription failed?**
→ Record a clear WAV audio. Whisper needs at least 1-2 seconds of speech.
