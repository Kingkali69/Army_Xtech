# Jarvis Voice Integration Report

## What I Found

### ✅ Voice Capabilities Present:
1. **VoiceIO Module** (`Evolving.py`)
   - Uses `speech_recognition` (Google API - needs internet)
   - Uses `pyttsx3` for text-to-speech (offline)
   - Basic listen/speak functionality

2. **Wake Word Detection** (`level2.py`)
   - Wake word: "ghost" or "trinity"
   - Uses `phrase_time_limit=2` (2 second listening window)
   - Currently requires wake word before listening

3. **Trinity Architecture**
   - GhostCore, EchoCore, ShellCore
   - Multi-agent system
   - Memory system (Flash, Session, Spectral)
   - Already has voice integration points

### ❌ Missing Features:
1. **2-Second Pause Detection** - Not implemented
   - User wants: Talk → 2 second pause → Jarvis responds
   - Current: Requires wake word first

2. **Offline Speech Recognition** - Uses Google API
   - Needs internet connection
   - Should use offline STT (Vosk, Whisper, etc.)

3. **Continuous Listening** - Not implemented
   - User mentioned "listen all the time"
   - Current: Only listens after wake word

---

## Integration Plan: Jarvis + NEXUS

### Phase 1: Voice Interface for NEXUS

**Goal:** Add voice interface to NEXUS so you can talk instead of type.

**Components Needed:**
1. **Voice Input Module** (Offline STT)
   - Replace Google API with Vosk (offline, lightweight)
   - Or use Whisper.cpp (better accuracy, heavier)

2. **2-Second Pause Detection**
   - Continuous listening
   - Detect silence for 2 seconds
   - Trigger NEXUS response

3. **Voice Output Module**
   - Use pyttsx3 (already in Jarvis)
   - NEXUS speaks responses

**File Structure:**
```
substrate/ai_layer/voice_interface.py
  - VoiceInput (offline STT)
  - VoiceOutput (TTS)
  - SilenceDetector (2-second pause)
  - VoiceLoop (continuous listening)
```

### Phase 2: Integration with NEXUS

**Integration Points:**
1. Replace text input in `omni_ai_chat.py` with voice
2. Add voice output to NEXUS responses
3. Connect to Trinity-enhanced LLM

**Flow:**
```
Microphone → VoiceInput (Vosk) → Text
  ↓
2-second pause detected
  ↓
Text → NEXUS (Trinity LLM) → Response
  ↓
Response → VoiceOutput (pyttsx3) → Speaker
```

---

## Implementation Options

### Option A: Lightweight (Vosk)
- **Pros:** Small model, fast, offline
- **Cons:** Lower accuracy than Whisper
- **Model Size:** ~50MB
- **Good for:** TinyLlama-sized system

### Option B: Better Accuracy (Whisper.cpp)
- **Pros:** Much better accuracy, offline
- **Cons:** Larger model, more CPU
- **Model Size:** ~75MB (base) to 1.5GB (large)
- **Good for:** Better understanding

### Option C: Hybrid (Wake Word + Continuous)
- **Pros:** Saves CPU, privacy-friendly
- **Cons:** Requires wake word
- **Flow:** Wake word → Listen → 2-second pause → Respond

---

## Recommended Approach

**For TinyLlama + NEXUS:**

1. **Use Vosk** (lightweight, offline)
   - Model: `vosk-model-small-en-us-0.15` (~40MB)
   - Fast enough for real-time
   - Works offline

2. **Implement 2-Second Pause Detection**
   - Continuous listening
   - Detect silence threshold
   - After 2 seconds → send to NEXUS

3. **Use pyttsx3** (already in Jarvis)
   - Offline TTS
   - Cross-platform
   - Simple integration

4. **Integrate with NEXUS**
   - Replace chat input with voice
   - Add voice output to responses
   - Keep Trinity intelligence

---

## Next Steps

1. ✅ **Create Voice Interface Module**
   - VoiceInput (Vosk)
   - SilenceDetector (2-second pause)
   - VoiceOutput (pyttsx3)

2. ✅ **Integrate with NEXUS**
   - Modify `omni_ai_chat.py` to use voice
   - Connect to Trinity-enhanced LLM

3. ✅ **Test**
   - Talk → 2-second pause → NEXUS responds
   - Verify offline operation

**Ready to build?** 🎤
