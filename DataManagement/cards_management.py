import json


def collect_cards(soc):
    try:
        data_chunks = []
        while True:
            chunk = soc.recv(4096)
            if not chunk:
                break
            data_chunks.append(chunk)

        if not data_chunks:
            print("No data received")
            return

        decoded_data = b''.join(data_chunks).decode("utf-8")
        cards = json.loads(decoded_data)
        print(f"Received {len(cards)} cards")

        return cards

    except Exception as e:
        print(f"Error: {e}")