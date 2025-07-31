# llm_interaction.py
import requests
import json
import logging
import google.generativeai as genai

# --- Ollama Class ---
class OllamaLLM:
    """A class to interact with a local LLM served by Ollama."""
    def __init__(self, model_name='mistral', host='http://localhost:11434'):
        self.model_name = model_name
        self.host = host
        self.api_url = f"{host}/api/generate"
        logging.info(f"OllamaLLM initialized for model: '{self.model_name}' at {self.host}")

    def generate_response(self, prompt, system_prompt):
        """Sends a prompt to the Ollama API and gets a response."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            response_data = response.json()
            return response_data.get('response', '').strip()
        except requests.exceptions.RequestException as e:
            logging.error(f"Ollama API request failed: {e}")
            return f"Error: Could not connect to Ollama server at {self.host}."
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON response from Ollama.")
            return "Error: Invalid response from Ollama server."

# --- Gemini Class ---
class GeminiLLM:
    """A class to interact with the Google Gemini API."""
    def __init__(self, model_name='gemini-1.5-flash', api_key=None):
        if not api_key:
            raise ValueError("Gemini API key is required.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logging.info(f"GeminiLLM initialized for model: '{model_name}'")

    def generate_response(self, prompt, system_prompt):
        """Sends a prompt to the Gemini API and gets a response."""
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAI:"
        try:
            response = self.model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            logging.error(f"Gemini API request failed: {e}")
            return f"Error: Gemini API call failed."