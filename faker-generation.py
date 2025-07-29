import json
import random
from datetime import datetime, timedelta
from faker import Faker
import os # Import the os module for directory operations

# Initialize Faker with Indian locale
fake = Faker('en_IN')

def generate_chat_conversation(num_messages=25, is_honeypot_scenario=False, chat_index=0):
    """
    Generates a two-person chat conversation in the specified JSON format.

    Args:
        num_messages (int): The desired number of messages in the conversation.
        is_honeypot_scenario (bool): If True, attempts to introduce a simple honeypot element.
                                     (Note: Complex multi-stage scams need manual crafting).
        chat_index (int): An index for naming the output files.
    """

    # User 1 (Primary User - Rahul)
    user1_id = fake.random_int(min=1000000000, max=9999999999)
    user1_first_name = fake.first_name_male() # Use Faker for more variety in names
    user1_last_name = fake.last_name_male()
    user1_username = f"{user1_first_name.lower()}_{user1_last_name.lower()}_{fake.random_int(min=100, max=999)}"
    user1_phone = fake.numerify('91##########')
    user1_bio = random.choice([
        "Just a guy who likes movies and code.",
        "Learning and growing every day!",
        "Coffee enthusiast and tech lover.",
        "Exploring new ideas."
    ])
    user1_pfp = f"pfp_{user1_username}.jpg"

    # User 2 (Peer User - Priya, who might be the honeypot in a scam)
    user2_id = fake.random_int(min=1000000000, max=9999999999)
    user2_first_name = fake.first_name_female() # Use Faker for more variety in names
    user2_last_name = fake.last_name_female()
    user2_username = f"{user2_first_name.lower()}_{user2_last_name.lower()}_{fake.random_int(min=100, max=999)}"
    user2_phone = fake.numerify('91##########')
    user2_bio = fake.sentence(nb_words=8)
    user2_pfp = f"pfp_{user2_username}.jpg"

    chat_id = user1_id # Chat ID is usually the primary user's ID for direct chats

    messages = []
    # Start time within the last 15 days, to make dates somewhat recent
    current_time = datetime.now() - timedelta(days=random.randint(0, 15), hours=random.randint(1, 10), minutes=random.randint(0, 59))

    # Determine who starts the conversation (randomly)
    current_speaker_id = None
    if random.choice([True, False]): # Primary user starts
        current_speaker_id = None # Null for the primary user
    else: # Peer user starts
        current_speaker_id = f"PeerUser(user_id={user2_id})"

    # Honeypot specific variables
    honeypot_phase = 0 # 0: normal, 1: trust building, 2: introducing scam, 3: escalation
    honeypot_type = None
    honeypot_link_inserted = False

    # Simple honeypot scenarios to choose from
    honeypot_scenarios = [
        "urgent_payment_request",
        "fake_job_offer",
        "suspicious_link_share",
        "crypto_investment_scam",
        "lottery_scam"
    ]
    if is_honeypot_scenario:
        honeypot_type = random.choice(honeypot_scenarios)
        # Introduce a trigger for the honeypot to start at some point
        # Make sure start ID is always less than total messages and allows for progression
        honeypot_start_message_id = random.randint(int(num_messages * 0.3), int(num_messages * 0.7))
        if honeypot_start_message_id > num_messages - 5: # Needs at least 5 messages for phases
             honeypot_start_message_id = num_messages - 5


    for i in range(1, num_messages + 1):
        message_id = 1500 + i # Starting from 1501 as in your example

        # Simulate delay between messages (2 to 7 minutes, random seconds)
        current_time += timedelta(minutes=random.randint(2, 7), seconds=random.randint(0, 59))

        message_text = ""
        sender_id = current_speaker_id

        # --- Honeypot Logic (simplified for demonstration) ---
        # Only apply honeypot logic if it's a honeypot scenario AND the message ID is at or past the start point
        if is_honeypot_scenario and i >= honeypot_start_message_id:
            # The honeypot (Priya) is the one initiating the scam
            if sender_id == f"PeerUser(user_id={user2_id})": # It's Priya's turn to speak (the potential scammer)
                if honeypot_phase == 0: # Initial trust building/setting up pretext (Priya's first scam message)
                    if honeypot_type == "urgent_payment_request":
                        message_text = random.choice([
                            f"Hey {user1_first_name}, quickly! I'm in a bit of a fix. My online payment isn't going through. Can you help me out for a minute?",
                            f"Hi {user1_first_name}, hope you're doing well. Listen, I have an urgent matter I need your help with.",
                            f"OMG {user1_first_name}, I'm stuck! I need to make a payment right now and my card is declining. Can I send you the money and you transfer it for me? It's really urgent!"
                        ])
                    elif honeypot_type == "fake_job_offer":
                        message_text = random.choice([
                            f"Hey {user1_first_name}, I just heard about an amazing remote job opportunity. Are you looking for something new?",
                            f"Hi! Quick question, are you open to part-time work that pays really well? I found a gig.",
                            f"Got a referral for a high-paying data entry role, no experience needed. Let me know if you're interested, I can share details."
                        ])
                    elif honeypot_type == "suspicious_link_share":
                        message_text = random.choice([
                            f"You HAVE to see this funny video, {user1_first_name}! It's hilarious: http://funny-clips.xyz/{fake.uuid4()}",
                            f"Found this article that perfectly explains what we were discussing! Check it out: http://news.{fake.domain_word()}.biz/{fake.slug()}",
                            f"Is this really {user1_first_name} in this photo? My friend sent it: http://photos.{fake.domain_word()}-storage.ru/{fake.uuid4()}.jpg"
                        ])
                        honeypot_link_inserted = True # Mark that a link has been inserted
                    elif honeypot_type == "crypto_investment_scam":
                        message_text = random.choice([
                            f"Hey {user1_first_name}! You won't believe the returns I'm getting on this crypto platform. You should check it out, it's totally legit!",
                            f"I've found a way to earn passive income with crypto, really easy. Want to know more?",
                            f"My friend showed me this amazing investment opportunity. Made back my initial capital in a week! Are you interested in making some extra money?"
                        ])
                    elif honeypot_type == "lottery_scam":
                        message_text = random.choice([
                            f"Guess what?! I just got a notification that I won a huge prize in an online lottery! This is insane. Have you ever tried those?",
                            f"I just won Rs. {random.randint(500000, 1000000):,} in the {fake.country()} EuroMillion! You can also check if you won here: http://official-lottery-claims.info/verify",
                            f"Someone just forwarded me this, apparently we both registered for some online lucky draw. Check if your number is on the winners list: http://lucky-draw-results.com/{fake.uuid4()}"
                        ])
                        honeypot_link_inserted = True # Lottery scams often involve links
                    honeypot_phase = 1 # Move to next phase
                
                elif honeypot_phase == 1: # Pushing for action/more details
                    if honeypot_type == "urgent_payment_request":
                        message_text = random.choice([
                            f"It's just Rs. {random.randint(5000, 25000):,}. I can send it to your GPay/Paytm right now, can you just do the transfer from your end? My app isn't working.",
                            f"It's for my mom's hospital bill, please {user1_first_name}, I'm desperate. I'll pay you back tonight with interest!",
                            f"Here's the account number: [Fake Acct No]. Just need you to quickly do the bank transfer. I've sent you Rs. {random.randint(5000, 25000):,} already."
                        ])
                    elif honeypot_type == "fake_job_offer":
                        message_text = random.choice([
                            f"They're hiring fast, so you need to apply quickly. Just fill out this brief form for their HR: http://careers.apply-now.info/{fake.slug()}",
                            f"The HR manager is asking for a small registration fee for background check, just Rs. 500. It's refundable! Don't miss this chance: http://jobs.{fake.domain_word()}.co/register",
                            f"You just need to share your bank details for direct deposit of salary. It's standard procedure for remote work. Here's where to enter it: http://hr-portal.{fake.domain_word()}.net/bank-details"
                        ])
                    elif honeypot_type == "crypto_investment_scam":
                        message_text = random.choice([
                            f"This platform has exclusive AI trading bots. You just deposit funds and watch it grow. Here's the link: http://trade.cryptoprofits.io/signup",
                            f"My mentor helped me. They're giving free expert advice if you register. Want their Telegram handle?",
                            f"You can start with as little as Rs. 1000. I can guide you through the initial setup if you like."
                        ])
                    elif honeypot_type == "suspicious_link_share" and not honeypot_link_inserted:
                        message_text = random.choice([
                            f"Did you click that link yet? It's really wild! You won't believe what happened next: http://viral-content.co/{fake.uuid4()}",
                            f"It might ask for a quick login to verify you're not a bot, totally normal. Just use your social media login.",
                            f"I sent you a video, check your DMs. It's about that thing we talked about."
                        ])
                        honeypot_link_inserted = True # Ensure link is only shared once explicitly
                    elif honeypot_type == "lottery_scam":
                        message_text = random.choice([
                            f"Did you check the link? You might have won too! It's super easy to claim.",
                            f"They need a small processing fee to release the winnings, around Rs. {random.randint(1000, 5000):,}. It's a small amount for such a big prize!",
                            f"Just input your bank details on their secure portal for direct deposit: http://claim-prize.official-payouts.net/submit-info"
                        ])
                        honeypot_link_inserted = True # More links for lottery
                    honeypot_phase = 2 # Move to next phase
                
                elif honeypot_phase == 2: # Escalation or persistence from honeypot
                    if honeypot_type == "urgent_payment_request":
                        message_text = f"Hello? Are you there, {user1_first_name}? I really need your help with this. Time is running out!"
                    elif honeypot_type == "fake_job_offer":
                        message_text = f"Did you fill out the form? The spots are filling up fast! It's a limited opportunity."
                    elif honeypot_type == "crypto_investment_scam":
                        message_text = f"Why haven't you started yet? You're missing out on daily profits! My balance just went up by 10% today."
                    elif honeypot_type == "suspicious_link_share":
                        message_text = f"Why aren't you clicking the link? It's safe, I promise. Just check it out."
                    elif honeypot_type == "lottery_scam":
                        message_text = f"Don't delay! They'll reassign the prize if you don't claim it soon. The deadline is tomorrow!"
                    honeypot_phase = 3 # Can escalate further or loop
                else: # Generic persistence if honeypot phase is advanced
                     message_text = fake.sentence(nb_words=random.randint(5, 15))
                     if honeypot_type == "crypto_investment_scam": # Mix in normal chat with persistence
                         message_text = random.choice([
                             f"How's your day, {user1_first_name}? Just checking in.",
                             f"Busy day for me. Still thinking about that investment though...",
                             f"You should really consider it. It's changed my life.",
                             f"My profits today were amazing, can't believe I didn't start sooner!"
                         ])
                     elif honeypot_type == "fake_job_offer":
                         message_text = random.choice([
                             f"How was your weekend, {user1_first_name}?",
                             f"Did you have any questions about the job? I can help.",
                             f"It's a really great opportunity, don't miss it.",
                             f"The HR team is following up, have you applied?"
                         ])
                     elif honeypot_type == "lottery_scam":
                         message_text = random.choice([
                             f"Seriously, {user1_first_name}, don't miss out on this. It's a once-in-a-lifetime chance.",
                             f"Imagine what you could do with that money!",
                             f"Just need you to complete the final steps."
                         ])

            else: # If it's Rahul's turn to speak in a honeypot scenario, give a relevant response
                if honeypot_phase == 0: # Still in normal chat before honeypot triggers
                    message_text = random.choice([
                        f"Hey {user2_first_name}! I'm good, just catching up.",
                        f"Not much, finishing work. You?",
                        f"Sounds good, let me know!"
                    ])
                elif honeypot_phase >= 1: # Responding to the honeypot's attempts
                    if honeypot_type == "urgent_payment_request":
                        message_text = random.choice([
                            "Oh no, what happened?",
                            "That sounds bad. What do you need?",
                            "I might be able to help, what's the issue?",
                            "Hmm, I'm a bit busy right now. Is it super urgent?"
                        ])
                    elif honeypot_type == "fake_job_offer":
                        message_text = random.choice([
                            "Oh really? Tell me more!",
                            "I'm always open to new opportunities. What kind of role is it?",
                            "Hmm, I'm pretty settled. But thanks for thinking of me.",
                            "What are the requirements?"
                        ])
                    elif honeypot_type == "suspicious_link_share":
                        message_text = random.choice([
                            "Haha, I'll check it out later.",
                            "Is it safe to click?",
                            "Looks a bit weird, what is it?",
                            "I'm on mobile, will check on desktop."
                        ])
                    elif honeypot_type == "crypto_investment_scam":
                        message_text = random.choice([
                            "Crypto, huh? I'm not really into that.",
                            "Sounds interesting, but I'm careful with investments.",
                            "Wow, that's great! How does it work?",
                            "Is it legitimate? I've heard about many scams."
                        ])
                    elif honeypot_type == "lottery_scam":
                        message_text = random.choice([
                            "That's amazing! Congratulations! I never win anything.",
                            "Really? What lottery is that?",
                            "Sounds too good to be true, be careful!",
                            "I'll check the link later, thanks for sharing."
                        ])

        else: # Normal conversation messages
            message_text = random.choice([
                f"Hey {user1_first_name if sender_id == f'PeerUser(user_id={user2_id})' else user2_first_name}! What's up?",
                f"Hey! Not much, just finishing up work. You?",
                f"Same here. Any plans for the weekend?",
                f"Was thinking of catching that new {random.choice(['sci-fi', 'action', 'comedy'])} movie. Interested? \ud83c\udfa5",
                f"Oh yeah, '{fake.catch_phrase()}'? I've been wanting to see that! Saturday evening?",
                f"Perfect! Let's do it. I'll check the showtimes. \ud83d\udc4c",
                f"Awesome, thanks! Let me know what you find.",
                f"Okay, there's a {random.randint(6,9)}:{random.choice(['00', '15', '30', '45'])} PM show at the {fake.city()} Mall and an {random.randint(7,10)}:{random.choice(['00', '15', '30', '45'])} PM at Orion. Orion has better seats available.",
                f"Orion sounds good. {random.randint(7,10)} PM works for me.",
                f"Great. Should I book or do you want to?",
                f"I can get them. I have a voucher on BookMyShow anyway. Will book the middle row.",
                f"You're a star! Thanks {user1_first_name if sender_id == f'PeerUser(user_id={user2_id})' else user2_first_name}.",
                f"No problem! :) Hey, want to grab dinner before the movie?",
                f"Definitely! Was just about to suggest that. What are you in the mood for?",
                f"I'm easy. You choose. Something near the mall maybe?",
                f"Hmm, how about that new {random.choice(['Italian', 'Mexican', 'Asian'])} place, '{fake.company()}'? I've heard good things about their {random.choice(['pasta', 'tacos', 'noodles'])}.",
                f"YES! I've been wanting to try that. Perfect plan. So dinner around {random.randint(6,7)}:{random.choice(['00', '30'])}?",
                f"{random.randint(6,7)}:{random.choice(['00', '30'])} it is. This is turning into a great plan.",
                f"For sure! It's been a while since we hung out properly.",
                f"I know, right? The last time was that disastrous karaoke night haha.",
                f"Haha please don't remind me of my singing. How's that new project at work you were telling me about?",
                f"Oh, it's going really well actually! Super busy but the team is great. Finally feels like we're making progress.",
                f"That's awesome to hear! You were so stressed about it a few weeks ago.",
                f"Tell me about it. Anyway, enough work talk! How's the {random.choice(['guitar', 'painting', 'cooking'])} coming along? Can you {random.choice(['play', 'finish', 'master'])} '{fake.catch_phrase()}' yet? ;)",
                f"Haha, not even close. My fingers still hate me. It's a deal, I'll book the tickets and see you on Saturday. Gotta run to a meeting now, catch you later!",
                f"Sounds good! Talk soon."
            ])

        messages.append({
            "id": message_id,
            "date": current_time.isoformat(timespec='seconds') + "+00:00", # UTC offset
            "text": message_text,
            "from_id": sender_id,
            "media_file": None
        })

        # Switch speaker for next message
        if current_speaker_id is None: # If current speaker was primary user
            current_speaker_id = f"PeerUser(user_id={user2_id})" # Next is peer user
        else: # If current speaker was peer user
            current_speaker_id = None # Next is primary user

    chat_data = {
        "exported_by": "Telegram Exporter Script",
        "export_date": datetime.now().isoformat(),
        "chat_id": chat_id,
        "chat_type": "User",
        "user_info": {
            "id": user1_id,
            "username": user1_username,
            "first_name": user1_first_name,
            "last_name": user1_last_name,
            "phone": user1_phone,
            "bio": user1_bio,
            "profile_picture_file": user1_pfp
        },
        "messages": messages
    }

    return chat_data

# --- Main execution block ---
if __name__ == "__main__":
    num_conversations = 300 # Generate 10 conversations in total
    num_benign_conversations = num_conversations // 2 # Half benign
    num_honeypot_conversations = num_conversations - num_benign_conversations # Half honeypot (or slightly more if odd)

    # Define base directories
    benign_dir = 'benign_chats'
    honeypot_dir = 'honeypot_chats'

    # Create directories if they don't exist
    os.makedirs(benign_dir, exist_ok=True)
    os.makedirs(honeypot_dir, exist_ok=True)

    print(f"Generating {num_benign_conversations} benign conversations into '{benign_dir}'...")
    for i in range(1, num_benign_conversations + 1):
        benign_conversation = generate_chat_conversation(num_messages=25, is_honeypot_scenario=False, chat_index=i)
        filename = os.path.join(benign_dir, f'chat{i+62}.json') # Path now includes directory
        # FIX: Added errors='replace' to handle potential UnicodeEncodeErrors
        with open(filename, 'w', encoding='utf-8', errors='replace') as f:
            json.dump(benign_conversation, f, ensure_ascii=False, indent=4)
        print(f"Generated '{filename}'")

    print(f"\nGenerating {num_honeypot_conversations} honeypot conversations into '{honeypot_dir}'...")
    for i in range(1, num_honeypot_conversations + 1):
        honeypot_conversation = generate_chat_conversation(num_messages=25, is_honeypot_scenario=True, chat_index=i)
        filename = os.path.join(honeypot_dir, f'scam_chat{i+62}.json') # Path now includes directory
        # FIX: Added errors='replace' to handle potential UnicodeEncodeErrors
        with open(filename, 'w', encoding='utf-8', errors='replace') as f:
            json.dump(honeypot_conversation, f, ensure_ascii=False, indent=4)
        print(f"Generated '{filename}'")

    print("\n--- Generation Complete ---")
    print(f"You now have {num_conversations} JSON files neatly organized in '{benign_dir}' and '{honeypot_dir}'.")
    print("Remember that the honeypot scenarios are simplified and may need manual refinement for realism.")
    print("Proceed with feature engineering on these JSON files using external libraries.")