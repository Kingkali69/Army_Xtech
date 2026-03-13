#!/usr/bin/env python3
"""
GhostAI - Mistral 7B Local Inference Wrapper
Loads Mistral 7B from local directory and provides production-ready inference.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List


class MistralLocal:
    """Local Mistral 7B inference wrapper with production settings."""

    # Model search paths (in priority order)
    MODEL_SEARCH_PATHS = [
        "~/models/mistral-7b",
        "~/models/mistral",
        "./models/mistral-7b",
        "./models/mistral",
        "/opt/models/mistral-7b",
        "/opt/models/mistral",
        "C:/models/mistral-7b",
        "C:/models/mistral",
    ]

    # Production inference parameters
    DEFAULT_TEMPERATURE = 0.3  # Consistent, low randomness
    DEFAULT_MAX_TOKENS = 2048  # Sufficient for detailed contract analysis
    DEFAULT_CONTEXT_LENGTH = 4096  # Full contract context

    SYSTEM_PROMPT = (
        "You are a security analyst. Parse penetration test contracts and extract intelligence. "
        "Be precise, structured, and focus on extracting actionable information about scope, "
        "targets, allowed tools, restrictions, timelines, and legal boundaries."
    )

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize Mistral 7B inference wrapper.

        Args:
            model_path: Explicit path to model directory. If None, auto-detect.
        """
        self.model_path = model_path or self._find_model()
        self.model = None
        self.tokenizer = None
        self._backend = None

        # Load model
        self._load_model()

    def _find_model(self) -> str:
        """Auto-detect Mistral 7B model location."""
        print("[GhostAI] Searching for Mistral 7B model...")

        for path_str in self.MODEL_SEARCH_PATHS:
            path = Path(path_str).expanduser()
            if path.exists():
                # Check for common model files
                has_gguf = list(path.glob("*.gguf"))
                has_safetensors = list(path.glob("*.safetensors"))
                has_bin = list(path.glob("*.bin"))

                if has_gguf or has_safetensors or has_bin:
                    print(f"[GhostAI] Found model at: {path}")
                    return str(path)

        # Model not found - return None to trigger mock mode
        print("[GhostAI] Model not found in standard locations")
        print("[GhostAI] Will use MOCK mode for testing")
        print("\nTo use real Mistral 7B inference:")
        for i, p in enumerate(self.MODEL_SEARCH_PATHS[:4], 1):
            print(f"  {i}. Place model in: {p}")

        return None

    def _load_model(self):
        """Load Mistral 7B model using available backend."""
        # No model path - use mock mode
        if not self.model_path:
            print("[GhostAI] Using MOCK mode (no model loaded)")
            self._backend = "mock"
            return

        print(f"[GhostAI] Loading model from: {self.model_path}")

        # Try llama-cpp-python first (fastest for GGUF models)
        if self._try_load_llama_cpp():
            return

        # Try transformers (for safetensors/pytorch models)
        if self._try_load_transformers():
            return

        # Fallback: Mock mode for development/testing
        print("[GhostAI] WARNING: No ML backend available, using MOCK mode")
        print("[GhostAI] Install: pip install llama-cpp-python OR pip install transformers torch")
        self._backend = "mock"

    def _try_load_llama_cpp(self) -> bool:
        """Try loading with llama-cpp-python (best for GGUF models)."""
        try:
            from llama_cpp import Llama

            # Find GGUF file
            model_files = list(Path(self.model_path).glob("*.gguf"))
            if not model_files:
                return False

            model_file = str(model_files[0])
            print(f"[GhostAI] Loading GGUF model: {model_file}")

            self.model = Llama(
                model_path=model_file,
                n_ctx=self.DEFAULT_CONTEXT_LENGTH,
                n_threads=4,
                n_gpu_layers=0,  # CPU mode (set to -1 for full GPU)
                verbose=False
            )

            self._backend = "llama-cpp"
            print("[GhostAI] ✓ Loaded with llama-cpp-python")
            return True

        except ImportError:
            return False
        except Exception as e:
            print(f"[GhostAI] llama-cpp load failed: {e}")
            return False

    def _try_load_transformers(self) -> bool:
        """Try loading with transformers (for safetensors/pytorch models)."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            print(f"[GhostAI] Loading with transformers...")

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )

            self._backend = "transformers"
            print("[GhostAI] ✓ Loaded with transformers")
            return True

        except ImportError:
            return False
        except Exception as e:
            print(f"[GhostAI] transformers load failed: {e}")
            return False

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate response from Mistral 7B.

        Args:
            prompt: User prompt
            temperature: Sampling temperature (default: 0.3)
            max_tokens: Max output tokens (default: 2048)
            system_prompt: System prompt override

        Returns:
            Generated text response
        """
        temp = temperature or self.DEFAULT_TEMPERATURE
        max_tok = max_tokens or self.DEFAULT_MAX_TOKENS
        sys_prompt = system_prompt or self.SYSTEM_PROMPT

        # Build full prompt
        full_prompt = f"<s>[INST] {sys_prompt}\n\n{prompt} [/INST]"

        if self._backend == "llama-cpp":
            return self._generate_llama_cpp(full_prompt, temp, max_tok)
        elif self._backend == "transformers":
            return self._generate_transformers(full_prompt, temp, max_tok)
        else:
            return self._generate_mock(prompt)

    def _generate_llama_cpp(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate with llama-cpp-python."""
        output = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            echo=False,
            stop=["</s>", "[INST]"]
        )
        return output['choices'][0]['text'].strip()

    def _generate_transformers(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate with transformers."""
        import torch

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract only the generated part (after prompt)
        response = response.split("[/INST]")[-1].strip()
        return response

    def _generate_mock(self, prompt: str) -> str:
        """Mock generation for development/testing."""
        return json.dumps({
            "TARGET_SYSTEMS": ["example.com", "192.168.1.0/24"],
            "SCOPE": ["Web application", "Internal network"],
            "TOOLS_ALLOWED": ["Nmap", "Burp Suite", "Metasploit"],
            "RESTRICTIONS": ["No DoS attacks", "No data exfiltration"],
            "TIMELINE": "2 weeks",
            "LEGAL_BOUNDARIES": ["Written authorization required", "Report findings only to client"]
        }, indent=2)

    def extract_json(self, text: str) -> Optional[Dict]:
        """
        Extract JSON from model response.
        Handles various formats and markdown code blocks.
        """
        # Try direct JSON parse
        try:
            return json.loads(text)
        except:
            pass

        # Extract from code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            try:
                return json.loads(text[start:end].strip())
            except:
                pass

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            try:
                return json.loads(text[start:end].strip())
            except:
                pass

        # Try to find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except:
                pass

        return None


def test_mistral_local():
    """Test Mistral local inference."""
    print("=" * 60)
    print("GhostAI - Mistral 7B Local Inference Test")
    print("=" * 60)

    try:
        # Initialize
        mistral = MistralLocal()

        # Test prompt
        test_prompt = """
        Parse this contract excerpt:

        "The penetration test will target the web application at https://example.com
        and internal network 192.168.1.0/24. Testing period: January 15-30, 2024.
        Authorized tools: Nmap, Burp Suite, SQLMap.
        RESTRICTIONS: No denial of service attacks, no data exfiltration."

        Extract the key information in JSON format.
        """

        print("\n[TEST] Generating response...")
        response = mistral.generate(test_prompt.strip())

        print("\n[RESPONSE]")
        print(response)

        print("\n[JSON EXTRACTION]")
        json_data = mistral.extract_json(response)
        if json_data:
            print(json.dumps(json_data, indent=2))
        else:
            print("Could not extract JSON")

        print("\n" + "=" * 60)
        print("✓ Test complete")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_mistral_local()
