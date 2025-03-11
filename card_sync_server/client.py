import socket
import json
import time
import os

ADDON_DIR = os.path.dirname(__file__)
SYNC_FILE_PATH = os.path.join(ADDON_DIR, "sync_log.json")
DECKS_CODES_PATH = os.path.join(ADDON_DIR, "decks_codes.json")

from .testAnkiConnected import (
    get_cards_from_deck, sync_card, update_json,
    get_value_from_json, sync_anki, check_for_deck_existence,
    get_code_from_deck, create_deck, check_for_deck_in_json,
    delete_deck_information, log_error
)

from .DataManagement.cards_management import collect_cards


class Client:
    HEADER = 64
    HOST = "127.0.0.1"
    PORT = 9999

    def __init__(self):
        self.sock = None

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.HOST, self.PORT))
            print("Connected to server.")
            return True
        except Exception as e:
            log_error(f"Server connection failed: {str(e)}")
            return False

    def send_cards(self, deck_name, callback=None):
        """Send cards to server (async)"""

        def on_cards_fetched(cards):
            if not cards:
                if callback:
                    callback(False, "No cards to send or failed to fetch cards")
                return

            try:
                if not self.connect_to_server():
                    if callback:
                        callback(False, "Failed to connect to server")
                    return

                self.sock.sendall(str(0).encode("utf-8"))
                deck_code = get_code_from_deck(deck_name)
                self.send_size_and_package(deck_code)
                json_data = json.dumps(cards)
                self.sock.sendall(json_data.encode("utf-8"))
                self.sock.shutdown(socket.SHUT_WR)

                response = self.sock.recv(1).decode("utf-8")
                if response == "1":
                    print("Cards sent and stored successfully.")
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

        print("Fetching cards...")
        get_cards_from_deck(deck_name, on_cards_fetched)

    def receive_cards(self, deck_name, callback=None):
        """Receive cards from server (async)"""
        try:
            if not self.connect_to_server():
                if callback:
                    callback(False, "Failed to connect to server")
                return

            timestamp = get_value_from_json(SYNC_FILE_PATH, deck_name)
            self.sock.sendall(str(1).encode("utf-8"))
            deck_code = get_code_from_deck(deck_name)
            self.send_size_and_package(deck_code)
            self.send_size_and_package(timestamp)
            self.sock.shutdown(socket.SHUT_WR)

            cards = collect_cards(self.sock)
            if not cards:
                if callback:
                    callback(False, "No cards received from server")
                return

            def on_deck_checked(success):
                sync_count = 0
                total_cards = len(cards)

                def on_card_synced(result):
                    nonlocal sync_count
                    sync_count += 1

                    if sync_count >= total_cards:
                        print("All cards collected and synced.")
                        if callback:
                            callback(True, f"Received and synced {sync_count} cards")

                for key, value in cards.items():
                    sync_card(value, on_card_synced)

            check_for_deck_existence(deck_name, on_deck_checked)

        except Exception as e:
            error_msg = f"Error receiving cards: {str(e)}"
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

    def receive_deck_from_code(self, deck_code, callback=None):
        """Receive a new deck from server using its code (async)"""

        def on_deck_checked(exists):
            if exists:
                print("The deck already exists.")
                if callback:
                    callback(False, "The deck already exists")
                return

            try:
                if not self.connect_to_server():
                    if callback:
                        callback(False, "Failed to connect to server")
                    return

                self.sock.sendall(str(2).encode("utf-8"))
                self.send_size_and_package(deck_code)
                self.sock.shutdown(socket.SHUT_WR)

                cards = collect_cards(self.sock)
                if not cards:
                    print(f"There is no deck with code {deck_code}")
                    if callback:
                        callback(False, f"No deck found with code {deck_code}")
                    return

                first_key = next(iter(cards))
                deck_name = cards[first_key]["deck_name"]

                def on_deck_created(result):
                    sync_count = 0
                    total_cards = len(cards)

                    def on_card_synced(result):
                        nonlocal sync_count
                        sync_count += 1

                        if sync_count >= total_cards:
                            # Update config files and sync with AnkiWeb
                            update_json(DECKS_CODES_PATH, deck_name, deck_code)
                            update_json(SYNC_FILE_PATH, deck_name, int(time.time()))

                            def on_anki_synced(success):
                                if callback:
                                    callback(True, f"Deck '{deck_name}' imported with {sync_count} cards")

                            sync_anki(on_anki_synced)

                    for key, value in cards.items():
                        sync_card(value, on_card_synced)

                create_deck(deck_name, on_deck_created)

            except Exception as e:
                error_msg = f"Error receiving deck: {str(e)}"
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


def workflow_simulation(client, create, receive, deck_name, new, delete, final_callback=None):
    """Run a workflow of operations with proper callbacks"""

    # THIS IS THE FIX FOR RECURSION ISSUES
    # We'll use a class to track state instead of recursion
    class WorkflowState:
        def __init__(self):
            self.result_messages = []
            self.operations = []
            self.current_op = 0

        def add_operation(self, op):
            self.operations.append(op)

        def on_operation_complete(self, success, message):
            self.result_messages.append(message)

            # IMPORTANT: Only proceed to next operation if we're still within bounds
            self.current_op += 1
            if self.current_op < len(self.operations):
                # Execute next operation
                try:
                    self.operations[self.current_op](self.on_operation_complete)
                except Exception as e:
                    error_msg = f"Error in operation {self.current_op}: {str(e)}"
                    log_error(error_msg)
                    self.result_messages.append(error_msg)

                    # Skip to final callback with error
                    if final_callback:
                        final_callback(False, "\n".join(self.result_messages))
            elif final_callback:
                final_callback(True, "\n".join(self.result_messages))

    # Initialize workflow state
    workflow = WorkflowState()

    # Define operations based on parameters
    if new:
        workflow.add_operation(lambda callback: client.receive_deck_from_code(deck_name, callback))
    else:
        if receive:
            workflow.add_operation(lambda callback: client.receive_cards(deck_name, callback))
        if create:
            workflow.add_operation(lambda callback: client.send_cards(deck_name, callback))

        # Update sync timestamp
        workflow.add_operation(lambda callback:
                               callback(update_json(SYNC_FILE_PATH, deck_name, int(time.time())),
                                        "Updated sync timestamp"))

        if delete:
            workflow.add_operation(lambda callback: delete_deck_information(deck_name,
                                                                            lambda result: callback(True,
                                                                                                    "Deleted deck information")))

        # Final AnkiWeb sync
        workflow.add_operation(lambda callback: sync_anki(
            lambda success: callback(success, "AnkiWeb sync complete")))

    # Start the workflow if we have operations
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