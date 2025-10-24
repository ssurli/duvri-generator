# database.py
import sqlite3
import os
from datetime import datetime

def init_db():
    conn = sqlite3.connect('duvri.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS duvri (
            id TEXT PRIMARY KEY,
            nome_progetto TEXT,
            committente_data TEXT,
            appaltatore_data TEXT,
            signatures TEXT,
            stato TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Chiama all'avvio
init_db()