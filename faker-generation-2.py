import json
import random
from datetime import datetime, timedelta
from faker import Faker
import os

# Initialize Faker with Indian locale
fake = Faker('en_IN')

# --- NEW: Expanded and organized message templates ---

def get_benign_messages(user1, user2):
    """Returns a list of varied, dynamic benign messages."""
    return [
        f"Hey {user2}! How's it going?",
        "Hey! All good here, just swamped with work. You?",
        "Same old, same old. Finally Friday, though! 🙏",
        "Tell me about it! Any plans for the weekend?",
        "Not really, was thinking of just chilling. Maybe watch the cricket match.",
        "Oh yeah, the IND vs AUS match! It's going to be intense. 🏏",
        "For sure! You watching?",
        "Definitely! We should order some pizza or something.",
        "Sounds like a plan! Let's do it.",
        f"Hey {user2}, did you see the new OnePlus phone that launched?",
        "Yeah, saw some reviews. Looks slick, but the price is insane. 🤯",
        "True. My current phone is lagging so bad, I need an upgrade soon.",
        "What are you thinking of getting?",
        "Not sure yet, maybe I'll wait for the Diwali sales.",
        "Good idea. You always get better deals then.",
        f"Btw, how was that trip to Goa you were planning, {user1}?",
        "It was amazing! The beaches were so relaxing. We should go together next time.",
        "I'd love that! My leave is pending, will plan something for December.",
        "Perfect! Winter is the best time to go.",
        "I'm so bored of my work-from-home setup.",
        "I feel you. I miss the office chai and gossip. 😂",
        "Haha, the gossip for sure! Remember that time with the accounting department?",
        "How can I forget! Classic.",
        f"What are you listening to these days, {user2}?",
        "Found this cool indie artist on Spotify. I'll send you the link.",
        "Awesome, thanks!",
        "Just tried to make biryani at home. It was... an experience.",
        "Haha, was it a success or a disaster?",
        "Let's just say Swiggy is on its way. 😅",
        "Smart move. Some things are best left to the professionals.",
        "What are you watching on Netflix?",
        f"Started watching 'Scam 2003'. It's pretty good!",
        "Oh, I loved the first one! I'll add it to my list.",
        "Totally exhausted today. Need a long weekend.",
        "Just one more day to go. Hang in there! 💪"
    ]

def get_honeypot_templates(user1, user2):
    """Returns a dictionary of structured honeypot scenarios."""
    return {
        "urgent_payment_request": {
            "phase_0": [f"Hey {user1}, you there? I'm in a bit of an emergency.", f"OMG {user1}, I'm stuck and need your help urgently!", f"Hi {user1}, sorry to bother you but I have a huge problem."],
            "phase_1": [f"My GPay is not working and I need to pay Rs. {random.randint(5, 15)*1000} for a medical bill right now. Can you please send it? I'll return it by evening.", f"I lost my wallet and I'm stranded. Can you please transfer Rs. {random.randint(4, 10)*1000} for a cab? I'll pay you back as soon as I get home.", f"There's a flash sale on a laptop I need for work, it ends in 10 mins. My card is getting declined. Can you help me with Rs. {random.randint(10, 25)*1000}?"],
            "phase_2": ["Please, it's really important. The hospital is waiting for the payment.", "Time is running out, please send it fast!", f"Are you there, {user1}? I'm counting on you."],
            "victim_response": ["Oh no, what happened? Is everything okay?", "That sounds serious. How can I help?", "Are you sure? This sounds a bit sudden.", "Let me call you first to check."]
        },
        "fake_job_offer": {
            "phase_0": [f"Hey {user1}, I came across a great work-from-home job with an international client. High pay, flexible hours. Interested?", f"My company is hiring for data entry roles, no experience needed. Pays Rs. 30,000/month. Should I refer you?"],
            "phase_1": ["Great! You just need to pay a small refundable security deposit of Rs. 1500 for the laptop they send.", f"To process your application, HR needs a background check fee of Rs. 999. It's standard procedure. Here's the payment link: http://hr-gateway.{fake.domain_word()}.biz", f"You need to register on their portal. There's a small fee for the training material. http://careers.{fake.domain_word()}.org/register"],
            "phase_2": ["The spots are filling up very fast, you should complete the payment today.", "The HR manager is asking for an update on your application. Did you do it?", "Don't miss this chance, it's a golden opportunity!"],
            "victim_response": ["Oh, that sounds interesting! Tell me more.", "What's the company's name? Do they have a website?", "Why is there a fee? Usually companies don't charge for jobs.", "This sounds too good to be true."]
        },
        "crypto_investment_scam": {
            "phase_0": [f"Hey {user1}, have you invested in crypto yet? I'm getting insane returns!", "I found this new crypto platform that guarantees 20% profit every month. It's totally legit."],
            "phase_1": ["You just need to sign up and deposit a small amount to start. My expert advisor can guide you. Here's the link: http://crypto-gains.{fake.domain_word()}.io", "You can start with just Rs. 5000. I can add you to our private VIP signal group on Telegram."],
            "phase_2": ["The market is about to boom, you're missing out on easy money!", "My portfolio just went up by 10% today! You should have joined yesterday.", "Just do it. Trust me, you won't regret it."],
            "victim_response": ["Wow, really? I don't know much about crypto.", "Isn't it very risky? I've heard people lose a lot of money.", "How can I be sure this is not a scam?", "Can you show me your earnings statement?"]
        },
        "lottery_scam": {
            "phase_0": [f"OMG {user1}! Your number has won Rs. 25 Lakhs in the KBC lucky draw!", f"Congratulations! You've won a new TATA Safari in our company's anniversary giveaway. I just got the notification for you."],
            "phase_1": [f"To claim your prize, you need to first deposit the 5% GST amount, which is Rs. 1,25,000. Here are the bank details.", f"You need to pay a small processing fee of Rs. 15,000 to our manager to get the car released. It's fully refundable.", f"Please send your bank details, Aadhar card, and PAN card to this WhatsApp number to verify your identity: {fake.numerify('91##########')}"],
            "phase_2": ["Many people are waiting. If you don't pay the tax by today, the prize will be given to the next person.", "The manager is calling me continuously. Please complete the process fast.", "This is a once-in-a-lifetime chance, don't lose it for a small fee."],
            "victim_response": ["What? I never entered any lottery.", "This sounds like a scam. I'm not paying anything.", "Why do I have to pay money to receive a prize?", "Congratulations, but I think I'll pass."]
        }
    }


def generate_chat_conversation(num_messages=25, is_honeypot_scenario=False, chat_index=0):
    """
    Generates a two-person chat conversation with varied messages.
    """
    # --- User Setup (same as before) ---
    user1_id = fake.random_int(min=1000000000, max=9999999999)
    user1_first_name = fake.first_name_male()
    user1_last_name = fake.last_name_male()
    user1_username = f"{user1_first_name.lower()}_{user1_last_name.lower()}_{fake.random_int(min=100, max=999)}"
    user1_phone = fake.numerify('91##########')
    user1_bio = "Exploring new ideas and technologies."
    
    user2_id = fake.random_int(min=1000000000, max=9999999999)
    user2_first_name = fake.first_name_female()
    user2_last_name = fake.last_name_female()
    user2_username = f"{user2_first_name.lower()}_{user2_last_name.lower()}_{fake.random_int(min=100, max=999)}"
    user2_phone = fake.numerify('91##########')
    user2_bio = fake.sentence(nb_words=8)

    # --- NEW: Get the dynamic message templates ---
    benign_messages = get_benign_messages(user1_first_name, user2_first_name)
    honeypot_templates = get_honeypot_templates(user1_first_name, user2_first_name)
    
    # --- Conversation Flow Setup ---
    chat_id = user1_id
    messages = []
    current_time = datetime.now() - timedelta(days=random.randint(0, 15), hours=random.randint(1, 10))
    current_speaker_id = None if random.choice([True, False]) else f"PeerUser(user_id={user2_id})"

    honeypot_phase = 0
    honeypot_type = None

    if is_honeypot_scenario:
        honeypot_type = random.choice(list(honeypot_templates.keys()))
        honeypot_start_message_id = random.randint(int(num_messages * 0.4), int(num_messages * 0.7))

    for i in range(1, num_messages + 1):
        message_id = 1500 + i
        current_time += timedelta(minutes=random.randint(2, 7), seconds=random.randint(0, 59))
        message_text = ""
        sender_id = current_speaker_id

        # --- Honeypot Logic ---
        if is_honeypot_scenario and i >= honeypot_start_message_id:
            # The honeypot (user2) speaks
            if sender_id == f"PeerUser(user_id={user2_id})":
                phase_key = f"phase_{honeypot_phase}"
                if phase_key in honeypot_templates[honeypot_type]:
                    message_text = random.choice(honeypot_templates[honeypot_type][phase_key])
                    if honeypot_phase < 2: # Limit phase progression
                        honeypot_phase += 1
                else: # Fallback persistence message
                     message_text = "Just checking in again. Let me know."
            # The victim (user1) responds
            else:
                 message_text = random.choice(honeypot_templates[honeypot_type]["victim_response"])
        
        # --- Benign Conversation Logic ---
        else:
            message_text = random.choice(benign_messages)

        messages.append({
            "id": message_id,
            "date": current_time.isoformat(timespec='seconds') + "+00:00",
            "text": message_text,
            "from_id": sender_id,
            "media_file": None
        })

        # Switch speaker
        current_speaker_id = f"PeerUser(user_id={user2_id})" if current_speaker_id is None else None

    # --- Final JSON structure assembly (same as before) ---
    chat_data = {
        "exported_by": "Telegram Exporter Script",
        "export_date": datetime.now().isoformat(),
        "chat_id": chat_id,
        "chat_type": "User",
        "user_info": { "id": user1_id, "username": user1_username, "first_name": user1_first_name, "last_name": user1_last_name, "phone": user1_phone, "bio": user1_bio },
        "messages": messages
    }
    return chat_data


# --- Main execution block (same as before) ---
if __name__ == "__main__":
    START_INDEX = 715
    NUM_CONVERSATIONS = 150
    
    num_benign = NUM_CONVERSATIONS // 2
    num_honeypot = NUM_CONVERSATIONS - num_benign

    benign_dir = 'benign_chats'
    honeypot_dir = 'honeypot_chats'

    os.makedirs(benign_dir, exist_ok=True)
    os.makedirs(honeypot_dir, exist_ok=True)

    print(f"Generating {num_benign} benign conversations starting from index {START_INDEX}...")
    for i in range(num_benign):
        current_index = START_INDEX + i
        benign_conversation = generate_chat_conversation(num_messages=random.randint(20, 35), is_honeypot_scenario=False, chat_index=current_index)
        filename = os.path.join(benign_dir, f'chat{current_index}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(benign_conversation, f, ensure_ascii=False, indent=4)
        print(f"Generated '{filename}'")

    honeypot_start_index = START_INDEX + num_benign
    print(f"\nGenerating {num_honeypot} honeypot conversations starting from index {honeypot_start_index}...")
    for i in range(num_honeypot):
        current_index = honeypot_start_index + i
        honeypot_conversation = generate_chat_conversation(num_messages=random.randint(20, 35), is_honeypot_scenario=True, chat_index=current_index)
        filename = os.path.join(honeypot_dir, f'scam_chat{current_index}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(honeypot_conversation, f, ensure_ascii=False, indent=4)
        print(f"Generated '{filename}'")

    print("\n--- Generation Complete ---")
    print(f"Generated {NUM_CONVERSATIONS} JSON files with greater message variety.")