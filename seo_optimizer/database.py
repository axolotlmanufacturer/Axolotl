"""SQLite-Datenzugriffsschicht fuer den Lokal-SEO Manager."""

import sqlite3
import os
from datetime import datetime

from seo_optimizer.data import CHECKLIST_CATALOG, DIRECTORIES
from seo_optimizer.data_seo import TECHNICAL_SEO_CATALOG, CRO_CATALOG

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

CREATE TABLE IF NOT EXISTS rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    position INTEGER,
    suchmaschine TEXT,
    ziel_url TEXT,
    datum TEXT NOT NULL,
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rankings_client_keyword
    ON rankings (client_id, keyword, datum);

CREATE TABLE IF NOT EXISTS content_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    titel TEXT NOT NULL,
    fokus_keyword TEXT,
    typ TEXT,
    status TEXT,
    faellig_am TEXT,
    ziel_url TEXT,
    wortziel INTEGER,
    notizen TEXT,
    erstellt_am TEXT,
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    score INTEGER,
    kritisch INTEGER DEFAULT 0,
    warnungen INTEGER DEFAULT 0,
    datum TEXT,
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
        for tabelle in ("checklist_status", "directory_status", "rankings", "content_items", "audits"):
            self.conn.execute(f"DELETE FROM {tabelle} WHERE client_id = ?", (client_id,))
        self.conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        self.conn.commit()

    def get_clients(self):
        rows = self.conn.execute("SELECT * FROM clients ORDER BY firma COLLATE NOCASE").fetchall()
        return [dict(row) for row in rows]

    def get_client(self, client_id):
        row = self.conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return dict(row) if row else None

    # -- Checkliste ---------------------------------------------------

    def get_checklist_status(self, client_id, catalog=None):
        """Status aller Items eines Katalogs; nicht gesetzte Items gelten als offen."""
        catalog = CHECKLIST_CATALOG if catalog is None else catalog
        rows = self.conn.execute(
            "SELECT item_key, erledigt FROM checklist_status WHERE client_id = ?",
            (client_id,),
        ).fetchall()
        status = {row["item_key"]: bool(row["erledigt"]) for row in rows}
        for items in catalog.values():
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

    def checklist_progress(self, client_id, catalog=None):
        """Liefert Gesamt- und Kategorie-Fortschritt (0-100) fuer einen Katalog."""
        catalog = CHECKLIST_CATALOG if catalog is None else catalog
        status = self.get_checklist_status(client_id, catalog)
        gesamt_total = 0
        gesamt_done = 0
        kategorien = {}
        for kategorie, items in catalog.items():
            total = len(items)
            done = sum(1 for key, _ in items if status.get(key))
            kategorien[kategorie] = round((done / total) * 100) if total else 0
            gesamt_total += total
            gesamt_done += done
        gesamt = round((gesamt_done / gesamt_total) * 100) if gesamt_total else 0
        return gesamt, kategorien

    def offene_punkte(self, client_id, catalog=None, limit=None):
        """Liefert die noch offenen Checklistenpunkte in Katalogreihenfolge.

        Die Reihenfolge der Kataloge/Kategorien spiegelt die Priorisierung wider,
        daher eignen sich die ersten Eintraege als 'naechste Schritte'.
        """
        catalog = CHECKLIST_CATALOG if catalog is None else catalog
        status = self.get_checklist_status(client_id, catalog)
        offen = []
        for kategorie, items in catalog.items():
            for key, text in items:
                if not status.get(key):
                    offen.append((kategorie, text))
        return offen[:limit] if limit else offen

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

    # -- Rankings -----------------------------------------------------

    def add_ranking(self, client_id, keyword, position, suchmaschine="google.de",
                    ziel_url="", datum=None):
        datum = datum or datetime.now().strftime("%Y-%m-%d")
        self.conn.execute(
            """
            INSERT INTO rankings (client_id, keyword, position, suchmaschine, ziel_url, datum)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (client_id, keyword.strip(), position, suchmaschine, ziel_url, datum),
        )
        self.conn.commit()

    def get_ranking_history(self, client_id, keyword):
        """Alle Messpunkte eines Keywords, chronologisch aufsteigend."""
        rows = self.conn.execute(
            """
            SELECT id, position, datum, suchmaschine, ziel_url
            FROM rankings WHERE client_id = ? AND keyword = ?
            ORDER BY datum ASC, id ASC
            """,
            (client_id, keyword),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_ranking_overview(self, client_id):
        """Je Keyword: aktuelle Position, vorherige Position, Veraenderung, beste Position."""
        keywords = [
            row["keyword"]
            for row in self.conn.execute(
                "SELECT DISTINCT keyword FROM rankings WHERE client_id = ? ORDER BY keyword COLLATE NOCASE",
                (client_id,),
            ).fetchall()
        ]
        overview = []
        for keyword in keywords:
            history = self.get_ranking_history(client_id, keyword)
            positionen = [h["position"] for h in history if h["position"] is not None]
            if not positionen:
                continue
            aktuell = positionen[-1]
            vorher = positionen[-2] if len(positionen) > 1 else None
            # Kleinere Position = besseres Ranking, daher vorher - aktuell.
            veraenderung = (vorher - aktuell) if vorher is not None else None
            overview.append({
                "keyword": keyword,
                "aktuell": aktuell,
                "vorher": vorher,
                "veraenderung": veraenderung,
                "beste": min(positionen),
                "messungen": len(positionen),
                "datum": history[-1]["datum"],
            })
        return overview

    def ranking_summary(self, client_id):
        """Kennzahlen ueber alle Keywords: Anzahl, Top-3/Top-10, Durchschnitt, Trend."""
        overview = self.get_ranking_overview(client_id)
        if not overview:
            return {"keywords": 0, "top3": 0, "top10": 0, "durchschnitt": None,
                    "verbessert": 0, "verschlechtert": 0}
        positionen = [o["aktuell"] for o in overview]
        return {
            "keywords": len(overview),
            "top3": sum(1 for p in positionen if p <= 3),
            "top10": sum(1 for p in positionen if p <= 10),
            "durchschnitt": round(sum(positionen) / len(positionen), 1),
            "verbessert": sum(1 for o in overview if (o["veraenderung"] or 0) > 0),
            "verschlechtert": sum(1 for o in overview if (o["veraenderung"] or 0) < 0),
        }

    def delete_ranking_keyword(self, client_id, keyword):
        self.conn.execute(
            "DELETE FROM rankings WHERE client_id = ? AND keyword = ?", (client_id, keyword)
        )
        self.conn.commit()

    # -- Redaktionsplan -------------------------------------------------

    def add_content_item(self, client_id, data):
        payload = {
            "client_id": client_id,
            "titel": data.get("titel", ""),
            "fokus_keyword": data.get("fokus_keyword", ""),
            "typ": data.get("typ", ""),
            "status": data.get("status", ""),
            "faellig_am": data.get("faellig_am", ""),
            "ziel_url": data.get("ziel_url", ""),
            "wortziel": data.get("wortziel") or 0,
            "notizen": data.get("notizen", ""),
            "erstellt_am": datetime.now().isoformat(timespec="seconds"),
        }
        columns = ", ".join(payload.keys())
        placeholders = ", ".join(f":{k}" for k in payload)
        cur = self.conn.execute(
            f"INSERT INTO content_items ({columns}) VALUES ({placeholders})", payload
        )
        self.conn.commit()
        return cur.lastrowid

    def update_content_item(self, item_id, data):
        felder = ["titel", "fokus_keyword", "typ", "status", "faellig_am",
                  "ziel_url", "wortziel", "notizen"]
        payload = {f: data.get(f, "") for f in felder}
        payload["wortziel"] = data.get("wortziel") or 0
        payload["id"] = item_id
        set_clause = ", ".join(f"{f} = :{f}" for f in felder)
        self.conn.execute(f"UPDATE content_items SET {set_clause} WHERE id = :id", payload)
        self.conn.commit()

    def delete_content_item(self, item_id):
        self.conn.execute("DELETE FROM content_items WHERE id = ?", (item_id,))
        self.conn.commit()

    def get_content_items(self, client_id):
        rows = self.conn.execute(
            "SELECT * FROM content_items WHERE client_id = ? ORDER BY faellig_am, id",
            (client_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def content_summary(self, client_id):
        """Anzahl der Inhalte je Status."""
        items = self.get_content_items(client_id)
        summary = {}
        for item in items:
            status = item.get("status") or "Ohne Status"
            summary[status] = summary.get(status, 0) + 1
        summary["gesamt"] = len(items)
        return summary

    # -- OnPage-Audits ----------------------------------------------------

    def save_audit(self, client_id, url, score, kritisch=0, warnungen=0):
        self.conn.execute(
            """
            INSERT INTO audits (client_id, url, score, kritisch, warnungen, datum)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (client_id, url, score, kritisch, warnungen,
             datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()

    def get_latest_audit(self, client_id):
        row = self.conn.execute(
            "SELECT * FROM audits WHERE client_id = ? ORDER BY datum DESC, id DESC LIMIT 1",
            (client_id,),
        ).fetchone()
        return dict(row) if row else None

    # -- Gesamtbewertung ----------------------------------------------------

    def gesamt_score(self, client_id):
        """Gewichteter Gesamt-SEO-Score (0-100) ueber alle Teilbereiche."""
        technik, _ = self.checklist_progress(client_id, TECHNICAL_SEO_CATALOG)
        lokal, _ = self.checklist_progress(client_id, CHECKLIST_CATALOG)
        cro, _ = self.checklist_progress(client_id, CRO_CATALOG)
        verzeichnisse = self.directory_progress(client_id)

        teilbereiche = {
            "Technik & OnPage": (technik, 0.35),
            "Lokale SEO": (lokal, 0.30),
            "Conversion": (cro, 0.20),
            "Verzeichnisse": (verzeichnisse, 0.15),
        }
        gesamt = round(sum(wert * gewicht for wert, gewicht in teilbereiche.values()))
        return gesamt, {name: wert for name, (wert, _) in teilbereiche.items()}
