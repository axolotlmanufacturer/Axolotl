"""SQLite-Datenzugriffsschicht fuer den Lokal-SEO Manager."""

import sqlite3
import os
from datetime import datetime

from seo_optimizer.data import CHECKLIST_CATALOG, DIRECTORIES

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firma TEXT NOT NULL,
    gewerk TEXT,
    strasse TEXT,
    plz TEXT,
    ort TEXT,
    bundesland TEXT,
    telefon TEXT,
    email TEXT,
    website TEXT,
    google_profil_url TEXT,
    einzugsgebiet TEXT,
    notizen TEXT,
    erstellt_am TEXT
);

CREATE TABLE IF NOT EXISTS checklist_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    item_key TEXT NOT NULL,
    erledigt INTEGER NOT NULL DEFAULT 0,
    aktualisiert_am TEXT,
    UNIQUE(client_id, item_key),
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS directory_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    dir_key TEXT NOT NULL,
    eingetragen INTEGER NOT NULL DEFAULT 0,
    profil_url TEXT,
    notiz TEXT,
    UNIQUE(client_id, dir_key),
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
);
"""

CLIENT_FIELDS = [
    "firma", "gewerk", "strasse", "plz", "ort", "bundesland",
    "telefon", "email", "website", "google_profil_url",
    "einzugsgebiet", "notizen",
]


class Database:
    """Kapselt alle Datenbankzugriffe des Lokal-SEO Managers."""

    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)) or ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    # -- Kunden -----------------------------------------------------

    def add_client(self, data):
        payload = {field: data.get(field, "") for field in CLIENT_FIELDS}
        payload["erstellt_am"] = datetime.now().isoformat(timespec="seconds")
        columns = ", ".join(payload.keys())
        placeholders = ", ".join(f":{key}" for key in payload.keys())
        cur = self.conn.execute(
            f"INSERT INTO clients ({columns}) VALUES ({placeholders})", payload
        )
        self.conn.commit()
        return cur.lastrowid

    def update_client(self, client_id, data):
        payload = {field: data.get(field, "") for field in CLIENT_FIELDS}
        payload["id"] = client_id
        set_clause = ", ".join(f"{field} = :{field}" for field in CLIENT_FIELDS)
        self.conn.execute(
            f"UPDATE clients SET {set_clause} WHERE id = :id", payload
        )
        self.conn.commit()

    def delete_client(self, client_id):
        self.conn.execute("DELETE FROM checklist_status WHERE client_id = ?", (client_id,))
        self.conn.execute("DELETE FROM directory_status WHERE client_id = ?", (client_id,))
        self.conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        self.conn.commit()

    def get_clients(self):
        rows = self.conn.execute("SELECT * FROM clients ORDER BY firma COLLATE NOCASE").fetchall()
        return [dict(row) for row in rows]

    def get_client(self, client_id):
        row = self.conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return dict(row) if row else None

    # -- Checkliste ---------------------------------------------------

    def get_checklist_status(self, client_id):
        rows = self.conn.execute(
            "SELECT item_key, erledigt FROM checklist_status WHERE client_id = ?",
            (client_id,),
        ).fetchall()
        status = {row["item_key"]: bool(row["erledigt"]) for row in rows}
        for items in CHECKLIST_CATALOG.values():
            for key, _ in items:
                status.setdefault(key, False)
        return status

    def set_checklist_item(self, client_id, item_key, erledigt):
        now = datetime.now().isoformat(timespec="seconds")
        self.conn.execute(
            """
            INSERT INTO checklist_status (client_id, item_key, erledigt, aktualisiert_am)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(client_id, item_key)
            DO UPDATE SET erledigt = excluded.erledigt, aktualisiert_am = excluded.aktualisiert_am
            """,
            (client_id, item_key, int(bool(erledigt)), now),
        )
        self.conn.commit()

    def checklist_progress(self, client_id):
        """Liefert Gesamt- und Kategorie-Fortschritt (0-100) fuer einen Kunden."""
        status = self.get_checklist_status(client_id)
        gesamt_total = 0
        gesamt_done = 0
        kategorien = {}
        for kategorie, items in CHECKLIST_CATALOG.items():
            total = len(items)
            done = sum(1 for key, _ in items if status.get(key))
            kategorien[kategorie] = round((done / total) * 100) if total else 0
            gesamt_total += total
            gesamt_done += done
        gesamt = round((gesamt_done / gesamt_total) * 100) if gesamt_total else 0
        return gesamt, kategorien

    # -- Verzeichnisse (Citations) ------------------------------------

    def get_directory_status(self, client_id):
        rows = self.conn.execute(
            "SELECT dir_key, eingetragen, profil_url, notiz FROM directory_status WHERE client_id = ?",
            (client_id,),
        ).fetchall()
        status = {
            row["dir_key"]: {
                "eingetragen": bool(row["eingetragen"]),
                "profil_url": row["profil_url"] or "",
                "notiz": row["notiz"] or "",
            }
            for row in rows
        }
        for key, _, _ in DIRECTORIES:
            status.setdefault(key, {"eingetragen": False, "profil_url": "", "notiz": ""})
        return status

    def set_directory_item(self, client_id, dir_key, eingetragen, profil_url="", notiz=""):
        self.conn.execute(
            """
            INSERT INTO directory_status (client_id, dir_key, eingetragen, profil_url, notiz)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(client_id, dir_key)
            DO UPDATE SET eingetragen = excluded.eingetragen,
                          profil_url = excluded.profil_url,
                          notiz = excluded.notiz
            """,
            (client_id, dir_key, int(bool(eingetragen)), profil_url, notiz),
        )
        self.conn.commit()

    def directory_progress(self, client_id):
        status = self.get_directory_status(client_id)
        total = len(DIRECTORIES)
        done = sum(1 for v in status.values() if v["eingetragen"])
        return round((done / total) * 100) if total else 0
