import socket

class Client:

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

        print("Connected", self)

# --- main ---

Client("localhost", 9999)