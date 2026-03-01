import streamlit as st
import requests

# Set page config
st.set_page_config(
    page_title="Nextleap Course Assistant",
    page_icon="🤖",
    layout="wide"
)

# Add custom CSS for minimalist design
st.markdown("""
<style>
    /* Main background and font */
    .stApp {
        background-color: #fcfcfc;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Hide top header and menu for minimalist look */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Clean title styling */
    h1 {
        font-weight: 300 !important;
        color: #2c3e50;
        text-align: center;
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
    }
    
    /* User message pill */
    [data-testid="stChatMessage"][data-baseweb="block"]:has([data-testid="userAvatar"]) {
        background-color: #f1f3f5 !important;
        border-radius: 1.5rem !important;
        padding: 1.5rem !important;
        margin-left: 20%;
        margin-right: 1rem;
        border-bottom-right-radius: 0 !important;
    }
    
    /* Assistant message pill */
    [data-testid="stChatMessage"][data-baseweb="block"]:has([data-testid="botAvatar"]) {
        background-color: #ffffff !important;
        border: 1px solid #eaeaea !important;
        border-radius: 1.5rem !important;
        padding: 1.5rem !important;
        margin-right: 20%;
        margin-left: 1rem;
        border-bottom-left-radius: 0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Input field styling */
    .stChatInputContainer {
        border-radius: 2rem !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;
        padding: 0.2rem !important;
    }
    
    .stChatInputContainer:focus-within {
        border: 1px solid #a0aec0 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Nextleap Assistant")
st.markdown("<p style='text-align: center; color: #7f8c8d; margin-top: -1.5rem; margin-bottom: 2rem;'>Ask questions about Nextleap cohorts and instructors.</p>", unsafe_allow_html=True)

# Backend API URL
API_URL = "http://localhost:8000/chat"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome! I can provide info about Nextleap courses based strictly on our website data. What would you like to know?"}
    ]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("E.g., Which courses does Arindam Mukherjee teach?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Send payload to FastAPI backend
            with st.spinner("Searching Knowledge Base..."):
                response = requests.post(
                    API_URL,
                    json={"query": prompt},
                    timeout=30
                )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "No answer received.")
                sources = data.get("sources", [])
                
                # Format sources
                if sources:
                    source_links = "\n\n**Sources:**\n" + "\n".join([f"- {s}" for s in sources])
                    full_response = answer + source_links
                else:
                    full_response = answer
                
                message_placeholder.markdown(full_response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                error_msg = f"Error: API returned status code {response.status_code}"
                message_placeholder.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to connect to backend API: `{e}`.\n\nMake sure the FastAPI backend is running!"
            message_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
