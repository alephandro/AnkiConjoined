import requests
import random
import time
import json

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
SYNC_FILE_PATH = "sync_log.json"
DECKS_CODES_PATH = "decks_codes.json"


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

            stable_uid = None
            for tag in note["tags"]:
                if tag.startswith("sync_uid:"):
                    stable_uid = tag[9:]
                    break

            cards.append({
                "note_id": note["noteId"],
                "stable_uid": stable_uid,
                "deck_name": deck_name,
                "model_name": note["modelName"],
                "fields": field_data,
                "tags": " ".join(note["tags"]),
                "created_at": note["noteId"],
                "last_modified": note["mod"],
                "interval": 1
            })
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


def find_card_with_tag(uid_tag):
    find_payload = {
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f"tag:{uid_tag}"
        }
    }
    find_response = requests.post(ANKI_CONNECT_URL, json=find_payload).json()
    return find_response.get("result", [])


def find_card_with_matching_fields(card_data):
    first_field_name = next(iter(card_data["fields"]))
    first_field_content = card_data["fields"][first_field_name]

    search_payload = {
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f'deck:"{card_data["deck_name"]}" {first_field_name}:"{first_field_content}"'
        }
    }

    search_response = requests.post(ANKI_CONNECT_URL, json=search_payload).json()
    return search_response.get("result", [])


def update_card(card_data, tags):
    update_payload = {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": card_data["note_id"],
                "fields": card_data["fields"],
                "tags": tags
            }
        }
    }
    update_response = requests.post(ANKI_CONNECT_URL, json=update_payload).json()
    return update_response


def update_tags(card_data, tags):
    payload = {
            "action": "updateNoteTags",
            "version": 6,
            "params": {
                "note": card_data["note_id"],
                "tags": tags
            }
    }
    update_response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    return update_response

def create_new_card(card_data, tags):
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


def sync_card(card_data):
    """Syncs a single card (insert/update) using AnkiConnect."""
    tags = card_data["tags"].split() if isinstance(card_data["tags"], str) else card_data["tags"]
    tags = [tag for tag in tags if not tag.startswith("sync_uid:")]

    uid_tag = f"sync_uid:{card_data['stable_uid']}"
    tags.append(uid_tag)

    note_with_tag = find_card_with_tag(uid_tag)
    if note_with_tag:
        card_data["note_id"] = note_with_tag[0]
        update_card(card_data, tags)
        update_tags(card_data, tags)
        return

    matching_note = find_card_with_matching_fields(card_data)
    if len(matching_note) > 0:
        card_data["note_id"] = matching_note[0]
        update_card(card_data, tags)
        update_tags(card_data, tags)
        return

    return create_new_card(card_data, tags)


def list_decks():
    """Fetches all deck names from Anki via AnkiConnect."""
    payload = {
        "action": "deckNames",
        "version": 6
    }

    response = requests.post(ANKI_CONNECT_URL, json=payload).json()
    return response.get("result", [])


def check_for_deck_existence(deck_name):
    """Retrieves all decks for checking purposes. If the deck does not exist, the function creates it."""
    decks = list_decks()
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


def generate_random_deck_code():
    with open('../DataManagement/random_words', 'r') as file:
        words = [word.strip() for word in file if 3 < len(word.strip()) < 11]
    selected_words = random.sample(words, 5)
    return "+".join(selected_words)


def get_code_from_deck(deck_name):
    deck_code = get_value_from_json(DECKS_CODES_PATH, deck_name)
    if deck_code == 0:
        deck_code = generate_random_deck_code()
        update_json(DECKS_CODES_PATH, deck_name, deck_code)
    return deck_code


if __name__ == "__main__":
    deck_name = 'TestDeck'

    '''print(f"Fetching cards from '{deck_name}'...")
    cards = get_cards_from_deck(deck_name)
    print_cards_simple(cards)'''

    print(get_code_from_deck(deck_name))

    '''print(f"Syncing new card to '{deck_name}'...")
    card = generate_random_card(deck_name)
    print(card)
    sync_card(card)'''
