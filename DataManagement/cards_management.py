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
    with open(RANDOM_WORDS_FILE_PATH, 'r') as file:
        words = [word.strip() for word in file if 3 < len(word.strip()) < 11]
    selected_words = random.sample(words, 5)
    return "+".join(selected_words)