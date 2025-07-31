import sqlite3
import json
from datetime import datetime, timedelta

# This script will populate your scam_intelligence.db with sample data.
# Make sure this script is in the same folder as your database file.

DB_NAME = "scam_intelligence.db"

# A list of realistic, fictional scammer data
dummy_scams = [
    {
        "chat_id": 101101101,
        "contact_name": "Anna CryptoQueen",
        "scam_type": "Investment Scam",
        "scammer_tactic": "Guaranteed high returns on a new cryptocurrency. Creates a sense of urgency and exclusivity.",
        "red_flags_identified": "['Pressure to invest quickly', 'Promises of guaranteed profit', 'Vague technical details', 'Asks for payment in crypto']",
        "extracted_details": json.dumps({"crypto_wallet_address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"}),
        "hacker_strategy_summary": "Lures victim with the promise of quick wealth through a fake crypto platform. The primary goal is to get the victim to transfer funds to a wallet controlled by the scammer."
    },
    {
        "chat_id": 202202202,
        "contact_name": "David The Traveler",
        "scam_type": "Romance Scam",
        "scammer_tactic": "Builds an emotional connection over several weeks, then fabricates an emergency (e.g., medical bill, stuck in a foreign country) requiring immediate financial help.",
        "red_flags_identified": "['Moves from dating app to private chat quickly', 'Professes love very early', 'Always has an excuse not to video call', 'Story is inconsistent', 'Sudden financial emergency']",
        "extracted_details": json.dumps({"requested_amount": 2500, "reason": "Stranded at airport, lost wallet"}),
        "hacker_strategy_summary": "Exploits emotional vulnerability to build trust before manufacturing a crisis that requires the victim to send money. This is a classic social engineering tactic."
    },
    {
        "chat_id": 303303303,
        "contact_name": "HR @ Global Tech Inc",
        "scam_type": "Job Scam",
        "scammer_tactic": "Offers a high-paying, remote job with minimal interview process. Requires the 'new hire' to pay for equipment or training materials upfront, promising reimbursement.",
        "red_flags_identified": "['Job offer seems too good to be true', 'Unprofessional communication (grammar errors)', 'Asks for money for equipment', 'Vague job description', 'Uses a public email domain like gmail.com']",
        "extracted_details": json.dumps({"company_name": "Global Tech Inc (Fake)", "upfront_fee": 499.99, "payment_method": "Bank Transfer"}),
        "hacker_strategy_summary": "Preys on job seekers by offering a dream job. The actual goal is to collect an 'advance fee' for non-existent equipment or services."
    },
    {
        "chat_id": 404404404,
        "contact_name": "SupportAgent007",
        "scam_type": "Technical Support Scam",
        "scammer_tactic": "Claims to be from a major tech company (e.g., Microsoft, Amazon) and says the victim's account has been compromised. Urges the victim to install remote access software to 'fix' the issue.",
        "red_flags_identified": "['Unsolicited contact', 'Creates a sense of panic', 'Asks for remote access to computer', 'Directs user to a fake login page']",
        "extracted_details": json.dumps({"impersonated_company": "Microsoft", "remote_software": "AnyDesk"}),
        "hacker_strategy_summary": "Uses fear and authority to trick the victim into granting remote access to their computer, which can be used to steal personal information, install malware, or access bank accounts."
    },
    {
        "chat_id": 505505505,
        "contact_name": "Prince Adebayo",
        "scam_type": "Advance-Fee Scam",
        "scammer_tactic": "Classic 'Nigerian Prince' scam. Claims the victim has been chosen to receive a large sum of money but must first pay a smaller fee for legal or administrative costs.",
        "red_flags_identified": "['Large sum of money offered for little or no reason', 'Request for an advance fee', 'Poor spelling and grammar', 'Emphasis on secrecy']",
        "extracted_details": json.dumps({"inheritance_amount": "10,500,000 USD", "fee_required": "1,500 USD"}),
        "hacker_strategy_summary": "A long-running scam that relies on pure greed. The scammer's goal is to convince the victim to send a small amount of money in the hopes of receiving a much larger, non-existent fortune."
    }
]

def seed_database():
    """Connects to the database and inserts the dummy data."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        print(f"✅ Successfully connected to {DB_NAME}")

        # Create the table if it doesn't exist (using the schema from your file)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE,
                contact_name TEXT,
                classification_timestamp TEXT,
                scam_type TEXT,
                scammer_tactic TEXT,
                red_flags_identified TEXT,
                extracted_details TEXT,
                hacker_strategy_summary TEXT
            )
        """)

        # Insert the data
        for i, scam in enumerate(dummy_scams):
            # Generate a slightly different timestamp for each entry
            timestamp = (datetime.now() - timedelta(days=len(dummy_scams) - i)).isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO scams (chat_id, contact_name, classification_timestamp, scam_type, scammer_tactic, red_flags_identified, extracted_details, hacker_strategy_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scam["chat_id"],
                scam["contact_name"],
                timestamp,
                scam["scam_type"],
                scam["scammer_tactic"],
                scam["red_flags_identified"],
                scam["extracted_details"],
                scam["hacker_strategy_summary"]
            ))
        
        conn.commit()
        print(f"✅ Successfully inserted/updated {len(dummy_scams)} records into the 'scams' table.")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("✅ Database connection closed.")

if __name__ == "__main__":
    seed_database()
