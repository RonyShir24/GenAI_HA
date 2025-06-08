# Medical Services ChatBot

This repository contains a pipeline for a two-phase chatbot for medical services:
1. **Information Collection** – gather basic user details (e.g name, HMO, tier).  
2. **Q&A** – answer user questions using a parsed HTML knowledge base and precomputed embeddings.

---
## Project Structure

```
Phase2/
├── parsed_hmo_data.json  # parsed HMO info 
├── embeddings.pkl        # precomputed OpenAI embeddings
├── phase2_data/          # raw HTML files (knowledge base)
├── ParseHTML.py          # script to parse HTML → JSON
├── ActivatePlatform.py   # Main UI script
├── FastAPI.py            # main FastAPI application
├── FastAPI_HelpFunction.py  # helper functions for the API
└── logs/                 # runtime log files
```

- **parsed_hmo_data.json** – Contains the structured HMO information extracted from the raw HTML files, ready for embedding and retrieval.  
- **embeddings.pkl** – Stores precomputed OpenAI embedding vectors for all parsed documents to enable fast similarity searches.  
- **phase2_data/** – Holds the original HTML files that serve as the knowledge base for the chatbot’s Q&A phase.  
- **ParseHTML.py** – A script that reads the raw HTML in `phase2_data/` and converts it into clean, structured JSON.  
- **ActivatePlatform.py** – The main UI script that orchestrates data loading, embedding creation, and platform startup.  
- **FastAPI.py** – Defines the FastAPI application with endpoints for both information collection and Q&A interactions.  
- **FastAPI_HelpFunction.py** – Provides helper functions for request handling, context management, and embedding lookup.  
- **logs/** – Directory where runtime log files are written to track chatbot activity and errors.  


---

## Prerequisites


1. Install the **required dependencies** from repository root folder:
    ```bash
    pip install -r requirements.txt
    ```
2. **Environment variables** - Fill the .env file with all the key and relevnt information. Can be found at from repository root folder.

---

## Installation

```bash
git clone <repository-url>
cd Phase2

# Create & activate a virtual environment
python -m venv .venv
source .venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt
```

---


## Regenerating Parsing & Embeddings

> **Note:** Preparsed data (`parsed_hmo_data.json`) and precomputed embeddings (`embeddings.pkl`) are already exsists in the project folder. 
You can recreate them anytime.

1. **Parse the raw HTML**  
   ```bash
   python ParseHTML.py
   ```
   - Reads all `.html` files under `Phase2\phase2_data`  
   - Produces `parsed_hmo_data.json`

2. **Build new embeddings**  
   ```bash
   python FastAPI.py
   ```
   - Load `parsed_hmo_data.json`  
   - Produces `embeddings.pkl`

---

## Running the API (Multi-User)

The FastAPI application is defined in `FastAPI.py` (with helpers in `FastAPI_HelpFunction.py`).

Run the backend side:
   ```bash
   python FastAPI.py
   ```

Run the UI:
   ```bash
streamlit run \ActivatePlatform.py
```
---


## Usage Flow

1. **Phase 1**  
   - Bot collects personal data from the user and manage all user session data and conversation history in client-side:
      - First and last name
      - ID number (valid 9-digit number)
      - Gender
      - Age (between 0 and 120)
      - HMO name (מכבי | מאוחדת | כללית)
      - HMO card number (9-digit)
      - Insurance membership tier (זהב | כסף | ארד)
      - Provide a confirmation step for users to review and correct their information.

2. **Phase 2**  
   - User asks medical-service questions  


