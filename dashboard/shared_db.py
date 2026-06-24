import sqlite3
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class DashboardDB:
    def __init__(self, db_path="bot_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Bot Status
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_status (
                    id INTEGER PRIMARY KEY,
                    status TEXT,
                    last_update TEXT,
                    start_time TEXT,
                    balance TEXT,
                    positions TEXT
                )
            ''')
            
            # Trade History
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    side TEXT,
                    price REAL,
                    amount REAL,
                    pnl REAL
                )
            ''')
            
            # Settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Trading Pairs (Symbols)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS symbols (
                    symbol TEXT PRIMARY KEY,
                    active INTEGER DEFAULT 1
                )
            ''')
            
            # Commands (e.g., stop, pause, resume)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT,
                    timestamp TEXT,
                    processed INTEGER DEFAULT 0
                )
            ''')
            
            # Update schema if start_time is missing (for existing databases)
            try:
                cursor.execute("ALTER TABLE bot_status ADD COLUMN start_time TEXT")
            except sqlite3.OperationalError:
                pass # already exists
                
            # Initial Status if empty
            cursor.execute("SELECT COUNT(*) FROM bot_status")
            if cursor.fetchone()[0] == 0:
                now = datetime.now().isoformat()
                cursor.execute("INSERT INTO bot_status (id, status, last_update, start_time) VALUES (1, 'RUNNING', ?, ?)", (now, now))
            
            conn.commit()

    def update_status(self, status=None, balance=None, positions=None, start_time=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            if status:
                cursor.execute("UPDATE bot_status SET status = ?, last_update = ? WHERE id = 1", (status, now))
            if balance is not None:
                cursor.execute("UPDATE bot_status SET balance = ?, last_update = ? WHERE id = 1", (json.dumps(balance), now))
            if positions is not None:
                cursor.execute("UPDATE bot_status SET positions = ?, last_update = ? WHERE id = 1", (json.dumps(positions), now))
            if start_time:
                cursor.execute("UPDATE bot_status SET start_time = ?, last_update = ? WHERE id = 1", (start_time, now))
            conn.commit()

    def get_logs(self, log_path="bot.log", lines=20):
        if not os.path.exists(log_path):
            return ["Log file not found."]
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                # Read last lines efficiently
                content = f.readlines()
                return [line.strip() for line in content[-lines:]]
        except Exception as e:
            return [f"Error reading logs: {str(e)}"]

    def get_status(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bot_status WHERE id = 1")
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res['balance'] = json.loads(res['balance']) if res['balance'] else {}
                res['positions'] = json.loads(res['positions']) if res['positions'] else []
                return res
            return {}

    def log_trade(self, symbol, side, price, amount, pnl=0.0):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO trades (timestamp, symbol, side, price, amount, pnl) VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), symbol, side, price, amount, pnl)
            )
            conn.commit()

    def get_trades(self, limit=50):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def send_command(self, command):
        with sqlite3.connect(self.db_path) as conn:
            if command in ['pause', 'resume']:
                status = 'PAUSED' if command == 'pause' else 'RUNNING'
                cursor = conn.cursor()
                cursor.execute("UPDATE bot_status SET status = ? WHERE id = 1", (status,))
            
            cursor = conn.cursor()
            cursor.execute("INSERT INTO commands (command, timestamp) VALUES (?, ?)", (command, datetime.now().isoformat()))
            conn.commit()

    def get_latest_command(self, mark_as_processed=True):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, command FROM commands WHERE processed = 0 ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                cmd_id, cmd = row
                if mark_as_processed:
                    cursor.execute("UPDATE commands SET processed = 1 WHERE id = ?", (cmd_id,))
                conn.commit()
                return cmd
            return None

    def get_settings(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def update_setting(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()

    def get_symbols(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT symbol FROM symbols WHERE active = 1")
            return [row[0] for row in cursor.fetchall()]

    def add_symbol(self, symbol):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO symbols (symbol, active) VALUES (?, 1)", (symbol,))
            conn.commit()

    def remove_symbol(self, symbol):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM symbols WHERE symbol = ?", (symbol,))
            conn.commit()
