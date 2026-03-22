"""
╔══════════════════════════════════════════════════════════════╗
║        HR RECRUITING AGENT — VOICE ENABLED MVP DEMO          ║
║        Groq (LLM) + Whisper (STT) + gTTS (TTS)              ║
╚══════════════════════════════════════════════════════════════╝

API KEYS NEEDED (see .env file):
─────────────────────────────────────────────────────────────
  SERVICE          KEY NAME          WHERE TO GET
  ─────────────────────────────────────────────────────────
  LLM (Groq)   →  GROQ_API_KEY   →  https://console.groq.com
─────────────────────────────────────────────────────────────
  NOTE: No other paid API keys needed.
  Whisper runs locally (free). gTTS uses Google TTS (free).

RESUME FOLDER:
──────────────
  Put all candidate PDF resumes inside:  sample_resumes/
  The app auto-detects every PDF in that folder.
  Naming tip: use candidate names as filenames.
  Example:  sample_resumes/john_doe.pdf
            sample_resumes/jane_smith.pdf
"""

import streamlit as st
import os
import json
import re
import time
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import PyPDF2
from groq import Groq
from gtts import gTTS
import io

# ── Load .env ────────────────────────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# 🔑  API KEY CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
#
#  The app reads GROQ_API_KEY in this priority order:
#
#    1. Streamlit Cloud secrets  →  for deployment on streamlit.io
#    2. .env file                →  for local development
#    3. Sidebar input field      →  fallback manual entry in the UI
#
# ─────────────────────────────────────────────────────────────────────────────

def get_groq_key() -> str:
    try:
        return st.secrets["GROQ_API_KEY"]          # Streamlit Cloud
    except Exception:
        pass
    key = os.getenv("GROQ_API_KEY")                # .env file
    if key:
        return key
    return st.session_state.get("manual_groq_key", "")  # sidebar


# ─────────────────────────────────────────────────────────────────────────────
# 📁  RESUME FOLDER PATH
# ─────────────────────────────────────────────────────────────────────────────
#
#  Place all candidate PDFs inside this folder.
#  Path is relative to where you run:  streamlit run app.py
#
#  Example structure:
#    hr_voice_mvp/
#    ├── app.py
#    ├── sample_resumes/       ← PUT RESUMES HERE
#    │   ├── john_doe.pdf
#    │   └── jane_smith.pdf
#    └── .env
#
RESUME_FOLDER = Path("sample_resumes")


# ─────────────────────────────────────────────────────────────────────────────
# 🎨  PAGE CONFIG & CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HR Voice Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

section[data-testid="stSidebar"] {
    background: #080F1A;
    border-right: 1px solid #0F2337;
}
section[data-testid="stSidebar"] * { color: #94A3B8 !important; }
section[data-testid="stSidebar"] .stTextArea textarea {
    background: #0D1B2E !important;
    border: 1px solid #1E3A5F !important;
    color: #E2E8F0 !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}
section[data-testid="stSidebar"] .stTextInput input {
    background: #0D1B2E !important;
    border: 1px solid #1E3A5F !important;
    color: #E2E8F0 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] label {
    font-size: 0.7rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    color: #475569 !important;
    font-weight: 700 !important;
}
.main .block-container { padding-top: 1.8rem; max-width: 1100px; }

.hero { margin-bottom: 24px; }
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: #080F1A;
    letter-spacing: -1.5px;
    line-height: 1.1;
}
.hero-teal { color: #00897B; }
.hero-sub { font-size: 0.9rem; color: #64748B; margin-top: 4px; }

.voice-box {
    background: #080F1A;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 20px;
    border: 1px solid #0F2337;
}
.voice-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #00897B;
    margin-bottom: 10px;
}
.transcript-box {
    background: #0D1B2E;
    border: 1px solid #1E3A5F;
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 0.92rem;
    color: #94A3B8;
    min-height: 60px;
    font-style: italic;
    margin-top: 10px;
}
.agent-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.rank-badge {
    background: #080F1A;
    color: white;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding: 2px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 8px;
    font-family: 'Syne', sans-serif;
}
.cand-name {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #080F1A;
}
.score-num {
    font-family: 'Syne', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    line-height: 1;
}
.s-high { color: #059669; }
.s-mid  { color: #D97706; }
.s-low  { color: #DC2626; }
.tag { display:inline-block; background:#F1F5F9; color:#475569; font-size:0.72rem; padding:2px 9px; border-radius:20px; margin:2px 3px 2px 0; }
.tag-r { background:#FEE2E2; color:#991B1B; }
.tag-g { background:#D1FAE5; color:#065F46; }
.lbl { font-size:0.65rem; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; color:#94A3B8; margin:10px 0 4px 0; }
.verdict { font-size:0.87rem; color:#475569; line-height:1.65; }
.stButton > button {
    background: #080F1A !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    padding: 10px 20px !important; width: 100% !important;
}
.stButton > button:hover { background: #00897B !important; }
.pipeline {
    display: flex; align-items: center; gap: 6px;
    margin: 16px 0 24px 0; flex-wrap: wrap;
}
.pnode {
    background: #F1F5F9; color: #475569;
    font-size: 0.72rem; font-weight: 700;
    padding: 5px 12px; border-radius: 20px;
    font-family: 'Syne', sans-serif;
    letter-spacing: 0.5px;
}
.pnode.active { background: #00897B; color: white; }
.parr { color: #CBD5E1; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 🔧  UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def read_pdf(path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        return f"[PDF parse error: {e}]"


def load_resumes() -> list[dict]:
    """
    Load all PDFs from RESUME_FOLDER.
    Each dict has: name, filename, text
    """
    if not RESUME_FOLDER.exists():
        return []
    resumes = []
    for pdf in sorted(RESUME_FOLDER.glob("*.pdf")):
        name = pdf.stem.replace("_", " ").replace("-", " ").title()
        resumes.append({
            "name": name,
            "filename": pdf.name,
            "text": read_pdf(pdf)
        })
    return resumes


def safe_json(raw: str) -> dict:
    """Strip markdown fences and parse JSON safely."""
    clean = re.sub(r"^```(?:json)?", "", raw.strip()).strip()
    clean = re.sub(r"```$", "", clean).strip()
    try:
        return json.loads(clean)
    except Exception:
        return {}


def llm(api_key: str, prompt: str, max_tokens: int = 700) -> str:
    """
    ╔════════════════════════════════════════════╗
    ║  LLM  →  Groq API                          ║
    ║  KEY  →  GROQ_API_KEY  (set in .env)        ║
    ║  MODEL→  llama-3.3-70b-versatile            ║
    ╚════════════════════════════════════════════╝
    """
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def transcribe_audio(api_key: str, audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    ╔════════════════════════════════════════════╗
    ║  SPEECH-TO-TEXT  →  Groq Whisper           ║
    ║  KEY  →  GROQ_API_KEY  (same key as LLM)   ║
    ║  MODEL→  whisper-large-v3-turbo             ║
    ║  COST →  FREE within Groq free tier         ║
    ╚════════════════════════════════════════════╝
    """
    client = Groq(api_key=api_key)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=(filename, f, "audio/wav"),
                language="en"
            )
        return result.text.strip()
    finally:
        os.unlink(tmp_path)


def text_to_speech(text: str) -> bytes:
    """
    ╔════════════════════════════════════════════╗
    ║  TEXT-TO-SPEECH  →  gTTS (Google TTS)      ║
    ║  KEY  →  NO API KEY NEEDED — 100% FREE     ║
    ║  NOTE →  Requires internet connection       ║
    ╚════════════════════════════════════════════╝
    """
    tts = gTTS(text=text[:500], lang="en", slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()


def score_cls(s: int) -> str:
    return "s-high" if s >= 70 else ("s-mid" if s >= 45 else "s-low")


def tags(items: list, cls: str = "") -> str:
    if not items:
        return '<span style="color:#94A3B8;font-size:0.8rem;">—</span>'
    return " ".join(f'<span class="tag {cls}">{i}</span>' for i in items[:8])


# ─────────────────────────────────────────────────────────────────────────────
# 🤖  4-AGENT PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def agent1_jd(api_key: str, jd: str) -> dict:
    """Agent 1 — JD Analyzer: extracts key requirements from JD."""
    prompt = f"""You are an expert HR analyst. Extract requirements from this job description.
Return ONLY valid JSON — no markdown, no extra text.

JD:
{jd[:2500]}

JSON schema:
{{
  "role_title": "...",
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill1"],
  "min_experience_years": <number or null>,
  "must_have": ["requirement 1", "requirement 2"]
}}"""
    return safe_json(llm(api_key, prompt, 500)) or {"role_title": "Role", "required_skills": [], "must_have": []}


def agent2_resume(api_key: str, text: str, name: str) -> dict:
    """Agent 2 — Resume Parser: extracts structured candidate profile."""
    prompt = f"""You are a resume parser. Extract candidate information.
Return ONLY valid JSON — no markdown, no extra text.

RESUME ({name}):
{text[:3000]}

JSON schema:
{{
  "candidate_name": "...",
  "total_experience_years": <number or null>,
  "current_role": "...",
  "skills": ["skill1", "skill2"],
  "education": ["degree1"],
  "certifications": []
}}"""
    result = safe_json(llm(api_key, prompt, 500))
    if not result.get("candidate_name"):
        result["candidate_name"] = name
    return result


def agent3_redflag(api_key: str, text: str, profile: dict) -> dict:
    """Agent 3 — RedFlag Detector: finds risks and positives."""
    prompt = f"""You are a critical HR risk analyst. Find red flags in this resume.
Return ONLY valid JSON — no markdown, no extra text.

PROFILE:
{json.dumps(profile, indent=2)[:1000]}

JSON schema:
{{
  "job_hopping": true/false,
  "employment_gaps": true/false,
  "red_flags": ["flag1", "flag2"],
  "positive_signals": ["signal1", "signal2"]
}}"""
    return safe_json(llm(api_key, prompt, 400)) or {"red_flags": [], "positive_signals": []}


def agent4_recruiter(api_key: str, jd: str, jd_req: dict, profile: dict, flags: dict) -> dict:
    """Agent 4 — Recruiter: final score, verdict, interview questions."""
    prompt = f"""You are a senior recruiter making a final hiring decision.
Return ONLY valid JSON — no markdown, no extra text.

JD REQUIREMENTS:
{json.dumps(jd_req, indent=2)[:800]}

CANDIDATE:
{json.dumps(profile, indent=2)[:800]}

RED FLAGS:
{json.dumps(flags, indent=2)[:400]}

JSON schema:
{{
  "score": <integer 0-100>,
  "match_level": "<Strong Match|Good Match|Partial Match|Weak Match>",
  "key_strengths": ["strength1", "strength2", "strength3"],
  "critical_gaps": ["gap1", "gap2"],
  "verdict": "<2-3 sentence hiring recommendation>",
  "interview_questions": ["q1", "q2", "q3"]
}}"""
    return safe_json(llm(api_key, prompt, 700)) or {"score": 0, "match_level": "Weak Match", "verdict": "Could not evaluate."}


def run_pipeline(api_key: str, jd: str, resumes: list[dict], progress_cb=None) -> list[dict]:
    """
    Run the full 4-agent pipeline across all resumes.
    Returns list of results sorted by score descending.
    """
    # Agent 1 runs once for the JD
    jd_req = agent1_jd(api_key, jd)

    results = []
    total = len(resumes)

    for i, r in enumerate(resumes):
        name = r["name"]
        if progress_cb:
            progress_cb(i, total, name)

        profile  = agent2_resume(api_key, r["text"], name)
        flags    = agent3_redflag(api_key, r["text"], profile)
        final    = agent4_recruiter(api_key, jd, jd_req, profile, flags)

        results.append({
            "name":       profile.get("candidate_name", name),
            "filename":   r["filename"],
            "profile":    profile,
            "flags":      flags,
            "final":      final,
            "jd_req":     jd_req,
        })

    results.sort(key=lambda x: x["final"].get("score", 0), reverse=True)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 🖼️  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 API Configuration")

    # ── GROQ API KEY ──────────────────────────────────────────────────────────
    # ╔════════════════════════════════════════════════════════╗
    # ║  GROQ_API_KEY                                          ║
    # ║  Used for: LLM (llama-3.3-70b) + Whisper STT          ║
    # ║  Get it:   https://console.groq.com                    ║
    # ║  Free tier: 14,400 req/day                             ║
    # ╚════════════════════════════════════════════════════════╝
    auto_key = get_groq_key()
    if auto_key:
        st.success("✅ Groq API key loaded")
    else:
        manual = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            help="Get your free key at console.groq.com"
        )
        st.session_state["manual_groq_key"] = manual

    st.divider()

    # ── RESUME STATUS ─────────────────────────────────────────────────────────
    st.markdown("### 📁 Resume Folder")
    resumes = load_resumes()
    if resumes:
        st.success(f"✅ {len(resumes)} resume(s) found")
        for r in resumes:
            st.markdown(f"- `{r['filename']}`")
    else:
        st.warning(
            f"No PDFs found in `{RESUME_FOLDER}/`\n\n"
            "Add candidate PDFs to the `sample_resumes/` folder and restart."
        )

    st.divider()

    # ── JD INPUT ──────────────────────────────────────────────────────────────
    st.markdown("### 📋 Job Description")
    jd_text = st.text_area(
        "Paste JD here",
        height=220,
        label_visibility="collapsed",
        placeholder="e.g. We are looking for a Senior Software Engineer with 5+ years Python experience..."
    )

    st.divider()

    # ── VOICE MODE TOGGLE ─────────────────────────────────────────────────────
    st.markdown("### 🎙️ Voice Mode")
    voice_enabled = st.toggle("Enable Voice Output", value=True)
    st.caption("When ON, agent will speak the top candidate summary aloud after screening.")

    st.divider()
    run_btn = st.button("🚀  Run Agent Pipeline")


# ─────────────────────────────────────────────────────────────────────────────
# 🖥️  MAIN AREA
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-title">HR <span class="hero-teal">Voice</span> Agent</div>
  <div class="hero-sub">4-Agent Pipeline · Groq llama-3.3-70b · Whisper STT · gTTS · Demo MVP</div>
</div>
""", unsafe_allow_html=True)

# ── Voice Input Section ───────────────────────────────────────────────────────
st.markdown("""
<div class="voice-box">
  <div class="voice-title">🎙️ Voice Input — Describe Your Ideal Candidate</div>
</div>
""", unsafe_allow_html=True)

col_voice, col_or, col_text = st.columns([3, 0.3, 3])

with col_voice:
    st.markdown("**Record your JD / requirements verbally:**")
    audio_input = st.audio_input("Speak now — describe the role and requirements")

    if audio_input is not None:
        groq_key = get_groq_key()
        if not groq_key:
            st.error("Enter your Groq API key in the sidebar first.")
        else:
            with st.spinner("Transcribing with Whisper..."):
                try:
                    transcript = transcribe_audio(groq_key, audio_input.read(), "recording.wav")
                    st.session_state["voice_transcript"] = transcript
                    st.success("✅ Transcription complete")
                except Exception as e:
                    st.error(f"Transcription failed: {e}")

    if st.session_state.get("voice_transcript"):
        st.markdown(f"""
        <div class="transcript-box">
        🗣️ <strong>Transcript:</strong><br>{st.session_state['voice_transcript']}
        </div>
        """, unsafe_allow_html=True)

        if st.button("📋 Use transcript as JD"):
            st.session_state["use_voice_as_jd"] = True
            st.rerun()

with col_or:
    st.markdown("<div style='text-align:center;color:#CBD5E1;padding-top:60px;font-size:1.2rem;'>or</div>", unsafe_allow_html=True)

with col_text:
    st.markdown("**Type your JD in the sidebar →**")
    st.markdown("""
    <div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
    padding:20px;color:#94A3B8;font-size:0.9rem;margin-top:8px;'>
    Paste your full job description in the sidebar text area.
    The agent will extract requirements and screen all resumes automatically.
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Pipeline Status ───────────────────────────────────────────────────────────
st.markdown("""
<div class="pipeline">
  <span class="pnode">📝 JD Analyzer</span>
  <span class="parr">→</span>
  <span class="pnode">👤 Resume Parser</span>
  <span class="parr">→</span>
  <span class="pnode">🚩 RedFlag Detector</span>
  <span class="parr">→</span>
  <span class="pnode">🎯 Recruiter Agent</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ▶️  RUN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
if run_btn:
    groq_key = get_groq_key()

    # Determine JD source (voice transcript or sidebar text)
    active_jd = jd_text.strip()
    if st.session_state.get("use_voice_as_jd") and st.session_state.get("voice_transcript"):
        active_jd = st.session_state["voice_transcript"]

    # Validations
    if not groq_key:
        st.error("❌ Enter your Groq API key in the sidebar.")
        st.stop()
    if not active_jd:
        st.error("❌ Provide a Job Description — either type it in the sidebar or record it via voice.")
        st.stop()
    if not resumes:
        st.error(f"❌ No resumes found in `{RESUME_FOLDER}/`. Add PDF files there first.")
        st.stop()

    # Progress tracking
    progress_bar = st.progress(0, text="Starting pipeline...")
    status_text  = st.empty()

    def update_progress(i, total, name):
        pct = int(((i + 1) / total) * 100)
        progress_bar.progress(pct / 100, text=f"Processing {name} ({i+1}/{total})...")
        status_text.markdown(f"**Agent 2 → 4** running on: `{name}`")

    try:
        # Step 1 — JD Analysis
        status_text.markdown("**Agent 1** — Analyzing Job Description...")
        progress_bar.progress(0.05, text="Agent 1: Analyzing JD...")

        # Full pipeline
        results = run_pipeline(groq_key, active_jd, resumes, update_progress)

        progress_bar.progress(1.0, text="✅ Pipeline complete!")
        status_text.empty()

        st.session_state["results"] = results
        st.session_state["active_jd"] = active_jd

        # ── Voice Output ──────────────────────────────────────────────────────
        if voice_enabled and results:
            top = results[0]
            score = top["final"].get("score", 0)
            name  = top["name"]
            match = top["final"].get("match_level", "")
            verdict = top["final"].get("verdict", "")

            voice_text = (
                f"Pipeline complete. {len(results)} candidates screened. "
                f"Top candidate is {name} with a score of {score} out of 100. "
                f"Match level: {match}. "
                f"{verdict}"
            )
            try:
                audio_bytes = text_to_speech(voice_text)
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                st.success("🔊 Voice summary playing...")
            except Exception:
                pass  # Silent fallback if TTS fails

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Pipeline error: {e}")
        st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 📊  RESULTS
# ─────────────────────────────────────────────────────────────────────────────
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]

    st.markdown(f"### 🏆 Ranked Results — {len(results)} Candidate{'s' if len(results) > 1 else ''}")

    for rank, r in enumerate(results, 1):
        f      = r["final"]
        score  = f.get("score", 0)
        sc     = score_cls(score)
        match  = f.get("match_level", "—")
        strengths = f.get("key_strengths", [])
        gaps   = f.get("critical_gaps", [])
        questions = f.get("interview_questions", [])
        verdict = f.get("verdict", "")
        flags   = r["flags"]

        st.markdown(f"""
        <div class="agent-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <div class="rank-badge">#{rank}</div>
              <div class="cand-name">{r['name']}</div>
              <div style="font-size:0.8rem;color:#64748B;margin-top:2px;">{match} · <code style="font-size:0.75rem;">{r['filename']}</code></div>
            </div>
            <div style="text-align:center;">
              <div class="score-num {sc}">{score}</div>
              <div style="font-size:0.72rem;color:#94A3B8;">/100</div>
            </div>
          </div>

          <div class="lbl">Key Strengths</div>
          <div>{tags(strengths, 'tag-g')}</div>

          <div class="lbl">Critical Gaps</div>
          <div>{tags(gaps, 'tag-r')}</div>

          <div class="lbl">Red Flags</div>
          <div>{tags(flags.get('red_flags', []), 'tag-r')}</div>

          <div class="lbl">Positive Signals</div>
          <div>{tags(flags.get('positive_signals', []))}</div>

          <div class="lbl">Recruiter Verdict</div>
          <div class="verdict">{verdict}</div>
        </div>
        """, unsafe_allow_html=True)

        # Voice button per candidate
        c1, c2 = st.columns([1, 5])
        with c1:
            if voice_enabled and st.button(f"🔊 Hear #{rank}", key=f"speak_{rank}"):
                speak_text = f"{r['name']}. Score {score} out of 100. {match}. {verdict}"
                try:
                    ab = text_to_speech(speak_text)
                    st.audio(ab, format="audio/mp3", autoplay=True)
                except Exception:
                    st.warning("TTS unavailable")
        with c2:
            with st.expander(f"💬 Interview Questions for {r['name']}"):
                for q in questions:
                    st.markdown(f"- {q}")

    # Summary scorecard
    st.markdown("---")
    st.markdown("### 📊 Scorecard Summary")
    st.dataframe(
        {
            "Rank":        list(range(1, len(results) + 1)),
            "Candidate":   [r["name"] for r in results],
            "Score":       [r["final"].get("score", 0) for r in results],
            "Match Level": [r["final"].get("match_level", "—") for r in results],
            "File":        [r["filename"] for r in results],
        },
        use_container_width=True,
        hide_index=True,
    )

else:
    # Empty state
    if not run_btn:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
          <div style="font-size:3rem;margin-bottom:16px;">🎙️</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#334155;margin-bottom:8px;">
            Voice-Enabled HR Recruiting Agent
          </div>
          <div style="font-size:0.9rem;color:#94A3B8;">
            1. Add resume PDFs to <code>sample_resumes/</code><br>
            2. Paste or speak your JD<br>
            3. Click Run — agent screens all candidates automatically
          </div>
        </div>
        """, unsafe_allow_html=True)
