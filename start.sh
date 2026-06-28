#!/bin/bash

# Start FastAPI backend in the background on port 8000
echo "Starting FastAPI backend on port 8000..."
python -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000)" &

# Wait for a moment to let FastAPI start
sleep 3

# Start Streamlit frontend on the port specified by the environment
# Render/Railway injects PORT for the public-facing service
echo "Starting Streamlit frontend on port ${PORT:-8501}..."
streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false
