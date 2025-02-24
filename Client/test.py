import hashlib
import sqlite3
import random
import time

def get_cards_from_deck(db_path, deck_name):
    """Retrieves all cards from a specified deck in an Anki database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM decks")
    decks = cursor.fetchall()

    deck_id = None
    for d_id, d_name in decks:
        if d_name == deck_name:
            deck_id = d_id
            break

    if not deck_id:
        print(f"Deck '{deck_name}' not found.")
        return []

    cursor.execute("""
        SELECT cards.id, notes.id, notes.flds, notes.tags, cards.ivl, cards.mod
        FROM cards
        JOIN notes ON cards.nid = notes.id
        WHERE cards.did = ?
    """, (deck_id,))

    cards = cursor.fetchall()
    conn.close()


    card_list = []
    for card_id, note_id, flds, tags, interval, mod_time in cards:
        fields = flds.split("\x1f")

        card_data = {
            "card_id": card_id,
            "note_id": note_id,
            "deck_id": deck_id,
            "question": fields[0],
            "answer": fields[1] if len(fields) > 1 else "",
            "tags": tags,
            "created_at": card_id,
            "last_modified": mod_time,
            "interval": interval
        }
        card_list.append(card_data)

    return card_list

def sync_card(db_path, card_data):
    """Syncs a single card (insert/update) into an Anki database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    card_id = card_data["card_id"]
    note_id = card_data["note_id"]
    deck_id = card_data["deck_id"]
    question = card_data["question"]
    answer = card_data["answer"]
    tags = card_data["tags"]
    created_at = card_data["created_at"]
    mod_time = int(time.time())

    guid = str(note_id)
    sfld = question
    csum = int(hashlib.sha1(sfld.encode()).hexdigest()[:8], 16)
    flags = 0
    data = ""

    cursor.execute("SELECT id FROM cards WHERE id = ?", (card_id,))
    existing_card = cursor.fetchone()

    if existing_card:
        cursor.execute("UPDATE notes SET flds = ?, sfld = ?, csum = ?, tags = ?, mod = ?, usn = -1 WHERE id = ?",
                       (f"{question}\x1f{answer}", sfld, csum, tags, mod_time, note_id))
        cursor.execute("UPDATE cards SET mod = ?, usn = -1 WHERE id = ?",
                       (mod_time, card_id))
        print(f"Updated card {card_id}")
    else:
        cursor.execute("INSERT INTO notes (id, guid, mid, flds, sfld, csum, tags, mod, usn, flags, data) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, -1, ?, ?)",
                       (note_id, guid, 1, f"{question}\x1f{answer}", sfld, csum, tags, mod_time, flags, data))

        cursor.execute("INSERT INTO cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data) "
                       "VALUES (?, ?, ?, ?, ?, -1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (card_id, note_id, deck_id, 0, mod_time, 0, 0, 0, 0, 2500, 0, 0, 0, 0, 0, 0, ""))

        print(f"Inserted new card {card_id}")

    conn.commit()
    conn.close()

def generate_random_card():
    """Generates a random test card with unique IDs and timestamps."""
    timestamp = int(time.time())
    random_id = random.randint(10 ** 12, 10 ** 13 - 1)

    card = {
        "card_id": random_id + 1,
        "note_id": random_id,
        "deck_id": 1740419417506,
        "question": 'Test Question ' + str(random.randint(1, 100)),
        "answer": 'Test Answer ' + str(random.randint(1, 100)),
        "tags": 'test',
        "created_at": timestamp,
        "last_modified": timestamp,
        "interval": 1
    }

    return card


def print_cards_simple(card_list):
    if not card_list:
        print("No se encontraron tarjetas.")
        return

    print(f"Se encontraron {len(card_list)} tarjetas:")
    print("-" * 80)

    for i, card in enumerate(card_list, 1):
        print(f"Tarjeta #{i}")
        print(f"ID: {card['card_id']}")
        print(f"Pregunta: {card['question']}")
        print(f"Respuesta: {card['answer']}")
        print(f"Etiquetas: {card['tags']}")
        print(f"Intervalo: {card['interval']} días")

        # Convertir timestamp a fecha legible
        from datetime import datetime
        modified_date = datetime.fromtimestamp(card['last_modified']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Última modificación: {modified_date}")
        print("-" * 80)


if __name__ == "__main__":
    source_db = "PathToOriginDB"
    target_db = "PathToTargetDB"
    deck_name = "TestDeck"

    print(f"Fetching cards from '{deck_name}'...")
    cards = get_cards_from_deck(source_db, deck_name)

    print(cards)
    print_cards_simple(cards)


    print(f"Syncing {len(cards)} cards to '{target_db}'...")
    sync_card(target_db, generate_random_card())

    print("Sync complete!")
