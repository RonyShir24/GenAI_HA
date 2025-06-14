# Medical Services ChatBot

This repository contains a pipeline for a two-phase microservice-based chatbot for medical services:
1. **Information Collection** – gather basic user details (e.g name, HMO, tier).  
2. **Q&A** – answer user questions using a parsed HTML knowledge base and precomputed embeddings.

---
## Project Structure

```
Phase2/
├── parsed_hmo_data.json  # parsed HMO info 
├── embeddings.pkl        # precomputed OpenAI embeddings
├── ParseHTML.py          # script to parse HTML → JSON
├── ActivatePlatform.py   # Main UI script
├── FastAPI.py            # main FastAPI application
├── FastAPI_HelpFunction.py  # helper functions for the API
└── logs/                 # runtime log files
```

- **parsed_hmo_data.json** – Contains the structured HMO information extracted from the raw HTML files, ready for embedding and retrieval.  
- **embeddings.pkl** – Stores precomputed OpenAI embedding for all parsed documents to enable fast similarity searches.  
- **ParseHTML.py** – A script that reads the raw HTML in `phase2_data/` and converts it into clean, structured JSON.  
- **ActivatePlatform.py** – The main UI script that hold platform startup.  
- **FastAPI.py** – Defines the FastAPI application with endpoints for both information collection and Q&A interactions.  
- **FastAPI_HelpFunction.py** – Provides helper functions for request handling. 
- **logs/** – Directory where runtime log files are written to track chatbot activity and errors.  


---

## Prerequisites


1. Install the **required dependencies** from repository root folder:
    ```bash
    pip install -r requirements.txt
    ```

    #### Installation

   ```bash
   git clone <repository-url>
   python -m venv .venv
   .venv\Scripts\activate 
   pip install -r requirements.txt
   ```

2. **Environment variables** - Fill the .env file with all the key and relevnt information. Can be found at the repository root folder.

---




## Regenerating Parsing & Embeddings

> **Note:** Preparsed data (`parsed_hmo_data.json`) and precomputed embeddings (`embeddings.pkl`) are already exsists in the project folder. 
You can recreate them anytime.

1. **Parse the raw HTML**  
   ```bash
   cd Phase2
   python ParseHTML.py
   ```
   - Reads all `.html` files under `Phase2\phase2_data`  
   - Produces `parsed_hmo_data.json`

2. **Build new embeddings**  
   ```bash
   cd Phase2
   python FastAPI.py
   ```
   - Load `parsed_hmo_data.json`  
   - Produces `embeddings.pkl`

---

## Running the API (Multi-User)

The FastAPI application is defined in `FastAPI.py` (with helpers in `FastAPI_HelpFunction.py`).

Run the backend side:
   ```bash
    cd Phase2
   python FastAPI.py
   ```

Run the UI:
   ```bash
cd Phase2
streamlit run ActivatePlatform.py
```
---


## Usage Flow

all user session data and conversation history in manage in the client-side

1. **Phase 1**  
   - Bot collects personal data from the user:
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


