import streamlit as st
import requests
import time
import random

# List of available models for user to select
models = [
    # "llama-3.1-405b-reasoning",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    
]
list_of_inputs = [
    "How can i help you?",
    "How can i assist you today?",
    "What's on your mind?",
    "Lets get cracking?",
    "Is there anything i can help with?",
    "I'm Batman!",
]
# Backend URLs for file upload and chat generation services
BACKEND_URL = "http://127.0.0.1:5000" # API for file upload and chat generation


# Function to upload files to the backend
def upload_files(files):
    url = f"{BACKEND_URL}/upload"
    files_data = [("files", file) for file in files]
    response = requests.post(url, files=files_data)
    return response.json()


def chat_response(func):
   def wrapper(question, model, temperature, session_id):
       response= func(question, model, temperature, session_id)
       for word in response.splitlines():
            yield word + " \n"
            time.sleep(0.005)
   return wrapper

# Function to generate chat response by interacting with backend
@chat_response
def generate_chat(question, model, temperature, session_id):
    url = f"{BACKEND_URL}/generate"
    payload = {
        "question": question,
        "model": model,
        "temperature": temperature,
        "session_id": session_id
        
    }
    response = requests.post(url, json=payload)
    return response.text


def main():
    # Title of the app
    st.markdown("<h1 style='text-align: center;'>Financial Document Assistant 💼</h1>", unsafe_allow_html=True)
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [] # Initialize an empty chat history
    
    for chat_history in st.session_state.chat_history:
        if chat_history['role'] == "user":
            with st.chat_message(chat_history["role"], avatar= "👨"):
                st.markdown(chat_history["content"])
        else:
            with st.chat_message(chat_history["role"], avatar= "🤖"):
                st.markdown(chat_history["content"])
    # Sidebar settings
    with st.sidebar:
        st.markdown("## ⚙ Settings")
        st.markdown("---")
        
        # Dropdown to select the model
        st.markdown("#### 🧠 AI Model")
        model = st.selectbox("Select AI model", models) 
         # Slider for selecting temperature (controls randomness in LLM responses)
        st.markdown("### 🌡 Temperature")
        temperature = st.slider("Temperature", min_value= 0.0, max_value= 1.0, step= 0.1, help = "generates text with more variety, can lead to hallucinations on higher numbers")
         # Text input for session ID (used to track user conversations)
        st.markdown("### 🔗 Session Id")
        session_id = st.text_input("Enter session id", help="used for tracking user conversation")

        st.markdown("---")
        
         # Section for document upload
        st.markdown("## 📂 Document Upload")
        uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True) # File uploader for multiple files
        if st.button("Process Documents"):# Button to trigger file upload process
            if uploaded_files : # Check if files are uploaded
                with st.spinner("Processing documents..."):# Show spinner while processing
                    result = upload_files(uploaded_files)# Call upload_files function to process files
                    if result.get("status_code") == 200:
                        st.success(result.get("detail", "Documents processed successfully"))
                    else:
                        st.error(result.get("detail", "Error processing documents"))
            else:
                st.warning("Please upload files") #Show warning if no files are uploaded
        
    
    if prompt := st.chat_input("How can i help you?"):
        with st.chat_message("user", avatar= "👨"):
            st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("assistant", avatar="🤖"):
            response =st.write_stream(generate_chat(prompt, model, temperature, session_id))

        st.session_state.chat_history.append({"role": "assistant", "content": response})


    

if __name__ == "__main__":
    main()