import json
import uuid
import os
import random

ADDON_DIR = os.path.dirname(__file__)
RANDOM_WORDS_FILE_PATH = os.path.join(ADDON_DIR, "random_words")

def collect_cards(soc):
    try:
        data_chunks = []
        while True:
            chunk = soc.recv(4096)
            if not chunk:
                break
            data_chunks.append(chunk)

        if not data_chunks:
            print("No data received")
            return

        decoded_data = b''.join(data_chunks).decode("utf-8")
        cards = json.loads(decoded_data)
        print(f"Received {len(cards)} cards")

        return cards

    except Exception as e:
        print(f"Error: {e}")


def generate_stable_uid():
    """Generate a stable unique identifier that won't change even if card content changes."""
    return str(uuid.uuid4())

def generate_random_deck_code():
    """Generate a random deck code from words"""
    try:
        if os.path.exists(RANDOM_WORDS_FILE_PATH):
            with open(RANDOM_WORDS_FILE_PATH, 'r') as file:
                words = [word.strip() for word in file if len(word.strip()) < 13]
        else:
            words = ["brave", "expert", "garden", "forest", "mountain", "river",
                     "ocean", "desert", "plain", "valley", "creek", "lake",
                     "spring", "autumn", "winter", "summer", "morning", "evening",
                     "night", "dawn", "dusk", "noon", "midnight", "today",
                     "tomorrow", "yesterday", "moment", "minute", "hour", "day"]

        selected_words = random.sample(words, 5)
        return "+".join(selected_words)
    except Exception as e:
        log_error(f"Error generating random deck code: {str(e)}")
        timestamp = int(time.time())
        return f"deck+code+{timestamp}"