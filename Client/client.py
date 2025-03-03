import socket
import json

from testAnkiConnected import get_cards_from_deck

class Client:
    HEADER = 64

    def __init__(self, host="localhost", port=9999):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        print("Connected to server.")

    def send_cards(self, deck_name):
        print("Fetching cards...")
        cards = get_cards_from_deck(deck_name, 0)
        '''
        Option to send cards --> code 0
        Send deck name
        Send cards
        '''
        try:
            self.sock.sendall(str(0).encode("utf-8"))

            deck_name_encoded = deck_name.encode("utf-8")
            deck_name_length = str(len(deck_name_encoded)).encode("utf-8")
            deck_name_length += b' ' * (self.HEADER - len(deck_name_length))
            self.sock.sendall(deck_name_length)
            self.sock.sendall(deck_name_encoded)

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

# --- main ---
if __name__ == "__main__":
    client = Client()
    client.send_cards('Kaishi 1.5k')
