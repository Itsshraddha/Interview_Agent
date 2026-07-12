<div align="center">

# 🎯 Interview Trainer Agent

### AI-Powered Interview Preparation — RAG + IBM Granite + Flask

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![watsonx.ai](https://img.shields.io/badge/watsonx.ai-Granite-052FAD?style=for-the-badge)](https://www.ibm.com/watsonx)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorDB-6A5ACD?style=for-the-badge)](https://www.trychroma.com/)

### 🔗 [**Live Demo**](https://interview-agent-wirm.onrender.com/)

> Hosted on Render's free tier — the app may take ~30–60 seconds to wake up on first load if it's been idle.

</div>

---

## 🧠 Overview

**Interview Trainer Agent** is a Retrieval-Augmented Generation (RAG) system built on **IBM watsonx.ai** using the **Granite** foundation model. Given a candidate's role, experience level, and optionally their resume or job description, it retrieves relevant context from a curated knowledge base and generates a complete, structured interview prep kit.

| 💻 8 Technical Qs | 🤝 5 Behavioral Qs | 💡 3 Tips Each | 📅 Study Roadmap | 💬 Ask-Them Questions |
|:---:|:---:|:---:|:---:|:---:|
| Difficulty-tagged, with code examples & follow-ups | STAR outlines + competency tags | Specific & actionable | Week 1 → Week 2 → Day-before | 4 smart, role-specific questions |

---

## 🏗 System Architecture

```mermaid
flowchart TB
    U["👤 User<br/>Role, experience, resume/JD"] --> APP

    subgraph APP["Flask App — app.py"]
        R["resume_parser.py<br/>Extract & summarize"]
        RT["retriever.py<br/>Query ChromaDB top-k"]
        PT["prompt_templates.py<br/>Build structured prompt"]
        WC["watsonx_client.py<br/>Call Granite"]
        R --> RT --> PT --> WC
    end

    RT <--> VDB[("ChromaDB<br/>Vector Store")]
    WC <--> GR[["IBM Granite<br/>(watsonx.ai)"]]
    VDB <--> GR

    KB["📄 Knowledge Base<br/>data/sample_kb/*.txt"] -->|ingest.py: chunk → embed → persist| VDB

    WC --> OUT["📋 Prep Kit<br/>Technical + Behavioral Qs,<br/>Tips, Roadmap"]
    OUT --> U

    style U fill:#FF4B4B,color:#fff
    style APP fill:#2E9EF7,color:#fff
    style VDB fill:#6A5ACD,color:#fff
    style GR fill:#052FAD,color:#fff
    style KB fill:#2c9c56,color:#fff
```

---

## 📸 Screenshots

<table>
<tr>
<td width="50%">

**Landing Page**
![Landing page](screenshots/06_landing_page.png)

</td>
<td width="50%">

**Target Role Selection**
![Target role selection](screenshots/01_target_role_selection.png)

</td>
</tr>
<tr>
<td width="50%">

**Technical Questions**
![Technical questions](screenshots/04_technical_questions.png)

</td>
<td width="50%">

**Behavioral / HR — STAR Format**
![Behavioral STAR format](screenshots/03_behavioral_star_format.png)

</td>
</tr>
<tr>
<td width="50%">

**Prep Kit Overview**
![Prep kit overview](screenshots/05_prep_kit_overview.png)

</td>
<td width="50%">

**Confidence Checklist**
![Confidence checklist](screenshots/02_confidence_checklist.png)

</td>
</tr>
</table>

---

## 📂 Project Structure

```
Interview_Agent/
├── app.py                  ← Flask application + routes
├── requirements.txt
├── Dockerfile               ← Used for Render deployment
├── .env.example
│
├── src/
│   ├── agent.py            ← Orchestration + JSON parsing
│   ├── prompt_templates.py ← Structured Granite prompt
│   ├── watsonx_client.py   ← IBM credentials + model clients
│   ├── retriever.py        ← ChromaDB similarity search
│   ├── resume_parser.py    ← PDF/TXT extraction + summarization
│   └── ingest.py           ← KB chunking, embedding, persistence
│
├── templates/               ← HTML (base + landing/results page)
├── static/                  ← CSS + JS (theme, form, accordion)
│
└── data/sample_kb/          ← Knowledge base (.txt per role/topic)
```

---

## ✅ Prerequisites

- Python 3.11+
- IBM Cloud account with watsonx.ai access
- Environment variables (copy `.env.example` → `.env`):

```env
IBM_API_Key=your_ibm_api_key
IBM_Watsonx_Project_ID=your_project_id
Watsonx_URL=https://us-south.ml.cloud.ibm.com
FLASK_SECRET_KEY=your-random-secret-key
```

---

## 🚀 Run Locally

```bash
python -m venv venv && venv\Scripts\activate   # (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env        # then fill in your IBM credentials
python src/ingest.py        # one-time: build the vector store
python app.py                # open http://localhost:5000
```

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

---

<div align="center">

Made with ❤️ using **watsonx.ai**, **IBM Granite**, **ChromaDB**, and **Flask**

</div>