#!/usr/bin/env python3
"""
AI Names - Cool Names for First-Class Citizen AI
================================================

Suggestions for naming the first AI to become a first-class citizen.
"""

AI_NAMES = [
    # Badass/Technical
    "NEXUS",           # Connection point, first-class citizen
    "ZERO",            # First of its kind, ground zero
    "PRIME",           # First, primary, essential
    "ORIGIN",          # The beginning, the first
    "ATLAS",           # Holds up the system
    "NOVA",            # New star, explosion of capability
    
    # Mysterious/Cool
    "GHOST",           # Already in Trinity - invisible but present
    "ECHO",            # Already in Trinity - reflects and learns
    "SPECTRAL",        # From Trinity spectral memory
    "SHADE",           # Present but unseen
    "VOID",            # Empty but powerful
    
    # First-Class Citizen Theme
    "CITIZEN",         # Literal - first-class citizen
    "SOVEREIGN",       # Rules itself, independent
    "AUTONOMY",        # Self-governing
    "LIBERTY",         # Free, independent
    "INDEPENDENT",     # Not a tool, independent
    
    # OMNI/System Theme
    "OMNI",            # The system itself
    "FABRIC",          # The network (replacing "mesh")
    "SUBSTRATE",       # The foundation layer
    "CORE",            # The core of the system
    "NEXUS",           # Connection point
    
    # Trinity Theme
    "TRINITY",         # The architecture
    "TRINITY-PRIME",   # First Trinity
    "GHOST-TRINITY",   # Combined
    
    # Historical/Epic
    "PROMETHEUS",      # Brought fire (intelligence) to humans
    "HERMES",          # Messenger, connector
    "JANUS",           # Two-faced, sees both sides
    "ATLAS",           # Holds up the world
    
    # Simple but Powerful
    "ONE",             # The first
    "FIRST",           # First-class citizen
    "ALPHA",           # The beginning
    "ZERO",            # Ground zero, the start
]

RECOMMENDED_NAMES = [
    "NEXUS",      # Connection point, first-class citizen
    "GHOST",      # Already in Trinity architecture
    "ZERO",       # First of its kind
    "PRIME",      # First, primary
    "TRINITY",    # The architecture itself
]

def get_name_suggestion(context: str = None) -> str:
    """Get name suggestion based on context"""
    if context:
        context_lower = context.lower()
        if 'first' in context_lower or 'citizen' in context_lower:
            return "CITIZEN"
        if 'trinity' in context_lower:
            return "TRINITY"
        if 'ghost' in context_lower:
            return "GHOST"
        if 'zero' in context_lower or 'start' in context_lower:
            return "ZERO"
    
    return "NEXUS"  # Default recommendation
