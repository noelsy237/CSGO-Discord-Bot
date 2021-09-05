import sqlite3

def get_db():
    db = sqlite3.connect(
        'csgobot.db',
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    return db

def close_db(db):
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute('DROP TABLE IF EXISTS guilds')
    db.execute('DROP TABLE IF EXISTS players')
    db.execute('CREATE TABLE guilds (id INTEGER PRIMARY KEY AUTOINCREMENT, alert_channel TEXT NOT NULL, add_date TEXT NOT NULL)')
    db.execute('''CREATE TABLE players (id INTEGER PRIMARY KEY AUTOINCREMENT, steam_id INT NOT NULL, author TEXT NOT NULL, 
        add_date TEXT NOT NULL, banned BOOL NOT NULL, guild_id INT NOT NULL,
        FOREIGN KEY (guild_id) REFERENCES guilds (id))''')
    db.close()