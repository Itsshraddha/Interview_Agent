# 🎯 Interview Trainer Agent

### AI-Powered Interview Preparation — RAG + IBM Granite + Flask

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![watsonx.ai](https://img.shields.io/badge/watsonx.ai-Granite-052FAD?style=for-the-badge)](https://www.ibm.com/watsonx)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorDB-6A5ACD?style=for-the-badge)](https://www.trychroma.com/)

---

## 🧠 Overview

**Interview Trainer Agent** is a Retrieval-Augmented Generation (RAG) system built on **watsonx.ai**
using the **IBM Granite / Llama** foundation model. Given a candidate's role, experience level, and
optionally their resume or job description, it retrieves relevant context from a **9-topic knowledge base**
and generates a complete, structured interview prep kit.

| 💻 8 Technical Qs | 🤝 5 Behavioral Qs | 💡 3 Tips Each | 📅 Study Roadmap | 💬 Ask-Them Questions |
|:---:|:---:|:---:|:---:|:---:|
| Difficulty-tagged, with code examples & follow-ups | STAR outlines + competency tags + red-flag warnings | Specific & actionable, not generic | Week 1 → Week 2 → Day-before | 4 smart, role-specific questions |

---

## 📂 Project Structure

```
Interview_Agent/
├── app.py                      ← Flask application factory + routes
├── requirements.txt
├── Procfile                    ← For Render / Railway deployment
├── Dockerfile                  ← For Hugging Face Spaces (Docker)
├── .env.example
│
├── src/
│   ├── agent.py               ← End-to-end orchestration + JSON parsing
│   ├── prompt_templates.py    ← Upgraded v2 prompt (8+5 questions, roadmap)
│   ├── watsonx_client.py      ← IBM credentials + model clients
│   ├── retriever.py           ← ChromaDB similarity search
│   ├── resume_parser.py       ← PDF/TXT extraction + LLM summarization
│   └── ingest.py              ← KB chunking, embedding, Chroma persistence
│
├── templates/
│   ├── base.html              ← Navbar, dark mode toggle, footer
│   └── index.html             ← Landing page + form + results (JS-rendered)
│
├── static/
│   ├── css/style.css          ← Full design system (light + dark theme)
│   └── js/app.js              ← Fetch submit, loading, accordion, tabs, TTS
│
└── data/sample_kb/            ← 9 knowledge base files
    ├── software_engineer.txt
    ├── data_analyst.txt
    ├── hr_behavioral.txt
    ├── general_interview_tips.txt
    ├── product_manager.txt    ← NEW
    ├── devops_engineer.txt    ← NEW
    ├── ml_engineer.txt        ← NEW
    ├── system_design_deep.txt ← NEW
    └── career_negotiation.txt ← NEW
```

---

## ✅ Prerequisites

- Python 3.11+
- IBM Cloud account with watsonx.ai access
- **Environment variables** (copy `.env.example` → `.env`):

```env
IBM_API_Key=your_ibm_api_key
IBM_Watsonx_Project_ID=your_project_id
Watsonx_URL=https://us-south.ml.cloud.ibm.com
FLASK_SECRET_KEY=your-random-secret-key
```

---

## 🚀 Local Setup & Run

```bash
# 1. Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 2. Install dependencies (Flask, watsonx.ai, ChromaDB — no Streamlit)
pip install -r requirements.txt

# 3. Configure credentials
cp .env.example .env
# Edit .env with your IBM Cloud credentials

# 4. Build the vector store (one-time, re-run after adding KB files)
python src/ingest.py

# 5. Run the Flask app
python app.py
# Open http://localhost:5000
```

**With Gunicorn (production-like locally):**
```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 1 --timeout 120
```

---

## 🌐 Free Deployment Guide

### Option 1 — Hugging Face Spaces (Docker) ✅ Recommended

**Best for:** AI/ML demos · Always-on (no cold starts) · 16 GB RAM · Free

1. Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space)
2. Select **Docker** as the SDK
3. Push your project to the Space repo:
   ```bash
   git remote add hf-spaces https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   git push hf-spaces main
   ```
4. Add secrets in **Settings → Repository Secrets**:
   - `IBM_API_Key`
   - `IBM_Watsonx_Project_ID`
   - `Watsonx_URL`
   - `FLASK_SECRET_KEY`
5. The Dockerfile handles everything — HF builds and deploys automatically.
6. Your app is live at: `https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space`

> **Tip:** Commit the `db/` folder using Git LFS to avoid rebuilding the vector store on every deploy:
> ```bash
> git lfs install
> git lfs track "db/**"
> git add .gitattributes db/
> git commit -m "add: chromadb index"
> ```

---

### Option 2 — Render.com

**Best for:** Quick demos · Auto HTTPS · Simple GitHub integration · Free tier

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repository
3. Set **Build Command:**
   ```
   pip install -r requirements.txt && python src/ingest.py
   ```
4. Set **Start Command:**
   ```
   gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
   ```
5. Add **Environment Variables** (same 4 keys as above)
6. Deploy — your app gets a free `*.onrender.com` HTTPS URL

> **Note:** Free tier sleeps after 15 min idle (cold start ~20s). Upgrade to paid for always-on.

---

### Option 3 — Railway.app

**Best for:** Fast deploys · $5/month free credit · Persistent disk

1. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
2. Railway auto-detects Python and uses the `Procfile`
3. Add environment variables in the Railway dashboard
4. The `$5/month` free credit covers ~500 hours

---

### Deployment Comparison

| Platform | Cold Start | Always On | Free Tier | Best For |
|---|---|---|---|---|
| HF Spaces (Docker) | None | ✅ | ✅ 16GB RAM | AI demos, public showcase |
| Render | ~20s | ❌ | ✅ 512MB | Quick prototypes |
| Railway | ~5s | ✅ | $5 credit | MVPs, side projects |

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

---

## 🔄 Rebuilding the Knowledge Base

After adding new `.txt` files to `data/sample_kb/`, always re-run:

```bash
python src/ingest.py
```

This drops and rebuilds the ChromaDB vector store from all 9 knowledge base files.

---

Made with ❤️ using **watsonx.ai**, **IBM Granite**, **ChromaDB**, and **Flask**
