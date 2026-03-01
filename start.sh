#!/bin/bash

# Start the FastAPI backend quietly in the background on arbitrary port 8000
echo "Starting backend RAG API..."
uvicorn phase4_backend.app:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# Give backend a second to bind
sleep 3

# Start the Streamlit frontend in the foreground and bind to the Cloud Provider's injected $PORT
# It securely talks sideways to our backgrounded API
echo "Starting Streamlit UI..."
export API_URL="http://localhost:8000/chat"
streamlit run phase5_frontend/app.py --server.port ${PORT:-8501} --server.address 0.0.0.0
