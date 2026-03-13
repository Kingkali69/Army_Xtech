#!/usr/bin/env python3
"""
NEXUS Voice Interface - Main Loop
=================================

Ambient voice interface. Say the phrase, 2-second silence detection triggers response.
Nexus pulls live data from OMNI endpoints and speaks back. No buttons after init.
"""

import os
import sys
import json
import time
import threading
import queue
import pyaudio
import numpy as np
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import vosk
    from .config import *
    from .nexus_brain import NexusBrain
    from .nexus_tts import NexusTTS
    from .nexus_api import NexusAPI
except ImportError:
    # Fallback for direct execution
    from config import *
    from nexus_brain import NexusBrain
    from nexus_tts import NexusTTS
    from nexus_api import NexusAPI

class NexusVoiceInterface:
    """Main NEXUS voice interface"""
    
    def __init__(self):
        self.running = False
        self.listening = False
        self.active_listening = False
        
        # Audio components
        self.audio = None
        self.stream = None
        self.model = None
        self.recognizer = None
        
        # NEXUS components
        self.brain = None
        self.tts = None
        self.api = None
        
        # Audio processing
        self.audio_queue = queue.Queue()
        self.silence_timer = 0
        self.last_audio_time = 0
        self.current_transcript = ""
        
        print("🔥 NEXUS Voice Interface initializing...")
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components"""
        try:
            # Initialize NEXUS components
            self.brain = NexusBrain()
            self.tts = NexusTTS()
            self.api = NexusAPI()
            
            # Initialize audio
            self._initialize_audio()
            
            # Load Vosk model
            self._load_vosk_model()
            
            print("✅ NEXUS Voice Interface ready")
            print(f"🎯 Wake phrase: '{WAKE_PHRASE}'")
            print(f"⏱️  Silence threshold: {SILENCE_THRESHOLD}s")
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            raise
    
    def _initialize_audio(self):
        """Initialize PyAudio"""
        try:
            self.audio = pyaudio.PyAudio()
            
            # Find microphone device
            device_index = self._find_microphone()
            
            # Create audio stream
            self.stream = self.audio.open(
                format=AUDIO_FORMAT,
                channels=AUDIO_CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=AUDIO_CHUNK_SIZE,
                stream_callback=self._audio_callback
            )
            
            print(f"🎤 Microphone initialized (device: {device_index})")
            
        except Exception as e:
            print(f"❌ Audio initialization failed: {e}")
            raise
    
    def _find_microphone(self):
        """Find microphone device"""
        if MIC_DEVICE_INDEX is not None:
            return MIC_DEVICE_INDEX
        
        # Auto-detect first input device
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"🎤 Found microphone: {info['name']}")
                return i
        
        return None
    
    def _load_vosk_model(self):
        """Load Vosk speech recognition model"""
        try:
            model_path = os.path.expanduser(VOSK_MODEL_PATH)
            
            # Download model if not exists
            if not os.path.exists(model_path):
                print("📥 Downloading Vosk model...")
                self._download_vosk_model(model_path)
            
            # Load model
            self.model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, SAMPLE_RATE)
            
            print("✅ Vosk model loaded")
            
        except Exception as e:
            print(f"❌ Failed to load Vosk model: {e}")
            raise
    
    def _download_vosk_model(self, model_path):
        """Download Vosk model"""
        try:
            import urllib.request
            import zipfile
            
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # Download small English model
            url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
            zip_path = model_path + ".zip"
            
            print(f"📥 Downloading from {url}...")
            urllib.request.urlretrieve(url, zip_path)
            
            print("📦 Extracting model...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(model_path))
            
            # Remove zip file
            os.remove(zip_path)
            
            print("✅ Model download complete")
            
        except Exception as e:
            print(f"❌ Model download failed: {e}")
            raise
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback"""
        if self.listening:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def start_listening(self):
        """Start voice interface"""
        if self.running:
            print("🔊 Already listening...")
            return
        
        self.running = True
        self.listening = True
        
        print("🎤 NEXUS Voice Interface active")
        print(f"💡 Say '{WAKE_PHRASE}' to activate")
        
        # Start audio stream
        self.stream.start_stream()
        
        # Start processing threads
        processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        processing_thread.start()
        
        silence_thread = threading.Thread(target=self._silence_detection_loop, daemon=True)
        silence_thread.start()
    
    def stop_listening(self):
        """Stop voice interface"""
        self.running = False
        self.listening = False
        self.active_listening = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.audio:
            self.audio.terminate()
        
        print("🛑 NEXUS Voice Interface stopped")
    
    def _processing_loop(self):
        """Main audio processing loop"""
        while self.running:
            try:
                # Get audio data
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get()
                    
                    # Process speech recognition
                    if self.recognizer.AcceptWaveform(audio_data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '').strip()
                        
                        if text:
                            self._process_speech(text)
                
                time.sleep(0.01)
                
            except Exception as e:
                print(f"❌ Audio processing error: {e}")
                time.sleep(0.1)
    
    def _silence_detection_loop(self):
        """Silence detection for auto-send"""
        while self.running:
            try:
                if self.active_listening:
                    current_time = time.time()
                    
                    # Check if silence threshold reached
                    if current_time - self.last_audio_time >= SILENCE_THRESHOLD:
                        if self.current_transcript.strip():
                            self._process_command(self.current_transcript)
                            self.current_transcript = ""
                            self.active_listening = False
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Silence detection error: {e}")
                time.sleep(0.1)
    
    def _process_speech(self, text):
        """Process recognized speech"""
        print(f"🎤 Heard: '{text}'")
        
        if not self.active_listening:
            # Check for wake phrase
            if WAKE_PHRASE.lower() in text.lower():
                print("🎯 Wake phrase detected!")
                self.active_listening = True
                self.current_transcript = ""
                self.last_audio_time = time.time()
                
                # Play acknowledgement
                self.tts.speak("Listening", self._acknowledgement_complete)
        else:
            # Active listening mode
            self.current_transcript += " " + text
            self.last_audio_time = time.time()
            print(f"📝 Building: '{self.current_transcript.strip()}'")
    
    def _acknowledgement_complete(self):
        """Called after acknowledgement speech"""
        # Reset silence timer after speaking
        self.last_audio_time = time.time()
    
    def _process_command(self, transcript):
        """Process complete command"""
        if not transcript.strip():
            return
        
        print(f"🎯 Processing: '{transcript.strip()}'")
        
        # Get response from brain
        response = self.brain.process_intent(transcript)
        
        # Speak response
        if response:
            self.tts.speak(response, self._response_complete)
    
    def _response_complete(self):
        """Called after response speech"""
        # Return to passive listening
        self.active_listening = False
        self.current_transcript = ""
        print("💡 Ready for next command")
    
    def get_status(self):
        """Get interface status"""
        return {
            "running": self.running,
            "listening": self.listening,
            "active_listening": self.active_listening,
            "model_loaded": self.model is not None,
            "tts_ready": self.tts is not None,
            "brain_ready": self.brain is not None,
            "current_transcript": self.current_transcript.strip()
        }

def main():
    """Main entry point"""
    print("🔥 NEXUS Voice Interface")
    print("========================")
    
    try:
        # Create interface
        nexus_voice = NexusVoiceInterface()
        
        # Start listening
        nexus_voice.start_listening()
        
        print("\n🎯 Commands:")
        print(f"  • Say '{WAKE_PHRASE}' to activate")
        print("  • 'systems report' - Get status")
        print("  • 'start omni' - Launch OMNI")
        print("  • 'what can you do' - Capabilities")
        print("  • 'security status' - Threat briefing")
        print("  • Ctrl+C to stop")
        print("\n🎤 Listening...")
        
        # Keep running
        try:
            while nexus_voice.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping voice interface...")
            nexus_voice.stop_listening()
            
    except Exception as e:
        print(f"❌ Voice interface error: {e}")

if __name__ == "__main__":
    main()
