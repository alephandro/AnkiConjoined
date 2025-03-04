import socket
import threading
import json
import os

from DataManagement.cards_management import collect_cards


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
                print(f"Connected to {addr}")
                threading.Thread(target=self.handle_client, args=(conn,)).start()
        except KeyboardInterrupt:
            print("Closing server")
            self.sock.close()

    def handle_client(self, conn):
        try:
            choice = conn.recv(1).decode("utf-8")
            deck_name_size = conn.recv(self.HEADER).decode("utf-8")
            deck_name = conn.recv(int(deck_name_size)).decode("utf-8")
            self.json_file = deck_name + ".json"
            match choice:
                case "0":
                    print("User is sending their updated/new cards")
                    self.add_cards(conn)
                case "1":
                    print("Sending the updated/new cards based on the user's timestamp")
                    timestamp_length = conn.recv(int(self.HEADER)).decode("utf-8")
                    timestamp = conn.recv(int(timestamp_length)).decode("utf-8")
                    cards = self.retrieve_cards_from_json(int(timestamp))
                    conn.send(json.dumps(cards).encode("utf-8"))
                case _:
                    print("Invalid choice")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()

    def add_cards(self, conn):
        try:
            cards = collect_cards(conn)
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

        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r") as infile:
                    existing_data = json.load(infile)

                    if isinstance(existing_data, list):
                        for card in existing_data:
                            if "note_id" in card:
                                all_cards[str(card["note_id"])] = card

                    elif isinstance(existing_data, dict):
                        all_cards = existing_data

                print(f"Loaded {len(all_cards)} existing cards from {self.json_file}")
            except json.JSONDecodeError:
                print(f"Error reading {self.json_file}, will create a new file")

        updated_count = 0
        new_count = 0

        for card in new_cards:
            if str(card["note_id"]) in all_cards:
                if card.get("last_modified", 0) > all_cards[str(card["note_id"])].get("last_modified", 0):
                    all_cards[str(card["note_id"])] = card
                    updated_count += 1
            else:
                all_cards[str(card["note_id"])] = card
                new_count += 1

        with open(self.json_file, "w") as outfile:
            json.dump(all_cards, outfile, indent=4)

        print(f"JSON updated: {new_count} new cards, {updated_count} cards updated")

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

# --- main ---
if __name__ == "__main__":
    server = Server()