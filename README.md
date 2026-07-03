<div align="center">

# 🎯 Interview Trainer Agent

### AI-Powered Interview Preparation, Personalized by RAG + Granite

![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=20&pause=1000&color=2E9EF7&center=true&vCenter=true&width=600&lines=Tailored+Technical+Questions;Behavioral+STAR+Answers;Resume-Aware+Prep+Kits;Powered+by+watsonx.ai)

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![watsonx.ai](https://img.shields.io/badge/watsonx.ai-Granite-052FAD?style=for-the-badge)](https://www.ibm.com/watsonx)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorDB-6A5ACD?style=for-the-badge)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-brightgreen?style=for-the-badge)](#-license)

<img src="https://user-images.githubusercontent.com/74038190/212284100-561aa473-3905-4a80-b561-0d28506553ee.gif" width="500">

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Data Flow](#-data-flow)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Setup & Run](#-setup--run)
- [Running Tests](#-running-tests)
- [License](#-license)

---

## 🧠 Overview

**Interview Trainer Agent** is a Retrieval-Augmented Generation (RAG) system built on **watsonx.ai** using the **Granite** foundation model family. Given a candidate's role, experience level, and (optionally) their resume or a target job description, it retrieves relevant context from a curated local knowledge base and generates a complete, structured interview prep kit — technical questions, behavioral STAR-format questions, model answers, and personalized improvement tips.

<div align="center">

| 🎓 Role-Aware | 📄 Resume-Aware | 🧩 RAG-Grounded | ⚡ Granite-Powered |
|:---:|:---:|:---:|:---:|
| Adapts to job role & seniority | Parses uploaded resume/JD PDFs | Retrieves from local ChromaDB | Uses `granite-3-3-8b-instruct` |

</div>

---

## 🏗 System Architecture

```mermaid
flowchart TB
    subgraph UI["🖥️ Streamlit UI — app.py"]
        A1[Name / Role / Experience Input]
        A2[Resume or JD PDF Upload]
    end

    subgraph ORCH["⚙️ Orchestrator — agent.py"]
        B1[1️⃣ resume_parser.py<br/>Extract & summarize PDF text]
        B2[2️⃣ retriever.py<br/>Query ChromaDB top-k chunks]
        B3[3️⃣ prompt_templates.py<br/>Build structured Granite prompt]
        B4[4️⃣ watsonx_client.py<br/>Call Granite via ModelInference]
        B5[5️⃣ Parse JSON response<br/>Return structured prep kit]
    end

    subgraph STORE["🗄️ Vector Store"]
        C1[(ChromaDB<br/>./db/)]
    end

    subgraph WX["☁️ watsonx.ai"]
        D1[["granite-3-3-8b-instruct<br/>(Generation)"]]
        D2[["slate-125m-english-rtrvr<br/>(Embeddings)"]]
    end

    subgraph INGEST["📥 One-Time Setup"]
        E1[ingest.py]
        E2[data/sample_kb/*.txt]
    end

    A1 --> B1
    A2 --> B1
    B1 --> B2
    B2 <--> C1
    B2 --> B3
    B3 --> B4
    B4 <--> D1
    C1 <--> D2
    B4 --> B5
    B5 --> UI

    E2 --> E1
    E1 -->|chunk → embed → persist| C1
    E1 <--> D2

    style UI fill:#FF4B4B,color:#fff
    style ORCH fill:#2E9EF7,color:#fff
    style STORE fill:#6A5ACD,color:#fff
    style WX fill:#052FAD,color:#fff
    style INGEST fill:#2c9c56,color:#fff
```

---

## 🔄 Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor U as 👤 User
    participant UI as Streamlit UI
    participant RP as resume_parser.py
    participant RT as retriever.py
    participant DB as ChromaDB
    participant PT as prompt_templates.py
    participant WX as watsonx.ai (Granite)
    participant AG as agent.py

    U->>UI: Enter name, role, experience
    U->>UI: (Optional) Upload resume/JD PDF
    UI->>AG: Submit profile + PDF
    AG->>RP: Extract & summarize PDF
    RP-->>AG: Resume summary text
    AG->>RT: Query relevant KB chunks
    RT->>DB: Similarity search (top-k)
    DB-->>RT: Matched text chunks
    RT-->>AG: Retrieved context
    AG->>PT: Build structured prompt
    PT-->>AG: Final Granite prompt
    AG->>WX: Send prompt via ModelInference
    WX-->>AG: JSON prep-kit response
    AG->>AG: Parse & validate JSON
    AG-->>UI: Structured prep kit
    UI-->>U: 📋 Questions, STAR answers, tips
```



---

## 📂 Project Structure

```
Interview_Agent/
│
├── 📄 README.md
├── 📄 requirements.txt
├── 📄 .env.example
│
├── 📁 data/
│   └── 📁 sample_kb/
│       ├── 📝 software_engineer.txt
│       ├── 📝 data_analyst.txt
│       ├── 📝 hr_behavioral.txt
│       └── 📝 general_interview_tips.txt
│
├── 📁 src/
│   ├── 🐍 __init__.py
│   ├── 🔑 watsonx_client.py     # watsonx.ai credential setup
│   ├── 📥 ingest.py             # KB chunking, embedding, Chroma persistence
│   ├── 🔍 retriever.py          # Chroma query wrapper
│   ├── 📄 resume_parser.py      # PDF text extraction + LLM summarization
│   ├── ✍️ prompt_templates.py   # Structured Granite prompt w/ few-shot example
│   └── 🧠 agent.py              # End-to-end orchestration + JSON parsing
│
├── 🖥️ app.py                    # Streamlit frontend
│
└── 📁 tests/
    ├── 🐍 __init__.py
    └── ✅ test_ingest.py
```

---

## ✅ Prerequisites

- 🐍 Python 3.11+
- 📦 `pip` (or a virtual environment manager)
- 🔑 watsonx.ai API key, Project ID, and endpoint URL (add these to `.env`)

---

## 🚀 Setup & Run

### 1️⃣ Clone / unzip the project

```bash
cd Interview_Agent
```

### 2️⃣ Create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your watsonx.ai credentials
```

### 5️⃣ Build the vector store (one-time)

```bash
python src/ingest.py
```

This reads all `.txt` files in `data/sample_kb/`, chunks them, embeds them using the Slate embedding model, and persists the Chroma vector store to `./db`.

### 6️⃣ Run the Streamlit app

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501** 🎉

<div align="center">
<img src="https://user-images.githubusercontent.com/74038190/213910845-af37a709-8995-40d6-be59-724526e3c3d7.gif" width="450">
</div>

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

---


<div align="center">

---

Made with ❤️ using **watsonx.ai**, **Granite**, and **Streamlit**

![Visitor Count](https://komarev.com/ghpvc/?username=interview-trainer-agent&label=Project%20Views&color=2E9EF7&style=for-the-badge)

</div>
