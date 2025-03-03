import socket
import json

from DataManagement.cards_management import collect_cards
from testAnkiConnected import get_cards_from_deck
from testAnkiConnected import sync_card


class Client:
    HEADER = 64

    def __init__(self, host="localhost", port=9999):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        print("Connected to server.")

    def send_cards(self, deck_name):
        print("Fetching cards...")
        cards = get_cards_from_deck(deck_name, 0)
        try:
            self.sock.sendall(str(0).encode("utf-8"))
            self.send_size_and_package(deck_name)
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

    def receive_cards(self, deck_name, timestamp):
        try:
            self.sock.sendall(str(1).encode("utf-8"))
            self.send_size_and_package(deck_name)
            self.send_size_and_package(timestamp)
            self.sock.shutdown(socket.SHUT_WR)

            cards = collect_cards(self.sock)
            for key, value in cards.items():
                sync_card(value)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.sock.close()


    def send_size_and_package(self, info):
        if not isinstance(info, str):
            info = str(info)

        info_encoded = info.encode("utf-8")
        info_length = str(len(info_encoded)).encode("utf-8")
        info_length += b' ' * (self.HEADER - len(info_length))
        self.sock.sendall(info_length)
        self.sock.sendall(info_encoded)

# --- main ---
if __name__ == "__main__":
    client = Client()
    client.send_cards("TestDeck")
    # client.receive_cards("TestDeck", str(1740659710367))


