# Install Voice Interface for NEXUS

## Quick Install

```bash
# Install Python packages
pip install vosk pyaudio pyttsx3

# Download Vosk model (offline speech recognition)
mkdir -p ~/.omni/models
cd ~/.omni/models

# Download small English model (~40MB)
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 vosk-model-small-en-us-0.15
```

## Run Voice Chat

```bash
python3 omni_voice_chat.py
```

## How It Works

1. **Speak** - Talk naturally into your microphone
2. **Pause 2 seconds** - After you finish speaking, wait 2 seconds
3. **NEXUS responds** - NEXUS processes your speech and responds via voice

## Features

- ✅ **Offline** - No internet required (uses Vosk)
- ✅ **Continuous listening** - Always listening
- ✅ **2-second pause detection** - Natural conversation flow
- ✅ **Voice output** - NEXUS speaks responses
- ✅ **Trinity-enhanced** - Full NEXUS intelligence

## Troubleshooting

**No microphone detected:**
```bash
# Check audio devices
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"
```

**Vosk model not found:**
- Download model from: https://alphacephei.com/vosk/models
- Place in: `~/.omni/models/vosk-model-small-en-us-0.15`

**Audio permissions (Linux):**
```bash
# Add user to audio group
sudo usermod -a -G audio $USER
# Log out and back in
```

## Alternative: Use speech_recognition (requires internet)

If Vosk doesn't work, it will fall back to `speech_recognition`:
```bash
pip install SpeechRecognition
```

**Note:** This requires internet connection (uses Google API).

---

**Ready to talk to NEXUS!** 🎤
