import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.expanduser("~"), "betting.db")


class DB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._init()
        self._миграция()

    def _init(self):
        c = self.conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS teams (
            name TEXT, sport TEXT DEFAULT 'шорт-хоккей',
            scored REAL DEFAULT 4.5, conceded REAL DEFAULT 4.5,
            form TEXT DEFAULT '', elo REAL DEFAULT 1500,
            updated TEXT, PRIMARY KEY (name, sport)
        );
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sport TEXT DEFAULT 'шорт-хоккей',
            team1 TEXT, team2 TEXT, line REAL,
            p1 REAL, px REAL, p2 REAL, total_exp REAL,
            rec TEXT, exact_score TEXT, actual_score TEXT,
            note TEXT, created TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS bank_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL, note TEXT, created TEXT
        );
        CREATE TABLE IF NOT EXISTS strategy_settings (
            name TEXT PRIMARY KEY, enabled INTEGER DEFAULT 1
        );
        """)
        self.conn.commit()

        for k, v in {"bank": "10000", "kelly": "0.25", "edge": "0.12",
                     "theme": "тёмная", "accent": "синий", "night_mode": "0",
                     "onboarding": "0", "sport_default": "шорт-хоккей",
                     "lang": "ru"}.items():
            if self.get_setting(k) is None:
                self.set_setting(k, v)

        # Инициализируем стратегии
        try:
            from strategies import имена_стратегий
            for имя, _ in имена_стратегий():
                self.conn.execute(
                    "INSERT OR IGNORE INTO strategy_settings(name, enabled) VALUES(?, 1)",
                    (имя,))
            self.conn.commit()
        except ImportError:
            pass

    def _миграция(self):
        try:
            self.conn.execute("ALTER TABLE history ADD COLUMN strategies TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        try:
            self.conn.execute("ALTER TABLE history ADD COLUMN divergence REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        self.conn.commit()

    def save_team(self, name, scored, conceded, form="", elo=1500, sport="шорт-хоккей"):
        self.conn.execute(
            "INSERT OR REPLACE INTO teams(name,sport,scored,conceded,form,elo,updated) VALUES(?,?,?,?,?,?,?)",
            (name, sport, scored, conceded, form, elo, datetime.now().isoformat()))
        self.conn.commit()

    def get_team(self, name, sport="шорт-хоккей"):
        r = self.conn.execute(
            "SELECT scored,conceded,form,elo FROM teams WHERE name=? AND sport=?",
            (name, sport)).fetchone()
        return {"scored": r[0], "conceded": r[1], "form": r[2], "elo": r[3]} if r else None

    def all_teams(self, sport=None):
        if sport:
            return self.conn.execute(
                "SELECT name,scored,conceded,form,elo FROM teams WHERE sport=? ORDER BY name",
                (sport,)).fetchall()
        return self.conn.execute(
            "SELECT name,scored,conceded,form,elo,sport FROM teams ORDER BY sport,name").fetchall()

    def delete_team(self, name, sport="шорт-хоккей"):
        self.conn.execute("DELETE FROM teams WHERE name=? AND sport=?", (name, sport))
        self.conn.commit()

    def update_elo(self, name, new_elo, sport="шорт-хоккей"):
        self.conn.execute("UPDATE teams SET elo=? WHERE name=? AND sport=?",
                          (new_elo, name, sport))
        self.conn.commit()

    def save_prediction(self, sport, t1, t2, line, r, rec, note="",
                        strategies="", divergence=0.0):
        ex = r.get("exact_score", (0, 0))
        cur = self.conn.execute(
            """INSERT INTO history
               (sport,team1,team2,line,p1,px,p2,total_exp,rec,exact_score,
                strategies,divergence,note,created)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (sport, t1, t2, line, r.get("p1", 0), r.get("px", 0), r.get("p2", 0),
             r.get("total_exp", 0), rec, f"{ex[0]}:{ex[1]}" if ex else "",
             strategies, divergence, note, datetime.now().isoformat()))
        self.conn.commit()
        return cur.lastrowid

    def set_actual_score(self, hid, score):
        self.conn.execute("UPDATE history SET actual_score=? WHERE id=?", (score, hid))
        self.conn.commit()

    def history(self, limit=50, sport=None):
        if sport:
            return self.conn.execute(
                """SELECT id,sport,team1,team2,line,rec,exact_score,actual_score,note,created
                   FROM history WHERE sport=? ORDER BY id DESC LIMIT ?""",
                (sport, limit)).fetchall()
        return self.conn.execute(
            """SELECT id,sport,team1,team2,line,rec,exact_score,actual_score,note,created
               FROM history ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()

    def history_for_backtest(self, sport=None):
        if sport:
            return self.conn.execute(
                "SELECT team1,team2,actual_score FROM history WHERE actual_score IS NOT NULL AND sport=?",
                (sport,)).fetchall()
        return self.conn.execute(
            "SELECT team1,team2,actual_score FROM history WHERE actual_score IS NOT NULL").fetchall()

    def history_with_strategies(self):
        try:
            return self.conn.execute(
                """SELECT rec,line,actual_score,strategies,divergence
                   FROM history WHERE actual_score IS NOT NULL""").fetchall()
        except sqlite3.OperationalError:
            return []

    def clear_history(self):
        self.conn.execute("DELETE FROM history")
        self.conn.commit()

    def export_csv(self, path):
        import csv
        rows = self.conn.execute(
            """SELECT sport,team1,team2,line,p1,px,p2,total_exp,rec,exact_score,actual_score,note,created
               FROM history ORDER BY id""").fetchall()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Спорт", "Команда 1", "Команда 2", "Линия", "P1", "PX", "P2",
                        "Ожид. тотал", "Рекомендация", "Прогноз", "Факт", "Заметка", "Дата"])
            w.writerows(rows)
        return path

    def get_setting(self, key, default=None):
        r = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r[0] if r else default

    def set_setting(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",
                          (key, str(value)))
        self.conn.commit()

    def get_strategy_enabled(self, name):
        r = self.conn.execute(
            "SELECT enabled FROM strategy_settings WHERE name=?", (name,)).fetchone()
        return bool(r[0]) if r else True

    def set_strategy_enabled(self, name, enabled):
        self.conn.execute(
            "INSERT OR REPLACE INTO strategy_settings(name, enabled) VALUES(?, ?)",
            (name, 1 if enabled else 0))
        self.conn.commit()

    def all_strategy_settings(self):
        rows = self.conn.execute("SELECT name, enabled FROM strategy_settings").fetchall()
        return {r[0]: bool(r[1]) for r in rows}

    def add_bank(self, amount, note=""):
        self.conn.execute("INSERT INTO bank_history(amount,note,created) VALUES(?,?,?)",
                          (amount, note, datetime.now().isoformat()))
        self.conn.commit()

    def bank_series(self, limit=50):
        return self.conn.execute(
            "SELECT amount,created FROM bank_history ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()[::-1]

    def bank_total(self):
        r = self.conn.execute("SELECT COALESCE(SUM(amount),0) FROM bank_history").fetchone()
        return r[0] or 0


db = DB()