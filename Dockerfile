# Use an official Python runtime as a parent image
# Compatible with ARM64 (OrangePi) and x86_64
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system-level dependencies required for
# sounddevice (portaudio19-dev) and ARM compatibility.
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the project files first to leverage Docker layer caching
COPY pyproject.toml setup.py ./

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy the application source code
COPY src/ ./src/
COPY config.ini .

# Create a models directory and copy all models into it
# This includes the wakeword and the Piper TTS models
RUN mkdir -p models
COPY models/ ./models/

# Download the Spanish Piper TTS model if not already present
COPY download_spanish_model.sh .
RUN chmod +x download_spanish_model.sh && ./download_spanish_model.sh

# Command to run the application when the container starts
CMD ["ollama-voice-assistant"]
