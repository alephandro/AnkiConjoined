import requests
import random
import time
import json
import os
import traceback
from threading import Thread
from aqt.qt import QObject, pyqtSignal
from aqt import mw

# Get the addon directory for absolute file paths
ADDON_DIR = os.path.dirname(__file__)
SYNC_FILE_PATH = os.path.join(ADDON_DIR, "sync_log.json")
DECKS_CODES_PATH = os.path.join(ADDON_DIR, "decks_codes.json")
ERROR_LOG_PATH = os.path.join(ADDON_DIR, "error_log.txt")
ANKI_CONNECT_URL = "http://127.0.0.1:8765"

# Worker class to handle AnkiConnect requests in background threads
class AnkiConnectWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, action, **params):
        super().__init__()
        self.action = action
        self.params = params

    # In testAnkiConnected.py - Update the AnkiConnectWorker.run method:

    def run(self):
        try:
            request_json = {
                "action": self.action,
                "version": 6,
                "params": self.params
            }

            # Add timeout to prevent hanging
            response = requests.post(ANKI_CONNECT_URL, json=request_json, timeout=5)

            # Handle HTTP errors
            if response.status_code != 200:
                self.error.emit(f"HTTP Error: {response.status_code}")
                return

            try:
                result = response.json()
            except json.JSONDecodeError:
                self.error.emit("Invalid JSON response")
                return

            if "error" in result and result["error"] is not None:
                self.error.emit(f"AnkiConnect error: {result['error']}")
            else:
                self.finished.emit(result)
        except requests.exceptions.ConnectionError:
            self.error.emit(f"Connection error: Failed to connect to AnkiConnect at {ANKI_CONNECT_URL}")
        except requests.exceptions.Timeout:
            self.error.emit("Connection timed out - AnkiConnect is not responding")
        except Exception as e:
            error_msg = f"Error in AnkiConnect request '{self.action}': {str(e)}"
            self.error.emit(error_msg)


def log_error(message):
    """Log errors to file for debugging"""
    try:
        with open(ERROR_LOG_PATH, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
            f.write(traceback.format_exc())
            f.write("\n---\n")
    except:
        pass  # Fallback in case logging itself fails


def anki_connect_request(action, success_callback, error_callback=None, retry_count=3, retry_delay=1.0, **params):
    """Make an AnkiConnect request in a background thread with retry on connection errors

    Args:
        action: The AnkiConnect action to perform
        success_callback: Callback function to handle successful results
        error_callback: Callback function to handle errors
        retry_count: Number of retries left (default 3)
        retry_delay: Delay between retries in seconds, will increase exponentially
        **params: Parameters for the AnkiConnect action
    """
    # Create a worker to execute the request
    worker = AnkiConnectWorker(action, **params)

    def handle_error(error_msg):
        if retry_count > 0 and ("Connection error" in error_msg or
                                "timed out" in error_msg or
                                "HTTP Error" in error_msg):
            print(f"Connection to AnkiConnect failed. Retrying in {retry_delay:.1f}s... ({retry_count} attempts left)")

            def retry_request():
                anki_connect_request(
                    action,
                    success_callback,
                    error_callback,
                    retry_count - 1,
                    retry_delay * 1.5,
                    **params
                )

            from aqt.qt import QTimer
            QTimer.singleShot(int(retry_delay * 1000), retry_request)
        else:
            log_error(f"{error_msg} (after {3 - retry_count} retries)")
            if error_callback:
                error_callback(error_msg)

    worker.finished.connect(success_callback)
    worker.error.connect(handle_error)

    thread = Thread(target=worker.run)
    thread.daemon = True
    thread.start()

# File operation utilities with error handling
def read_json_file(file_path, default=None):
    """Read a JSON file with error handling"""
    if default is None:
        default = {}
    
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default
    except Exception as e:
        log_error(f"Error reading JSON file {file_path}: {str(e)}")
        return default

def write_json_file(file_path, data):
    """Write to a JSON file with error handling"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        log_error(f"Error writing to JSON file {file_path}: {str(e)}")
        return False

def get_cards_from_deck(deck_name, callback):
    """Retrieves all cards from a specified deck using AnkiConnect (async)"""
    def on_find_notes_result(result):
        if "result" not in result:
            callback([])
            return
            
        note_ids = result["result"]
        if not note_ids:
            print(f"Deck '{deck_name}' not found or empty.")
            callback([])
            return
            
        anki_connect_request("notesInfo", on_notes_info_result, on_error, notes=note_ids)
    
    def on_notes_info_result(result):
        if "result" not in result:
            callback([])
            return
            
        cards = []
        target_timestamp = get_value_from_json(SYNC_FILE_PATH, deck_name)
        
        for note in result["result"]:
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
        
        callback(cards)
    
    def on_error(error_msg):
        log_error(f"Error getting cards from deck '{deck_name}': {error_msg}")
        callback([])
    
    anki_connect_request("findNotes", on_find_notes_result, on_error, query=f"deck:\"{deck_name}\"")

def update_json(file_path, deck_name, value):
    """Creates an entry in a json file or updates an existing one."""
    data = read_json_file(file_path)
    data[deck_name] = value
    return write_json_file(file_path, data)

def get_value_from_json(file_path, deck_name):
    """Returns the value assigned to a deck. If the deck does not exist, returns 0."""
    data = read_json_file(file_path)
    return data.get(deck_name, 0)

def find_card_with_tag(uid_tag, callback):
    """Find cards with a specific tag (async)"""
    def on_result(result):
        if "result" in result:
            callback(result["result"])
        else:
            callback([])
    
    def on_error(error_msg):
        log_error(f"Error finding card with tag '{uid_tag}': {error_msg}")
        callback([])
    
    anki_connect_request("findNotes", on_result, on_error, query=f"tag:{uid_tag}")

def find_card_with_matching_fields(card_data, callback):
    """Find cards with matching fields (async)"""
    first_field_name = next(iter(card_data["fields"]))
    first_field_content = card_data["fields"][first_field_name]
    
    def on_result(result):
        if "result" in result:
            callback(result["result"])
        else:
            callback([])
    
    def on_error(error_msg):
        log_error(f"Error finding card with matching fields: {error_msg}")
        callback([])
    
    query = f'deck:"{card_data["deck_name"]}" {first_field_name}:"{first_field_content}"'
    anki_connect_request("findNotes", on_result, on_error, query=query)

def update_card(card_data, tags, callback):
    """Update an existing card (async)"""
    def on_result(result):
        callback(result)
    
    def on_error(error_msg):
        log_error(f"Error updating card {card_data['note_id']}: {error_msg}")
        callback({"error": error_msg})
    
    anki_connect_request("updateNoteFields", on_result, on_error, 
                         note={"id": card_data["note_id"], 
                               "fields": card_data["fields"], 
                               "tags": tags})

def update_tags(card_data, tags, callback):
    """Update tags on an existing card (async)"""
    def on_result(result):
        callback(result)
    
    def on_error(error_msg):
        log_error(f"Error updating tags for card {card_data['note_id']}: {error_msg}")
        callback({"error": error_msg})
    
    anki_connect_request("updateNoteTags", on_result, on_error, 
                         note=card_data["note_id"], tags=tags)

def create_new_card(card_data, tags, callback):
    """Create a new card (async)"""
    def on_result(result):
        callback(result)
    
    def on_error(error_msg):
        log_error(f"Error creating new card: {error_msg}")
        callback({"error": error_msg})
    
    anki_connect_request("addNote", on_result, on_error, 
                         note={"deckName": card_data["deck_name"],
                               "modelName": card_data["model_name"],
                               "fields": card_data["fields"],
                               "tags": tags,
                               "options": {"allowDuplicate": False}})

def sync_card(card_data, final_callback=None):
    """Syncs a single card (insert/update) using AnkiConnect (async)"""
    tags = card_data["tags"].split() if isinstance(card_data["tags"], str) else card_data["tags"]
    tags = [tag for tag in tags if not tag.startswith("sync_uid:")]
    
    uid_tag = f"sync_uid:{card_data['stable_uid']}"
    tags.append(uid_tag)
    
    def on_tag_search_complete(note_with_tag):
        if note_with_tag:
            card_data["note_id"] = note_with_tag[0]
            update_card(card_data, tags, on_update_complete)
        else:
            find_card_with_matching_fields(card_data, on_field_search_complete)
    
    def on_field_search_complete(matching_note):
        if matching_note:
            card_data["note_id"] = matching_note[0]
            update_card(card_data, tags, on_update_complete)
        else:
            create_new_card(card_data, tags, on_create_complete)
    
    def on_update_complete(result):
        update_tags(card_data, tags, on_tags_updated)
    
    def on_tags_updated(result):
        if final_callback:
            final_callback(result)
    
    def on_create_complete(result):
        if final_callback:
            final_callback(result)
    
    find_card_with_tag(uid_tag, on_tag_search_complete)


# In testAnkiConnected.py - Update the list_decks function:

def list_decks(callback, error_callback=None):
    """Fetches all deck names from Anki via AnkiConnect (async)"""

    def on_result(result):
        if "result" in result:
            callback(result["result"])
        else:
            if error_callback:
                error_callback("No result in response")
            else:
                # Fallback to provide at least some decks
                try:
                    # Get decks directly from Anki's collection
                    deck_names = [d['name'] for d in mw.col.decks.all()]
                    callback(deck_names)
                except:
                    callback(["Default"])

    def on_error(error_msg):
        log_error(f"Error listing decks: {error_msg}")
        if error_callback:
            error_callback(error_msg)
        else:
            # Fallback to provide at least some decks
            try:
                # Get decks directly from Anki's collection
                deck_names = [d['name'] for d in mw.col.decks.all()]
                callback(deck_names)
            except:
                callback(["Default"])

    anki_connect_request("deckNames", on_result, on_error)

def check_for_deck_existence(deck_name, callback=None):
    """Checks if a deck exists and creates it if not (async)"""
    def on_decks_listed(decks):
        if deck_name not in decks:
            create_deck(deck_name, on_deck_created)
        elif callback:
            callback(True)
    
    def on_deck_created(result):
        if callback:
            callback("result" in result)
    
    list_decks(on_decks_listed)

def create_deck(deck_name, callback=None):
    """Creates a new deck (async)"""
    def on_result(result):
        if callback:
            callback(result)
    
    def on_error(error_msg):
        log_error(f"Error creating deck '{deck_name}': {error_msg}")
        if callback:
            callback({"error": error_msg})
    
    anki_connect_request("createDeck", on_result, on_error, deck=deck_name)

def delete_deck(deck_name, callback=None):
    """Deletes a deck (async)"""
    def on_result(result):
        if callback:
            callback(result)
    
    def on_error(error_msg):
        log_error(f"Error deleting deck '{deck_name}': {error_msg}")
        if callback:
            callback({"error": error_msg})
    
    anki_connect_request("deleteDecks", on_result, on_error, 
                         decks=[deck_name], cardsToo=True)

def delete_key_from_json(key, path):
    """Removes a key from a JSON file"""
    data = read_json_file(path)
    if key in data:
        del data[key]
        write_json_file(path, data)

def delete_deck_information(deck_name, callback=None):
    """Deletes a deck and its sync information (async)"""
    def on_deck_deleted(result):
        delete_key_from_json(deck_name, SYNC_FILE_PATH)
        delete_key_from_json(deck_name, DECKS_CODES_PATH)
        if callback:
            callback(result)
    
    delete_deck(deck_name, on_deck_deleted)

def generate_random_card(deck_name):
    """Generates a random test card matching the stored JSON format."""
    timestamp = int(time.time())
    random_id = random.randint(10 ** 12, 10 ** 13 - 1)

    return {
        "note_id": random_id,
        "stable_uid": str(random.uuid4()),  # Generate a proper stable_uid
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
        print("No cards found.")
        return

    print(f"Found {len(card_list)} cards:")
    print("-" * 80)

    for i, card in enumerate(card_list, 1):
        print(f"Card #{i}")
        print(f"Note ID: {card['note_id']}")
        print(f"Deck: {card['deck_name']}")
        print(f"Model: {card['model_name']}")

        for field_name, field_value in card["fields"].items():
            print(f"{field_name}: {field_value}")

        print(f"Tags: {card['tags']}")
        print(f"Last modified: {card['last_modified']}")
        print("-" * 80)

def sync_anki(callback=None):
    """Triggers a sync with AnkiWeb using AnkiConnect (async)"""
    def on_result(result):
        print("✅ Sync successful!")
        if callback:
            callback(True)
    
    def on_error(error_msg):
        print(f"❌ Sync failed: {error_msg}")
        log_error(f"Sync failed: {error_msg}")
        if callback:
            callback(False)
    
    anki_connect_request("sync", on_result, on_error)

def generate_random_deck_code():
    """Generate a random deck code from words"""
    try:
        random_words_path = os.path.join(ADDON_DIR, "DataManagement", "random_words")
        if os.path.exists(random_words_path):
            with open(random_words_path, 'r') as file:
                words = [word.strip() for word in file if 3 < len(word.strip()) < 11]
        else:
            # Fallback if file doesn't exist
            words = ["brave", "expert", "garden", "forest", "mountain", "river", 
                     "ocean", "desert", "plain", "valley", "creek", "lake", 
                     "spring", "autumn", "winter", "summer", "morning", "evening",
                     "night", "dawn", "dusk", "noon", "midnight", "today", 
                     "tomorrow", "yesterday", "moment", "minute", "hour", "day"]
            
        selected_words = random.sample(words, 5)
        return "+".join(selected_words)
    except Exception as e:
        log_error(f"Error generating random deck code: {str(e)}")
        # Fallback with a timestamp-based code
        timestamp = int(time.time())
        return f"deck+code+{timestamp}"

def get_code_from_deck(deck_name):
    """Get or generate a code for a deck"""
    deck_code = get_value_from_json(DECKS_CODES_PATH, deck_name)
    if deck_code == 0:
        deck_code = generate_random_deck_code()
        update_json(DECKS_CODES_PATH, deck_name, deck_code)
    return deck_code


# Update this function in testAnkiConnected.py
def check_for_deck_in_json(deck_code, callback=None):
    """Check if a deck code exists in the config"""
    try:
        data = read_json_file(DECKS_CODES_PATH)

        result = False
        for key, value in data.items():
            if value == deck_code:
                result = True
                break

        # If a callback was provided, call it with the result
        if callback:
            callback(result)

        # Also return the result for backward compatibility
        return result
    except Exception as e:
        log_error(f"Error checking deck code: {str(e)}")
        if callback:
            callback(False)
        return False

# Initialize the config files if they don't exist
def ensure_config_files():
    """Make sure config files exist with valid JSON content"""

    # Create empty dictionaries as default content
    default_content = {}

    # Check sync file
    if not os.path.exists(SYNC_FILE_PATH):
        with open(SYNC_FILE_PATH, "w") as f:
            json.dump(default_content, f, indent=4)
    else:
        # Test if the file can be read as JSON
        try:
            with open(SYNC_FILE_PATH, "r") as f:
                json.load(f)
        except json.JSONDecodeError:
            # If invalid JSON, overwrite with valid empty JSON
            with open(SYNC_FILE_PATH, "w") as f:
                json.dump(default_content, f, indent=4)

    # Check decks codes file
    if not os.path.exists(DECKS_CODES_PATH):
        with open(DECKS_CODES_PATH, "w") as f:
            json.dump(default_content, f, indent=4)
    else:
        # Test if the file can be read as JSON
        try:
            with open(DECKS_CODES_PATH, "r") as f:
                json.load(f)
        except json.JSONDecodeError:
            # If invalid JSON, overwrite with valid empty JSON
            with open(DECKS_CODES_PATH, "w") as f:
                json.dump(default_content, f, indent=4)

# Call this at module load time
ensure_config_files()

# Example usage if run directly
if __name__ == "__main__":
    def on_cards_retrieved(cards):
        print_cards_simple(cards)
    
    def on_deck_code(deck_name):
        print(f"Deck code for '{deck_name}': {get_code_from_deck(deck_name)}")
    
    deck_name = 'TestDeck'
    on_deck_code(deck_name)
    
    # The following would be called from a menu item or action
    # get_cards_from_deck(deck_name, on_cards_retrieved)
