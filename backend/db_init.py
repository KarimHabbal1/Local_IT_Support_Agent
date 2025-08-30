import sqlite3

conn = sqlite3.connect('support_agent.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue TEXT NOT NULL,
    status TEXT NOT NULL,
    assigned_to INTEGER,
    logs TEXT,
    FOREIGN KEY (assigned_to) REFERENCES users(id)
)''')
conn.commit()
conn.close()
