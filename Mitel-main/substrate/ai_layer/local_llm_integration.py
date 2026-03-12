#!/usr/bin/env python3
"""
Local LLM Integration - TinyLlama
==================================

Integrates TinyLlama model for local AI inference.
Works with GGUF format models downloaded from Hugging Face.
"""

import sys
import os
import logging
from typing import Optional, Dict, Any, List

# Add paths
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import llama-cpp-python
LLAMA_CPP_AVAILABLE = False
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    logger.warning("[LOCAL_LLM] llama-cpp-python not available. Install with: pip install llama-cpp-python")


class LocalLLM:
    """
    Local LLM wrapper for TinyLlama.
    
    Uses llama-cpp-python to load GGUF models.
    """
    
    DEFAULT_MODEL_PATH = os.path.expanduser("~/.omni/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
    
    def __init__(self, model_path: Optional[str] = None, n_ctx: int = 2048, n_threads: int = 4):
        """
        Initialize local LLM.
        
        Args:
            model_path: Path to GGUF model file (default: ~/.omni/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf)
            n_ctx: Context window size
            n_threads: Number of CPU threads
        """
        if not LLAMA_CPP_AVAILABLE:
            raise ImportError("llama-cpp-python not available. Install with: pip install llama-cpp-python")
        
        self.model_path = model_path or self.DEFAULT_MODEL_PATH
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        logger.info(f"[LOCAL_LLM] Loading model: {self.model_path}")
        
        try:
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=0,  # CPU only for now (set to >0 for GPU)
                verbose=False
            )
            logger.info("[LOCAL_LLM] Model loaded successfully")
        except Exception as e:
            logger.error(f"[LOCAL_LLM] Failed to load model: {e}")
            raise
    
    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7,
                 stop: List[str] = None) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: Stop sequences
            
        Returns:
            Generated text
        """
        if stop is None:
            stop = ["</s>", "<|user|>", "<|system|>"]
        
        try:
            output = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                echo=False
            )
            
            generated_text = output['choices'][0]['text'].strip()
            return generated_text
        except Exception as e:
            logger.error(f"[LOCAL_LLM] Generation failed: {e}")
            return ""
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 256,
             temperature: float = 0.7) -> str:
        """
        Chat completion API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Assistant response
        """
        # Format messages using Zephyr template
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"<|system|>\n{content}</s>")
            elif role == 'user':
                prompt_parts.append(f"<|user|>\n{content}</s>")
            elif role == 'assistant':
                prompt_parts.append(f"<|assistant|>\n{content}</s>")
        
        # Add assistant prompt
        prompt_parts.append("<|assistant|>\n")
        prompt = "\n".join(prompt_parts)
        
        return self.generate(prompt, max_tokens=max_tokens, temperature=temperature)
    
    def analyze_transfer_decision(self, file_path: str, file_size: int,
                                 network_conditions: Dict[str, float]) -> Dict[str, Any]:
        """
        Use LLM to analyze file transfer decision.
        
        Args:
            file_path: File path
            file_size: File size in bytes
            network_conditions: Network metrics (bandwidth, latency, etc.)
            
        Returns:
            Analysis dict with recommendations
        """
        prompt = f"""Analyze this file transfer scenario:
File: {file_path}
Size: {file_size / (1024*1024):.2f} MB
Network: {network_conditions.get('bandwidth_mbps', 0):.1f} Mbps, {network_conditions.get('latency_ms', 0):.1f}ms latency

Recommend:
1. Optimal chunk size (in KB)
2. Priority level (CRITICAL, HIGH, NORMAL, LOW)
3. Should retry if failed (yes/no)
4. Reasoning

Format as JSON with keys: chunk_size_kb, priority, should_retry, reasoning"""

        response = self.generate(prompt, max_tokens=200, temperature=0.3)
        
        # Parse response (simplified - in production would use proper JSON parsing)
        return {
            'analysis': response,
            'model': 'TinyLlama-1.1B'
        }


# Export
__all__ = ['LocalLLM', 'LLAMA_CPP_AVAILABLE']
