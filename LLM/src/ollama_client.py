"""
Ollama API client for local LLM inference.
"""

import json
import requests


_OLLAMA_FORMAT_JSON_SUPPORTED = None  # None=unknown, True=supported, False=disabled


def call_ollama_api(prompt, ollama_model_name, ollama_api_url="http://localhost:11434/api/generate", output_format=None):
    """
    Generic function to call the Ollama generate API with safe formatting and auto-disable.

    - If output_format == "json", we attempt one request with format="json" unless previously disabled.
    - On the first failure (HTTP error or JSON parse problem), we permanently disable format usage
      for this kernel session and retry without format. Subsequent calls skip the format attempt.
      
    Args:
        prompt: The prompt text to send to the model
        ollama_model_name: Name of the Ollama model to use
        ollama_api_url: URL of the Ollama API endpoint
        output_format: Optional output format (e.g., "json")
        
    Returns:
        str: Response text from the model, or None if call fails
    """
    global _OLLAMA_FORMAT_JSON_SUPPORTED

    headers = {'Content-Type': 'application/json'}

    def _build_payload(include_format: bool):
        payload = {
            "model": ollama_model_name,
            "prompt": prompt,
            "stream": False
        }
        if include_format and isinstance(output_format, str) and output_format.lower() == "json":
            payload["format"] = "json"
        return payload

    def _post(payload):
        resp = requests.post(ollama_api_url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns {response: "..."}
        return data.get('response', '').strip()

    wants_json = isinstance(output_format, str) and output_format.lower() == "json"

    # First attempt with format if requested and not known-bad
    if wants_json and _OLLAMA_FORMAT_JSON_SUPPORTED is not False:
        try:
            response_text = _post(_build_payload(include_format=True))
            # If we got here, it worked
            _OLLAMA_FORMAT_JSON_SUPPORTED = True
            return response_text
        except requests.exceptions.RequestException as e:
            # Disable for future calls and fall back silently
            if _OLLAMA_FORMAT_JSON_SUPPORTED is not False:
                print("Ollama format=\"json\" appears unsupported; disabling and retrying without format.")
            _OLLAMA_FORMAT_JSON_SUPPORTED = False
        except Exception as e:
            if _OLLAMA_FORMAT_JSON_SUPPORTED is not False:
                print("Unexpected error using format=\"json\"; disabling and retrying without format.")
            _OLLAMA_FORMAT_JSON_SUPPORTED = False

    # Fallback: no format
    try:
        return _post(_build_payload(include_format=False))
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API (no format): {e}")
        return None
    except Exception as e:
        print(f"Unexpected error (no format): {e}")
        return None
