#!/bin/bash

# F1 Animation Project Setup Script

echo "--- Setting up F1 Animation Environment ---"

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 could not be found. Please install Python 3."
    exit 1
fi
echo "Python 3 found."

# 2. Check for FFmpeg (Required for saving animations)
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: ffmpeg could not be found. Animations might fail to save."
    echo "Please install ffmpeg (e.g., 'brew install ffmpeg' on macOS)."
else
    echo "ffmpeg found."
fi

# 3. Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment 'venv'..."
    python3 -m venv venv
else
    echo "Virtual environment 'venv' already exists."
fi

# 4. Install Dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "--- Setup Complete! ---"
echo "To run the project:"
echo "1. Activate the environment: source venv/bin/activate"
echo "2. Generate data/video:      python generate_season.py --year 2025"
echo "3. Start web server:         python -m http.server"
