#!/bin/bash

# Deploy script for Stock Alerter Streamlit App
# This script can be run manually on the VPS for testing

echo "🚀 Starting deployment of Stock Alerter..."

# Set variables
PROJECT_DIR="/path/to/your/stockalerter"  # Update this path
SCREEN_SESSION="stockalerter"
STREAMLIT_PORT="8501"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if required commands exist
if ! command_exists git; then
    echo "❌ Git is not installed"
    exit 1
fi

if ! command_exists python3; then
    echo "❌ Python3 is not installed"
    exit 1
fi

if ! command_exists screen; then
    echo "❌ Screen is not installed. Install with: apt-get install screen"
    exit 1
fi

# Navigate to project directory
echo "📁 Navigating to project directory..."
cd "$PROJECT_DIR" || {
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
}

# Pull latest changes
echo "⬇️  Pulling latest changes from GitHub..."
git pull origin deploy || {
    echo "❌ Failed to pull changes from GitHub"
    exit 1
}

# Install UV if not already installed
if ! command_exists uv; then
    echo "📦 Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
uv pip install --system -r requirements.txt || {
    echo "❌ Failed to install dependencies"
    exit 1
}

# Stop existing processes
echo "🛑 Stopping existing Streamlit processes..."
pkill -f "streamlit run" 2>/dev/null || true

# Check if screen session exists and kill it
echo "🔍 Checking for existing screen session..."
if screen -list 2>/dev/null | grep -q "$SCREEN_SESSION"; then
    echo "🗑️  Killing existing screen session..."
    screen -S "$SCREEN_SESSION" -X quit 2>/dev/null || true
    sleep 2
fi

# Start new screen session with Streamlit
echo "🎬 Starting new Streamlit app in screen session..."
screen -dmS "$SCREEN_SESSION" bash -c "cd '$PROJECT_DIR' && streamlit run Home.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0; exec bash"

# Wait and check if the session is running
sleep 3
if screen -list 2>/dev/null | grep -q "$SCREEN_SESSION"; then
    echo "✅ Streamlit app successfully started in screen session '$SCREEN_SESSION'"
    echo "📋 Active screen sessions:"
    screen -list 2>/dev/null || echo "No screen sessions found"
    echo ""
    echo "🌐 App should be accessible at: http://your-vps-ip:$STREAMLIT_PORT"
    echo "🖥️  To view the app logs, run: screen -r $SCREEN_SESSION"
    echo "🔧 To stop the app, run: screen -S $SCREEN_SESSION -X quit"
else
    echo "❌ Failed to start screen session"
    exit 1
fi

echo "🎉 Deployment completed successfully!" 