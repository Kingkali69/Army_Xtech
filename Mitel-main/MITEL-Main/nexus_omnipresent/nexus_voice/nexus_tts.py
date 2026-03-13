#!/usr/bin/env python3
"""
NEXUS Text-to-Speech
====================

Voice output for NEXUS responses.
Authoritative, master specialist voice.
"""

import pyttsx3
import threading
import time
from .config import VOICE_RATE, VOICE_VOLUME, VOICE_GENDER

class NexusTTS:
    """NEXUS voice output system"""
    
    def __init__(self):
        self.engine = None
        self.speaking = False
        self.voice_thread = None
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the TTS engine"""
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice
            self._configure_voice()
            
            print("🔊 NEXUS voice engine initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize voice engine: {e}")
            self.engine = None
    
    def _configure_voice(self):
        """Configure voice settings"""
        if not self.engine:
            return
        
        # Set rate (words per minute)
        self.engine.setProperty('rate', VOICE_RATE)
        
        # Set volume
        self.engine.setProperty('volume', VOICE_VOLUME)
        
        # Select voice based on gender preference
        voices = self.engine.getProperty('voices')
        selected_voice = None
        
        if VOICE_GENDER.lower() == "male":
            # Try to find a male voice
            for voice in voices:
                if "male" in voice.name.lower():
                    selected_voice = voice.id
                    break
        else:
            # Try to find a female voice
            for voice in voices:
                if "female" in voice.name.lower():
                    selected_voice = voice.id
                    break
        
        # Use selected voice or fallback to first voice
        if selected_voice:
            self.engine.setProperty('voice', selected_voice)
        elif voices:
            self.engine.setProperty('voice', voices[0].id)
        
        print(f"🔊 Voice configured: {selected_voice or voices[0].name if voices else 'None'}")
    
    def speak(self, text, callback=None):
        """Speak text asynchronously"""
        if not self.engine:
            print(f"🔊 NEXUS: {text}")
            if callback:
                callback()
            return
        
        # Don't interrupt current speech
        if self.speaking:
            print("🔊 NEXUS busy...")
            return
        
        # Start speaking in thread
        self.voice_thread = threading.Thread(
            target=self._speak_thread,
            args=(text, callback),
            daemon=True
        )
        self.voice_thread.start()
    
    def _speak_thread(self, text, callback):
        """Thread function for speaking"""
        try:
            self.speaking = True
            
            # Preprocess text for better speech
            processed_text = self._preprocess_text(text)
            
            print(f"🔊 NEXUS speaking: {processed_text}")
            
            # Speak the text
            self.engine.say(processed_text)
            self.engine.runAndWait()
            
            print("🔊 NEXUS finished speaking")
            
        except Exception as e:
            print(f"❌ Speech error: {e}")
        finally:
            self.speaking = False
            
            # Call callback if provided
            if callback:
                callback()
    
    def _preprocess_text(self, text):
        """Preprocess text for better TTS"""
        # Replace abbreviations with full words
        replacements = {
            "OMNI": "Omni",
            "M.I.T.E.L.": "Mitel",
            "NEXUS": "Nexus",
            "USB": "U S B",
            "AI": "A I",
            "API": "A P I",
            "STT": "S T T",
            "TTS": "T T S",
            "CRDT": "C R D T",
            "MDCS": "M D C S"
        }
        
        processed = text
        for abbr, full in replacements.items():
            processed = processed.replace(abbr, full)
        
        # Add pauses for commas and periods
        processed = processed.replace(",", " ,")
        processed = processed.replace(".", " .")
        processed = processed.replace("!", " !")
        processed = processed.replace("?", " ?")
        
        return processed
    
    def stop(self):
        """Stop current speech"""
        if self.engine and self.speaking:
            try:
                self.engine.stop()
                self.speaking = False
                print("🔊 NEXUS speech stopped")
            except Exception as e:
                print(f"❌ Failed to stop speech: {e}")
    
    def is_speaking(self):
        """Check if currently speaking"""
        return self.speaking
    
    def get_available_voices(self):
        """Get list of available voices"""
        if not self.engine:
            return []
        
        voices = self.engine.getProperty('voices')
        return [
            {
                'id': voice.id,
                'name': voice.name,
                'gender': voice.gender,
                'languages': voice.languages
            }
            for voice in voices
        ]
    
    def set_voice(self, voice_id):
        """Set specific voice"""
        if not self.engine:
            return False
        
        try:
            self.engine.setProperty('voice', voice_id)
            print(f"🔊 Voice changed to: {voice_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to set voice: {e}")
            return False
    
    def test_voice(self):
        """Test voice output"""
        test_text = f"{self.node_name if hasattr(self, 'node_name') else 'NEXUS'} voice system online. All systems operational."
        self.speak(test_text)

# Test function
def test_tts():
    """Test TTS system"""
    tts = NexusTTS()
    
    print("Available voices:")
    for voice in tts.get_available_voices():
        print(f"  - {voice['name']}")
    
    print("\nTesting voice:")
    tts.test_voice()
    
    # Wait for speech to complete
    while tts.is_speaking():
        time.sleep(0.1)

if __name__ == "__main__":
    test_tts()
