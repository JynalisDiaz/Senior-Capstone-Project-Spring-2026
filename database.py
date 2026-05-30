import sqlite3
from datetime import datetime

# Database file will be created in your Web_Tool folder
DATABASE = "database.db"

def get_db():
    # Connect to the database
    conn = sqlite3.connect(DATABASE)
    # This lets us access rows like dictionaries
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Create the database and tables if they dont exist yet
    conn = get_db()
    cursor = conn.cursor()

    # Create the analyses table
    # This stores every submission a user makes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_text TEXT NOT NULL,
            verdict TEXT NOT NULL,
            confidence TEXT NOT NULL,
            flag_count INTEGER NOT NULL,
            flags TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def save_analysis(job_text, verdict, confidence, flags):
    # Save a single analysis to the database
    conn = get_db()
    cursor = conn.cursor()

    # Convert flags list to a readable string for storage
    flag_summary = " | ".join([f["flag"] for f in flags]) if flags else "None"

    cursor.execute('''
        INSERT INTO analyses (job_text, verdict, confidence, flag_count, flags, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        job_text,
        verdict,
        confidence,
        len(flags),
        flag_summary,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

def get_all_analyses():
    # Retrieve all past analyses, most recent first
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM analyses ORDER BY timestamp DESC
    ''')

    rows = cursor.fetchall()
    conn.close()
    return rows

def get_recent_analyses(limit=10):
    # Retrieve only the most recent analyses
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM analyses ORDER BY timestamp DESC LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()
    return rows
