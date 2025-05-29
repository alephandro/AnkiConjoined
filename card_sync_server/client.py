import socket
import json
import time
import os
from aqt import mw
from aqt.qt import QObject, pyqtSignal, QSettings, QMessageBox
from aqt.utils import showWarning

from .auth_manager import AuthManager
from .login_dialog import LoginDialog
from .testAnkiConnected import (
    get_cards_from_deck, sync_card, update_json,
    get_value_from_json, sync_anki, check_for_deck_existence,
    get_code_from_deck, create_deck, check_for_deck_in_json,
    delete_deck_information, list_decks, log_error,
    anki_connect_request
)

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
SYNC_FILE_PATH = os.path.join(ADDON_DIR, "sync_log.json")
DECKS_CODES_PATH = os.path.join(ADDON_DIR, "decks_codes.json")


class Client(QObject):
    HEADER = 64

    operation_complete = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self.settings = QSettings("AnkiConjoined", "CardSync")
        self.server_host = self.settings.value("server_host", "127.0.0.1")
        self.server_port = int(self.settings.value("server_port", 9999))

        self.auth_manager = AuthManager(ADDON_DIR)
        self.sock = None

    def ensure_authenticated(self, parent=None):
        """Make sure user is authenticated before performing operations"""
        if self.auth_manager.is_authenticated():
            print("User is already authenticated")
            return True

        print("User needs to authenticate")
        return LoginDialog.get_credentials(parent)

    def connect_to_server(self):
        """Connect to the server"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_host, self.server_port))
            print(f"Connected to server at {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            error_msg = f"Server connection failed: {str(e)}"
            log_error(error_msg)
            showWarning(f"Could not connect to the sync server.\n\n{error_msg}")
            return False

    def send_cards(self, deck_name, callback=None):
        if not self.ensure_authenticated(mw):
            if callback:
                callback(False, "Authentication required")
            return

        def on_cards_fetched(cards):
            if not cards:
                if callback:
                    callback(False, "No cards to send or failed to fetch cards")
                return

            def send_to_server():
                try:
                    from aqt.utils import tooltip
                    tooltip("Sending cards to server...", period=2000)

                    if not self.connect_to_server():
                        if callback:
                            callback(False, "Failed to connect to server")
                        return

                    self.sock.sendall(str(0).encode("utf-8"))

                    username = self.auth_manager.get_username()
                    self.send_size_and_package(username)

                    deck_code = get_code_from_deck(deck_name)
                    self.send_size_and_package(deck_code)

                    self.send_size_and_package(deck_name)

                    json_data = json.dumps(cards)
                    self.sock.sendall(json_data.encode("utf-8"))
                    self.sock.shutdown(socket.SHUT_WR)

                    response = self.sock.recv(1).decode("utf-8")
                    if response == "1":
                        print("Cards sent and stored successfully.")
                        tooltip("✅ Cards sent successfully!", period=3000)
                        if callback:
                            callback(True, "Cards sent successfully")
                    else:
                        print(f"Error: Server returned '{response}'")
                        if callback:
                            callback(False, f"Server error: {response}")

                except Exception as e:
                    error_msg = f"Error sending cards: {str(e)}"
                    log_error(error_msg)
                    if callback:
                        callback(False, error_msg)
                finally:
                    if self.sock:
                        try:
                            self.sock.close()
                        except:
                            pass
                    self.sock = None

            cards_needing_uid = []

            for card in cards:
                if not card.get("stable_uid"):
                    import uuid
                    new_uid = str(uuid.uuid4())
                    card["stable_uid"] = new_uid
                    cards_needing_uid.append((card["note_id"], new_uid))

            if cards_needing_uid:
                from aqt.utils import tooltip

                print(f"Adding tags to {len(cards_needing_uid)} cards...")
                tooltip(f"🏷️ Adding tags to {len(cards_needing_uid)} cards...", period=3000)

                tags_updated = 0
                total_to_update = len(cards_needing_uid)
                batch_size = 10
                current_batch = 0
                total_batches = (total_to_update + batch_size - 1) // batch_size

                def process_next_batch():
                    nonlocal current_batch

                    start_idx = current_batch * batch_size
                    end_idx = min((current_batch + 1) * batch_size, total_to_update)

                    if start_idx >= total_to_update:
                        send_to_server()
                        return

                    batch = cards_needing_uid[start_idx:end_idx]
                    progress_msg = f"📦 Processing batch {current_batch + 1}/{total_batches} ({start_idx + 1}-{end_idx} of {total_to_update})"
                    print(progress_msg)
                    tooltip(progress_msg, period=2000)

                    batch_completed = 0

                    def on_tag_updated(result):
                        nonlocal batch_completed, tags_updated, current_batch
                        batch_completed += 1
                        tags_updated += 1

                        if batch_completed >= len(batch):
                            current_batch += 1
                            remaining_batches = total_batches - current_batch

                            if remaining_batches > 0:
                                tooltip(f"⏳ {remaining_batches} batches remaining...", period=1500)

                            from aqt.qt import QTimer
                            QTimer.singleShot(100, process_next_batch)

                    def on_tag_error(error_msg):
                        nonlocal batch_completed, tags_updated, current_batch
                        print(f"Error adding tag: {error_msg}")
                        batch_completed += 1
                        tags_updated += 1

                        if batch_completed >= len(batch):
                            current_batch += 1
                            remaining_batches = total_batches - current_batch

                            if remaining_batches > 0:
                                tooltip(f"⏳ {remaining_batches} batches remaining...", period=1500)

                            from aqt.qt import QTimer
                            QTimer.singleShot(100, process_next_batch)

                    for note_id, uid in batch:
                        tag = f"sync_uid:{uid}"
                        anki_connect_request("addTags", on_tag_updated, on_tag_error,
                                             notes=[note_id], tags=tag)

                process_next_batch()
            else:
                send_to_server()

        print("Fetching cards...")
        get_cards_from_deck(deck_name, on_cards_fetched)

    def receive_cards(self, deck_name, callback=None):
        """Receive cards from server (async)"""
        if not self.ensure_authenticated(mw):
            if callback:
                callback(False, "Authentication required")
            return

        try:
            from aqt.utils import tooltip
            tooltip("📥 Connecting to server...", period=2000)

            if not self.connect_to_server():
                tooltip("❌ Failed to connect", period=3000)
                if callback:
                    callback(False, "Failed to connect to server")
                return

            tooltip("🔄 Requesting cards from server...", period=2000)

            self.sock.sendall(str(1).encode("utf-8"))

            username = self.auth_manager.get_username()
            self.send_size_and_package(username)

            deck_code = get_code_from_deck(deck_name)
            self.send_size_and_package(deck_code)

            timestamp = get_value_from_json(SYNC_FILE_PATH, deck_name)
            self.send_size_and_package(timestamp)

            response = self.sock.recv(1).decode("utf-8")
            if response != "1":
                tooltip("❌ Access denied", period=3000)
                if callback:
                    callback(False, "Access denied or server error")
                return

            tooltip("📦 Downloading card data...", period=3000)
            print("Starting to collect cards from server...")

            try:
                cards = collect_cards(self.sock)
            except Exception as e:
                tooltip(f"❌ Download error: {str(e)}", period=4000)
                print(f"Error collecting cards: {e}")
                if callback:
                    callback(False, f"Error downloading cards: {str(e)}")
                return

            if not cards:
                tooltip("ℹ️ No new cards to sync", period=3000)
                if callback:
                    callback(False, "No cards received from server")
                return

            total_cards = len(cards)
            print(f"Successfully downloaded {total_cards} cards")
            tooltip(f"✅ Downloaded {total_cards} cards. Starting sync...", period=3000)

            def on_deck_checked(success):
                if not success:
                    tooltip("❌ Deck check failed", period=3000)
                    if callback:
                        callback(False, "Deck check failed")
                    return

                sync_count = 0

                def on_card_synced(result):
                    nonlocal sync_count
                    sync_count += 1

                    if sync_count >= total_cards:
                        print("All cards collected and synced.")
                        tooltip("🎉 All cards synced successfully!", period=4000)
                        if callback:
                            callback(True, f"Received and synced {sync_count} cards")

                cards_list = list(cards.items())
                batch_size = 5  # Reducir el tamaño del lote
                current_batch = 0
                total_batches = (total_cards + batch_size - 1) // batch_size

                def process_next_batch():
                    nonlocal current_batch

                    start_idx = current_batch * batch_size
                    end_idx = min((current_batch + 1) * batch_size, total_cards)

                    if start_idx >= total_cards:
                        return

                    batch = cards_list[start_idx:end_idx]
                    progress_msg = f"⚡ Syncing batch {current_batch + 1}/{total_batches} ({start_idx + 1}-{end_idx} of {total_cards})"
                    print(progress_msg)
                    tooltip(progress_msg, period=2000)

                    batch_completed = 0

                    def on_batch_card_synced(result):
                        nonlocal batch_completed, current_batch
                        on_card_synced(result)
                        batch_completed += 1

                        if batch_completed >= len(batch):
                            current_batch += 1
                            remaining_batches = total_batches - current_batch

                            if remaining_batches > 0:
                                tooltip(f"⏳ {remaining_batches} batches remaining...", period=1500)
                                from aqt.qt import QTimer
                                QTimer.singleShot(200, process_next_batch)  # Pausa más larga

                    for key, value in batch:
                        sync_card(value, on_batch_card_synced)

                tooltip(f"🚀 Starting sync of {total_cards} cards in batches of {batch_size}...", period=3000)
                from aqt.qt import QTimer
                QTimer.singleShot(500, process_next_batch)  # Pausa inicial

            check_for_deck_existence(deck_name, on_deck_checked)

        except Exception as e:
            error_msg = f"Error receiving cards: {str(e)}"
            print(f"Exception in receive_cards: {error_msg}")
            log_error(error_msg)
            tooltip(f"❌ Error: {str(e)}", period=4000)
            if callback:
                callback(False, error_msg)
        finally:
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
            self.sock = None

    def receive_deck_from_code(self, deck_code, callback=None):
        """Receive a new deck from server using its code (async)"""
        if not self.ensure_authenticated(mw):
            if callback:
                callback(False, "Authentication required")
            return

        def on_deck_checked(exists):
            if exists:
                print("The deck already exists.")
                from aqt.utils import tooltip
                tooltip("⚠️ Deck already exists", period=3000)
                if callback:
                    callback(False, "The deck already exists")
                return

            try:
                from aqt.utils import tooltip
                tooltip("📥 Connecting to server...", period=2000)

                if not self.connect_to_server():
                    tooltip("❌ Failed to connect", period=3000)
                    if callback:
                        callback(False, "Failed to connect to server")
                    return

                tooltip("🔍 Requesting deck from server...", period=2000)
                self.sock.sendall(str(2).encode("utf-8"))

                username = self.auth_manager.get_username()
                self.send_size_and_package(username)

                self.send_size_and_package(deck_code)

                response = self.sock.recv(1).decode("utf-8")
                if response != "1":
                    tooltip("❌ Access denied or deck not found", period=3000)
                    if callback:
                        callback(False, "Access denied or server error")
                    return

                deck_name_size = self.sock.recv(self.HEADER).decode("utf-8")
                deck_name = self.sock.recv(int(deck_name_size)).decode("utf-8")

                tooltip(f"📦 Downloading deck: {deck_name}...", period=3000)
                print(f"Downloading deck: {deck_name}")

                cards = collect_cards(self.sock)
                if not cards:
                    print(f"No cards in deck with code {deck_code}, creating empty deck")
                    tooltip(f"📁 Creating empty deck: {deck_name}", period=3000)

                    def on_deck_created(result):
                        update_json(DECKS_CODES_PATH, deck_name, deck_code)
                        update_json(SYNC_FILE_PATH, deck_name, int(time.time()))

                        def on_anki_synced(success):
                            tooltip("✅ Empty deck created!", period=3000)
                            if callback:
                                callback(True, f"Empty deck '{deck_name}' created successfully")

                        sync_anki(on_anki_synced)

                    create_deck(deck_name, on_deck_created)
                    return

                total_cards = len(cards)
                print(f"Downloaded {total_cards} cards for deck: {deck_name}")
                tooltip(f"✅ Downloaded {total_cards} cards. Creating deck...", period=3000)

                def on_deck_created(result):
                    sync_count = 0

                    tooltip(f"🚀 Starting import of {total_cards} cards...", period=3000)

                    def on_card_synced(result):
                        nonlocal sync_count
                        sync_count += 1

                        if sync_count >= total_cards:
                            update_json(DECKS_CODES_PATH, deck_name, deck_code)
                            update_json(SYNC_FILE_PATH, deck_name, int(time.time()))

                            def on_anki_synced(success):
                                tooltip("🎉 Deck imported successfully!", period=4000)
                                if callback:
                                    callback(True, f"Deck '{deck_name}' imported with {sync_count} cards")

                            sync_anki(on_anki_synced)

                    cards_list = list(cards.items())
                    batch_size = 20
                    current_batch = 0
                    total_batches = (total_cards + batch_size - 1) // batch_size

                    def process_next_batch():
                        nonlocal current_batch

                        start_idx = current_batch * batch_size
                        end_idx = min((current_batch + 1) * batch_size, total_cards)

                        if start_idx >= total_cards:
                            return

                        batch = cards_list[start_idx:end_idx]
                        progress_msg = f"⚡ Importing batch {current_batch + 1}/{total_batches} ({start_idx + 1}-{end_idx} of {total_cards})"
                        print(progress_msg)
                        tooltip(progress_msg, period=2000)

                        batch_completed = 0

                        def on_batch_card_synced(result):
                            nonlocal batch_completed, current_batch
                            on_card_synced(result)
                            batch_completed += 1

                            if batch_completed >= len(batch):
                                current_batch += 1
                                remaining_batches = total_batches - current_batch

                                if remaining_batches > 0:
                                    tooltip(f"⏳ {remaining_batches} batches remaining...", period=1500)
                                    from aqt.qt import QTimer
                                    QTimer.singleShot(100, process_next_batch)

                        for key, value in batch:
                            sync_card(value, on_batch_card_synced)

                    from aqt.qt import QTimer
                    QTimer.singleShot(500, process_next_batch)

                create_deck(deck_name, on_deck_created)

            except Exception as e:
                error_msg = f"Error receiving deck: {str(e)}"
                log_error(error_msg)
                tooltip(f"❌ Import error: {str(e)}", period=4000)
                if callback:
                    callback(False, error_msg)
            finally:
                if self.sock:
                    try:
                        self.sock.close()
                    except:
                        pass
                self.sock = None

        check_for_deck_in_json(deck_code, on_deck_checked)

    def send_size_and_package(self, info):
        """Send data size followed by data"""
        if not isinstance(info, str):
            info = str(info)

        info_encoded = info.encode("utf-8")
        info_length = str(len(info_encoded)).encode("utf-8")
        info_length += b' ' * (self.HEADER - len(info_length))
        self.sock.sendall(info_length)
        self.sock.sendall(info_encoded)

    def logout(self):
        """Log out the current user"""
        self.auth_manager.logout()
        QMessageBox.information(
            mw,
            "Logged Out",
            "You have been logged out successfully."
        )


def workflow_simulation(client, create, receive, deck_name, new, delete, final_callback=None):
    """Run a workflow of operations with proper callbacks"""

    if not client.ensure_authenticated(mw):
        if final_callback:
            final_callback(False, "Authentication required")
        return

    class WorkflowState:
        def __init__(self):
            self.result_messages = []
            self.operations = []
            self.current_op = 0

        def add_operation(self, op):
            self.operations.append(op)

        def on_operation_complete(self, success, message):
            self.result_messages.append(message)
            self.current_op += 1
            if self.current_op < len(self.operations):
                try:
                    self.operations[self.current_op](self.on_operation_complete)
                except Exception as e:
                    error_msg = f"Error in operation {self.current_op}: {str(e)}"
                    log_error(error_msg)
                    self.result_messages.append(error_msg)

                    if final_callback:
                        final_callback(False, "\n".join(self.result_messages))
            elif final_callback:
                final_callback(True, "\n".join(self.result_messages))

    workflow = WorkflowState()

    if new:
        workflow.add_operation(lambda callback: client.receive_deck_from_code(deck_name, callback))
    else:
        if receive:
            workflow.add_operation(lambda callback: client.receive_cards(deck_name, callback))
        if create:
            workflow.add_operation(lambda callback: client.send_cards(deck_name, callback))

        workflow.add_operation(lambda callback:
                               callback(update_json(SYNC_FILE_PATH, deck_name, int(time.time())),
                                        "Updated sync timestamp"))

        if delete:
            workflow.add_operation(lambda callback: delete_deck_information(deck_name,
                                                                            lambda result: callback(True,
                                                                                                    "Deleted deck information")))
        workflow.add_operation(lambda callback: sync_anki(
            lambda success: callback(success, "AnkiWeb sync complete")))

    if workflow.operations:
        try:
            workflow.operations[0](workflow.on_operation_complete)
        except Exception as e:
            error_msg = f"Error starting workflow: {str(e)}"
            log_error(error_msg)
            if final_callback:
                final_callback(False, error_msg)
    elif final_callback:
        final_callback(True, "No operations to perform")


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
