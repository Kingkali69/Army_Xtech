#!/usr/bin/env python3
"""
Voice Interface for NEXUS
=========================

Voice input/output for NEXUS (Trinity-enhanced AI).
- Offline speech recognition (Vosk)
- 2-second pause detection
- Text-to-speech output (pyttsx3)
- Continuous listening
"""

import sys
import os
import time
import threading
import queue
import logging
from typing import Optional, Callable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import voice libraries
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("[VOICE] pyaudio not available - install with: pip install pyaudio")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("[VOICE] pyttsx3 not available - install with: pip install pyttsx3")

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    logger.warning("[VOICE] vosk not available - install with: pip install vosk")

# Fallback to speech_recognition if Vosk not available
if not VOSK_AVAILABLE:
    try:
        import speech_recognition as sr
        SPEECH_RECOGNITION_AVAILABLE = True
        logger.info("[VOICE] Using speech_recognition as fallback (requires internet)")
    except ImportError:
        SPEECH_RECOGNITION_AVAILABLE = False
        logger.warning("[VOICE] speech_recognition not available")


class VoiceInput:
    """
    Offline voice input using Vosk (or fallback to speech_recognition).
    Detects 2-second pause to trigger response.
    """
    
    def __init__(self, model_path: Optional[str] = None, pause_threshold: float = 2.0):
        """
        Initialize voice input.
        
        Args:
            model_path: Path to Vosk model (None = auto-download)
            pause_threshold: Seconds of silence before triggering (default: 2.0)
        """
        self.pause_threshold = pause_threshold
        self.running = False
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()
        self.current_text = ""
        self.last_speech_time = 0
        self.silence_start = None
        
        # Initialize Vosk if available
        self.vosk_model = None
        self.vosk_recognizer = None
        self.audio_stream = None
        
        if VOSK_AVAILABLE and PYAUDIO_AVAILABLE:
            self._init_vosk(model_path)
        elif SPEECH_RECOGNITION_AVAILABLE:
            self._init_speech_recognition()
        else:
            logger.error("[VOICE] No speech recognition available!")
    
    def _init_vosk(self, model_path: Optional[str]):
        """Initialize Vosk offline STT"""
        try:
            if model_path is None:
                # Try to find model in common locations
                model_paths = [
                    os.path.expanduser("~/.omni/models/vosk-model-small-en-us-0.15"),
                    os.path.expanduser("~/.omni/models/vosk-model-en-us-0.22"),
                    "/usr/share/vosk-models/vosk-model-small-en-us-0.15",
                ]
                
                model_path = None
                for path in model_paths:
                    if os.path.exists(path):
                        model_path = path
                        break
                
                if model_path is None:
                    logger.warning("[VOICE] Vosk model not found. Download from: https://alphacephei.com/vosk/models")
                    logger.warning("[VOICE] Place in: ~/.omni/models/vosk-model-small-en-us-0.15")
                    return
            
            logger.info(f"[VOICE] Loading Vosk model from: {model_path}")
            self.vosk_model = Model(model_path)
            self.vosk_recognizer = KaldiRecognizer(self.vosk_model, 16000)
            self.vosk_recognizer.SetWords(True)
            logger.info("[VOICE] Vosk model loaded - offline STT ready")
        except Exception as e:
            logger.error(f"[VOICE] Failed to initialize Vosk: {e}")
            self.vosk_model = None
    
    def _init_speech_recognition(self):
        """Initialize speech_recognition (fallback, requires internet)"""
        try:
            self.sr_recognizer = sr.Recognizer()
            self.sr_microphone = sr.Microphone()
            logger.info("[VOICE] Using speech_recognition (requires internet)")
        except Exception as e:
            logger.error(f"[VOICE] Failed to initialize speech_recognition: {e}")
    
    def start_listening(self, callback: Callable[[str], None]):
        """
        Start continuous listening.
        
        Args:
            callback: Function to call when text is ready (after pause)
        """
        if self.running:
            return
        
        self.running = True
        self.callback = callback
        
        if VOSK_AVAILABLE and self.vosk_model and PYAUDIO_AVAILABLE:
            self._start_vosk_listening()
        elif SPEECH_RECOGNITION_AVAILABLE:
            self._start_speech_recognition_listening()
        else:
            logger.error("[VOICE] Cannot start listening - no STT available")
    
    def _start_vosk_listening(self):
        """Start Vosk-based listening"""
        try:
            import pyaudio
            
            # Audio parameters
            CHUNK = 4096
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            
            p = pyaudio.PyAudio()
            self.audio_stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            logger.info("[VOICE] Listening... (speak, then pause 2 seconds)")
            
            # Start audio processing thread
            self.audio_thread = threading.Thread(
                target=self._process_audio_vosk,
                daemon=True
            )
            self.audio_thread.start()
            
            # Start pause detection thread
            self.pause_thread = threading.Thread(
                target=self._detect_pause,
                daemon=True
            )
            self.pause_thread.start()
            
        except Exception as e:
            logger.error(f"[VOICE] Failed to start Vosk listening: {e}")
            self.running = False
    
    def _process_audio_vosk(self):
        """Process audio stream with Vosk"""
        while self.running:
            try:
                data = self.audio_stream.read(4096, exception_on_overflow=False)
                
                if self.vosk_recognizer.AcceptWaveform(data):
                    result = self.vosk_recognizer.Result()
                    import json
                    result_dict = json.loads(result)
                    text = result_dict.get('text', '').strip()
                    
                    if text:
                        self.current_text += " " + text
                        self.current_text = self.current_text.strip()
                        self.last_speech_time = time.time()
                        self.silence_start = None
                        logger.debug(f"[VOICE] Heard: {text}")
                else:
                    # Partial result
                    partial = self.vosk_recognizer.PartialResult()
                    partial_dict = json.loads(partial)
                    partial_text = partial_dict.get('partial', '').strip()
                    
                    if partial_text:
                        self.last_speech_time = time.time()
                        self.silence_start = None
            except Exception as e:
                logger.error(f"[VOICE] Audio processing error: {e}")
                time.sleep(0.1)
    
    def _detect_pause(self):
        """Detect 2-second pause and trigger callback"""
        while self.running:
            try:
                current_time = time.time()
                
                if self.last_speech_time > 0:
                    silence_duration = current_time - self.last_speech_time
                    
                    if silence_duration >= self.pause_threshold:
                        # 2-second pause detected
                        if self.current_text and self.silence_start is None:
                            # First time hitting pause threshold
                            self.silence_start = current_time
                            logger.info(f"[VOICE] Pause detected ({self.pause_threshold}s) - processing: {self.current_text}")
                            
                            # Trigger callback
                            text_to_send = self.current_text
                            self.current_text = ""
                            self.last_speech_time = 0
                            self.silence_start = None
                            
                            if self.callback:
                                self.callback(text_to_send)
                
                time.sleep(0.1)  # Check every 100ms
            except Exception as e:
                logger.error(f"[VOICE] Pause detection error: {e}")
                time.sleep(0.1)
    
    def _start_speech_recognition_listening(self):
        """Start speech_recognition-based listening (fallback)"""
        def listen_loop():
            while self.running:
                try:
                    with self.sr_microphone as source:
                        logger.info("[VOICE] Listening... (speak, then pause 2 seconds)")
                        self.sr_recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio = self.sr_recognizer.listen(source, phrase_time_limit=5, timeout=None)
                    
                    try:
                        text = self.sr_recognizer.recognize_google(audio)
                        if text:
                            logger.info(f"[VOICE] Heard: {text}")
                            if self.callback:
                                self.callback(text)
                    except sr.UnknownValueError:
                        logger.debug("[VOICE] Could not understand audio")
                    except sr.RequestError as e:
                        logger.error(f"[VOICE] Speech recognition error: {e}")
                except Exception as e:
                    logger.error(f"[VOICE] Listening error: {e}")
                    time.sleep(1)
        
        self.listen_thread = threading.Thread(target=listen_loop, daemon=True)
        self.listen_thread.start()
    
    def stop_listening(self):
        """Stop listening"""
        self.running = False
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
        logger.info("[VOICE] Stopped listening")


class VoiceOutput:
    """
    Text-to-speech output using pyttsx3 (offline).
    """
    
    def __init__(self):
        """Initialize voice output"""
        self.engine = None
        
        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                # Set voice properties
                voices = self.engine.getProperty('voices')
                if voices:
                    # Try to use a male voice if available
                    for voice in voices:
                        if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                            self.engine.setProperty('voice', voice.id)
                            break
                
                self.engine.setProperty('rate', 150)  # Speech rate
                self.engine.setProperty('volume', 0.9)  # Volume
                logger.info("[VOICE] TTS engine initialized")
            except Exception as e:
                logger.error(f"[VOICE] Failed to initialize TTS: {e}")
        else:
            logger.warning("[VOICE] TTS not available")
    
    def speak(self, text: str):
        """
        Speak text.
        
        Args:
            text: Text to speak
        """
        if not self.engine:
            logger.warning("[VOICE] TTS not available, cannot speak")
            return
        
        try:
            logger.info(f"[VOICE] Speaking: {text[:50]}...")
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"[VOICE] Failed to speak: {e}")


class VoiceInterface:
    """
    Complete voice interface for NEXUS.
    Combines voice input (with pause detection) and output.
    """
    
    def __init__(self, pause_threshold: float = 2.0):
        """
        Initialize voice interface.
        
        Args:
            pause_threshold: Seconds of silence before triggering (default: 2.0)
        """
        self.pause_threshold = pause_threshold
        self.voice_input = VoiceInput(pause_threshold=pause_threshold)
        self.voice_output = VoiceOutput()
        self.on_text_received: Optional[Callable[[str], str]] = None
        self.running = False
        
        logger.info("[VOICE_INTERFACE] Initialized")
        logger.info(f"[VOICE_INTERFACE] Pause threshold: {pause_threshold}s")
    
    def set_text_handler(self, handler: Callable[[str], str]):
        """
        Set handler for received text.
        
        Args:
            handler: Function(text) -> response_text
        """
        self.on_text_received = handler
    
    def start(self):
        """Start voice interface"""
        if self.running:
            return
        
        self.running = True
        
        def handle_text(text: str):
            """Handle received text"""
            logger.info(f"[VOICE_INTERFACE] Received: {text}")
            
            if self.on_text_received:
                try:
                    response = self.on_text_received(text)
                    if response:
                        self.voice_output.speak(response)
                except Exception as e:
                    logger.error(f"[VOICE_INTERFACE] Error processing text: {e}")
                    self.voice_output.speak("Sorry, I encountered an error.")
        
        self.voice_input.start_listening(handle_text)
        logger.info("[VOICE_INTERFACE] Started - speak and pause 2 seconds")
    
    def stop(self):
        """Stop voice interface"""
        self.running = False
        self.voice_input.stop_listening()
        logger.info("[VOICE_INTERFACE] Stopped")


# Export
__all__ = ['VoiceInterface', 'VoiceInput', 'VoiceOutput', 'VOSK_AVAILABLE', 'TTS_AVAILABLE']
