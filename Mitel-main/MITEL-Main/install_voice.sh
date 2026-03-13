#!/bin/bash
# Install Voice Interface for NEXUS
# Makes it easy to talk instead of type

set -e

echo "======================================================================"
echo "  Installing Voice Interface for NEXUS"
echo "======================================================================"
echo ""

# Install Python packages
echo "Installing Python packages..."
pip install vosk pyaudio pyttsx3 || {
    echo "⚠️  pip install failed, trying pip3..."
    pip3 install vosk pyaudio pyttsx3
}

echo "✅ Python packages installed"
echo ""

# Download Vosk model
echo "Downloading Vosk model (offline speech recognition)..."
MODEL_DIR="$HOME/.omni/models"
MODEL_NAME="vosk-model-small-en-us-0.15"
MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

if [ -d "$MODEL_NAME" ]; then
    echo "✅ Vosk model already exists: $MODEL_PATH"
else
    echo "Downloading model (~40MB)..."
    wget -q --show-progress https://alphacephei.com/vosk/models/$MODEL_NAME.zip || {
        echo "❌ Download failed. Please download manually:"
        echo "   https://alphacephei.com/vosk/models/$MODEL_NAME.zip"
        echo "   Extract to: $MODEL_PATH"
        exit 1
    }
    
    echo "Extracting..."
    unzip -q $MODEL_NAME.zip
    rm $MODEL_NAME.zip
    
    echo "✅ Vosk model installed: $MODEL_PATH"
fi

echo ""
echo "======================================================================"
echo "  ✅ INSTALLATION COMPLETE"
echo "======================================================================"
echo ""
echo "To use voice chat:"
echo "  python3 omni_voice_chat.py"
echo ""
echo "How it works:"
echo "  1. Speak naturally into your microphone"
echo "  2. Pause 2 seconds after speaking"
echo "  3. NEXUS responds automatically"
echo ""
echo "Press Ctrl+C to stop"
echo ""
