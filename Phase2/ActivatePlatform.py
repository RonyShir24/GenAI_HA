import streamlit as st
import os
from dotenv import load_dotenv
import logging
import sys
import FastAPI_HelpFunction as FAI 


# ─── Initializtion ──────────────────────────────────────────────────

load_dotenv()
FASTAPI_URL = "http://localhost:8000"
format="%(asctime)s [%(levelname)s] %(message)s"
formatter = logging.Formatter(format)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_h = logging.StreamHandler(sys.stdout)
console_h.setFormatter(formatter)
logger.addHandler(console_h)

file_h = logging.FileHandler(os.getenv("FrontLogPATH"), mode="a", encoding="utf-8")
file_h.setFormatter(formatter)
logger.addHandler(file_h)


def initialize_stages():
    """
    Set up session state variables. This runs once at app launch.
    
    - QA_Stage: tracks whether user information gathering is complete.
    - messages: stores the chat history as a list of message dicts.
    - user_details: holds relevent extracted user information in a key–value dict.
    """
    
    if "QA_Stage" not in st.session_state:
        st.session_state.QA_Stage = False

    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    if "userdetailes" not in st.session_state:
        st.session_state.userdetailes = {}
        
    logger.info(f"Successfully initialize")  
        
# ─── Streamlit - User Information Gathering UI ──────────────────────────────────────────────────
          
def UserInformationCollection_UI():
    """
    Display UMedical Services ChatBot!I elements to collect user information.
    
    This function:
    1. Prompt the user for required details (e.g., name, age...).
    2. Store each messages in `st.session_state.messages`.
    3. Advance the QA stage flag (`st.session_state.QA_Stage`) once all fields are filled.
    """
    st.title("""Medical Services ChatBot""")
    
    prompt_text = """
    Welcome to Medical Services ChatBot :)\n
    To provide you with the most accurate assistance, please share a few basic details about yourself.
    For each question, please reply with a short answer.

    Once you’ve filled in all required details, please confirm your information.
    """

    st.markdown(prompt_text)

    with st.sidebar:

        st.header("Chat Settings")
        st.markdown("""***Hi user! Please provide the required details***""")
        st.markdown(
            "You can enter your responses in English or Hebrew"
            "and if you eanr the chatbot to switch language- just ask for it!"
        )        
        
        if FAI.check_api_health():
            st.success("API Connected")
        else:
            st.error("API Disconnected")
            st.stop()
            
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    if prompt := st.chat_input("Type your message here..."):

        st.session_state.messages.append({
            "role": "user", 
            "content": prompt
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                response_data = FAI.call_fastapi_chatCollectData(
                    prompt, 
                    st.session_state.messages,
                )
                
                if response_data:
                    assistant_response = response_data["response"]
                    MovetoQA = response_data["collection_complete"]
                    
                    if not MovetoQA: 
                        st.markdown(assistant_response)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": assistant_response
                        })
                        
                        logger.info(f"Successfully answer user prompt")  

                        
                    else:
                        st.markdown("All information was collected succsusfully! when you ready to move forward to the QA phase send me a READY massage")

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": assistant_response
                        })
                        
                        st.session_state.userdetailes = response_data["Personal_Information"]
                        st.session_state.QA_Stage = True
                        MovetoQA = False
                        
                        logger.info(f"Successfully answer user prompt")  
                
                else:
                    error_msg = "Sorry, I couldn't process your request. Please try again."
                    st.error(error_msg)
                    logger.error(f"Error calling API: {str(error_msg)}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })




# ─── Streamlit - User Q&A UI ──────────────────────────────────────────────────

def QA_UI():
    """
    Display UI elements to Q&A phase.
    
    This function:
    1. Answer the user messages by working with HTNL base knowledge.
    2. Store each messages in `st.session_state.messages`.

    """
    logger.info(f"Successfully move to QA")
    st.title(f""" Hi {st.session_state.userdetailes["user_full_name"]}! Ask me anything!""")
    
    with st.sidebar:
        st.header("Chat Settings") 
        st.markdown(f"""***Hello {st.session_state.userdetailes["user_full_name"]}***""")
        st.markdown(f"""***HMO name - {st.session_state.userdetailes["user_hmo"]}***""")
        st.markdown(f"""***Insurance membership tier -   {st.session_state.userdetailes["user_tier"]}***""")
        st.markdown(
            "You can enter your responses in English or Hebrew"
            "and if you eanr the chatbot to switch language- just ask for it!"
        )    
        
        if FAI.check_api_health():
            st.success("API Connected")
        else:
            st.error("API Disconnected")
            st.stop()
            
    chat_container = st.container()
    
    with chat_container:
        with st.chat_message(st.session_state.messages[-1]["role"]):
                st.markdown(st.session_state.messages[-1]["content"])

    if prompt := st.chat_input("Type your message here..."):

        st.session_state.messages.append({
            "role": "user", 
            "content": prompt
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):    
             
                response_data = FAI.QAaking(
                    prompt, 
                    st.session_state.userdetailes["user_hmo"],
                    st.session_state.userdetailes["user_tier"],
                    st.session_state.messages,
                )
                
                if response_data:
                    assistant_response = response_data["response"]
                    st.markdown(assistant_response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                    
                    logger.info(f"Successfully answer user prompt")      
                    
                else:
                    error_msg = "Sorry, I couldn't process your request. Please try again."
                    st.error(error_msg)
                    logger.error(f"Error calling API: {str(error_msg)}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                                

if __name__ == '__main__':
    initialize_stages()
    if st.session_state.QA_Stage :
        QA_UI()
    else:
        UserInformationCollection_UI()