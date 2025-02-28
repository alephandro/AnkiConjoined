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

            '''
            self.save_cards_to_json(cards)
            '''

            ''' 
            Acknowledge for future implementation
            conn.sendall("Cards received and saved successfully".encode("utf-8"))
            '''

        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()



# --- main ---
if __name__ == "__main__":
    Server()