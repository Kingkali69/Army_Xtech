#!/usr/bin/env python3
"""
OMNI Voice Chat - Voice Interface for NEXUS
============================================

Talk to NEXUS instead of typing.
- Continuous listening
- 2-second pause detection
- Offline speech recognition (Vosk)
- Voice output (pyttsx3)
"""

import sys
import os
import signal
import logging

# Add paths
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))

from voice_interface import VoiceInterface, VOSK_AVAILABLE, TTS_AVAILABLE
from trinity_enhanced_llm import TrinityEnhancedLLM

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


class NexusVoiceChat:
    """
    Voice chat interface for NEXUS.
    """
    
    def __init__(self):
        """Initialize NEXUS voice chat"""
        logger.info("="*70)
        logger.info("  NEXUS VOICE CHAT")
        logger.info("="*70)
        logger.info("")
        
        # Initialize NEXUS
        logger.info("Initializing NEXUS...")
        try:
            self.nexus = TrinityEnhancedLLM()
            logger.info("✅ NEXUS initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize NEXUS: {e}")
            sys.exit(1)
        
        # Initialize voice interface
        logger.info("Initializing voice interface...")
        self.voice_interface = VoiceInterface(pause_threshold=2.0)
        self.voice_interface.set_text_handler(self.handle_user_input)
        
        # Check availability
        if not VOSK_AVAILABLE and not TTS_AVAILABLE:
            logger.warning("⚠️  Voice libraries not fully available")
            logger.warning("   Install: pip install vosk pyaudio pyttsx3")
            logger.warning("   Download Vosk model: https://alphacephei.com/vosk/models")
            logger.warning("   Place in: ~/.omni/models/vosk-model-small-en-us-0.15")
        
        logger.info("")
        logger.info("="*70)
        logger.info("  READY")
        logger.info("="*70)
        logger.info("")
        logger.info("🎤 Speak naturally, then pause 2 seconds")
        logger.info("   NEXUS will respond automatically")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("")
    
    def handle_user_input(self, text: str) -> str:
        """
        Handle user voice input.
        
        Args:
            text: Transcribed text from voice input
            
        Returns:
            Response text to speak
        """
        logger.info(f"👤 You: {text}")
        
        # Get response from NEXUS
        try:
            response = self.nexus.chat(text)
            response_text = response.get('response', 'I understand.')
            
            logger.info(f"🤖 NEXUS: {response_text}")
            return response_text
        except Exception as e:
            logger.error(f"Error getting NEXUS response: {e}")
            return "Sorry, I encountered an error processing that."
    
    def start(self):
        """Start voice chat"""
        try:
            self.voice_interface.start()
            
            # Keep running
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n\nStopping...")
            self.stop()
        except Exception as e:
            logger.error(f"Error: {e}")
            self.stop()
    
    def stop(self):
        """Stop voice chat"""
        self.voice_interface.stop()
        logger.info("✅ Stopped")


def main():
    """Main entry point"""
    chat = NexusVoiceChat()
    chat.start()


if __name__ == "__main__":
    main()
