import socket
import threading
import json
import os


class Server:
    def __init__(self, host="localhost", port=9999, json_file="anki_cards.json"):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen()
        self.json_file = json_file

        print(f"Server listening on {host}:{port}")
        print(f"Data will be stored in: {json_file}")

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
            data_chunks = []
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data_chunks.append(chunk)

            if not data_chunks:
                print("No data received")
                return

            decoded_data = b''.join(data_chunks).decode("utf-8")
            cards = json.loads(decoded_data)
            print(f"Received {len(cards)} cards")

            self.save_cards_to_json(cards)


            ''' 
            Acknowledge for future implementation
            conn.sendall("Cards received and saved successfully".encode("utf-8"))
            '''

        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()

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


# --- main ---
if __name__ == "__main__":
    Server()