# create_dataset.py
import os
import glob
import json
import re
from pprint import pprint

import pandas as pd
import spacy

# We import the functions directly from your existing feature extractor script
from feature_extractor import (calculate_behavioral_features,
                               calculate_linguistic_features,
                               calculate_graph_proxy_features)

def process_single_chat_file(file_path, nlp_model):
    """Loads a single JSON file and returns its engineered features."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  - Skipping {os.path.basename(file_path)} due to load error: {e}")
        return None

    df = pd.DataFrame(data.get('messages', []))
    if df.empty:
        print(f"  - Skipping {os.path.basename(file_path)}: No messages found.")
        return None

    # --- Run the same preprocessing as before ---
    df['date'] = pd.to_datetime(df['date'])
    df['text'] = df['text'].astype(str)
    
    user_id = data.get('user_info', {}).get('id')
    contact_id_str_series = df[df['from_id'].notna()]['from_id']
    if user_id is None or contact_id_str_series.empty:
        print(f"  - Skipping {os.path.basename(file_path)}: Could not identify user/contact ID.")
        return None
        
    contact_id_str = contact_id_str_series.iloc[0]
    contact_id_match = re.search(r'(\d+)', contact_id_str)
    if not contact_id_match:
        return None
    contact_id = int(contact_id_match.group(1))

    df['sender_id'] = df['from_id'].apply(lambda x: user_id if pd.isna(x) else contact_id)
    df['sender_type'] = df['sender_id'].apply(lambda x: 'user' if x == user_id else 'contact')

    # --- Calculate all features ---
    behavioral = calculate_behavioral_features(df, user_id, contact_id)
    linguistic = calculate_linguistic_features(df, nlp_model)
    graph = calculate_graph_proxy_features(df)
    
    # --- Combine all features into a single dictionary ---
    # We flatten the dictionary for easy CSV conversion
    final_features = {**behavioral, **linguistic, **graph}
    
    # We don't need the conceptual feature in our final dataset
    final_features.pop('isolation_index_CONCEPTUAL', None)
    
    return final_features


def main():
    """Main function to find chat files, process them, and create a CSV."""
    print("Loading spaCy model (this may take a moment)...")
    nlp = spacy.load("en_core_web_sm")

    all_chat_features = []
    
    # Define the folders and their corresponding labels
    data_map = {
        'benign_chats': 0,
        'honeypot_chats': 1
    }

    for folder, label in data_map.items():
        print(f"\nProcessing folder: '{folder}' with label: {label}")
        json_files = glob.glob(os.path.join(folder, '*.json'))
        if not json_files:
            print(f"  - No JSON files found in '{folder}'. Please check the folder setup.")
            continue
            
        for file_path in json_files:
            print(f"  - Analyzing {os.path.basename(file_path)}...")
            features = process_single_chat_file(file_path, nlp)
            
            if features:
                features['label'] = label  # Add the all-important label
                all_chat_features.append(features)

    if not all_chat_features:
        print("\nNo data was processed. Could not create dataset.")
        return

    # --- Create the final DataFrame and save to CSV ---
    print("\nAssembling final dataset...")
    final_df = pd.DataFrame(all_chat_features)
    
    # Fill any potential missing values with 0
    final_df.fillna(0, inplace=True)
    
    output_filename = 'training_data.csv'
    final_df.to_csv(output_filename, index=False)
    
    print(f"\n✅ Success! Your dataset has been created.")
    print(f"    - Total conversations processed: {len(final_df)}")
    print(f"    - Saved to: {output_filename}")
    print("\nFinal Dataset Preview:")
    print(final_df.head())


if __name__ == "__main__":
    main()