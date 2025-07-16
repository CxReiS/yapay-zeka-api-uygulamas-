import sqlite3
from PyQt6.QtCore import QDateTime, Qt
import uuid
import os

class ChatDatabase:
    def __init__(self, db_path="chats.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                sender TEXT,
                message TEXT,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    def create_chat(self, name):
        chat_id = str(uuid.uuid4())
        now = QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
        self.conn.execute("INSERT INTO chats (id, name, created_at) VALUES (?, ?, ?)", (chat_id, name, now))
        self.conn.commit()
        return chat_id

    def save_message(self, chat_id, sender, message):
        timestamp = QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
        self.conn.execute("INSERT INTO messages (chat_id, sender, message, timestamp) VALUES (?, ?, ?, ?)",
                          (chat_id, sender, message, timestamp))
        self.conn.commit()

    def load_chats(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM chats")
        return cursor.fetchall()

    def load_messages(self, chat_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT sender, message, timestamp FROM messages WHERE chat_id=? ORDER BY id", (chat_id,))
        return cursor.fetchall()
