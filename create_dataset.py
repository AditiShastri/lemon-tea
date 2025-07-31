# create_dataset.py (Robust Version)
import os
import glob
import json
import pandas as pd
import spacy
from feature_extractor import process_chat_history_for_features, is_recent_id

def main():
    """
    Finds chat files, robustly processes them using the main feature extractor,
    and creates a master training CSV.
    """
    print("Loading spaCy model...")
    nlp = spacy.load("en_core_web_sm")

    all_chat_features = []
    data_map = {
        'benign_chats': 0,
        'honeypot_chats': 1
    }

    for folder, label in data_map.items():
        print(f"\nProcessing folder: '{folder}' with label: {label}")
        json_files = glob.glob(os.path.join(folder, '*.json'))

        if not json_files:
            print(f"  - No JSON files found in '{folder}'.")
            continue

        for file_path in json_files:
            filename = os.path.basename(file_path)
            print(f"  - Analyzing {filename}...")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                user_info = data.get('user_info')
                history_list = data.get('messages')

                if not user_info or not isinstance(history_list, list):
                    print(f"  - Skipping {filename}: JSON is missing 'user_info' or 'messages' list.")
                    continue
                
                user_id = user_info.get('id')
                if not user_id:
                    print(f"  - Skipping {filename}: 'id' not found in 'user_info'.")
                    continue

                contact_id = data.get('chat_id')
                if not contact_id or contact_id == user_id:
                    found_id = None
                    for msg in history_list:
                        sender = msg.get('from_id') or msg.get('peer_id', {}).get('user_id')
                        if sender and sender != user_id:
                            found_id = sender
                            break
                    contact_id = found_id

                if contact_id is None:
                    print(f"  - Skipping {filename}: Could not determine contact_id.")
                    continue

                features_df = process_chat_history_for_features(
                    history_list=history_list,
                    user_id=user_id,
                    contact_id=contact_id,
                    nlp_model=nlp
                )

                if features_df is not None:
                    features = features_df.to_dict('records')[0]
                    features['id_is_recent'] = is_recent_id(contact_id)
                    features['label'] = label
                    all_chat_features.append(features)

            except json.JSONDecodeError:
                print(f"  - Skipping {filename}: Invalid JSON format.")
            except Exception as e:
                print(f"  - ERROR processing {filename}: {e}")

    if not all_chat_features:
        print("\nNo data was processed. Could not create dataset.")
        return

    final_df = pd.DataFrame(all_chat_features).fillna(0)
    output_filename = 'training_data.csv'
    final_df.to_csv(output_filename, index=False)
    print(f"\n✅ Success! Dataset created at '{output_filename}' with {len(final_df)} samples.")


if __name__ == "__main__":
    main()