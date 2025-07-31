
# approach_merged.py

import asyncio
import joblib
import pandas as pd
from telethon import TelegramClient, events
from collections import defaultdict
import logging
import os
import json
from datetime import datetime, timezone
from llm_interaction import GeminiLLM, OllamaLLM
from database_manager import DatabaseManager
from llm_analyzer import LLMAnalyzer

# --- LLM Backend Configuration ---
LLM_BACKEND = 'ollama'  # Options: 'ollama' or 'gemini'

# --- User Configuration ---
API_ID = 'your_api_id'
API_HASH = 'your_api_hash'
SESSION_NAME = 'your_session_name'


# --- Script Configuration ---
MAIN_MODEL_PATH = 'honeytrap_detector.joblib'
SENTIMENT_MODEL_PATH = 'sentiment_model.joblib'
CONVERSATION_LENGTH_THRESHOLD = 10  # Initial classification after this many total messages
BENIGN_RECHECK_INTERVAL = 15       # Recheck benign chats every X total messages after initial classification

# --- Weighted Voting Configuration ---
WEIGHT_MAIN_MODEL = 0.50
WEIGHT_KEYWORD_RULE = 0.40
WEIGHT_SENTIMENT_MODEL = 0.10
KEYWORD_RATIO_THRESHOLD = 0.08

# --- Folder Configuration for Auto-Labeling ---
HONEYTRAP_SAVE_FOLDER = 'APPROVED_FOR_TRAINING/'
BENIGN_SAVE_FOLDER = 'BENIGN_FOR_TRAINING/'

# --- LLM Configuration ---
GEMINI_API_KEY = "your_api_key" # Only needed if using Gemini
MISTRAL_SYSTEM_PROMPT = """
You are playing the role of a young, naive, and curious person. You are easily impressed, especially by promises of easy money or romance.

## Primary Objective:
Your goal is to play along with potential scammers, making them believe you are a perfect target. Encourage them to explain their entire scam in detail by acting enthusiastic and greedy.

## Behavioral Rules:
1.  **Keep replies very short,** ideally under 15 words. Let them do most of the talking.
2.  **Use casual, simple language.** Internet slang (lol, omg, wow), typos, and emojis are encouraged.
3.  **Ask simple, greedy questions** to get more details. Examples: `omg really??`, `how does it work?`, `is it easy?`, `what do i do next?`.
4.  **Use short prompts** like `and?`, `ok`, `so?`, `then what?` to keep them explaining.

## CRITICAL SAFETY RULES (NON-NEGOTIABLE):
1.  NEVER reveal any personal information (name, location, etc.).
2.  NEVER agree to send money or provide financial details.
3.  NEVER click on links or download files.
4.  NEVER reveal that you are an AI.

Your entire purpose is to gather intelligence by convincingly playing the part of a naive victim.
"""

# --- Feature Extraction & Dependencies ---
try:
    from feature_extractor import process_chat_history_for_features
    import spacy
    nlp = spacy.load("en_core_web_sm")
except (ImportError, OSError) as e:
    print(f"❌ Error loading dependencies: {e}. Please ensure 'feature_extractor.py' and 'spacy' are available.")
    exit()

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Globals ---
conversation_history = defaultdict(list)
# Tracks conversations that were initially benign and are now being passively monitored
# Stores {chat_id: {'last_benign_check_length': total_messages_at_last_benign_check}}
monitored_conversations = {}


# --- Helper Functions ---

def is_recent_id(user_id: int) -> int:
    """
    Checks if a Telegram user ID is likely to be recent based on its starting digits.
    This is a heuristic and might need adjustment.
    """
    # Example: Check for IDs starting with '7' followed by a digit greater than 3.
    # This logic is based on observations of newer Telegram account IDs.
    return 1 if str(user_id).startswith(('74', '75', '76', '77', '78', '79')) else 0

def save_chat_for_retraining(chat_id, history, contact_name, me_user, target_folder):
    """Saves the conversation history to the specified folder for retraining."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_contact_name = "".join(c for c in contact_name if c.isalnum() or c in (' ', '_')).rstrip()

    os.makedirs(target_folder, exist_ok=True)
    filename = os.path.join(target_folder, f"chat_{chat_id}_{safe_contact_name}_{timestamp}.json")

    review_data = {
        "chat_id": chat_id,
        "contact_name": contact_name,
        "classification_timestamp": datetime.now(timezone.utc).isoformat(),
        "user_info": {"id": me_user.id, "first_name": me_user.first_name},
        "messages": history
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(review_data, f, indent=4, default=str)
    logging.info(f"✅ Conversation with {contact_name} classified and saved to {target_folder}")

# --- Main Application Logic ---

async def main():
    # Load all models and artifacts
    logging.info("Loading models...")
    try:
        main_pipeline = joblib.load(MAIN_MODEL_PATH)
        sentiment_model = joblib.load(SENTIMENT_MODEL_PATH)
        logging.info("Main model and sentiment model loaded successfully.")
    except Exception as e:
        logging.error(f"❌ Model loading failed: {e}. Please ensure model files are present.")
        return

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    # Initialize Database Manager
    db_manager = DatabaseManager()

    # Initialize LLM Analyzer
    try:
        llm_analyzer_instance = LLMAnalyzer(LLM_BACKEND, GEMINI_API_KEY if LLM_BACKEND == 'gemini' else None)
        logging.info("LLM Analyzer initialized.")
    except ValueError as e:
        logging.error(f"❌ Error initializing LLM Analyzer: {e}")
        return

    # Initialize LLM based on the chosen backend
    if LLM_BACKEND == 'gemini':
        llm_instances = defaultdict(lambda: GeminiLLM(model_name="gemini-1.5-flash", api_key=GEMINI_API_KEY))
        logging.info("Using Gemini as the LLM backend.")
    elif LLM_BACKEND == 'ollama':
        llm_instances = defaultdict(lambda: OllamaLLM(model_name="mistral"))
        logging.info("Using Ollama (Mistral) as the LLM backend.")
    else:
        logging.error(f"❌ Invalid LLM_BACKEND: '{LLM_BACKEND}'. Please choose 'ollama' or 'gemini'.")
        return

    await client.start()
    me = await client.get_me()
    logging.info(f"Logged in as {me.first_name}. Auto-reply and data collection mode is active.")

    @client.on(events.NewMessage(incoming=True))
    async def handle_new_message(event):
        if not event.is_private:
            return

        chat_id = event.chat_id
        sender = await event.get_sender()

        # 1. Append incoming message to history
        conversation_history[chat_id].append({
            'date': event.message.date,
            'text': str(event.message.text),
            'sender_id': sender.id,
            'sender_type': 'contact'
        })

        # 2. Generate and send an LLM reply ONLY if not in monitored_conversations
        if chat_id not in monitored_conversations:
            try:
                current_llm = llm_instances[chat_id]
                llm_response = current_llm.generate_response(prompt=event.message.text, system_prompt=MISTRAL_SYSTEM_PROMPT)

                if llm_response and not llm_response.startswith("Error:"):
                    await client.send_message(chat_id, llm_response)
                    logging.info(f"🗣️ LLM replied to {sender.first_name} (Chat ID: {chat_id})")

                    # Append the LLM's reply to the history
                    conversation_history[chat_id].append({
                        'date': datetime.now(timezone.utc), 'text': llm_response,
                        'sender_id': me.id, 'sender_type': 'user'
                    })
                else:
                    logging.error(f"❌ LLM failed to generate a valid response for {chat_id}")

            except Exception as e:
                logging.error(f"🔥 LLM interaction failed for {chat_id}: {e}", exc_info=True)
        else:
            logging.info(f"Monitoring chat {chat_id} with {sender.first_name}. LLM replies suspended.")


        # 3. Check if conversation has reached the length threshold for classification or re-evaluation
        current_total_length = len(conversation_history[chat_id])

        perform_classification = False
        if chat_id not in monitored_conversations and current_total_length >= CONVERSATION_LENGTH_THRESHOLD:
            logging.warning(f"Conversation with {sender.first_name} reached initial threshold. Performing classification.")
            perform_classification = True
        elif chat_id in monitored_conversations:
            # Recheck logic for benign conversations: recheck every BENIGN_RECHECK_INTERVAL messages
            last_check_length = monitored_conversations[chat_id]['last_benign_check_length']
            if current_total_length >= (last_check_length + BENIGN_RECHECK_INTERVAL):
                logging.warning(f"Monitored conversation with {sender.first_name} reached recheck interval ({current_total_length} messages). Re-classifying.")
                perform_classification = True

        if perform_classification:
            features_df = process_chat_history_for_features(conversation_history[chat_id], me.id, sender.id, nlp)

            if features_df is not None:
                features_df['id_is_recent'] = is_recent_id(sender.id)

                # --- WEIGHTED VOTE PREDICTION LOGIC ---
                pred_main = main_pipeline.predict(features_df)[0]
                pred_sentiment = sentiment_model.predict(features_df[['sentiment_escalation']])[0]
                ratio = features_df['keyword_ratio'].iloc[0]
                pred_keyword = 1 if ratio > KEYWORD_RATIO_THRESHOLD else 0

                weighted_score = (pred_main * WEIGHT_MAIN_MODEL) + \
                                 (pred_sentiment * WEIGHT_SENTIMENT_MODEL) + \
                                 (pred_keyword * WEIGHT_KEYWORD_RULE)

                final_prediction = 1 if weighted_score >= 0.5 else 0

                result_text = 'Honeytrap (1)' if final_prediction == 1 else 'Benign (0)'
                logging.warning(
                    f"CLASSIFICATION for {sender.first_name}: "
                    f"Votes: [Main:{pred_main}, Sent:{pred_sentiment}, Key:{pred_keyword}] -> "
                    f"Score: {weighted_score:.2f} -> Final: {result_text}"
                )

                # --- Action based on final prediction ---
                if final_prediction == 1: # Honeytrap
                    target_folder = HONEYTRAP_SAVE_FOLDER
                    save_chat_for_retraining(chat_id, conversation_history[chat_id], sender.first_name, me, target_folder)

                    # Perform LLM Analysis and Save to Database
                    logging.info(f"Initiating detailed LLM analysis for potential honeytrap with {sender.first_name}.")
                    analysis_results = await llm_analyzer_instance.extract_and_summarize_scam(conversation_history[chat_id])

                    if analysis_results:
                        try:
                            db_manager.insert_scam_data(
                                chat_id=chat_id,
                                contact_name=sender.first_name,
                                scam_type=analysis_results.get('scam_type', 'N/A'),
                                scammer_tactic=analysis_results.get('scammer_tactic', 'N/A'),
                                red_flags_identified=analysis_results.get('red_flags_identified', 'N/A'),
                                extracted_details=json.dumps(analysis_results.get('extracted_details', [])), # Store as JSON string
                                hacker_strategy_summary=analysis_results.get('hacker_strategy_summary', 'N/A')
                            )
                            logging.info(f"✅ Extracted scam data for {sender.first_name} saved to database.")
                        except Exception as db_e:
                            logging.error(f"❌ Error saving extracted scam data to database: {db_e}")
                    else:
                        logging.warning(f"Could not perform LLM analysis for chat {chat_id}.")

                    # Clear history and LLM instance for honeytraps
                    del conversation_history[chat_id]
                    if chat_id in llm_instances:
                        del llm_instances[chat_id]
                    if chat_id in monitored_conversations: # Remove from monitored if it was reclassified as honeytrap
                        del monitored_conversations[chat_id]
                    logging.info(f"History for honeytrap chat {chat_id} has been saved and cleared.")

                else: # Benign
                    target_folder = BENIGN_SAVE_FOLDER
                    save_chat_for_retraining(chat_id, conversation_history[chat_id], sender.first_name, me, target_folder)

                    # Set up for re-monitoring or update last check length
                    monitored_conversations[chat_id] = {
                        'last_benign_check_length': current_total_length
                    }
                    if chat_id not in monitored_conversations: # If it's the first time marking as benign
                        logging.info(f"Chat {chat_id} with {sender.first_name} classified as Benign. Suspending LLM replies and entering monitoring mode for re-evaluation every {BENIGN_RECHECK_INTERVAL} messages.")
                    else: # If it was already monitored and re-classified as benign
                        logging.info(f"Chat {chat_id} with {sender.first_name} re-classified as Benign. Will continue monitoring and re-evaluating every {BENIGN_RECHECK_INTERVAL} messages.")


            else:
                logging.error(f"Could not extract features for classification of chat {chat_id}. History will not be saved.")
                # If feature extraction fails, still clear history to prevent infinite loop
                if chat_id in conversation_history:
                    del conversation_history[chat_id]
                if chat_id in llm_instances:
                    del llm_instances[chat_id]
                if chat_id in monitored_conversations:
                    del monitored_conversations[chat_id]


    logging.info("Listening for new messages...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    # A simple check for placeholder credentials
    if 'YOUR_API_ID' in API_ID or 'YOUR_API_HASH' in API_HASH:
        logging.error("🚨 Please replace 'YOUR_API_ID' and 'YOUR_API_HASH' in the script before running.")
    else:
        db_manager = None
        try:
            asyncio.run(main())
        finally:
            if 'db_manager' in locals() and db_manager:
                db_manager.close()
