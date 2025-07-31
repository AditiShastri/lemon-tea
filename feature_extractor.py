# feature_extractor.py
import pandas as pd
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
from datetime import timedelta
import logging

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Define Comprehensive Keyword Sets ---
EMOTIONAL_WORDS = {'lonely', 'sad', 'trust', 'secret', 'desperate', 'afraid', 'love', 'heartbroken', 'soulmate'}
URGENT_WORDS = {'now', 'quick', 'immediately', 'urgent', 'hurry', 'today', 'instant', 'right away'}
FINANCIAL_WORDS = {'investment', 'crypto', 'profit', 'guarantee', 'bank', 'money', 'rich', 'cash', 'wire', 'fee'}
GREEDY_WORDS = {'easy money', 'risk-free', 'huge return', 'guaranteed profit', 'once in a lifetime', 'get rich'}
ALL_SUSPICIOUS_WORDS = EMOTIONAL_WORDS | URGENT_WORDS | FINANCIAL_WORDS | GREEDY_WORDS

def calculate_behavioral_features(df_chat, user_id, contact_id):
    """Calculates features based on the timing and patterns of messages."""
    features = {}
    user_messages = df_chat[df_chat['sender_type'] == 'user']
    contact_messages = df_chat[df_chat['sender_type'] == 'contact']
    avg_user_latency = user_messages['date'].diff().mean().total_seconds()
    avg_contact_latency = contact_messages['date'].diff().mean().total_seconds()
    if pd.notna(avg_user_latency) and avg_user_latency > 0 and pd.notna(avg_contact_latency):
        features['latency_ratio'] = avg_contact_latency / avg_user_latency
    else:
        features['latency_ratio'] = 0
    contact_questions = contact_messages['text'].str.contains(r'\?', na=False).sum()
    total_contact_messages = len(contact_messages)
    features['contact_question_ratio'] = contact_questions / total_contact_messages if total_contact_messages > 0 else 0
    time_diffs = df_chat['date'].diff() > timedelta(hours=1)
    initiations = df_chat[time_diffs]
    contact_initiations = initiations[initiations['sender_type'] == 'contact']
    total_initiations = len(initiations)
    features['contact_initiation_rate'] = len(contact_initiations) / total_initiations if total_initiations > 0 else 0
    unsociable_hours = df_chat['date'].dt.hour.between(1, 6).sum()
    features['unsociable_hours_ratio'] = unsociable_hours / len(df_chat) if len(df_chat) > 0 else 0
    return features

def calculate_linguistic_features(df_chat, nlp_model):
    """Calculates features based on content, sentiment, and keyword ratios."""
    features = {}
    contact_messages = df_chat[df_chat['sender_type'] == 'contact']
    default_features = {
        'avg_contact_sentiment': 0, 'sentiment_escalation': 0,
        'keyword_ratio': 0, 'money_entity_count': 0
    }
    if contact_messages.empty:
        return default_features

    contact_text = " ".join(contact_messages['text'].astype(str))
    text_lower = contact_text.lower()
    analyzer = SentimentIntensityAnalyzer()
    contact_sentiments = contact_messages['text'].astype(str).apply(
        lambda text: analyzer.polarity_scores(text)['compound']
    )
    features['avg_contact_sentiment'] = contact_sentiments.mean() if not contact_sentiments.empty else 0
    features['sentiment_escalation'] = 0
    if len(contact_sentiments) >= 10:
        midpoint = len(contact_sentiments) // 2
        first_half = contact_sentiments.iloc[:midpoint].mean()
        second_half = contact_sentiments.iloc[midpoint:].mean()
        if pd.notna(first_half) and pd.notna(second_half):
            features['sentiment_escalation'] = abs(second_half - first_half)

    keyword_chars = sum(len(word) for word in ALL_SUSPICIOUS_WORDS if word in text_lower)
    total_chars = len(contact_text)
    features['keyword_ratio'] = keyword_chars / total_chars if total_chars > 0 else 0
    doc = nlp_model(contact_text)
    features['money_entity_count'] = len([ent for ent in doc.ents if ent.label_ == 'MONEY'])
    return features

def calculate_graph_proxy_features(df_chat):
    """Calculates proxy features for graph-based analysis from a single chat."""
    if df_chat.empty:
        return {'messages_per_day': 0}
    chat_duration_days = (df_chat['date'].max() - df_chat['date'].min()).days
    chat_duration_days = max(chat_duration_days, 1)
    return {'messages_per_day': len(df_chat) / chat_duration_days}

def is_recent_id(user_id: int) -> int:
    """Returns 1 if user_id is recent, else 0."""
    if user_id is None: return 0
    return int(str(user_id).startswith(('74', '75', '76', '77', '78', '79')))

def process_chat_history_for_features(history_list, user_id, contact_id, nlp_model):
    """
    Processes raw chat history and calculates all features.
    This is the main orchestrator function.
    """
    if not history_list:
        logging.warning("Cannot process features: received an empty history list.")
        return None
    
    df_chat = pd.DataFrame(history_list)
    df_chat['date'] = pd.to_datetime(df_chat['date'], errors='coerce')
    df_chat.dropna(subset=['date'], inplace=True)
    
    df_chat['text'] = df_chat['text'].fillna('').astype(str)
    df_chat['sender_id'] = df_chat['sender_id'].astype(int)
    df_chat['sender_type'] = df_chat['sender_id'].apply(lambda x: 'user' if x == int(user_id) else 'contact')
    df_chat = df_chat.sort_values(by='date').reset_index(drop=True)
    
    behavioral = calculate_behavioral_features(df_chat, user_id, contact_id)
    linguistic = calculate_linguistic_features(df_chat, nlp_model)
    graph = calculate_graph_proxy_features(df_chat)
    all_features = {**behavioral, **linguistic, **graph}
    
    return pd.DataFrame([all_features])