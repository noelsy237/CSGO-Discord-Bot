import sqlite3

def get_db():
    db = sqlite3.connect(
        'database.db',
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    return db

def close_db(db):
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute('DROP TABLE IF EXISTS players')
    db.execute('CREATE TABLE players (id INTEGER PRIMARY KEY AUTOINCREMENT, steamID INT NOT NULL, author TEXT NOT NULL, addedDate TEXT NOT NULL, banned BOOL NOT NULL)')
    db.close()