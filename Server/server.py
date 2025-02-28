import socket
import threading
import json


class Server:
    def __init__(self, host="localhost", port=9999):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen()

        print("Server listening on", (host, port))

        while True:
            try:
                conn, addr = self.sock.accept()
                print("Connected to", addr)
                threading.Thread(target=self.handle_client, args=(conn,)).start()
            except KeyboardInterrupt:
                break
            finally:
                print("Closing server")
                self.sock.close()

    def handle_client(self, conn):
        try:
            data = conn.recv(4096)
            if not data:
                return

            decoded_data = data.decode("utf-8")
            cards = json.loads(decoded_data)

            print("I received", len(cards), "cards")
            print("Received cards:", cards)

        except Exception as e:
            print("Error:", e)
        finally:
            conn.close()


# --- main ---
Server()
