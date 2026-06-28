# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for compiling python extensions (e.g. chromadb dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make the start script executable
RUN chmod +x start.sh

# Expose the Streamlit port
EXPOSE 8501

# Run the startup script
CMD ["./start.sh"]
