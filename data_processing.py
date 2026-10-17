import re
import json
import pandas as pd
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "task1_d.json"
DB_PATH = BASE_DIR / "books.db"

PRICE_RE = re.compile(r'^(\D+)(\d+\.\d+)$')
CURRENCY_MAP = {"$": "USD", "€": "EUR"}

def read_books(path):
    with open(path, 'r', encoding='utf-8') as f:
        s = f.read()

    reg_str = re.sub(r':(\w+)=>', r'"\1":', s)
    data = json.loads(reg_str)
    return data


def parse_price(s):
    m = re.search(PRICE_RE, s)
    if m is None:
        raise ValueError(f"bad price {s!r}")
    signs = m.group(1)
    price = m.group(2)
    if signs not in CURRENCY_MAP:
        raise ValueError(f"unknown currency {signs!r}")
    sign_maped = CURRENCY_MAP[signs]
    return (sign_maped, float(price))

def clean_books(data):
    cleaned = []
    for rec in data:
        try:
            currency, price = parse_price(rec['price'])
        except ValueError as e:
            raise ValueError(f"record {rec['id']}: {e}") from e
        cleaned.append({**rec, "currency": currency, "price": price})
    return cleaned

def load_books(conn, books):
    conn.execute('DROP TABLE IF EXISTS books')
    conn.execute('CREATE TABLE books (' \
    'id TEXT PRIMARY KEY NOT NULL,' \
    'title TEXT,' \
    'author TEXT,' \
    'genre TEXT,' \
    'publisher TEXT,' \
    'year INTEGER,' \
    'price DECIMAL(10,2),' \
    'currency TEXT)')
    books_payload = pd.DataFrame(books)
    books_payload['id'] = books_payload['id'].astype(str)
    books_payload.to_sql("books", conn, if_exists="append", index=False)
    conn.commit()

def build_summary(conn):
    conn.execute("DROP TABLE IF EXISTS summary")
    conn.execute("""
        CREATE TABLE summary AS
        SELECT
            year,
            COUNT(*) as book_count,
            ROUND(AVG(CASE WHEN currency = 'EUR' THEN price * 1.2 ELSE price END), 2) AS average_price
        FROM books
        GROUP BY year
        ORDER BY year
""")
    conn.commit()

def main():
    conn = sqlite3.connect(DB_PATH)
    books = clean_books(read_books(DATA_PATH))

    load_books(conn, books)
    build_summary(conn)

    print("books rows:  ", conn.execute("SELECT COUNT(*) FROM books").fetchone()[0])
    print("summary rows:", conn.execute("SELECT COUNT(*) FROM summary").fetchone()[0])
    print("sum of book_count:", conn.execute("SELECT SUM(book_count) FROM summary").fetchone()[0])
    for row in conn.execute("SELECT * FROM summary"):
        print(row)

    conn.close()


if __name__ == "__main__":
    main()