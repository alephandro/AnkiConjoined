import socket
import threading
import json
import os
import sys
import django

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SERVER_DIR, 'WebServer'))
sys.path.append(PROJECT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebServer.settings')
django.setup()

from django.contrib.auth.models import User
from login.models import Deck, UserDeck
from login.views import save_deck_user_privilege, new_deck_local, retrieve_deck_name
from DataManagement.cards_management import *


def check_for_privilege(username, deck_code, privileges):
    try:
        user = User.objects.get(username=username)
        user_deck = UserDeck.objects.get(user=user, deck__deck_code=deck_code)
        return user_deck.privilege in privileges
    except (User.DoesNotExist, UserDeck.DoesNotExist, Deck.DoesNotExist):
        print(f"User {username} not found or doesn't have access to deck {deck_code}")
        return False
    except Exception as e:
        print(f"Error checking privileges: {str(e)}")
        return False


class Server:
    HEADER = 64

    def __init__(self, host="localhost", port=9999):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen()
        self.json_file = ""

        print(f"Server listening on {host}:{port}")

        try:
            while True:
                conn, addr = self.sock.accept()
                print(f"\n\n\nConnected to {addr}")
                threading.Thread(target=self.handle_client, args=(conn,)).start()
        except KeyboardInterrupt:
            print("Closing server")
            self.sock.close()

    def handle_client(self, conn):
        try:
            choice = conn.recv(1).decode("utf-8")
            username_size = conn.recv(self.HEADER).decode("utf-8")
            username = conn.recv(int(username_size)).decode("utf-8")
            deck_code_size = conn.recv(self.HEADER).decode("utf-8")
            deck_code = conn.recv(int(deck_code_size)).decode("utf-8").strip()
            self.json_file = deck_code + ".json"

            match choice:
                case "0":
                    print("User is trying to send their updated/new cards")
                    print("Checking for privilege...")
                    deck_name_size = conn.recv(self.HEADER).decode("utf-8")
                    deck_name = conn.recv(int(deck_name_size)).decode("utf-8")

                    if not os.path.exists(self.json_file):
                        print("Creating new deck...")
                        conn.sendall(str(1).encode("utf-8"))
                        self.add_cards(conn, True)
                        new_deck_local(deck_name, deck_code)
                        save_deck_user_privilege(username, deck_code, "c")

                    elif check_for_privilege(username, deck_code, ["c", "m", "w"]):
                        print("Privilege found, sending ok...")
                        conn.sendall(str(1).encode("utf-8"))
                        self.add_cards(conn, False)


                    else:
                        print("Privilege not found or invalid, sending fail...")
                        conn.sendall(str(0).encode("utf-8"))

                case "1":
                    print("Trying to send the updated/new cards based on the user's timestamp")
                    print("Checking for privilege...")

                    if check_for_privilege(username, deck_code, ["c", "m", "w", "r"]):
                        print("Privilege found, sending ok...")
                        conn.sendall(str(1).encode("utf-8"))
                        timestamp_length = conn.recv(int(self.HEADER)).decode("utf-8")
                        timestamp = conn.recv(int(timestamp_length)).decode("utf-8")
                        cards = self.retrieve_cards_from_json(int(timestamp))
                        conn.send(json.dumps(cards).encode("utf-8"))

                    else:
                        print("Privilege not found, sending fail...")
                        conn.sendall(str(0).encode("utf-8"))

                case "2":
                    print("Trying to send new deck to the user")
                    print("Checking for privilege...")

                    if check_for_privilege(username, deck_code, ["c", "m", "w", "r"]):
                        print("Privilege found, sending ok...")
                        conn.sendall(str(1).encode("utf-8"))
                        deck_name = retrieve_deck_name(deck_code)
                        self.send_size_and_package_server(conn, deck_name)
                        cards = self.retrieve_cards_from_json(0)
                        conn.send(json.dumps(cards).encode("utf-8"))

                    else:
                        print("Privilege not found, sending fail...")
                        conn.sendall(str(0).encode("utf-8"))

                case _:
                    print("Invalid choice")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()

    def add_cards(self, conn, new):
        try:
            cards = collect_cards(conn)
            if new:
                self.create_deck(cards)
            else:
                self.save_cards_to_json(cards)
            print("Sending success response (1)")
            conn.sendall(str(1).encode("utf-8"))

        except Exception as e:
            print(f"Error: {e}")
            print("Sending error response (0)")
            conn.sendall(str(0).encode("utf-8"))

    def save_cards_to_json(self, new_cards):
        """Save cards to JSON file, merging with existing data if the file exists."""
        all_cards = {}

        try:
            with open(self.json_file, "r") as infile:
                existing_data = json.load(infile)

                if isinstance(existing_data, list):
                    for card in existing_data:
                        if "stable_uid" in card:
                            all_cards[str(card["stable_uid"])] = card

                elif isinstance(existing_data, dict):
                    all_cards = existing_data

            print(f"Loaded {len(all_cards)} existing cards from {self.json_file}")
        except json.JSONDecodeError:
            print(f"Error reading {self.json_file}, will create a new file")

        updated_count = 0
        new_count = 0

        for card in new_cards:
            if not card.get("stable_uid"):
                card["stable_uid"] = generate_stable_uid()
                all_cards[card["stable_uid"]] = card
                new_count += 1
            elif str(card["stable_uid"]) in all_cards:
                if card.get("last_modified", 0) > all_cards[str(card["stable_uid"])].get("last_modified", 0):
                    all_cards[str(card["stable_uid"])] = card
                    updated_count += 1
            else:
                all_cards[str(card["stable_uid"])] = card
                new_count += 1

        with open(self.json_file, "w") as outfile:
            json.dump(all_cards, outfile, indent=4)

        print(f"JSON updated: {new_count} new cards, {updated_count} cards updated")

    def create_deck(self, new_cards):
        all_cards = {}

        for card in new_cards:
            all_cards[str(card["stable_uid"])] = card

        with open(self.json_file, "w") as outfile:
            json.dump(all_cards, outfile, indent=4)

        print(f"JSON created: {len(new_cards)} new cards")

    def retrieve_cards_from_json(self, timestamp):
        """Retrieve the newer/updated cards from JSON file based on the timestamp introduced as parameter."""
        cards = {}
        try:
            with open(self.json_file, "r") as infile:
                cards = json.load(infile)
            print(f"Loaded {len(cards)} existing cards from {self.json_file}")
        except json.JSONDecodeError:
            print(f"Error reading {self.json_file}, will create a new file")

        return {k: v for k, v in cards.items() if v["last_modified"] > timestamp}

    def send_size_and_package_server(self, conn, info):
        """Send data size followed by data"""
        if not isinstance(info, str):
            info = str(info)

        info_encoded = info.encode("utf-8")
        info_length = str(len(info_encoded)).encode("utf-8")
        info_length += b' ' * (self.HEADER - len(info_length))
        conn.sendall(info_length)
        conn.sendall(info_encoded)



# --- main ---
if __name__ == "__main__":
    server = Server()