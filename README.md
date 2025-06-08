# Document Intelligence & Medical Services ChatBot

This repository contains two unrelated phases of the home assigment:
1. **Phase 1** – Extraction of structured data from documents using Document Intelligence and LLM model.  
2. **Phase 2** – Medical Services Chatbot with both user data collection step and a Q&A step.

---
## Directory Structure

```
GENAI_HA/
├── Phase1/
│   ├── phase1_data/
│   ├── ActivatePlatform.py
│   ├── Phase1.py
├── Phase2/
│   ├── parsed_hmo_data.json
│   ├── embeddings.pkl
│   ├── phase2_data/
│   ├── ParseHTML.py
│   ├── ActivatePlatform.py
│   ├── FastAPI.py
│   ├── FastAPI_HelpFunction.py
│   └── logs/
└── README.md  # (This file)
└── requirements.txt
└──.env.example
```

## Phase 1: Document Intelligence Extraction

- **Goal**: Parse and extract fields from various document formats (e.g., JPG, PDFs) into structured JSON.  
- **Key Scripts**:
  - `ActivatePlatform.py` – launches the UI and serve as main script.  
  - `Phase1.py` - backend functions (analysis and metrics)
  
- **Data**:
  - `phase1_data/` – Raw documents for extraction.  

---

## Phase 2: Medical Services ChatBot

- **Goal**: A two-phase chatbot:
  1. **Information Collection** – Gather user details (e.g name, HMO, tier).  
  2. **Q&A** – Answer medical service queries using HTML knowledge base and embeddings.
     
- **Key Files**:  
  - `parsed_hmo_data.json` – Parsed HMO information.  
  - `embeddings.pkl` – Precomputed embeddings for retrieval.  
  - `phase2_data/` – Raw HTML knowledge base.  
  - `ParseHTML.py` – Parses HTML files to JSON.  
  - `ActivatePlatform.py` – launches the UI ans main pipline script.  
  - `FastAPI.py` – FastAPI application with endpoints.  
  - `FastAPI_HelpFunction.py` – Helper functions for request handling.  
  - `logs/` – Runtime log files.  

---

## Prerequisites

Both files are shared between the two assignments.
  - `.env.example` – Template for environment variables.  Copy the file and fill all relevent fields. 
  - `requirements.txt` – Python dependencies.

  - An Azure credentials

---

## Setup & Installation

```bash
# Clone the repository
git clone <your-repo-url> 
cd project-root

# Phase 1 setup
cd Phase1
python -m venv .venv
source .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env

# Phase 2 setup
cd Phase2
python -m venv .venv
source .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

---

## Running Each Phase

### Phase 1

```bash
cd Phase1
streamlit run \ActivatePlatform.py
```
---

### Phase 2

```bash
cd Phase1
python FastAPI.py                     
streamlit run \ActivatePlatform.py 
```

