"""Tabs fuer die Content-Produktion: Redaktionsplan, Briefing und Textanalyse."""

import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, filedialog

from seo_optimizer.content_tools import (
    analysiere_text, empfehlungen_zum_text, erstelle_briefing, briefing_als_text,
)
from seo_optimizer.data_seo import CONTENT_TYPES, CONTENT_STATUS, WORTZIEL_JE_TYP
from seo_optimizer.gui.base import BaseTab
from seo_optimizer.gui.style import FONT_BOLD, FONT_SMALL
from seo_optimizer.gui.widgets import StatTile


class RedaktionsplanTab(BaseTab):
    """Planung und Statusverfolgung aller Inhalte eines Kunden."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.aktuelle_id = None
        self._build()

    def _build(self):
        self.zusammenfassung_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.zusammenfassung_var, style="Muted.TLabel").pack(fill="x")

        spalten = ("titel", "typ", "keyword", "status", "faellig", "wortziel")
        self.tree = ttk.Treeview(self, columns=spalten, show="headings", height=11, selectmode="browse")
        for spalte, text, breite in [
            ("titel", "Titel", 250), ("typ", "Typ", 150), ("keyword", "Fokus-Keyword", 150),
            ("status", "Status", 130), ("faellig", "Faellig am", 95), ("wortziel", "Wortziel", 75),
        ]:
            self.tree.heading(spalte, text=text)
            self.tree.column(spalte, width=breite, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(8, 8))
        self.tree.bind("<<TreeviewSelect>>", self._uebernehme_auswahl)
        self.tree.tag_configure("ueberfaellig", foreground="#b3261e")
        self.tree.tag_configure("fertig", foreground="#127a3e")

        formular = ttk.Labelframe(self, text="Inhalt bearbeiten", padding=10)
        formular.pack(fill="x")
        formular.columnconfigure(1, weight=1)
        formular.columnconfigure(3, weight=1)

        ttk.Label(formular, text="Titel *").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=3)
        self.titel_var = tk.StringVar()
        ttk.Entry(formular, textvariable=self.titel_var).grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(formular, text="Fokus-Keyword").grid(row=0, column=2, sticky="w", padx=(10, 6), pady=3)
        self.keyword_var = tk.StringVar()
        ttk.Entry(formular, textvariable=self.keyword_var).grid(row=0, column=3, sticky="ew", pady=3)

        ttk.Label(formular, text="Typ").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=3)
        self.typ_var = tk.StringVar(value=CONTENT_TYPES[0])
        typ_box = ttk.Combobox(formular, textvariable=self.typ_var, values=CONTENT_TYPES, state="readonly")
        typ_box.grid(row=1, column=1, sticky="ew", pady=3)
        typ_box.bind("<<ComboboxSelected>>", self._typ_gewechselt)

        ttk.Label(formular, text="Status").grid(row=1, column=2, sticky="w", padx=(10, 6), pady=3)
        self.status_var = tk.StringVar(value=CONTENT_STATUS[0])
        ttk.Combobox(formular, textvariable=self.status_var, values=CONTENT_STATUS,
                     state="readonly").grid(row=1, column=3, sticky="ew", pady=3)

        ttk.Label(formular, text="Faellig am").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=3)
        self.faellig_var = tk.StringVar()
        ttk.Entry(formular, textvariable=self.faellig_var).grid(row=2, column=1, sticky="ew", pady=3)

        ttk.Label(formular, text="Wortziel").grid(row=2, column=2, sticky="w", padx=(10, 6), pady=3)
        self.wortziel_var = tk.StringVar(value="800")
        ttk.Entry(formular, textvariable=self.wortziel_var).grid(row=2, column=3, sticky="ew", pady=3)

        ttk.Label(formular, text="Ziel-URL").grid(row=3, column=0, sticky="w", padx=(0, 6), pady=3)
        self.url_var = tk.StringVar()
        ttk.Entry(formular, textvariable=self.url_var).grid(row=3, column=1, columnspan=3, sticky="ew", pady=3)

        knopfleiste = ttk.Frame(formular)
        knopfleiste.grid(row=4, column=0, columnspan=4, sticky="e", pady=(10, 0))
        ttk.Button(knopfleiste, text="Neu", command=self.neues_formular).pack(side="left", padx=(0, 6))
        ttk.Button(knopfleiste, text="Speichern", style="Primary.TButton",
                   command=self.speichern).pack(side="left")
        ttk.Button(knopfleiste, text="Loeschen", style="Danger.TButton",
                   command=self.loeschen).pack(side="left", padx=(6, 0))

        ttk.Label(formular, text="Datumsformat: JJJJ-MM-TT", style="Muted.TLabel").grid(
            row=5, column=0, columnspan=4, sticky="w", pady=(6, 0))

    def _typ_gewechselt(self, _event=None):
        self.wortziel_var.set(str(WORTZIEL_JE_TYP.get(self.typ_var.get(), 800)))

    def load_client(self, client):
        super().load_client(client)
        self.neues_formular()
        self.aktualisiere()

    def aktualisiere(self):
        for zeile in self.tree.get_children():
            self.tree.delete(zeile)
        if self.client is None:
            self.zusammenfassung_var.set("")
            return

        heute = datetime.now().strftime("%Y-%m-%d")
        for item in self.app.db.get_content_items(self.client["id"]):
            faellig = item.get("faellig_am") or ""
            status = item.get("status") or ""
            if status == "Veroeffentlicht":
                tag = "fertig"
            elif faellig and faellig < heute:
                tag = "ueberfaellig"
            else:
                tag = ""
            self.tree.insert("", "end", iid=str(item["id"]), tags=(tag,), values=(
                item["titel"], item.get("typ", ""), item.get("fokus_keyword", ""),
                status, faellig, item.get("wortziel") or "",
            ))

        kennzahlen = self.app.db.content_summary(self.client["id"])
        gesamt = kennzahlen.pop("gesamt", 0)
        teile = [f"{anzahl}x {status}" for status, anzahl in sorted(kennzahlen.items())]
        self.zusammenfassung_var.set(
            f"{gesamt} geplante Inhalte" + (f"  ({', '.join(teile)})" if teile else "")
        )

    def _uebernehme_auswahl(self, _event=None):
        auswahl = self.tree.selection()
        if not auswahl or self.client is None:
            return
        item_id = int(auswahl[0])
        items = {i["id"]: i for i in self.app.db.get_content_items(self.client["id"])}
        item = items.get(item_id)
        if not item:
            return
        self.aktuelle_id = item_id
        self.titel_var.set(item["titel"])
        self.keyword_var.set(item.get("fokus_keyword") or "")
        self.typ_var.set(item.get("typ") or CONTENT_TYPES[0])
        self.status_var.set(item.get("status") or CONTENT_STATUS[0])
        self.faellig_var.set(item.get("faellig_am") or "")
        self.wortziel_var.set(str(item.get("wortziel") or ""))
        self.url_var.set(item.get("ziel_url") or "")

    def neues_formular(self):
        self.aktuelle_id = None
        self.titel_var.set("")
        self.keyword_var.set("")
        self.typ_var.set(CONTENT_TYPES[0])
        self.status_var.set(CONTENT_STATUS[0])
        self.faellig_var.set("")
        self.wortziel_var.set(str(WORTZIEL_JE_TYP.get(CONTENT_TYPES[0], 800)))
        self.url_var.set("")
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def speichern(self):
        if self.client is None:
            return
        titel = self.titel_var.get().strip()
        if not titel:
            messagebox.showwarning("Titel fehlt", "Bitte einen Titel fuer den Inhalt eingeben.")
            return

        faellig = self.faellig_var.get().strip()
        if faellig and not self._datum_gueltig(faellig):
            messagebox.showwarning("Datum ungueltig", "Bitte das Faelligkeitsdatum als JJJJ-MM-TT angeben.")
            return

        try:
            wortziel = int(self.wortziel_var.get().strip() or 0)
        except ValueError:
            messagebox.showwarning("Wortziel ungueltig", "Das Wortziel muss eine Zahl sein.")
            return

        daten = {
            "titel": titel,
            "fokus_keyword": self.keyword_var.get().strip(),
            "typ": self.typ_var.get(),
            "status": self.status_var.get(),
            "faellig_am": faellig,
            "wortziel": wortziel,
            "ziel_url": self.url_var.get().strip(),
            "notizen": "",
        }
        if self.aktuelle_id:
            self.app.db.update_content_item(self.aktuelle_id, daten)
        else:
            self.aktuelle_id = self.app.db.add_content_item(self.client["id"], daten)
        self.aktualisiere()
        if self.tree.exists(str(self.aktuelle_id)):
            self.tree.selection_set(str(self.aktuelle_id))
        self.app.on_client_updated(self.client["id"])

    def loeschen(self):
        if self.aktuelle_id is None:
            messagebox.showinfo("Nichts ausgewaehlt", "Bitte zuerst einen Inhalt in der Liste waehlen.")
            return
        if not messagebox.askyesno("Inhalt loeschen", "Diesen geplanten Inhalt wirklich loeschen?"):
            return
        self.app.db.delete_content_item(self.aktuelle_id)
        self.neues_formular()
        self.aktualisiere()
        self.app.on_client_updated(self.client["id"])

    @staticmethod
    def _datum_gueltig(datum):
        try:
            datetime.strptime(datum, "%Y-%m-%d")
            return True
        except ValueError:
            return False


class BriefingTab(BaseTab):
    """Erzeugt ein vollstaendiges Redaktionsbriefing zu einem Fokus-Keyword."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.briefing = None
        self._build()

    def _build(self):
        eingabe = ttk.Frame(self)
        eingabe.pack(fill="x")
        eingabe.columnconfigure(1, weight=1)

        ttk.Label(eingabe, text="Fokus-Keyword *").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.keyword_var = tk.StringVar()
        ttk.Entry(eingabe, textvariable=self.keyword_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(eingabe, text="Ort").grid(row=0, column=2, sticky="w", padx=(10, 6))
        self.ort_var = tk.StringVar()
        ttk.Entry(eingabe, textvariable=self.ort_var, width=18).grid(row=0, column=3)

        ttk.Label(eingabe, text="Inhaltstyp").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(6, 0))
        self.typ_var = tk.StringVar(value=CONTENT_TYPES[0])
        ttk.Combobox(eingabe, textvariable=self.typ_var, values=CONTENT_TYPES,
                     state="readonly").grid(row=1, column=1, sticky="ew", pady=(6, 0))

        knopfleiste = ttk.Frame(self)
        knopfleiste.pack(fill="x", pady=(10, 8))
        ttk.Button(knopfleiste, text="Briefing erstellen", style="Primary.TButton",
                   command=self.erstelle).pack(side="left")
        ttk.Button(knopfleiste, text="In Zwischenablage",
                   command=self.kopiere).pack(side="left", padx=8)
        ttk.Button(knopfleiste, text="Als Textdatei speichern",
                   command=self.speichere).pack(side="left")
        ttk.Button(knopfleiste, text="In Redaktionsplan uebernehmen",
                   command=self.uebernehme_in_plan).pack(side="left", padx=8)

        textbereich = ttk.Frame(self)
        textbereich.pack(fill="both", expand=True)
        scroll = ttk.Scrollbar(textbereich, orient="vertical")
        self.text = tk.Text(textbereich, wrap="word", font=("Consolas", 10),
                            yscrollcommand=scroll.set, state="disabled")
        scroll.config(command=self.text.yview)
        self.text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def load_client(self, client):
        super().load_client(client)
        self.briefing = None
        self._setze_text("")
        if client is None:
            self.keyword_var.set("")
            self.ort_var.set("")
            return
        self.ort_var.set(client.get("ort", "") or "")
        self.keyword_var.set("")

    def _setze_text(self, inhalt):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", inhalt)
        self.text.config(state="disabled")

    def erstelle(self):
        if self.client is None:
            return
        keyword = self.keyword_var.get().strip()
        if not keyword:
            messagebox.showinfo("Keyword fehlt", "Bitte ein Fokus-Keyword eingeben.")
            return
        self.briefing = erstelle_briefing(
            keyword, self.client.get("gewerk", ""), self.ort_var.get().strip(), self.typ_var.get()
        )
        self._setze_text(briefing_als_text(self.briefing))

    def kopiere(self):
        if not self.briefing:
            messagebox.showinfo("Kein Briefing", "Bitte zuerst ein Briefing erstellen.")
            return
        self.clipboard_clear()
        self.clipboard_append(briefing_als_text(self.briefing))
        messagebox.showinfo("Kopiert", "Das Briefing wurde in die Zwischenablage kopiert.")

    def speichere(self):
        if not self.briefing:
            messagebox.showinfo("Kein Briefing", "Bitte zuerst ein Briefing erstellen.")
            return
        pfad = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=f"briefing-{self.briefing['fokus_keyword'].replace(' ', '-')}.txt",
            filetypes=[("Textdatei", "*.txt")])
        if not pfad:
            return
        with open(pfad, "w", encoding="utf-8") as datei:
            datei.write(briefing_als_text(self.briefing))
        messagebox.showinfo("Gespeichert", f"Briefing gespeichert unter:\n{pfad}")

    def uebernehme_in_plan(self):
        """Legt aus dem Briefing direkt einen Eintrag im Redaktionsplan an."""
        if not self.briefing or self.client is None:
            messagebox.showinfo("Kein Briefing", "Bitte zuerst ein Briefing erstellen.")
            return
        self.app.db.add_content_item(self.client["id"], {
            "titel": self.briefing["title_vorschlag"],
            "fokus_keyword": self.briefing["fokus_keyword"],
            "typ": self.briefing["typ"],
            "status": "Briefing erstellt",
            "wortziel": self.briefing["wortziel"],
            "ziel_url": self.briefing["url_vorschlag"],
            "faellig_am": "",
            "notizen": "",
        })
        self.app.on_client_updated(self.client["id"])
        self.app.aktualisiere_content_tabs()
        messagebox.showinfo("Uebernommen",
                            "Der Inhalt wurde im Redaktionsplan angelegt (Status: Briefing erstellt).")


class TextAnalyseTab(BaseTab):
    """Prueft einen Text auf Lesbarkeit, Umfang und Keyword-Einsatz."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        eingabe = ttk.Frame(self)
        eingabe.pack(fill="x")
        ttk.Label(eingabe, text="Fokus-Keyword").pack(side="left")
        self.keyword_var = tk.StringVar()
        ttk.Entry(eingabe, textvariable=self.keyword_var, width=28).pack(side="left", padx=8)
        ttk.Label(eingabe, text="Wortziel").pack(side="left", padx=(10, 0))
        self.wortziel_var = tk.StringVar(value="800")
        ttk.Entry(eingabe, textvariable=self.wortziel_var, width=8).pack(side="left", padx=8)
        ttk.Button(eingabe, text="Text analysieren", style="Primary.TButton",
                   command=self.analysiere).pack(side="left")
        ttk.Button(eingabe, text="Leeren", command=self.leeren).pack(side="left", padx=8)

        kacheln = ttk.Frame(self)
        kacheln.pack(fill="x", pady=(10, 8))
        self.kachel_woerter = StatTile(kacheln, "Woerter")
        self.kachel_woerter.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.kachel_lesbarkeit = StatTile(kacheln, "Lesbarkeit (Flesch)")
        self.kachel_lesbarkeit.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_dichte = StatTile(kacheln, "Keyword-Dichte")
        self.kachel_dichte.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_satzlaenge = StatTile(kacheln, "Woerter je Satz")
        self.kachel_satzlaenge.pack(side="left", fill="x", expand=True, padx=(6, 0))

        bereiche = ttk.Frame(self)
        bereiche.pack(fill="both", expand=True)

        links = ttk.Labelframe(bereiche, text="Text einfuegen", padding=8)
        links.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(links, orient="vertical")
        self.text = tk.Text(links, wrap="word", font=("Segoe UI", 10), height=14,
                            yscrollcommand=scroll.set)
        scroll.config(command=self.text.yview)
        self.text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        rechts = ttk.Labelframe(bereiche, text="Empfehlungen & Begriffe", padding=8)
        rechts.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scroll2 = ttk.Scrollbar(rechts, orient="vertical")
        self.ergebnis_text = tk.Text(rechts, wrap="word", font=("Segoe UI", 10), height=14,
                                     yscrollcommand=scroll2.set, state="disabled")
        scroll2.config(command=self.ergebnis_text.yview)
        self.ergebnis_text.pack(side="left", fill="both", expand=True)
        scroll2.pack(side="right", fill="y")

    def load_client(self, client):
        super().load_client(client)
        self.leeren()

    def leeren(self):
        self.text.delete("1.0", "end")
        self._setze_ergebnis("")
        for kachel in (self.kachel_woerter, self.kachel_lesbarkeit,
                       self.kachel_dichte, self.kachel_satzlaenge):
            kachel.set_wert("-")

    def _setze_ergebnis(self, inhalt):
        self.ergebnis_text.config(state="normal")
        self.ergebnis_text.delete("1.0", "end")
        self.ergebnis_text.insert("1.0", inhalt)
        self.ergebnis_text.config(state="disabled")

    def analysiere(self):
        inhalt = self.text.get("1.0", "end").strip()
        if not inhalt:
            messagebox.showinfo("Kein Text", "Bitte zuerst einen Text einfuegen.")
            return

        try:
            wortziel = int(self.wortziel_var.get().strip() or 0) or None
        except ValueError:
            wortziel = None

        analyse = analysiere_text(inhalt, self.keyword_var.get().strip())

        self.kachel_woerter.set_wert(analyse["woerter"], f"{analyse['lesezeit_minuten']} Min. Lesezeit")
        self.kachel_lesbarkeit.set_wert(analyse["lesbarkeit"], analyse["lesbarkeit_label"])
        self.kachel_dichte.set_wert(f"{analyse['keyword_dichte']} %", analyse["dichte_bewertung"])
        self.kachel_satzlaenge.set_wert(analyse["woerter_je_satz"],
                                        f"{analyse['lange_saetze']} sehr lange Saetze")

        zeilen = ["EMPFEHLUNGEN", ""]
        zeilen += [f"- {tipp}" for tipp in empfehlungen_zum_text(analyse, wortziel)]
        zeilen += ["", "HAEUFIGSTE BEGRIFFE", ""]
        zeilen += [f"  {begriff}: {anzahl}x" for begriff, anzahl in analyse["begriffe"]]
        if analyse["lange_saetze_beispiele"]:
            zeilen += ["", "ZU LANGE SAETZE (Auszug)", ""]
            for satz in analyse["lange_saetze_beispiele"]:
                gekuerzt = satz if len(satz) <= 180 else satz[:180] + " ..."
                zeilen.append(f"- {gekuerzt}")
        self._setze_ergebnis("\n".join(zeilen))
