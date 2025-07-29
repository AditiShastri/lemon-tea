# Import the necessary components from the Telethon library
from telethon import TelegramClient, events
import asyncio

# --- Configuration ---
# Replace with your own api_id and api_hash from my.telegram.org
API_ID = 23205405 
API_HASH = '16c7a91f1026c849ce88826f087601db'

# The session file will be created automatically on the first run.
# It stores your login info so you don't have to log in every time.
SESSION_NAME = 'my_protector_session'

# --- The Analysis Engine (V1.0 - very simple!) ---
# We will make this more complex in Part 2.
def analyze_message_v1(message_text):
    """A very basic function to check for suspicious keywords."""
    risk_score = 0
    suspicious_keywords = ['crypto', 'investment', 'guaranteed', 'secret', 'lonely', 'win money']
    
    # Convert message to lowercase for case-insensitive matching
    message_lower = message_text.lower()
    
    for keyword in suspicious_keywords:
        if keyword in message_lower:
            print(f"  [!] Found suspicious keyword: {keyword}")
            risk_score += 10 # Add 10 points for each keyword
            
    return risk_score

# --- The Telegram Client ---
# Create the client instance
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Define an event handler for new messages
# This function will run automatically whenever a new private message arrives.
# Correct way for modern Telethon
@client.on(events.NewMessage) # <-- Remove private=True from here
async def handle_new_message(event):
    """This function is triggered on every new message."""
    # Add this check to only process private messages
    if event.is_private:
        # --- All your original code now goes inside this if-statement ---
        message_text = event.message.text
        sender = await event.get_sender()
        sender_id = sender.id

        print(f"\n--- New Private Message from User ID: {sender_id} ---")
        print(f"Message: \"{message_text}\"")

        # Run the analysis
        risk_score = analyze_message_v1(message_text) # Or your latest analysis function

        # Check the result and take action
        print(f"Calculated Risk Score: {risk_score}")
        if risk_score > 0:
            print("  [ACTION] This message looks suspicious. A nudge would be sent here.")
        else:
            print("  [ACTION] Message seems normal.")

# --- Main function to start the client ---
async def main():
    """Main function to connect and run the client."""
    print("Starting the Telegram honeytrap detector...")
    # Connect to Telegram
    await client.start()
    print("Client is running. Listening for new messages...")
    # Keep the script running until you stop it (e.g., with Ctrl+C)
    await client.run_until_disconnected()

# Run the main function
if __name__ == '__main__':
    # asyncio.run() is used to execute the asynchronous main function
    asyncio.run(main())