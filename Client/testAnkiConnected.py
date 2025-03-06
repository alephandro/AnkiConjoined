import requests
import random
import time
import json

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
SYNC_FILE_PATH = "sync_log.json"



def get_cards_from_deck(deck_name):
    """Retrieves all cards from a specified deck using AnkiConnect."""
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f"deck:\"{deck_name}\""
        }
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
    target_timestamp = get_value_from_json(SYNC_FILE_PATH, deck_name)
    for note in response.get("result", []):
        if note["mod"] > target_timestamp:
            fields = note["fields"]

            field_data = {field_name: field_info["value"] for field_name, field_info in fields.items()}

            cards.append({
                "note_id": note["noteId"],
                "deck_name": deck_name,
                "model_name": note["modelName"],
                "fields": field_data,
                "tags": " ".join(note["tags"]),
                "created_at": note["noteId"],
                "last_modified": note["mod"],
                "interval": 1
            })
    if cards:
        lc_timestamp = cards[-1]["last_modified"]
        update_json(SYNC_FILE_PATH, deck_name, lc_timestamp)
    return cards


def update_json(file_path, deck_name, value):
    """Creates an entry in a json file or updates an existing one."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    data[deck_name] = value

    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


def get_value_from_json(file_path, deck_name):
    """Returns the value assigned to a deck. If the deck does not exist, returns 0."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    return data.get(deck_name, 0)



def sync_card(card_data):
    """Syncs a single card (insert/update) using AnkiConnect."""
    check_payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {
            "notes": [card_data["note_id"]]
        }
    }
    check_response = requests.post(ANKI_CONNECT_URL, json=check_payload).json()

    if check_response.get("result") and any(check_response["result"]):
        update_payload = {
            "action": "updateNoteFields",
            "version": 6,
            "params": {
                "note": {
                    "id": card_data["note_id"],
                    "fields": card_data["fields"],
                    "tags": card_data["tags"]
                }
            }
        }
        update_response = requests.post(ANKI_CONNECT_URL, json=update_payload).json()
        return update_response

    else:
        tags = card_data["tags"].split() if isinstance(card_data["tags"], str) else card_data["tags"]

        payload = {
            "action": "addNote",
            "version": 6,
            "params": {
                "note": {
                    "deckName": card_data["deck_name"],
                    "modelName": card_data["model_name"],
                    "fields": card_data["fields"],
                    "tags": tags,
                    "options": {
                        "allowDuplicate": False
                    }
                }
            }
        }

        response = requests.post(ANKI_CONNECT_URL, json=payload).json()
        return response


def check_for_deck_existence(deck_name):
    """Retrieves all decks for checking purposes. If the deck does not exist, the function creates it."""
    payload = {
        "action": "deckNames",
        "version": 6
    }

    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    decks = response.get("result", [])
    if not deck_name in decks:
        create_deck(deck_name)



def create_deck(deck_name):
    payload = {
        "action": "createDeck",
        "version": 6,
        "params": {
            "deck": deck_name
        }
    }

    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    return response

def generate_random_card(deck_name):
    """Generates a random test card matching the stored JSON format."""
    timestamp = int(time.time())
    random_id = random.randint(10 ** 12, 10 ** 13 - 1)

    return {
            "note_id": random_id,
            "deck_name": deck_name,
            "model_name": "Basic",
            "fields": {
                "Front": f"Test Question {random.randint(1, 100)}",
                "Back": f"Test Answer {random.randint(1, 100)}"
            },
            "tags": "test",
            "created_at": random_id,
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
        print(f"Note ID: {card['note_id']}")
        print(f"Deck: {card['deck_name']}")
        print(f"Model: {card['model_name']}")

        for field_name, field_value in card["fields"].items():
            print(f"{field_name}: {field_value}")

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


def list_decks():
    """Fetches all deck names from Anki via AnkiConnect."""
    payload = {
        "action": "deckNames",
        "version": 6
    }

    response = requests.post(ANKI_CONNECT_URL, json=payload)
    data = response.json()

    if data.get("error"):
        print("Error:", data["error"])
        return []

    return data.get("result", [])



def generate_random_deck_code():
    with open('../DataManagement/random_words', 'r') as file:
        words = [word.strip() for word in file if len(word.strip()) > 3]
    selected_words = random.sample(words, 5)
    return "+".join(selected_words)



if __name__ == "__main__":
    deck_name = 'TestDeck'

    print(f"Fetching cards from '{deck_name}'...")
    cards = get_cards_from_deck(deck_name)
    print_cards_simple(cards)

    print(generate_random_deck_code())

    '''print(f"Syncing new card to '{deck_name}'...")
    card = generate_random_card(deck_name)
    print(card)
    sync_card(card)'''
