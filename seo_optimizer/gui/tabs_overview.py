"""Dashboard-Tab: Gesamtstatus eines Kunden auf einen Blick."""

import tkinter as tk
from tkinter import ttk

from seo_optimizer.data import CHECKLIST_CATALOG
from seo_optimizer.data_seo import TECHNICAL_SEO_CATALOG, CRO_CATALOG
from seo_optimizer.gui.base import BaseTab
from seo_optimizer.gui.style import COLORS, FONT_BOLD, FONT_SMALL
from seo_optimizer.gui.widgets import ProgressRow, StatTile, ScrollableFrame


class OverviewTab(BaseTab):
    """Fasst Score, Fortschritte, Rankings und naechste Schritte zusammen."""

    def __init__(self, parent, app):
        super().__init__(parent, app, padding=0)
        self._build()

    def _build(self):
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        container = ttk.Frame(scroll.inner, padding=16)
        container.pack(fill="both", expand=True)

        # Kennzahlen-Kacheln
        kacheln = ttk.Frame(container)
        kacheln.pack(fill="x")
        self.kachel_score = StatTile(kacheln, "Gesamt-SEO-Score")
        self.kachel_score.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.kachel_rankings = StatTile(kacheln, "Keywords in Top 10")
        self.kachel_rankings.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_position = StatTile(kacheln, "Durchschnittsposition")
        self.kachel_position.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_content = StatTile(kacheln, "Geplante Inhalte")
        self.kachel_content.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_audit = StatTile(kacheln, "Letzter Website-Score")
        self.kachel_audit.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # Fortschritt je Teilbereich
        bereiche = ttk.Labelframe(container, text="Fortschritt je Teilbereich", padding=12)
        bereiche.pack(fill="x", pady=(14, 0))
        self.fortschritte = {}
        for name in ("Technik & OnPage", "Lokale SEO", "Conversion", "Verzeichnisse"):
            zeile = ProgressRow(bereiche, name)
            zeile.pack(fill="x", pady=5)
            self.fortschritte[name] = zeile

        ttk.Label(
            bereiche,
            text="Gewichtung im Gesamtscore: Technik & OnPage 35 %, Lokale SEO 30 %, "
                 "Conversion 20 %, Verzeichnisse 15 %.",
            style="Muted.TLabel", wraplength=700, justify="left",
        ).pack(anchor="w", pady=(8, 0))

        # Naechste Schritte
        schritte = ttk.Labelframe(container, text="Naechste empfohlene Schritte", padding=12)
        schritte.pack(fill="both", expand=True, pady=(14, 0))

        spalten = ("bereich", "kategorie", "massnahme")
        self.tree = ttk.Treeview(schritte, columns=spalten, show="headings", height=12)
        for spalte, text, breite in [
            ("bereich", "Bereich", 130), ("kategorie", "Kategorie", 200),
            ("massnahme", "Offene Massnahme", 470),
        ]:
            self.tree.heading(spalte, text=text)
            self.tree.column(spalte, width=breite, anchor="w")
        self.tree.pack(fill="both", expand=True)

        ttk.Label(
            schritte,
            text="Die Reihenfolge folgt der Priorisierung der Checklisten - "
                 "von oben nach unten abarbeiten.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(6, 0))

    def load_client(self, client):
        super().load_client(client)
        self.aktualisiere()

    def aktualisiere(self):
        for zeile in self.tree.get_children():
            self.tree.delete(zeile)

        if self.client is None:
            for kachel in (self.kachel_score, self.kachel_rankings, self.kachel_position,
                           self.kachel_content, self.kachel_audit):
                kachel.set_wert("-")
            for zeile in self.fortschritte.values():
                zeile.set_value(0)
            return

        client_id = self.client["id"]
        gesamt, teilbereiche = self.app.db.gesamt_score(client_id)
        self.kachel_score.set_wert(gesamt, "von 100 Punkten")
        for name, zeile in self.fortschritte.items():
            zeile.set_value(teilbereiche.get(name, 0))

        rankings = self.app.db.ranking_summary(client_id)
        self.kachel_rankings.set_wert(
            f"{rankings['top10']}/{rankings['keywords']}" if rankings["keywords"] else "-",
            f"{rankings['top3']} in den Top 3" if rankings["keywords"] else "keine Daten")
        schnitt = rankings["durchschnitt"]
        if schnitt is not None:
            trend = f"{rankings['verbessert']} besser / {rankings['verschlechtert']} schlechter"
        else:
            trend = "keine Daten"
        self.kachel_position.set_wert(schnitt if schnitt is not None else "-", trend)

        content = self.app.db.content_summary(client_id)
        gesamt_content = content.get("gesamt", 0)
        veroeffentlicht = content.get("Veroeffentlicht", 0)
        self.kachel_content.set_wert(gesamt_content, f"{veroeffentlicht} veroeffentlicht")

        audit = self.app.db.get_latest_audit(client_id)
        if audit:
            self.kachel_audit.set_wert(audit["score"],
                                       f"{audit['kritisch']} kritische Maengel")
        else:
            self.kachel_audit.set_wert("-", "noch keine Analyse")

        # Offene Punkte aus allen drei Katalogen zusammenfuehren
        for bereich, katalog in (
            ("Technik & OnPage", TECHNICAL_SEO_CATALOG),
            ("Lokale SEO", CHECKLIST_CATALOG),
            ("Conversion", CRO_CATALOG),
        ):
            for kategorie, massnahme in self.app.db.offene_punkte(client_id, katalog, limit=5):
                self.tree.insert("", "end", values=(bereich, kategorie, massnahme))
