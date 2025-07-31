# run_retraining_pipeline.py (Unified)
import pandas as pd
import os
import json
import spacy
import joblib
import lightgbm as lgb
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import classification_report

# Use the same feature extractor as the live detector
from feature_extractor import process_chat_history_for_features, is_recent_id

# --- Configuration ---
APPROVED_FOLDER = 'APPROVED_FOR_TRAINING/'
BENIGN_FOLDER = 'BENIGN_FOR_TRAINING/'
ARCHIVE_FOLDER = 'ARCHIVED_TRAINING_DATA/'
TRAINING_CSV = 'training_data.csv'
MAIN_MODEL_PATH = 'honeytrap_detector.joblib'
SENTIMENT_MODEL_PATH = 'sentiment_model.joblib'
MIN_FILES_TO_RETRAIN = 10

def prepare_data_and_check_for_updates():
    """
    Checks for new files, processes them using the main feature extractor,
    appends to the master CSV, and returns True if retraining should proceed.
    """
    print("--- 1. Checking for new training data ---")
    os.makedirs(APPROVED_FOLDER, exist_ok=True)
    os.makedirs(BENIGN_FOLDER, exist_ok=True)
    os.makedirs(ARCHIVE_FOLDER, exist_ok=True)

    approved_files = [(os.path.join(APPROVED_FOLDER, f), 1) for f in os.listdir(APPROVED_FOLDER) if f.endswith('.json')]
    benign_files = [(os.path.join(BENIGN_FOLDER, f), 0) for f in os.listdir(BENIGN_FOLDER) if f.endswith('.json')]
    all_new_files = approved_files + benign_files

    if os.path.exists(MAIN_MODEL_PATH) and len(all_new_files) < MIN_FILES_TO_RETRAIN:
        print(f"Skipping retraining. Found {len(all_new_files)} new files, need at least {MIN_FILES_TO_RETRAIN}.")
        return False

    if all_new_files:
        print(f"Found {len(all_new_files)} new files to process...")
        nlp = spacy.load("en_core_web_sm")
        master_df = pd.read_csv(TRAINING_CSV) if os.path.exists(TRAINING_CSV) else pd.DataFrame()
        
        for filepath, label in all_new_files:
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                user_id = data['user_info']['id']
                history = data['messages']
                contact_id = data.get('chat_id')
                if not contact_id: # Fallback
                    for msg in history:
                        sender = msg.get('from_id')
                        if sender and sender != user_id:
                            contact_id = sender
                            break
                
                if contact_id:
                    features_df = process_chat_history_for_features(history, user_id, contact_id, nlp)
                    if features_df is not None:
                        features = features_df.to_dict('records')[0]
                        features['id_is_recent'] = is_recent_id(contact_id)
                        features['label'] = label
                        master_df = pd.concat([master_df, pd.DataFrame([features])], ignore_index=True)
                
                os.rename(filepath, os.path.join(ARCHIVE_FOLDER, filename))
            except Exception as e:
                print(f"Error processing {filename}: {e}")
        
        master_df.drop_duplicates(inplace=True, ignore_index=True)
        master_df.to_csv(TRAINING_CSV, index=False)
        print(f"✅ Updated '{TRAINING_CSV}' with new data.")
    
    return True

def train_main_model():
    """Trains and saves the main complex model pipeline."""
    print("\n--- 2a. Training Main Detector Model ---")
    df = pd.read_csv(TRAINING_CSV)
    X = df.drop('label', axis=1)
    y = df['label']
    
    pipeline = Pipeline([
        ('feature_selection', SelectKBest(f_classif)),
        ('model', lgb.LGBMClassifier(objective='binary', random_state=42, is_unbalance=True))
    ])
    param_grid = {
        'feature_selection__k': range(8, len(X.columns) + 1),
        'model__learning_rate': [0.01, 0.05, 0.1],
        'model__n_estimators': [100, 200, 300],
    }
    random_search = RandomizedSearchCV(estimator=pipeline, param_distributions=param_grid, n_iter=10,
                                       scoring='f1_weighted', cv=3, n_jobs=-1, verbose=0, random_state=42)
    
    random_search.fit(X, y)
    print(f"🏆 Main Model Best Params: {random_search.best_params_}")
    
    joblib.dump(random_search.best_estimator_, MAIN_MODEL_PATH)
    print(f"✅ Main model pipeline saved to '{MAIN_MODEL_PATH}'")

def train_sentiment_model():
    """Trains and saves the simple sentiment escalation model."""
    print("\n--- 2b. Training Sentiment Escalation Model ---")
    df = pd.read_csv(TRAINING_CSV)
    X = df[['sentiment_escalation']]
    y = df['label']
    
    model = LogisticRegression(random_state=42, class_weight='balanced')
    model.fit(X, y)
    
    joblib.dump(model, SENTIMENT_MODEL_PATH)
    print(f"✅ Sentiment model saved to '{SENTIMENT_MODEL_PATH}'")

if __name__ == "__main__":
    if prepare_data_and_check_for_updates():
        try:
            train_main_model()
            train_sentiment_model()
            print("\n--- ✅ Retraining pipeline finished successfully! ---")
        except Exception as e:
            print(f"\n--- ❌ An error occurred during model training: {e} ---")
    else:
        print("\n--- Pipeline finished. No retraining was performed. ---")