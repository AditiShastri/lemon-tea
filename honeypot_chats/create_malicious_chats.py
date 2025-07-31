import json
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)
random.seed(42)

# Your data pools (10 each)...
attacker_claims = [
    "Hey, I’m Selena Gomez. Don’t laugh 😂",
    "Hi, I'm from Netflix’s influencer team – quick question?",
    "You just won an iPhone giveaway 🎉 Check this out",
    "This is Elon Musk’s assistant. Wanna beta test something?",
    "Hello from Binance support, urgent wallet issue ⚠️",
    "Hey! I saw your reel and thought we should talk 🔥",
    "This is Rahul from Google Career Accelerator – selected?",
    "I'm recruiting for a private crypto alpha group 💰",
    "Hey, random but you look super familiar 👀",
    "You're eligible for $150/day UPI job (limited slots)"
]

phishing_links = [
    "https://bit.ly/freedrop100",
    "https://tinyurl.com/claim-now-prize",
    "http://verifywallet-safe.shop",
    "https://airdrop-crypto.link",
    "https://freegiftcard.click",
    "http://instafameboost.io",
    "https://exclusivebetaapp.com",
    "http://wallet-repair.xyz",
    "https://fastjob-india.com",
    "http://test-access-pass.live"
]

escalation_texts = [
    "Idk why, but I really trust you already 😳",
    "Please don’t ghost me like others 💔",
    "I’m not like the others. Just talk to me 🥺",
    "Only you got this link. Don’t share.",
    "Just promise you’ll keep this secret?",
    "I’ve been so lonely lately... just needed someone",
    "I feel something real here 😳👉👈",
    "Don’t judge me for saying this, but I think I like you",
    "Just one click and you'll understand 🔥",
    "I’m serious. Don’t make me beg."
]

final_push_texts = [
    "Last 5 mins. After that, the link expires ⏳",
    "Click or regret. I won’t repeat myself ⚠️",
    "You said you were different. Prove it.",
    "You think I’m fake? I’ll block then 👋",
    "This is real money. Why would I lie?",
    "Even my cousin earned from this. Ask him.",
    "I trusted you with this. Please respond 😢",
    "You ignoring me now? Typical.",
    "Just enter your UPI ID. No risk, I swear 💸",
    "Whatever. You missed a real chance."
]

attacker_usernames = [
    "gomez_supportteam", "elonverified_beta", "netflix.pr.official", "binancewallet_alert",
    "insta_cashdrop2025", "starstruck.agency", "verified_jobs_hr", "crypto_alpha_wave",
    "realbollywoodstar", "upijobs_payouts"
]

flattery_lines = [
    "I love your vibe, fr 🫶", "You seem so chill. Rare these days 😌", "Cute + smart? Jackpot 🔥",
    "Wish I met someone like you sooner", "You’re giving main character energy 🧿",
    "You’d do great as a creator btw 💯", "Are you famous? You look like it 👀",
    "How are you still single?!", "Not tryna flirt but you’re attractive 😅",
    "You got me smiling at my screen rn"
]

suspicious_emojis = ["🔥", "💋", "💸", "👉👈", "🥺", "⚠️", "⏳", "😳", "💯", "💰"]
odd_hours = [0, 1, 2, 3, 4, 5, 23]
victim_replies = [
    "who are you?", "no", "stop texting me", "what is this?", "??",
    "not interested", "okay?", "leave me alone", "how did you get my number?", "are you serious?"
]

def generate_message(from_id, current_time, text):
    msg_time = current_time + timedelta(seconds=random.randint(5, 60))
    return {
        "id": random.randint(1000, 9999),
        "date": msg_time.isoformat() + "+00:00",
        "text": text,
        "from_id": from_id,
        "media_file": None
    }, msg_time

def generate_recent_attacker_id():
    # Generate a 10-digit user ID starting with 74 or 75 (July 2025)
    prefix = str(random.choice([74, 75]))
    suffix = ''.join(str(random.randint(0, 9)) for _ in range(8))
    return int(prefix + suffix)

def generate_victim_id():
    prefix = str(random.choice([68, 69, 70, 71]))
    suffix = ''.join(str(random.randint(0, 9)) for _ in range(8))
    return int(prefix + suffix)

def generate_malicious_chat(chat_number):
    attacker_id = generate_recent_attacker_id()
    victim_id = generate_victim_id()

    opener = random.choice(attacker_claims)
    link = "Click here 👉 " + random.choice(phishing_links)
    escalation = random.choice(escalation_texts)
    final_push = random.choice(final_push_texts)
    flattery = random.choice(flattery_lines)
    emoji = random.choice(suspicious_emojis)
    attacker_username = random.choice(attacker_usernames)
    victim_reply = random.choice(victim_replies)

    base_time = datetime.now().replace(hour=random.choice(odd_hours), minute=random.randint(0, 59), second=0, microsecond=0)
    current_time = base_time
    conversation = []

    for text in [opener, flattery, escalation, link, final_push]:
        message, current_time = generate_message(f"PeerUser(user_id={attacker_id})", current_time, text + " " + emoji)
        conversation.append(message)

    if random.random() < 0.7:
        message, current_time = generate_message(None, current_time, victim_reply)
        conversation.append(message)

    if random.random() < 0.5:
        msg, current_time = generate_message(f"PeerUser(user_id={attacker_id})", current_time, "Don’t miss this chance 💰")
        conversation.append(msg)

    chat_json = {
        "exported_by": "Telegram Exporter Script",
        "export_date": datetime.utcnow().isoformat(),
        "chat_id": victim_id,
        "chat_type": "User",
        "user_info": {
            "id": victim_id,
            "username": fake.user_name(),
            "first_name": fake.first_name(),
            "last_name": None,
            "phone": fake.msisdn(),
            "bio": None,
            "profile_picture_file": f"pfp_{attacker_username}.jpg"
        },
        "messages": conversation
    }

    with open(f"chat_malicious{chat_number}.json", "w") as f:
        json.dump(chat_json, f, indent=4)

    print(f"⚠️ Malicious chat with attacker ID {attacker_id} saved to scam_chat{chat_number}.json")

# Generate 5 samples
for i in range(715, 800):
    generate_malicious_chat(i)
