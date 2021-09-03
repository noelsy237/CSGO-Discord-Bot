import sqlite3

db = sqlite3.connect("csgobot.sqlite")
con = db.cursor()
con.execute('DROP TABLE IF EXISTS players')
con.execute('CREATE TABLE players (id INTEGER PRIMARY KEY AUTOINCREMENT, steamID INT NOT NULL, author TEXT NOT NULL, addedDate TEXT NOT NULL, notified BOOL NOT NULL)')
db.close()