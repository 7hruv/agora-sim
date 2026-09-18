import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "agora.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create agents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            name TEXT PRIMARY KEY,
            traits TEXT,
            mood TEXT,
            money INTEGER,
            inventory TEXT
        )
    ''')
    
    # Create events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            round INTEGER,
            actor TEXT,
            action TEXT,
            target TEXT,
            dialogue TEXT,
            mood_after TEXT,
            money_after INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Initialize agents if not exists
    cursor.execute("SELECT COUNT(*) FROM agents")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO agents (name, traits, mood, money, inventory) VALUES (?, ?, ?, ?, ?)",
            ("Mira", "proud, greedy, curious", "neutral", 20, "3 fish")
        )
        cursor.execute(
            "INSERT INTO agents (name, traits, mood, money, inventory) VALUES (?, ?, ?, ?, ?)",
            ("Leo", "cautious, friendly, honest", "neutral", 20, "3 bread")
        )
    
    conn.commit()
    conn.close()

def reset_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS agents")
    cursor.execute("DROP TABLE IF EXISTS events")
    conn.commit()
    conn.close()
    init_db()

def get_agents():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents")
    agents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return agents

def get_agent(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents WHERE name = ?", (name,))
    row = cursor.fetchone()
    agent = dict(row) if row else None
    conn.close()
    return agent

def update_agent(name, mood=None, money=None, inventory=None):
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    values = []
    if mood is not None:
        updates.append("mood = ?")
        values.append(mood)
    if money is not None:
        updates.append("money = ?")
        values.append(money)
    if inventory is not None:
        updates.append("inventory = ?")
        values.append(inventory)
    if updates:
        values.append(name)
        cursor.execute(f"UPDATE agents SET {', '.join(updates)} WHERE name = ?", values)
        conn.commit()
    conn.close()

def add_event(round_num, actor, action, target, dialogue, mood_after, money_after):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO events (round, actor, action, target, dialogue, mood_after, money_after)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (round_num, actor, action, target, dialogue, mood_after, money_after)
    )
    conn.commit()
    conn.close()

def get_events(limit=30):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return list(reversed(events))

def get_all_events():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY id ASC")
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return events

def get_current_round():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(round) FROM events")
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

def get_recent_events(agent_name, limit=3):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM events WHERE actor != ? ORDER BY id DESC LIMIT ?",
        (agent_name, limit)
    )
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return list(reversed(events))
