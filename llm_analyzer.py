# llm_analyzer.py
from llm_interaction import GeminiLLM, OllamaLLM
import json
import logging

class LLMAnalyzer:
    def __init__(self, llm_backend, api_key=None):
        self.llm_backend = llm_backend
        self.api_key = api_key
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        if self.llm_backend == 'gemini':
            if not self.api_key:
                raise ValueError("API Key is required for Gemini LLM backend.")
            return GeminiLLM(model_name="gemini-1.5-flash", api_key=self.api_key)
        elif self.llm_backend == 'ollama':
            return OllamaLLM(model_name="mistral")
        else:
            raise ValueError(f"Unsupported LLM backend: {self.llm_backend}")

    async def extract_and_summarize_scam(self, conversation_history):
        full_conversation = "\n".join([f"{msg['sender_type']}: {msg['text']}" for msg in conversation_history])

        extraction_prompt = f"""
        Analyze the following conversation to extract specific details about a potential scam and summarize the scammer's strategy.

        Conversation:
        ---
        {full_conversation}
        ---

        Please provide your output in a JSON format with the following keys:
        - "scam_type": (e.g., "Investment Scam", "Romance Scam", "Job Scam", "Pig Butchering Scam", "Tech Support Scam", "Lottery Scam", "Phishing")
        - "scammer_tactic": A brief description of the primary tactic used by the scammer (e.g., "building fake romantic relationship", "offering high returns on fake investments", "impersonating tech support").
        - "red_flags_identified": A comma-separated list of red flags observed (e.g., "unsolicited contact", "promises of guaranteed high returns", "pressure to act quickly", "request for personal information", "poor grammar").
        - "extracted_details": A list of specific pieces of information extracted about the scam (e.g., "platform mentioned: fake-investments.com", "requested amount: $500", "contact method: WhatsApp", "fake company name: Global Wealth Management").
        - "hacker_strategy_summary": A 2-3 sentence summary of the scammer's overall strategy.

        If a piece of information is not present or cannot be confidently determined, use "N/A" or an empty list/string as appropriate.
        """

        try:
            response_text = self.llm.generate_response(prompt=extraction_prompt)
            if response_text and not response_text.startswith("Error:"):
                # Attempt to parse the JSON response. The LLM might include conversational filler.
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_string = response_text[json_start:json_end]
                    analysis = json.loads(json_string)
                    return analysis
                else:
                    logging.error(f"LLM response did not contain valid JSON: {response_text}")
                    return None
            else:
                logging.error(f"LLM failed to generate a valid analysis response: {response_text}")
                return None
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from LLM response: {e}\nResponse was: {response_text}")
            return None
        except Exception as e:
            logging.error(f"Error during LLM analysis: {e}", exc_info=True)
            return None