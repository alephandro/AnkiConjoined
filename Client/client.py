import socket
import json
from testAnkiConnected import get_cards_from_deck

class Client:
    def __init__(self, host="localhost", port=9999):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        print("Connected to server.")

    def send_cards(self):
        print("Fetching cards...")
        cards = get_cards_from_deck("TestDeck", 0)

        json_data = json.dumps(cards)
        self.sock.sendall(json_data.encode("utf-8"))

        print("Cards sent successfully.")
        self.sock.close()

# --- main ---
client = Client()
client.send_cards()
