import streamlit as st
import requests
from typing import  Dict


# ─── Initializtion ──────────────────────────────────────────────────

FASTAPI_URL = "http://localhost:8000"


# ─── Function implementation ──────────────────────────────────────────────────

def check_api_health() -> bool:
    """Check if FastAPI service is healthy"""
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def call_fastapi_chatCollectData(message: str, history : list) -> Dict:
    """
    Send a chat message and its conversation history to the FastAPI endpoint for data collection.

    Args:
        message (str): The user’s input.
        history (list): Previous conversation messages.

    Returns:
        Dict: The parsed JSON response returned by the FastAPI chat endpoint.
    """
        
    payload = {
        "message": message,
        "history" : history,
    }
        
    try:
        response = requests.post(
            f"{FASTAPI_URL}/chatCollectUserData",
            json=payload,
            timeout=300
        )
        
        response.raise_for_status()
        return response.json()
    
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling API: {str(e)}")
        return None

        
def QAaking(message: str,hmo_name: str,tier: str,history : list)-> Dict:
    """
    Submit a question along with context to the FastAPI QA endpoint for a specific HMO and service tier.

    Args:
        message (str): The user’s question.
        hmo_name (str): Name of the HMO.
        tier (str): The service tier of the user.
        history (list): Previous conversation messages.

    Returns:
        Dict: The parsed JSON response from the FastAPI QA service.
    """
    
    data = {
    "prompt": message,
    "hmo_name": hmo_name, 
    "tier": tier,
    "history":history
    }

    try:
        response = requests.post(
            f"{FASTAPI_URL}/ask",
            json=data,
            timeout=30)
        
        response.raise_for_status()
        result = response.json()
        
        return result
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling API: {str(e)}")
        return None
