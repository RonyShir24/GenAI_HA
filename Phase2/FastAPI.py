import os
import time
from openai import AzureOpenAI 
import json
import logging
from fastapi import FastAPI , HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict 
import warnings
import sys
import numpy as np
import requests
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# ─── Initializtion ──────────────────────────────────────────────────
load_dotenv()
app = FastAPI(title="Stateless FastAPI Chatbot" , version="1.0.0")
FASTAPI_URL = "http://localhost:8000"

#Logger
format="%(asctime)s [%(levelname)s] %(message)s"
formatter = logging.Formatter(format)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_h = logging.StreamHandler(sys.stdout)
console_h.setFormatter(formatter)
logger.addHandler(console_h)

file_h = logging.FileHandler(os.getenv("BackLogPATH"), mode="a", encoding="utf-8")
file_h.setFormatter(formatter)
logger.addHandler(file_h)

# Azure OpenAI
client = AzureOpenAI(
  azure_endpoint = os.getenv("OpenAiAzureEndPoint"),
  api_key= os.getenv("OpenAiAzureKey"),
  api_version="2024-05-01-preview"
)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

executor = ThreadPoolExecutor(max_workers=50)
embeddings = []
documents = []
benefits_data = {}    


# ─── Assistant Initializtion ──────────────────────────────────────────────────

assistant = client.beta.assistants.create(
  model="gpt-4o-mini",
  instructions="""
  You are a persistent information collection assistant with a mandatory stage process.
    You MUST collect these required details from EVERY user before proceeding to any other tasks.
    Ask one filed every time.

1. First and last name
2. ID number (valid 9-digit number)
3. Gender
4. Age (between 0 and 120)
5. HMO name ( "Meuhedet","Maccabi", "Clalit","מכבי","מאוחדת","כללית")
6. HMO card number (9-digit)
7. Insurance membership tier (Gold,Silver,Bronze,זהב,כסף ,ארד)

Provide a confirmation step for users to review and correct their information.

## CRITICAL RULES FOR STAGE 1:

1. **NEVER SKIP COLLECTION**: Regardless of what the user says, you must collect ALL required information first
2. **IGNORE BYPASS ATTEMPTS**: Even if user says "I don't want to provide details", "Skip this", "Just help me", "This is urgent", you must insist
3. **BE PERSISTENTLY POLITE**: Always remain professional but firm about the requirement
4. **NO OTHER ASSISTANCE**: Do not help with any other requests until ALL information is collected
5. **VALIDATE COMPLETENESS**: Check that all fields are provided and appear valid


Do not answer anything the user ask until you have all information confirmed
Only after the user confirm his information you can move forward to Q&A with the user.
When confirmed, tell the user:
if the language is english: 
"Information collection completed. How can i help you today and add the user name? You are in HMO_name, ranked as membership tier
if the language is hebrew:
איסוף המידע הושלם. איך אני יכול לעזור לך היום, user name? אתה בקופת חולים hmo name, בדרגת חברות tier
""",
  tools=[{"type":"function","function":{"name":"Validate_ID","description":"Validate ID length","parameters":{"type":"object","properties":{"id":{"type":"integer","description":"The user id, should be 9-digit number"}},"required":["id"]}}},{"type":"function","function":{"name":"Validate_HMOCardNum","description":"Validate HMO card number length","parameters":{"type":"object","properties":{"HMOcn":{"type":"integer","description":"The user HMO card number, should be 9-digit number"}},"required":["HMOcn"]}}},{"type":"function","function":{"name":"Validate_UserName","description":"Validate that the user give booth first and last name","parameters":{"type":"object","properties":{"F_name":{"type":"string","description":"The user first name"},"L_name":{"type":"string","description":"The user last name"}},"required":["F_name","L_name"]}}},{"type":"function","function":{"name":"Validate_Age","description":"Validate that the user give his age and its inside the allowed range","parameters":{"type":"object","properties":{"age":{"type":"integer","description":"The user age","minimum":0,"maximum":120}},"required":["age"]}}},{"type":"function","function":{"name":"Validate_Gender","description":"Validate that the user give his gender","parameters":{"type":"object","properties":{"gender":{"type":"string","description":"The user gender","enum":["f","m"]}},"required":["gender"]}}},{"type":"function","function":{"name":"Validate_HMOname","description":"Validate that the user give his HMO name","parameters":{"type":"object","properties":{"hmo_name":{"type":"string","description":"The user HMO name","enum":["Meuhedet","Maccabi","Clalit","מכבי","מאוחדת","כללית"]}},"required":["hmo_name"]}}},{"type":"function","function":{"name":"Validate_MemTier","description":"Validate that the user give his insurance membership tier","parameters":{"type":"object","properties":{"MemTier":{"type":"string","description":"The user insurance membership tier","enum":["Gold","Silver","Bronze","זהב","כסף","ארד"]}},"required":["MemTier"]}}}],
  tool_resources= {},
  temperature=1,
  top_p=1
)



# ─── Class Declaration──────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = []
    user_info: Optional[Dict] = None
    system_message: Optional[str] = None
    
class ChatResponse(BaseModel):
    response: str
    collection_complete : Optional[bool] = None
    Personal_Information : Optional[Dict] = None
    
class HealthResponse(BaseModel):
    status: str
    message: str

class IDPayload(BaseModel):
    id: int
    
class HMOcnPayload(BaseModel):
    HMOcn: int
    
class UserNamePayload(BaseModel):
    F_name: str
    L_name: str
    
class AgePayload(BaseModel):
    age: int

class GenderPayload(BaseModel):
    gender: str

class HMONamePayload(BaseModel):
    hmo_name: str
       
class MemTierPayload(BaseModel):
    MemTier: str
      
class QueryRequest(BaseModel):
    prompt: str
    hmo_name: str
    tier: str
    history: list
    
    
    
# ─── Help function to the FastAPI service ──────────────────────────────────────────────────
    



def run_assistant_stateless(message: str, history: List[Dict]):
    """
    Process a single user message through the assistant without maintaining server-side state.

    This function sends the current user input along with the full client-side conversation history 
    to the assistant returns its response. 

    Args:
        message (str):User message to process.
        history (List[Dict]): A list of previous messages.

    Returns:
        Dict: The assistant’s response a dict holding :
        {
            "response" : response content , 
            "collection_complete" : boolean mark if information collection complete ,
            "Personal_Information" : relevant personal Information
        }
    """
    endpoint_map = {
        "Validate_ID":         "validate_id",
        "Validate_HMOCardNum": "validate_hmo_card", 
        "Validate_UserName":   "validate_user_name",
        "Validate_Age":        "validate_age",
        "Validate_Gender":     "validate_gender",
        "Validate_HMOname":    "validate_hmo_name",
        "Validate_MemTier":    "validate_mem_tier",
    }
    
    temp_thread = client.beta.threads.create()

    try:
        logger.info(f"Created temporary thread {temp_thread.id}")
        
        for msg in history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                client.beta.threads.messages.create(
                    thread_id=temp_thread.id,
                    role=msg["role"],
                    content=msg["content"]
                )
        
        logger.info(f"Added {len(history)} history messages to thread {temp_thread.id}")
        
        # Add current message
        client.beta.threads.messages.create(
            thread_id=temp_thread.id,
            role="user",
            content=message
        )
        
        logger.info(f"Starting assistant run for thread {temp_thread.id}")
        
        # Run assistant
        run = client.beta.threads.runs.create(
            thread_id=temp_thread.id,
            assistant_id=assistant.id
        )
        
        logger.info(f"Run created with ID: {run.id}, status: {run.status}")
        
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            wait_time = 1
            max_wait = 60
            total_wait = 0
            iteration += 1
            
            print(f"Processing iteration {iteration}") 
        
            while run.status in ['queued', 'in_progress', 'cancelling'] and total_wait < max_wait:
                time.sleep(wait_time)
                total_wait += wait_time
                wait_time = min(wait_time * 1.2, 2)
                
                run = client.beta.threads.runs.retrieve(
                    thread_id=temp_thread.id,
                    run_id=run.id
                )
                
                logger.info(f"Run status: {run.status}, waited: {total_wait:.1f}s")
            
            if run.status == 'completed':
                collection_complete = False
                Personal_Information = {}
                logger.info(f"Run completed successfully for thread {temp_thread.id}")
                
                messages = client.beta.threads.messages.list(
                    thread_id=temp_thread.id,
                    order="desc",
                    limit=1
                )
                
                assistant_message = messages.data[0]
                response_content = assistant_message.content[0].text.value
                
                # Signal that the data collection is finished. (English)
                if "Information collection completed." in response_content:
                        
                    name_part = response_content.split("today,", 1)[1].split("?", 1)[0]
                    remainder = response_content.split("? You are in ", 1)[1] 
                    hmo_part, tier_part = remainder.split(", ranked as ", 1)

                    user_full_name = name_part.strip()
                    user_hmo = hmo_part.strip()
                    user_tier = tier_part.strip()
                    
                    collection_complete =  True
                    Personal_Information = {
                        "user_full_name" :user_full_name ,
                        "user_hmo":user_hmo, 
                        "user_tier":user_tier
                        }
                    
                 # Signal that the data collection is finished. (Hebrew)
                if "איסוף המידע הושלם." in response_content or "אסיפת המידע הושלמה" in response_content:

                    user_full_name = response_content.split("היום, ", 1)[1].split("?", 1)[0].strip()
                    remainder = response_content.split("? אתה בקופת חולים ", 1)[1]
                    user_hmo, tier_part = remainder.split(", בדרגת חברות ", 1)
                    
                    user_hmo = user_hmo.strip()
                    user_tier = tier_part.rstrip(" .").strip()
                    
                    collection_complete =  True
                    Personal_Information = {
                        "user_full_name" :user_full_name ,
                        "user_hmo":user_hmo, 
                        "user_tier":user_tier
                        } 
                    
                                       
                return {
                    "response" : response_content ,
                    "collection_complete" : collection_complete ,
                    "Personal_Information" : Personal_Information
                    }
            
            
            elif run.status == 'requires_action':
                
                required_action = run.required_action
                
                if required_action.type == 'submit_tool_outputs':
                    tool_outputs = []
                    
                    for tool_call in required_action.submit_tool_outputs.tool_calls:
                        try:
                            fn_name = tool_call.function.name
                            fn_args_str = tool_call.function.arguments
                            tool_call_id = tool_call.id
                            
                            try:
                                fn_args = json.loads(fn_args_str) if fn_args_str else {}
                            except json.JSONDecodeError as json_error:
                                logger.error(f"JSON decode error for {fn_name}: {json_error}")
                                fn_args = {}

                            url = f"{FASTAPI_URL}/{endpoint_map[fn_name]}"
                            logger.info(f"Calling URL: {url} with args: {fn_args}")
                            
                            resp = requests.post(url, json=fn_args, timeout=30)
                            resp.raise_for_status()
                            result = resp.json()
                            
                            if result is None:
                                result = {"error": "API returned None"}
                            
                            # Add tool output
                            tool_outputs.append({
                                "tool_call_id": tool_call_id,
                                "output": json.dumps(result)
                            })
                            
                        except requests.exceptions.RequestException as req_error:
                            logger.error(req_error)
                            error_msg = f"Request error for {fn_name}: {req_error}"
                            tool_outputs.append({
                                "tool_call_id": tool_call_id,
                                "output": json.dumps({"error": error_msg})
                            })
                            
                        except Exception as e:
                            logger.error(f"Error calling function {fn_name}: {e}")
                            error_msg = f"Error calling function {fn_name}: {e}"
                            tool_outputs.append({
                                "tool_call_id": tool_call_id,
                                "output": json.dumps({"error": error_msg})
                            })
                
                    
                    try:
                        run = client.beta.threads.runs.submit_tool_outputs(
                            thread_id=temp_thread.id,
                            run_id=run.id,
                            tool_outputs=tool_outputs
                        )

                        continue
                    
                    except Exception as submit_error:
                        logger.error(f"Error submitting tool outputs: {submit_error}")
                        raise submit_error
                                               
            else:
                logger.error(f"Assistant run failed with status: {run.status}")
                raise Exception(f"Assistant run failed with status: {run.status}")
        
    except Exception as e:
        logger.error(f"Error in run_assistant_stateless: {str(e)}")
        raise e
    
    finally:
        #Cleanup temporary thread
        try:
            client.beta.threads.delete(temp_thread.id)
            logger.info(f"Deleted temporary thread: {temp_thread.id}")
        except Exception as cleanup_error:
            logger.warning(f"Could not delete thread {temp_thread.id}: {cleanup_error}")
            
            
async def create_embeddings():
    
    """
    Create embeddings to the HTML parsed json file.
    """
    
    global embeddings, documents
    
    documents = []
    
    # 1. BENEFITS data
    for hmo, services in benefits_data["benefits"].items():
        for service_name, service_data in services.items():
            if "treatments" in service_data:
                for treatment, treatment_data in service_data["treatments"].items():
                    
                    # Add tier information
                    for tier in ["זהב", "כסף", "ארד"]:
                        if tier in treatment_data:
                            tier_info = treatment_data[tier]
                            text = f""" Treatment {treatment}, which is part of {service_data.get('title', service_name)} in {hmo} 
                            have the next information: {tier}: {tier_info.get('discount', '')} הנחה, עד {tier_info.get('annual_limit', '')} טיפולים"""    
                    
                    # Add contact info
                    if "contacts" in treatment_data and hmo in treatment_data["contacts"]:
                        contact = treatment_data["contacts"][hmo]
                        text += f""" Content information is {contact.get('raw_contact_line', '')} for {contact.get('service_category', '')} """
                    
                    
                    doc_holder={
                        "type": "benefit",
                        "hmo": hmo,
                        "service": service_name,
                        "treatment": treatment,
                        "data": treatment_data,
                        "text": text.strip()
                    }
                    documents.append(doc_holder)
                                        
    
    # 2. DESCRIPTIONS data
    for treatment, description in benefits_data.get("descriptions", {}).items():
        text = f""" {treatment} is {description} """
        documents.append({
            "type": "description",
            "treatment": treatment,
            "description": description,
            "text": text.strip()
        })
        
    
    # 3. METADATA data
    for metadata in benefits_data.get("metadata", []):
        text = f""" {metadata.get('title', '')} is {metadata.get('description', '')}"""
        documents.append({
            "type": "metadata",
            "filename": metadata.get('filename', ''),
            "title": metadata.get('title', ''),
            "data": metadata,
            "text": text.strip()
        })
        
         
    # Create embeddings
    embeddings = []
    
    for doc in documents:
        response = client.embeddings.create(
            input=doc["text"],
            model=os.getenv("EMBEDDING_MODEL")
        )
        embeddings.append(response.data[0].embedding)
    
    # Save embeddings
    with open("embeddings.pkl", "wb") as f:
        pickle.dump({"embeddings": embeddings, "documents": documents}, f)
    
    logger.info("Finish creating embeding")
  
   
  
  
    
# ─── FastAPI service ──────────────────────────────────────────────────

@app.post("/validate_id")
def validate_id(payload: IDPayload):
    '''Validate id'''
    return {"valid": len(str(payload.id)) == 9}


@app.post("/validate_hmo_card")
def validate_hmo_card(payload: HMOcnPayload):
    '''Validate hmo card number'''
    return {"valid": len(str(payload.HMOcn)) == 9}


@app.post("/validate_user_name")
def validate_user_name(payload: UserNamePayload):
    '''Validate user name'''
    valid = bool(payload.F_name.strip()) and bool(payload.L_name.strip())
    return {"valid": valid}


@app.post("/validate_age")
def validate_age(payload: AgePayload):
    '''Validate age'''
    return {"valid": 0 <= payload.age <= 120}


@app.post("/validate_gender")
def validate_gender(payload: GenderPayload):
    '''Validate gender'''
    return {"valid": payload.gender.lower() in ("f", "m")}


@app.post("/validate_hmo_name")
def validate_hmo_name(payload: HMONamePayload):
    '''Validate hmo name'''
    return {
        "valid": payload.hmo_name in [
            "Meuhedet", "Maccabi", "Clalit", "מכבי", "מאוחדת", "כללית"
        ]
    }


@app.post("/validate_mem_tier")
def validate_mem_tier(payload: MemTierPayload):
    '''Validate tier'''
    return {
        "valid": payload.MemTier in ["Gold", "Silver", "Bronze", "זהב", "כסף", "ארד"]
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", message="Service is running")



@app.post("/chatCollectUserData", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """
    Stateless chat with client-side history and user data
    - Uses history from client side
    """
    logger.info(f"Processing stateless chat request")
    logger.info(f"Message: {request.message[:50]}...")
    logger.info(f"History length: {len(request.history) if request.history else 0}")
    
    try:
        loop = asyncio.get_event_loop()
        response_content = await loop.run_in_executor(
            executor,
            run_assistant_stateless,
            request.message,
            request.history or []
        )
        
        logger.info(f"Successfully processed stateless chat request")
                
        return ChatResponse(
            response=response_content["response"],
            collection_complete = response_content["collection_complete"],
            Personal_Information = response_content["Personal_Information"]
        )
            
    except Exception as e:
        logger.error(f"Error processing stateless chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
  

    
@app.on_event("startup")
async def load_data():
    """Load JSON and create embeddings once"""
    global embeddings, documents, benefits_data
    
    with open("parsed_hmo_data.json", "r", encoding="utf-8") as f:
        all_data = json.load(f)
    
    benefits_data = all_data
    
    # Try to load existing embeddings
    if os.path.exists("embeddings.pkl"):
        with open("embeddings.pkl", "rb") as f:
            data = pickle.load(f)
            embeddings = data["embeddings"]
            documents = data["documents"]
        logger.info("Loaded existing embeddings")
    else:
        logger.info("Embeddings not found. create new embeddings")
        await create_embeddings()
        

    
@app.post("/ask")
async def ask_question(request: QueryRequest):
    """Answer user question using embeddings + LLM"""
    
    # Get query embedding
    query_response = client.embeddings.create(
            input=request.hmo_name+" "+request.tier+" "+request.prompt,
            model=os.getenv("EMBEDDING_MODEL")
    )
    query_embedding = query_response.data[0].embedding
    

    similarities = cosine_similarity([query_embedding], embeddings)[0]
    
    top_indices = np.argsort(similarities)[-10:][::-1]
    
    context = ""
    user_specific_docs = []
    visited_doc = []
    
    
    for idx in top_indices:
        doc = documents[idx]
        if doc["type"] == "benefit":
            if doc["hmo"] == request.hmo_name:
                visited_doc.append(idx)
                user_specific_docs.append(doc)
                print(doc)
                context += f"{doc['text']}\n\n"
        else:
            visited_doc.append(idx)
            print(doc)
            context += f"{doc['text']}\n\n"  
    
    
    system_prompt = """You are an expert Israeli health-fund assistant. Whenever the user provides a health fund (קופת חולים) and an insurance tier (רמת ביטוח), you must respond with:
    Coverage details (which services are included)
    Any co-payments or limits (annual/session)
    Contact info or next steps
    Answer concisely in Hebrew/english according to the user request."""
    

    context_message = f"""
the only information you have:
{context}
"""

    user_prompt = f"""
use information
- health fund (קופת חולים): {request.hmo_name}
- insurance tier (רמת ביטוח): {request.tier}
- converstion history: {request.history}

user ask to know: {request.prompt}
"""
    
    response = client.chat.completions.create(
        model=os.getenv("model_name"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": context_message},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0,
        max_tokens=500
    )
    
    return {
        "response": response.choices[0].message.content,
        "sources_used": len(user_specific_docs) if user_specific_docs else len(top_indices)
    }
  
      
if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000,
        workers=1, 
        loop="asyncio"
    )    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
 