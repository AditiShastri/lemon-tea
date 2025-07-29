# final_detector.py
"""
This script acts as a real-time security monitor for a Telegram account.
It listens for new messages, maintains conversation context, and uses a
pre-trained machine learning model to predict and alert for potential honeytraps.
"""

import asyncio
import joblib
import pandas as pd
from telethon import TelegramClient, events
from collections import defaultdict
import logging

# --- User Configuration ---
# IMPORTANT: Replace these with your actual Telegram API credentials.
# You can get these from my.telegram.org.
API_ID = 'YOUR_API_ID'
API_HASH = 'YOUR_API_HASH'
SESSION_NAME = 'telegram_security_monitor'

# --- Script Configuration ---
MODEL_PATH = 'honeytrap_detector.joblib'
# Number of consecutive "Honeytrap" predictions to trigger an alert.
THREAT_THRESHOLD = 3
# Maximum number of messages to keep in memory for each chat history.
MAX_HISTORY_LENGTH = 50

# --- Feature Extraction ---
# (Assuming feature_extractor.py is in the same directory)
try:
    from feature_extractor import (
        calculate_behavioral_features,
        calculate_linguistic_features,
        calculate_graph_proxy_features,
    )
    import spacy
    # Load the spaCy model once
    nlp = spacy.load("en_core_web_sm")
except (ImportError, OSError) as e:
    print(f"Error loading dependencies: {e}")
    print("Please ensure feature_extractor.py is in the same directory and you have run:")
    print("python -m spacy download en_core_web_sm")
    exit()


# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- Global Variables ---
# In-memory storage for conversation histories and threat counters.
conversation_history = defaultdict(list)
threat_counters = defaultdict(int)


def extract_features_from_history(chat_history_df, user_id, contact_id):
    """
    Extracts all required features from the chat history DataFrame.
    """
    if chat_history_df.empty:
        return None

    # Combine all feature extraction steps
    behavioral = calculate_behavioral_features(chat_history_df, user_id, contact_id)
    linguistic = calculate_linguistic_features(chat_history_df, nlp)
    graph = calculate_graph_proxy_features(chat_history_df)

    # Combine all features into a single dictionary
    all_features = {**behavioral, **linguistic, **graph}

    # The conceptual feature is not used by the model, so we remove it.
    if 'isolation_index_CONCEPTUAL' in all_features:
        del all_features['isolation_index_CONCEPTUAL']

    # Convert to DataFrame for the model
    return pd.DataFrame([all_features])


async def main():
    """
    Main function to initialize the client, load the model,
    and start listening for messages.
    """
    # --- Load the Model ---
    try:
        logging.info(f"Loading model from {MODEL_PATH}...")
        model = joblib.load(MODEL_PATH)
        logging.info("Model loaded successfully.")
    except FileNotFoundError:
        logging.error(f"Error: Model file not found at '{MODEL_PATH}'.")
        return
    except Exception as e:
        logging.error(f"An error occurred while loading the model: {e}")
        return

    # --- Initialize Telegram Client ---
    if API_ID == 'YOUR_API_ID' or API_HASH == 'YOUR_API_HASH':
        logging.error("Please replace 'YOUR_API_ID' and 'YOUR_API_HASH' with your credentials.")
        return

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    try:
        await client.start()
        logging.info("Telegram client started successfully.")
        me = await client.get_me()
        logging.info(f"Logged in as {me.first_name} (ID: {me.id})")
    except Exception as e:
        logging.error(f"Failed to start Telegram client: {e}")
        return

    @client.on(events.NewMessage(incoming=True))
    async def handle_new_message(event):
        """
        Event handler for new incoming messages.
        """
        # We are only interested in private chats
        if not event.is_private:
            return

        chat_id = event.chat_id
        sender = await event.get_sender()
        message_text = event.message.text
        message_date = event.message.date

        logging.info(f"New message from {sender.first_name} (Chat ID: {chat_id}): '{message_text}'")

        # --- Maintain Conversation History ---
        # Add the new message to the history
        conversation_history[chat_id].append({
            'date': message_date,
            'text': message_text,
            'sender_id': sender.id,
            'sender_type': 'contact' # Since it's an incoming message
        })

        # Keep the history from getting too long
        if len(conversation_history[chat_id]) > MAX_HISTORY_LENGTH:
            conversation_history[chat_id].pop(0)

        # Create a DataFrame from the history
        history_df = pd.DataFrame(conversation_history[chat_id])
        history_df['date'] = pd.to_datetime(history_df['date'])

        # --- Analyze in Real-Time ---
        features_df = extract_features_from_history(history_df, me.id, sender.id)

        if features_df is None:
            logging.warning(f"Could not extract features for chat {chat_id}. Not enough data.")
            return

        # --- Predict Risk ---
        try:
            prediction = model.predict(features_df)[0]
            logging.info(f"Prediction for chat {chat_id}: {prediction}")

            # --- Alert Intelligently ---
            if prediction == 'Honeytrap':
                threat_counters[chat_id] += 1
                logging.warning(f"Threat detected for chat {chat_id}. Counter: {threat_counters[chat_id]}")
                if threat_counters[chat_id] >= THREAT_THRESHOLD:
                    alert_message = (
                        f"🚨 HIGH-RISK ALERT 🚨\n"
                        f"Consecutive threats detected in chat with {sender.first_name} (ID: {chat_id}).\n"
                        f"Please review this conversation carefully."
                    )
                    # Send alert to your "Saved Messages"
                    await client.send_message('me', alert_message)
                    logging.critical(f"High-risk alert sent for chat {chat_id}.")
                    # Reset counter after sending an alert to avoid spamming
                    threat_counters[chat_id] = 0
            else: # Benign
                # If the conversation is benign, reset the counter.
                if threat_counters[chat_id] > 0:
                    logging.info(f"Threat counter for chat {chat_id} reset to 0.")
                    threat_counters[chat_id] = 0

        except Exception as e:
            logging.error(f"An error occurred during prediction for chat {chat_id}: {e}")


    logging.info("Listening for new messages...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    # Ensure the event loop is managed correctly
    try:
        asyncio.run(main())
    except (ValueError, TypeError) as e:
        # This can happen if the API ID/Hash are not integers.
        logging.error(f"Configuration error: {e}. Please ensure API_ID is an integer.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
