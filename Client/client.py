import socket
import json
import time

from DataManagement.cards_management import collect_cards
from testAnkiConnected import (SYNC_FILE_PATH, DECKS_CODES_PATH, get_cards_from_deck, sync_card, update_json,
                               get_value_from_json, sync_anki, check_for_deck_existence,
                               get_code_from_deck, create_deck, check_for_deck_in_json)


class Client:
    HEADER = 64
    HOST = "127.0.0.1"
    PORT = 9999


    def __init__(self):
        self.sock = None


    def connect_to_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.HOST, self.PORT))
        print("Connected to server.")


    def send_cards(self, deck_name):
        print("Fetching cards...")
        cards = get_cards_from_deck(deck_name)
        try:
            self.connect_to_server()
            self.sock.sendall(str(0).encode("utf-8"))
            deck_code = get_code_from_deck(deck_name)
            self.send_size_and_package(deck_code)
            json_data = json.dumps(cards)
            self.sock.sendall(json_data.encode("utf-8"))
            self.sock.shutdown(socket.SHUT_WR)

            response = self.sock.recv(1).decode("utf-8")
            if response == "1":
                print("Cards sent and stored successfully.")
            else:
                print(f"Error: Server returned '{response}'")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.sock.close()


    def receive_cards(self, deck_name):
        try:
            self.connect_to_server()
            timestamp = get_value_from_json(SYNC_FILE_PATH, deck_name)
            self.sock.sendall(str(1).encode("utf-8"))
            deck_code = get_code_from_deck(deck_name)
            self.send_size_and_package(deck_code)
            self.send_size_and_package(timestamp)
            self.sock.shutdown(socket.SHUT_WR)

            cards = collect_cards(self.sock)
            check_for_deck_existence(deck_name)

            for key, value in cards.items():
                sync_card(value)

            print("Cards collected.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.sock.close()


    def receive_deck_from_code(self, deck_code):
        if check_for_deck_in_json(deck_code):
            print("The deck already exists.")
            return
        try:
            self.connect_to_server()
            self.sock.sendall(str(2).encode("utf-8"))
            self.send_size_and_package(deck_code)
            self.sock.shutdown(socket.SHUT_WR)

            cards = collect_cards(self.sock)
            if cards is None:
                print(f"There is no deck with code {deck_code}")
                return
            first_key = next(iter(cards))
            deck_name = cards[first_key]["deck_name"]
            create_deck(deck_name)

            for key, value in cards.items():
                sync_card(value)

            update_json(DECKS_CODES_PATH, deck_name, deck_code)
            update_json(SYNC_FILE_PATH, deck_name, int(time.time()))
            sync_anki()

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.sock.close()



    '''def sync_cards_parallel(self, cards):
        if not cards:
            print("No cards to sync.")
            return 0, 0

        max_workers = min(10, len(cards))
        print(f"Syncing {len(cards)} cards with {max_workers} parallel workers...")

        completed = 0
        successes = 0
        failures = 0
        total = len(cards)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_card = {executor.submit(sync_card, value): key for key, value in cards.items()}

            for future in concurrent.futures.as_completed(future_to_card):
                card_key = future_to_card[future]
                try:
                    result = future.result()
                    if isinstance(result, dict) and result.get("error"):
                        failures += 1
                        print(f"\nCard {card_key} error: {result['error']}")
                    else:
                        successes += 1
                except Exception as exc:
                    failures += 1
                    print(f"\nCard {card_key} exception: {exc}")
                finally:
                    completed += 1
                    progress = completed / total * 100
                    sys.stdout.write(f"\rProgress: {progress:.1f}% ({completed}/{total})")
                    sys.stdout.flush()

        print(f"\nSync completed: {successes} cards synced successfully, {failures} failures")
        return successes, failures'''


    def send_size_and_package(self, info):
        if not isinstance(info, str):
            info = str(info)

        info_encoded = info.encode("utf-8")
        info_length = str(len(info_encoded)).encode("utf-8")
        info_length += b' ' * (self.HEADER - len(info_length))
        self.sock.sendall(info_length)
        self.sock.sendall(info_encoded)


def workflow_simulation(client, create, receive, deck_name, new):
    if new:
        client.receive_deck_from_code(deck_name)
        return
    if receive:
        client.receive_cards(deck_name)
    if create:
        client.send_cards(deck_name)
    update_json(SYNC_FILE_PATH, deck_name, int(time.time()))
    sync_anki()


# --- main ---
if __name__ == "__main__":
    client = Client()
    deck_name = "TestKaishi"
    action = "receive"

    match action:
        case "create":
            workflow_simulation(client, True, False, deck_name, False)
        case "receive":
            workflow_simulation(client, False, True, deck_name, False)
        case "update":
            workflow_simulation(client, True, True, deck_name, False)
        case "new_deck":
            workflow_simulation(client, True, False,
                                "brave+initiated+messaging+edition+tune",True)



