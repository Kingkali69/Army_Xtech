#!/usr/bin/env python3
"""
NEXUS Voice Configuration
========================

All settings in one place for voice interface.
"""

# OMNI Connection
OMNI_HOST = "localhost"
OMNI_PORT = 8888
NEXUS_DAEMON_PORT = 9999

# Voice Settings
SILENCE_THRESHOLD = 2.0      # seconds before auto-send
WAKE_PHRASE = "nexus"        # trigger word to start listening
SAMPLE_RATE = 16000

# Model Paths (will download if needed)
VOSK_MODEL_PATH = "/tmp/vosk-model-small-en-us-0.15"

# Voice Settings
VOICE_RATE = 175             # words per minute (authoritative)
VOICE_VOLUME = 1.0
VOICE_GENDER = "male"        # prefer male, deep voice

# System Settings
NODE_NAME = "GhostOne"
DEBUG_MODE = True
AUTO_START_LISTENING = True

# Audio Device Settings
MIC_DEVICE_INDEX = None       # Auto-detect
AUDIO_CHUNK_SIZE = 1024
AUDIO_FORMAT = pyaudio.paInt16
AUDIO_CHANNELS = 1

# Conversation Settings
MAX_SPEECH_DURATION = 30.0    # max seconds before auto-cut
MIN_SPEECH_DURATION = 0.5     # min seconds to consider as speech
CONFIDENCE_THRESHOLD = 0.5

# NEXUS Personality
NEXUS_PERSONA = {
    "tone": "authoritative",
    "style": "master_specialist", 
    "role": "first_class_citizen",
    "expertise": ["infrastructure", "security", "distributed_computing", "post_internet_ops"]
}
