"""
NEXUS Voice Interface Package
==============================

Ambient voice control for NEXUS omnipresent system.
"""

from .nexus_voice import NexusVoiceInterface
from .nexus_brain import NexusBrain
from .nexus_tts import NexusTTS
from .nexus_api import NexusAPI

__version__ = "1.0.0"
__author__ = "NEXUS Development"

# Main interface
def create_voice_interface():
    """Create NEXUS voice interface"""
    return NexusVoiceInterface()

# Quick start function
def start_voice():
    """Quick start voice interface"""
    interface = create_voice_interface()
    interface.start_listening()
    return interface
