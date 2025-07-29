import asyncio
import json
import os
from getpass import getpass
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from datetime import datetime

# --- Configuration ---
API_ID = 21292459  # <--- REPLACE WITH YOUR API ID
API_HASH = 'b65ce927aeb778a9cd0d3e5695249c93' # <--- REPLACE WITH YOUR API HASH

# How often to check for new messages, in seconds.
# Avoid setting this too low to respect Telegram's API limits.
POLLING_INTERVAL = 5 

SESSION_FILE = 'my_telegram_session'
MEDIA_DIRECTORY = 'media'

# --- Helper to convert data for JSON ---
def json_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()
    return str(o)

async def main():
    """Main function to run the continuous monitor."""

    # Create the media directory if it doesn't exist
    if not os.path.exists(MEDIA_DIRECTORY):
        os.makedirs(MEDIA_DIRECTORY)

    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.start(
        phone=lambda: input('Please enter your phone number (e.g., +919876543210): '),
        password=lambda: getpass('Please enter your 2FA password (if any): '),
        code_callback=lambda: input('Please enter the code you received: ')
    )
    print("Client connected. Starting to monitor for new messages...")

    try:
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new messages...")
            # Iterate through all your dialogs (chats)
            async for dialog in client.iter_dialogs():
                # We only care about one-on-one chats with users, not bots, groups or channels
                if dialog.is_user and not dialog.entity.bot:
                    entity = dialog.entity
                    
                    # Define filename based on username, with a fallback to user ID
                    filename = f"{entity.username or f'user_{entity.id}'}.json"
                    
                    chat_data = {}
                    last_known_id = 0
                    
                    # Try to load existing data for this chat
                    try:
                        with open(filename, 'r', encoding='utf-8') as f:
                            chat_data = json.load(f)
                        # Get the ID of the last message we have stored
                        if chat_data['messages']:
                            last_known_id = chat_data['messages'][-1]['id']
                    except FileNotFoundError:
                        # If no file exists, create a new structure
                        chat_data = {
                            'chat_id': entity.id,
                            'chat_type': 'User',
                            'user_info': {},
                            'messages': []
                        }

                    # Fetch new messages since the last known message
                    new_messages = []
                    async for message in client.iter_messages(entity, min_id=last_known_id):
                        message_dict = {
                            'id': message.id,
                            'date': message.date,
                            'text': message.text,
                            'from_id': getattr(message.from_id, 'user_id', None),
                            'media_file': None
                        }
                        if message.media:
                            media_path = await message.download_media(file=MEDIA_DIRECTORY)
                            message_dict['media_file'] = media_path
                        
                        new_messages.append(message_dict)

                    if new_messages:
                        print(f"   > Found {len(new_messages)} new message(s) in chat with '{entity.first_name}'. Updating {filename}...")
                        
                        # New messages from iter_messages are newest-first, so reverse them
                        new_messages.reverse()
                        chat_data['messages'].extend(new_messages)
                        
                        # Refresh user info in case it changed (bio, pfp, etc.)
                        full_user = await client(GetFullUserRequest(entity.id))
                        pfp_path = await client.download_profile_photo(entity, file=f"{MEDIA_DIRECTORY}/{entity.username or entity.id}_pfp.jpg")
                        
                        chat_data['user_info'] = {
                            'id': entity.id,
                            'username': entity.username,
                            'first_name': entity.first_name,
                            'last_name': entity.last_name,
                            'phone': entity.phone,
                            'bio': full_user.full_user.about,
                            'profile_picture_file': pfp_path
                        }
                        
                        # Write the updated data back to the file
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(chat_data, f, ensure_ascii=False, indent=4, default=json_converter)
            
            # Wait for the specified interval before checking again
            print(f"Check complete. Waiting for {POLLING_INTERVAL} seconds...")
            await asyncio.sleep(POLLING_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    finally:
        await client.disconnect()
        print("Client disconnected.")

if __name__ == "__main__":
    asyncio.run(main())