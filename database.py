# database.py
import sqlite3
import os
from datetime import datetime

# Percorso assoluto del database (compatibile con PythonAnywhere)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'duvri.db')

def get_db_path():
    """Restituisce il percorso assoluto del database"""
    return DB_PATH

def init_db():
    """Inizializza il database SQLite"""
    conn = sqlite3.connect(DB_PATH)
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
    print(f"✅ Database inizializzato: {DB_PATH}")

# Chiama all'avvio
init_db()