import requests
import random
import time

ANKI_CONNECT_URL = "http://127.0.0.1:8765"


def get_cards_from_deck(deck_name, timestamp):
    """Retrieves all cards from a specified deck using AnkiConnect."""
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": f"deck:{deck_name}"}
    }

    response = requests.post(ANKI_CONNECT_URL, json=payload).json()

    note_ids = response.get("result", [])

    if not note_ids:
        print(f"Deck '{deck_name}' not found or empty.")
        return []

    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {"notes": note_ids}
    }
    response = requests.post(ANKI_CONNECT_URL, json=payload).json()

    cards = []
    for note in response.get("result", []):
        if note["mod"] > timestamp:
            fields = note["fields"]
            cards.append({
                "note_id": note["noteId"],
                "deck_id": note["modelName"],
                "question": fields["Front"]["value"],
                "answer": fields["Back"]["value"],
                "tags": " ".join(note["tags"]),
                "created_at": note["noteId"],
                "last_modified": note["mod"],
                "interval": 1
            })

    return cards


def sync_card(deck_name, card_data):
    """Syncs a single card (insert/update) using AnkiConnect."""
    payload = {
        "action": "addNotes",
        "version": 6,
        "params": {
            "notes": [{
                "deckName": deck_name,
                "modelName": "Basic",
                "fields": {
                    "Front": card_data["question"],
                    "Back": card_data["answer"]
                },
                "tags": card_data["tags"].split(),
                "options": {"allowDuplicate": False}
            }]
        }
    }

    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    print("Sync Response:", response)


def generate_random_card(deck_name):
    """Generates a random test card with unique IDs and timestamps."""
    timestamp = int(time.time())
    random_id = random.randint(10 ** 12, 10 ** 13 - 1)

    return {
        "note_id": random_id,
        "deck_id": deck_name,
        "question": f"Test Question {random.randint(1, 100)}",
        "answer": f"Test Answer {random.randint(1, 100)}",
        "tags": "test",
        "created_at": timestamp,
        "last_modified": timestamp,
        "interval": 1
    }


def print_cards_simple(card_list):
    if not card_list:
        print("No se encontraron tarjetas.")
        return

    print(f"Se encontraron {len(card_list)} tarjetas:")
    print("-" * 80)

    for i, card in enumerate(card_list, 1):
        print(f"Tarjeta #{i}")
        print(f"Pregunta: {card['question']}")
        print(f"Respuesta: {card['answer']}")
        print(f"Etiquetas: {card['tags']}")
        print(f"Última modificación: {card['last_modified']}")
        print("-" * 80)


def sync_anki():
    """Triggers a sync with AnkiWeb using AnkiConnect."""
    response = requests.post(ANKI_CONNECT_URL, json={"action": "sync", "version": 6}).json()

    if response.get("error"):
        print("❌ Sync failed:", response["error"])
    else:
        print("✅ Sync successful!")


if __name__ == "__main__":
    deck_name = "TestDeck"  # Change this to your target deck

    print(f"Fetching cards from '{deck_name}'...")
    cards = get_cards_from_deck(deck_name, 1740659441)
    print_cards_simple(cards)

'''
    print(f"Syncing new card to '{deck_name}'...")
    sync_card(deck_name, generate_random_card(deck_name))

    print("Sync complete! Triggering AnkiWeb sync...")
    sync_anki()
'''