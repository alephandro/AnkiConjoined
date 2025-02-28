import socket
import threading


class Server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("localhost", 9999))
        self.sock.listen(1)

        while True:
            try:
                print("Waiting for connection...")
                conn, addr = self.sock.accept()
                print("Connected to", addr)
                threading.Thread(self.handle_client()).start()
            except Exception as e:
                print(e)
            finally:
                if socket:
                    socket.close()



    def handle_client(connection):
        print("Connected", connection)

# --- main ---

Server()

