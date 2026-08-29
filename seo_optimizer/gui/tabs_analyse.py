"""Tabs fuer Website-Analyse: OnPage-Audit und Ranking-Ueberwachung."""

import csv
import queue
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import ttk, messagebox, filedialog

from seo_optimizer.onpage_analyzer import analysiere_url, AuditFehler, KRITISCH, WARNUNG, HINWEIS, OK
from seo_optimizer.gui.base import BaseTab
from seo_optimizer.gui.style import COLORS, FONT_BOLD, FONT_SMALL
from seo_optimizer.gui.widgets import StatTile, RankingChart

SCHWERE_FARBE = {
    KRITISCH: "#b3261e",
    WARNUNG: "#b26a00",
    HINWEIS: "#0f4c81",
    OK: "#127a3e",
}
SCHWERE_TEXT = {
    KRITISCH: "Kritisch",
    WARNUNG: "Warnung",
    HINWEIS: "Hinweis",
    OK: "In Ordnung",
}


class OnPageAuditTab(BaseTab):
    """Prueft eine URL live auf die wichtigsten SEO- und Conversion-Kriterien."""

    # Poll-Intervall (ms), in dem der Hauptthread auf das Analyse-Ergebnis wartet.
    POLL_MS = 100

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.ergebnis = None
        self._laeuft = False
        # Tkinter darf nur aus dem Hauptthread bedient werden. Der Worker-Thread
        # legt sein Ergebnis daher in diese Queue, die der Hauptthread abfragt.
        self._ergebnis_queue = queue.Queue()
        self._build()

    def _build(self):
        eingabe = ttk.Frame(self)
        eingabe.pack(fill="x")
        eingabe.columnconfigure(1, weight=1)

        ttk.Label(eingabe, text="URL").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.url_var = tk.StringVar()
        ttk.Entry(eingabe, textvariable=self.url_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(eingabe, text="Fokus-Keyword").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(6, 0))
        self.keyword_var = tk.StringVar()
        ttk.Entry(eingabe, textvariable=self.keyword_var).grid(row=1, column=1, sticky="ew", pady=(6, 0))

        knopfleiste = ttk.Frame(self)
        knopfleiste.pack(fill="x", pady=(10, 8))
        self.start_button = ttk.Button(knopfleiste, text="Seite analysieren",
                                       style="Primary.TButton", command=self.starte_analyse)
        self.start_button.pack(side="left")
        ttk.Button(knopfleiste, text="Seite im Browser oeffnen",
                   command=self._oeffne_url).pack(side="left", padx=8)
        ttk.Button(knopfleiste, text="Befunde als CSV",
                   command=self.export_csv).pack(side="left")

        self.status_var = tk.StringVar(value="Noch keine Analyse durchgefuehrt.")
        ttk.Label(self, textvariable=self.status_var, style="Muted.TLabel").pack(fill="x")

        # Kennzahlen-Kacheln
        self.kachel_leiste = ttk.Frame(self)
        self.kachel_leiste.pack(fill="x", pady=(10, 6))
        self.kachel_score = StatTile(self.kachel_leiste, "SEO-Score der Seite")
        self.kachel_score.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.kachel_kritisch = StatTile(self.kachel_leiste, "Kritische Maengel")
        self.kachel_kritisch.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_warnung = StatTile(self.kachel_leiste, "Warnungen")
        self.kachel_warnung.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_ok = StatTile(self.kachel_leiste, "Bestandene Pruefungen")
        self.kachel_ok.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.kennzahl_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.kennzahl_var, style="Muted.TLabel").pack(fill="x", pady=(0, 6))

        # Befundliste
        spalten = ("schwere", "titel", "hinweis", "empfehlung")
        self.tree = ttk.Treeview(self, columns=spalten, show="headings", height=12)
        for spalte, text, breite in [
            ("schwere", "Bewertung", 90), ("titel", "Pruefung", 170),
            ("hinweis", "Befund", 320), ("empfehlung", "Empfehlung", 340),
        ]:
            self.tree.heading(spalte, text=text)
            self.tree.column(spalte, width=breite, anchor="w")

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        for schwere, farbe in SCHWERE_FARBE.items():
            self.tree.tag_configure(schwere, foreground=farbe)

    def load_client(self, client):
        super().load_client(client)
        self.ergebnis = None
        for zeile in self.tree.get_children():
            self.tree.delete(zeile)
        self._setze_kacheln(None)
        self.kennzahl_var.set("")
        if client is None:
            self.url_var.set("")
            self.keyword_var.set("")
            self.status_var.set("Noch keine Analyse durchgefuehrt.")
            return
        self.url_var.set(client.get("website", "") or "")
        self.keyword_var.set("")
        letzter = self.app.db.get_latest_audit(client["id"])
        if letzter:
            datum = letzter["datum"][:10] if letzter.get("datum") else "?"
            self.status_var.set(
                f"Letzte gespeicherte Analyse: {letzter['url']} - Score {letzter['score']} (vom {datum})"
            )
        else:
            self.status_var.set("Noch keine Analyse durchgefuehrt.")

    # -- Analyse (im Hintergrund, damit die Oberflaeche reagierbar bleibt) --

    def starte_analyse(self):
        if self.client is None or self._laeuft:
            return
        url = self.url_var.get().strip()
        if not url:
            messagebox.showinfo("URL fehlt", "Bitte eine URL angeben (z. B. https://www.beispiel.de).")
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_var.set(url)

        self._laeuft = True
        self.start_button.config(state="disabled")
        self.status_var.set(f"Analysiere {url} ...")
        keyword = self.keyword_var.get().strip()

        thread = threading.Thread(target=self._analyse_thread, args=(url, keyword), daemon=True)
        thread.start()
        self.after(self.POLL_MS, self._pruefe_ergebnis)

    def _analyse_thread(self, url, keyword):
        """Laeuft im Hintergrund-Thread und legt das Ergebnis in die Queue.

        Hier wird bewusst kein Tkinter-Aufruf gemacht (auch kein after()),
        da die Tk-Schnittstelle nicht threadsicher ist.
        """
        try:
            self._ergebnis_queue.put((analysiere_url(url, fokus_keyword=keyword), None))
        except AuditFehler as fehler:
            self._ergebnis_queue.put((None, str(fehler)))
        except Exception as fehler:  # unerwartete Fehler nicht stillschweigend verlieren
            self._ergebnis_queue.put((None, f"Unerwarteter Fehler bei der Analyse: {fehler}"))

    def _pruefe_ergebnis(self):
        """Wird im Hauptthread ausgefuehrt und wartet auf das Analyse-Ergebnis."""
        try:
            ergebnis, fehlermeldung = self._ergebnis_queue.get_nowait()
        except queue.Empty:
            if self._laeuft:
                self.after(self.POLL_MS, self._pruefe_ergebnis)
            return
        self._analyse_fertig(ergebnis, fehlermeldung)

    def _analyse_fertig(self, ergebnis, fehlermeldung):
        self._laeuft = False
        self.start_button.config(state="normal")

        if fehlermeldung:
            self.status_var.set(fehlermeldung)
            messagebox.showerror("Analyse fehlgeschlagen", fehlermeldung)
            return

        self.ergebnis = ergebnis
        for zeile in self.tree.get_children():
            self.tree.delete(zeile)

        reihenfolge = {KRITISCH: 0, WARNUNG: 1, HINWEIS: 2, OK: 3}
        befunde = sorted(ergebnis["befunde"], key=lambda b: reihenfolge.get(b["schwere"], 9))
        for befund in befunde:
            self.tree.insert("", "end", tags=(befund["schwere"],), values=(
                SCHWERE_TEXT.get(befund["schwere"], befund["schwere"]),
                befund["titel"], befund["hinweis"], befund["empfehlung"],
            ))

        self._setze_kacheln(ergebnis)
        self.kennzahl_var.set("  |  ".join(f"{k}: {v}" for k, v in ergebnis["kennzahlen"].items()))
        self.status_var.set(
            f"Analyse abgeschlossen: {ergebnis['url']} (HTTP {ergebnis['status']}) am "
            f"{datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        if self.client is not None:
            self.app.db.save_audit(
                self.client["id"], ergebnis["url"], ergebnis["score"],
                ergebnis["anzahl"][KRITISCH], ergebnis["anzahl"][WARNUNG],
            )
            self.app.on_client_updated(self.client["id"])

    def _setze_kacheln(self, ergebnis):
        if not ergebnis:
            for kachel in (self.kachel_score, self.kachel_kritisch,
                           self.kachel_warnung, self.kachel_ok):
                kachel.set_wert("-")
            return
        self.kachel_score.set_wert(f"{ergebnis['score']}", "von 100 Punkten")
        self.kachel_kritisch.set_wert(ergebnis["anzahl"][KRITISCH], "sofort beheben")
        self.kachel_warnung.set_wert(ergebnis["anzahl"][WARNUNG], "mittelfristig")
        self.kachel_ok.set_wert(ergebnis["anzahl"][OK], "erfuellt")

    def _oeffne_url(self):
        url = self.url_var.get().strip()
        if url:
            webbrowser.open(url if url.startswith("http") else "https://" + url)

    def export_csv(self):
        if not self.ergebnis:
            messagebox.showinfo("Keine Daten", "Bitte zuerst eine Analyse durchfuehren.")
            return
        pfad = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="onpage-audit.csv",
            filetypes=[("CSV-Datei", "*.csv")])
        if not pfad:
            return
        with open(pfad, "w", newline="", encoding="utf-8") as datei:
            schreiber = csv.writer(datei)
            schreiber.writerow(["Bewertung", "Pruefung", "Befund", "Empfehlung"])
            for befund in self.ergebnis["befunde"]:
                schreiber.writerow([SCHWERE_TEXT.get(befund["schwere"], befund["schwere"]),
                                    befund["titel"], befund["hinweis"], befund["empfehlung"]])
        messagebox.showinfo("Export erfolgreich", f"Befunde gespeichert unter:\n{pfad}")


class RankingTab(BaseTab):
    """Erfasst und visualisiert Ranking-Positionen je Keyword."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        # Kennzahlen
        kacheln = ttk.Frame(self)
        kacheln.pack(fill="x", pady=(0, 10))
        self.kachel_keywords = StatTile(kacheln, "Ueberwachte Keywords")
        self.kachel_keywords.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.kachel_top3 = StatTile(kacheln, "in den Top 3")
        self.kachel_top3.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_top10 = StatTile(kacheln, "in den Top 10")
        self.kachel_top10.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_schnitt = StatTile(kacheln, "Durchschnittsposition")
        self.kachel_schnitt.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # Eingabezeile
        eingabe = ttk.Labelframe(self, text="Neue Messung erfassen", padding=10)
        eingabe.pack(fill="x", pady=(0, 10))
        eingabe.columnconfigure(1, weight=1)

        ttk.Label(eingabe, text="Keyword").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.keyword_var = tk.StringVar()
        ttk.Entry(eingabe, textvariable=self.keyword_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(eingabe, text="Position").grid(row=0, column=2, sticky="w", padx=(10, 6))
        self.position_var = tk.StringVar()
        ttk.Entry(eingabe, textvariable=self.position_var, width=8).grid(row=0, column=3)

        ttk.Label(eingabe, text="Datum").grid(row=0, column=4, sticky="w", padx=(10, 6))
        self.datum_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(eingabe, textvariable=self.datum_var, width=12).grid(row=0, column=5)

        ttk.Button(eingabe, text="Erfassen", style="Primary.TButton",
                   command=self.erfasse_messung).grid(row=0, column=6, padx=(10, 0))

        ttk.Label(eingabe, text="Tipp: Position 0 oder leer lassen, wenn die Seite nicht in den Top 100 steht.",
                  style="Muted.TLabel").grid(row=1, column=0, columnspan=7, sticky="w", pady=(6, 0))

        # Tabelle + Diagramm nebeneinander
        unten = ttk.Frame(self)
        unten.pack(fill="both", expand=True)

        links = ttk.Frame(unten)
        links.pack(side="left", fill="both", expand=True)

        spalten = ("keyword", "aktuell", "veraenderung", "beste", "messungen", "datum")
        self.tree = ttk.Treeview(links, columns=spalten, show="headings", height=10, selectmode="browse")
        for spalte, text, breite in [
            ("keyword", "Keyword", 200), ("aktuell", "Aktuell", 65),
            ("veraenderung", "Trend", 70), ("beste", "Beste", 60),
            ("messungen", "Messungen", 80), ("datum", "Letzte Messung", 105),
        ]:
            self.tree.heading(spalte, text=text)
            self.tree.column(spalte, width=breite, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._zeige_verlauf)
        self.tree.tag_configure("besser", foreground="#127a3e")
        self.tree.tag_configure("schlechter", foreground="#b3261e")

        knopfleiste = ttk.Frame(links)
        knopfleiste.pack(fill="x", pady=(8, 0))
        ttk.Button(knopfleiste, text="Keyword entfernen", style="Danger.TButton",
                   command=self.entferne_keyword).pack(side="left")
        ttk.Button(knopfleiste, text="CSV importieren", command=self.import_csv).pack(side="left", padx=8)
        ttk.Button(knopfleiste, text="CSV exportieren", command=self.export_csv).pack(side="left")

        rechts = ttk.Frame(unten)
        rechts.pack(side="left", fill="both", expand=True, padx=(12, 0))
        ttk.Label(rechts, text="Ranking-Verlauf", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))
        self.chart = RankingChart(rechts)
        self.chart.pack(fill="both", expand=True)
        ttk.Label(rechts, text="Keyword in der Tabelle auswaehlen, um den Verlauf zu sehen.",
                  style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

    def load_client(self, client):
        super().load_client(client)
        self.keyword_var.set("")
        self.position_var.set("")
        self.chart.set_daten([], "")
        self.aktualisiere()

    def aktualisiere(self):
        for zeile in self.tree.get_children():
            self.tree.delete(zeile)
        if self.client is None:
            for kachel in (self.kachel_keywords, self.kachel_top3,
                           self.kachel_top10, self.kachel_schnitt):
                kachel.set_wert("-")
            return

        uebersicht = self.app.db.get_ranking_overview(self.client["id"])
        for eintrag in uebersicht:
            veraenderung = eintrag["veraenderung"]
            if veraenderung is None:
                trend, tag = "neu", ""
            elif veraenderung > 0:
                trend, tag = f"+{veraenderung}", "besser"
            elif veraenderung < 0:
                trend, tag = str(veraenderung), "schlechter"
            else:
                trend, tag = "0", ""
            self.tree.insert("", "end", iid=eintrag["keyword"], tags=(tag,), values=(
                eintrag["keyword"], eintrag["aktuell"], trend,
                eintrag["beste"], eintrag["messungen"], eintrag["datum"],
            ))

        kennzahlen = self.app.db.ranking_summary(self.client["id"])
        self.kachel_keywords.set_wert(kennzahlen["keywords"])
        self.kachel_top3.set_wert(kennzahlen["top3"])
        self.kachel_top10.set_wert(kennzahlen["top10"])
        schnitt = kennzahlen["durchschnitt"]
        self.kachel_schnitt.set_wert(schnitt if schnitt is not None else "-")

    def _zeige_verlauf(self, _event=None):
        auswahl = self.tree.selection()
        if not auswahl or self.client is None:
            return
        keyword = auswahl[0]
        verlauf = self.app.db.get_ranking_history(self.client["id"], keyword)
        self.chart.set_daten([(e["datum"], e["position"]) for e in verlauf], keyword)

    def erfasse_messung(self):
        if self.client is None:
            return
        keyword = self.keyword_var.get().strip()
        if not keyword:
            messagebox.showinfo("Keyword fehlt", "Bitte ein Keyword eingeben.")
            return

        position = self._lies_position()
        if position is None:
            return

        datum = self.datum_var.get().strip() or datetime.now().strftime("%Y-%m-%d")
        if not self._datum_gueltig(datum):
            messagebox.showwarning("Datum ungueltig", "Bitte das Datum im Format JJJJ-MM-TT angeben.")
            return

        self.app.db.add_ranking(self.client["id"], keyword, position, datum=datum)
        self.keyword_var.set("")
        self.position_var.set("")
        self.aktualisiere()
        if self.tree.exists(keyword):
            self.tree.selection_set(keyword)
        self.app.on_client_updated(self.client["id"])

    def _lies_position(self):
        """Liest das Positionsfeld; leer/0 bedeutet 'nicht in den Top 100'."""
        rohwert = self.position_var.get().strip()
        if not rohwert or rohwert == "0":
            return 101
        try:
            position = int(rohwert)
        except ValueError:
            messagebox.showwarning("Ungueltige Position", "Bitte eine ganze Zahl als Position eingeben.")
            return None
        if position < 1 or position > 200:
            messagebox.showwarning("Ungueltige Position", "Die Position muss zwischen 1 und 200 liegen.")
            return None
        return position

    @staticmethod
    def _datum_gueltig(datum):
        try:
            datetime.strptime(datum, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def entferne_keyword(self):
        auswahl = self.tree.selection()
        if not auswahl or self.client is None:
            messagebox.showinfo("Kein Keyword gewaehlt", "Bitte zuerst ein Keyword in der Tabelle waehlen.")
            return
        keyword = auswahl[0]
        if not messagebox.askyesno("Keyword entfernen",
                                   f"Alle Messungen fuer \"{keyword}\" loeschen?"):
            return
        self.app.db.delete_ranking_keyword(self.client["id"], keyword)
        self.chart.set_daten([], "")
        self.aktualisiere()
        self.app.on_client_updated(self.client["id"])

    def import_csv(self):
        """Importiert Messungen aus einer CSV mit Spalten Keyword;Position;Datum."""
        if self.client is None:
            return
        pfad = filedialog.askopenfilename(filetypes=[("CSV-Datei", "*.csv"), ("Alle Dateien", "*.*")])
        if not pfad:
            return
        importiert, uebersprungen = 0, 0
        try:
            with open(pfad, newline="", encoding="utf-8-sig") as datei:
                probe = datei.read(2048)
                datei.seek(0)
                try:
                    dialekt = csv.Sniffer().sniff(probe, delimiters=";,\t")
                except csv.Error:
                    dialekt = csv.excel
                leser = csv.reader(datei, dialekt)
                for zeile in leser:
                    if len(zeile) < 2:
                        uebersprungen += 1
                        continue
                    keyword = zeile[0].strip()
                    try:
                        position = int(zeile[1].strip())
                    except ValueError:
                        uebersprungen += 1  # z. B. Kopfzeile
                        continue
                    datum = zeile[2].strip() if len(zeile) > 2 and self._datum_gueltig(zeile[2].strip()) \
                        else datetime.now().strftime("%Y-%m-%d")
                    if not keyword or position < 1:
                        uebersprungen += 1
                        continue
                    self.app.db.add_ranking(self.client["id"], keyword, position, datum=datum)
                    importiert += 1
        except OSError as fehler:
            messagebox.showerror("Import fehlgeschlagen", f"Datei konnte nicht gelesen werden:\n{fehler}")
            return

        self.aktualisiere()
        self.app.on_client_updated(self.client["id"])
        messagebox.showinfo(
            "Import abgeschlossen",
            f"{importiert} Messungen importiert, {uebersprungen} Zeilen uebersprungen.")

    def export_csv(self):
        if self.client is None:
            return
        uebersicht = self.app.db.get_ranking_overview(self.client["id"])
        if not uebersicht:
            messagebox.showinfo("Keine Daten", "Es sind noch keine Rankings erfasst.")
            return
        pfad = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="rankings.csv",
            filetypes=[("CSV-Datei", "*.csv")])
        if not pfad:
            return
        with open(pfad, "w", newline="", encoding="utf-8") as datei:
            schreiber = csv.writer(datei, delimiter=";")
            schreiber.writerow(["Keyword", "Aktuelle Position", "Veraenderung",
                                "Beste Position", "Messungen", "Letzte Messung"])
            for eintrag in uebersicht:
                schreiber.writerow([
                    eintrag["keyword"], eintrag["aktuell"],
                    eintrag["veraenderung"] if eintrag["veraenderung"] is not None else "",
                    eintrag["beste"], eintrag["messungen"], eintrag["datum"],
                ])
        messagebox.showinfo("Export erfolgreich", f"Rankings gespeichert unter:\n{pfad}")
