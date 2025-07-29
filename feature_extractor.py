# feature_extractor.py
"""
This script loads a Telegram chat history from a JSON file, processes it,
and calculates a variety of behavioral, linguistic, and graph-based features
to be used for machine learning analysis.
"""
import json
import re
from datetime import timedelta
from pprint import pprint

import pandas as pd
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- SCRIPT CONFIGURATION ---
CHAT_JSON_FILE = 'chat_data.json'


def calculate_behavioral_features(df_chat, user_id, contact_id):
    """Calculates features based on the timing and patterns of messages."""
    features = {}
    
    user_messages = df_chat[df_chat['sender_type'] == 'user']
    contact_messages = df_chat[df_chat['sender_type'] == 'contact']

    # --- Response Latency Ratio ---
    avg_user_latency = user_messages['date'].diff().mean().total_seconds()
    avg_contact_latency = contact_messages['date'].diff().mean().total_seconds()
    
    if avg_user_latency and avg_user_latency > 0 and avg_contact_latency:
        features['latency_ratio'] = avg_contact_latency / avg_user_latency
    else:
        features['latency_ratio'] = 0

    # --- Question Ratio ---
    contact_questions = contact_messages['text'].str.contains(r'\?').sum()
    total_contact_messages = len(contact_messages)
    features['contact_question_ratio'] = contact_questions / total_contact_messages if total_contact_messages > 0 else 0

    # --- Initiation Rate (Simplified: new session after 1 hour of silence) ---
    time_diffs = df_chat['date'].diff() > timedelta(hours=1)
    initiations = df_chat[time_diffs]
    contact_initiations = initiations[initiations['sender_type'] == 'contact']
    total_initiations = len(initiations)
    features['contact_initiation_rate'] = len(contact_initiations) / total_initiations if total_initiations > 0 else 0

    # --- Session Timing (Unsociable Hours: 1 AM - 6 AM) ---
    unsociable_hours = df_chat['date'].dt.hour.between(1, 6).sum()
    features['unsociable_hours_ratio'] = unsociable_hours / len(df_chat) if len(df_chat) > 0 else 0

    return features


def calculate_linguistic_features(df_chat, nlp_model):
    """Calculates features based on the content and sentiment of messages."""
    features = {}
    contact_text = " ".join(df_chat[df_chat['sender_type'] == 'contact']['text'].astype(str))
    
    # --- Sentiment Analysis ---
    analyzer = SentimentIntensityAnalyzer()
    df_chat['sentiment'] = df_chat['text'].astype(str).apply(lambda text: analyzer.polarity_scores(text)['compound'])
    features['avg_contact_sentiment'] = df_chat[df_chat['sender_type'] == 'contact']['sentiment'].mean()
    
    # --- Keyword and Entity Analysis ---
    emotional_words = {'lonely', 'sad', 'trust', 'secret', 'desperate', 'afraid'}
    financial_words = {'investment', 'crypto', 'profit', 'guarantee', 'bank', 'money', 'rich'}
    urgent_words = {'now', 'quick', 'immediately', 'urgent', 'hurry'}
    
    text_lower = contact_text.lower()
    features['emotional_word_count'] = sum(1 for word in emotional_words if word in text_lower)
    features['financial_word_count'] = sum(1 for word in financial_words if word in text_lower)
    features['urgent_word_count'] = sum(1 for word in urgent_words if word in text_lower)

    doc = nlp_model(contact_text)
    features['money_entity_count'] = len([ent for ent in doc.ents if ent.label_ == 'MONEY'])

    return features


def calculate_graph_proxy_features(df_chat):
    """Calculates proxy features for graph-based analysis from a single chat."""
    features = {}
    
    # --- Proxy for Centrality: Interaction Frequency ---
    chat_duration_days = (df_chat['date'].max() - df_chat['date'].min()).days
    # Ensure duration is at least 1 to avoid division by zero for short chats
    chat_duration_days = max(chat_duration_days, 1)
    features['messages_per_day'] = len(df_chat) / chat_duration_days

    # --- Proxy for Isolation Index (Conceptual) ---
    features['isolation_index_CONCEPTUAL'] = "Requires data from ALL user chats for a real calculation."

    return features


def main():
    """Main function to load data, run feature engineering, and print results."""
    print("Loading spaCy model...")
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("spaCy model 'en_core_web_sm' not found.")
        print("Please run: python -m spacy download en_core_web_sm")
        return

    print(f"Loading chat data from '{CHAT_JSON_FILE}'...")
    try:
        with open(CHAT_JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: '{CHAT_JSON_FILE}' not found. Please check the filename.")
        return

    df = pd.DataFrame(data['messages'])
    if df.empty:
        print("No messages found in the JSON file.")
        return

    # --- Data Cleaning and Preprocessing ---
    df['date'] = pd.to_datetime(df['date'])
    df['text'] = df['text'].astype(str) # Ensure text column is string type
    
    user_id = data['user_info']['id']
    contact_id_str_series = df[df['from_id'].notna()]['from_id']
    if contact_id_str_series.empty:
        print("Could not identify contact ID. The chat might only have outgoing messages.")
        return
        
    contact_id_str = contact_id_str_series.iloc[0]
    contact_id_match = re.search(r'(\d+)', contact_id_str)
    if not contact_id_match:
        print(f"Could not parse contact ID from string: {contact_id_str}")
        return
    contact_id = int(contact_id_match.group(1))

    df['sender_id'] = df['from_id'].apply(lambda x: user_id if pd.isna(x) else contact_id)
    df['sender_type'] = df['sender_id'].apply(lambda x: 'user' if x == user_id else 'contact')

    # --- Feature Calculation ---
    engineered_features = {
        'behavioral': calculate_behavioral_features(df, user_id, contact_id),
        'linguistic': calculate_linguistic_features(df, nlp),
        'graph_proxy': calculate_graph_proxy_features(df)
    }

    print("\n--- ✅ FINAL ENGINEERED FEATURES ---")
    pprint(engineered_features)


if __name__ == "__main__":
    main()