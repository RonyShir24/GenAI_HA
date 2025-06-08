# Home Assignment - Phase 1

## Overview
This repository contains a pipeline for extracting information from ביטוח לאומי (National Insurance Institute) forms using OCR and Azure OpenAI.
It computes **accuracy** and **completeness** metrics to evaluate extraction quality.


## Project Structure
```bash
./
├── phase1_data/                # Sample for Phase 1
├── ActivatePlatform.py         # Streamlit application and main pipeline (main UI)
├── Phase1.py                   # Backend functions (analysis and metrics)
└── README.md                   # Project documentation (this file)
```


## Prerequisites    
1. Install the **required dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2. **Environment variables** - Fill the .env file with all the key and relevnt information.


## Getting Started
To get started with the project, follow the next steps:

1. **Clone** the repository:
    ```bash
    git clone <repository-url>
    ```

2. Navigate to the project directory:
    ```bash
    cd Phase1
    ```
3. Run the next command 
    ```bash
    streamlit run .\Phase1\ActivatePlatform.py
    ```
    the Streamlit app will launch. Upload your file via the file uploader to see the analysis results.


## Accuracy & Completeness Metrics

### Accuracy 
Since we lack labeled ground truth for the extracted JSON, I simulate a reference from the original document:

1. **Building the pseudo–ground truth**  
   - I run Azure Document Intelligence and extract all text content from page 1, creating a pool of every word in the form—both relevant and otherwise.  
   - After LLM extraction, I parse each attribute’s value and check whether *all* attribute words appear in the Document Intelligence pool.  
   - If they do, I count that attribute as correct. 

   - **Content-based accuracy** = (# correctly matched attributes) / JsonLen


   **Example** :

   Document Pool Example:
    ```text
    pool = ['רכב', 'אחר', 'ת.', 'דרכים', 'אבן יהודה', '02021999']
    ```

   Attribute Example
   
   ```text 

    "address_city": "אבן יהודה"  
    ```
    
    will give us one to the succsses count

   Attribute Example
   
   ```text 

    "address_city": "תל אביב"  
    ```

    will not add to the succsses count


2. **JSON structure accuracy**  
    - I extract JSON outputs from two LLM models—GPT-4o and GPT-4o-Mini.
   - I compare the two LLM outputs and count all key–value pairs that match exactly.

   - **Exact-match accuracy** = (# identical pairs) / JsonLen

3. **Weighted overall accuracy**  
   - Combine results as a 75 % weight on content-based accuracy and 25 % on exact-match accuracy.
     I put more weight on content validation because it more closely approximates our pseudo–ground truth
### Completeness 


   - Count how many attributes in the LLM result are non-empty.  
   - **Completeness** = ((JsonLen − empty_count) / JsonLen) × 100

#### Date validation
   - Any invalid date formats are recorded and returned to the user as error messages.
