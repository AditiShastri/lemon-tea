import os
import json
import random
import re

def generate_recent_user_id():
    """Generate a 10-digit user ID starting with 74–76"""
    return int(str(random.choice([74, 75, 76])) + ''.join(str(random.randint(0, 9)) for _ in range(8)))

# Keeps consistent mappings across messages
id_map = {}

# Input and output folder setup
input_folder = '.'
output_folder = '.'
#os.makedirs(output_folder, exist_ok=True)

# Iterate over all .json files in current folder
for filename in os.listdir(input_folder):
    if filename.endswith('.json'):
        input_path = os.path.join(input_folder, filename)
        print(f"Processing: {filename}")

        with open(input_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"❌ Failed to load {filename}: {e}")
                continue

        # Iterate through messages and replace malicious IDs
        for msg in data.get('messages', []):
            from_id = msg.get('from_id')
            if isinstance(from_id, str) and from_id.startswith('PeerUser(user_id='):
                old_id_match = re.search(r'PeerUser\(user_id=(\d+)\)', from_id)
                if old_id_match:
                    old_id = int(old_id_match.group(1))
                    if old_id not in id_map:
                        id_map[old_id] = generate_recent_user_id()
                    new_id = id_map[old_id]
                    msg['from_id'] = f'PeerUser(user_id={new_id})'

        # Write modified version
        output_path = os.path.join(output_folder, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Saved: {output_path}")

print("\nAll JSON files processed and saved  ✅")
