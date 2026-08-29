"""Die funktionalen Tabs der Kundenansicht."""

import csv
import os
import webbrowser
from functools import partial
from tkinter import ttk, messagebox, filedialog
import tkinter as tk

from seo_optimizer.data import CHECKLIST_CATALOG, DIRECTORIES, GEWERKE
from seo_optimizer.keyword_generator import generate_keywords
from seo_optimizer.report import save_report
from seo_optimizer.gui.base import BaseTab
from seo_optimizer.gui.widgets import ScrollableFrame, ProgressRow
from seo_optimizer.gui.style import FONT_BOLD, FONT_SMALL


class StammdatenTab(BaseTab):
    FIELDS = [
        ("firma", "Firmenname *"),
        ("gewerk", "Gewerk"),
        ("strasse", "Strasse & Hausnummer"),
        ("plz", "PLZ"),
        ("ort", "Ort"),
        ("bundesland", "Bundesland"),
        ("telefon", "Telefon"),
        ("email", "E-Mail"),
        ("website", "Website"),
        ("google_profil_url", "Google-Unternehmensprofil-URL"),
        ("einzugsgebiet", "Einzugsgebiet (Orte, kommagetrennt)"),
    ]

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.vars = {key: tk.StringVar() for key, _ in self.FIELDS}
        self.notiz_text = None
        self._build()

    def _build(self):
        self.columnconfigure(1, weight=1)
        row = 0
        for key, label in self.FIELDS:
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=5, padx=(0, 10))
            if key == "gewerk":
                widget = ttk.Combobox(
                    self, textvariable=self.vars[key], values=list(GEWERKE.keys()),
                    state="readonly", width=40,
                )
            else:
                widget = ttk.Entry(self, textvariable=self.vars[key], width=42)
            widget.grid(row=row, column=1, sticky="ew", pady=5)
            row += 1

        ttk.Label(self, text="Notizen").grid(row=row, column=0, sticky="nw", pady=5, padx=(0, 10))
        self.notiz_text = tk.Text(self, height=5, width=42, font=("Segoe UI", 10), wrap="word")
        self.notiz_text.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Button(self, text="Speichern", style="Primary.TButton", command=self.save).grid(
            row=row, column=1, sticky="e", pady=(14, 0)
        )
        self.status_label = ttk.Label(self, text="", style="Muted.TLabel")
        self.status_label.grid(row=row, column=0, sticky="w", pady=(14, 0))

    def load_client(self, client):
        super().load_client(client)
        self.status_label.config(text="")
        if client is None:
            for var in self.vars.values():
                var.set("")
            self.notiz_text.delete("1.0", "end")
            return
        for key, var in self.vars.items():
            var.set(client.get(key, "") or "")
        self.notiz_text.delete("1.0", "end")
        self.notiz_text.insert("1.0", client.get("notizen", "") or "")

    def save(self):
        if self.client is None:
            return
        firma = self.vars["firma"].get().strip()
        if not firma:
            messagebox.showwarning("Fehlende Angabe", "Bitte einen Firmennamen eingeben.")
            return
        data = {key: var.get().strip() for key, var in self.vars.items()}
        data["notizen"] = self.notiz_text.get("1.0", "end").strip()
        self.app.db.update_client(self.client["id"], data)
        self.status_label.config(text="Gespeichert.")
        self.app.on_client_updated(self.client["id"])


class ChecklistTab(BaseTab):
    """Abhakbare Checkliste fuer einen beliebigen Katalog (lokal, technisch, CRO)."""

    def __init__(self, parent, app, catalog=None, titel="Gesamtfortschritt SEO-Checkliste"):
        super().__init__(parent, app)
        self.catalog = catalog if catalog is not None else CHECKLIST_CATALOG
        self.titel = titel
        self.item_vars = {}
        self.category_progress = {}
        self._build()

    def _build(self):
        self.overall_progress = ProgressRow(self, self.titel)
        self.overall_progress.pack(fill="x", pady=(0, 12))

        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        container = scroll.inner

        for kategorie, items in self.catalog.items():
            frame = ttk.Labelframe(container, text=kategorie, padding=10)
            frame.pack(fill="x", pady=8, padx=2)

            progress = ProgressRow(frame, "Fortschritt Kategorie")
            progress.pack(fill="x", pady=(0, 8))
            self.category_progress[kategorie] = progress

            for key, text in items:
                var = tk.BooleanVar(value=False)
                self.item_vars[key] = var
                cb = ttk.Checkbutton(
                    frame, text=text, variable=var,
                    command=partial(self._on_toggle, key),
                )
                cb.pack(anchor="w", pady=1)

    def _on_toggle(self, item_key):
        if self.client is None:
            return
        value = self.item_vars[item_key].get()
        self.app.db.set_checklist_item(self.client["id"], item_key, value)
        self._refresh_progress()
        self.app.on_client_updated(self.client["id"])

    def load_client(self, client):
        super().load_client(client)
        if client is None:
            for var in self.item_vars.values():
                var.set(False)
            self.overall_progress.set_value(0)
            for progress in self.category_progress.values():
                progress.set_value(0)
            return
        status = self.app.db.get_checklist_status(client["id"], self.catalog)
        for key, var in self.item_vars.items():
            var.set(status.get(key, False))
        self._refresh_progress()

    def _refresh_progress(self):
        gesamt, kategorien = self.app.db.checklist_progress(self.client["id"], self.catalog)
        self.overall_progress.set_value(gesamt)
        for kategorie, progress in self.category_progress.items():
            progress.set_value(kategorien.get(kategorie, 0))


class DirectoryTab(BaseTab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.rows = {}
        self._build()

    def _build(self):
        self.progress_row = ProgressRow(self, "Fortschritt Branchenverzeichnisse (Citations)")
        self.progress_row.pack(fill="x", pady=(0, 12))

        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        container = scroll.inner

        header = ttk.Frame(container)
        header.pack(fill="x", pady=(0, 4))
        ttk.Label(header, text="Eingetragen", width=10, style="Bold.TLabel").grid(row=0, column=0)
        ttk.Label(header, text="Verzeichnis", width=28, style="Bold.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="Eigene Profil-URL", style="Bold.TLabel").grid(row=0, column=2, sticky="w")

        for dir_key, name, base_url in DIRECTORIES:
            row = ttk.Frame(container)
            row.pack(fill="x", pady=3)
            row.columnconfigure(2, weight=1)

            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(row, variable=var, command=partial(self._on_change, dir_key))
            cb.grid(row=0, column=0, padx=(4, 0))

            ttk.Label(row, text=name, width=28).grid(row=0, column=1, sticky="w")

            url_var = tk.StringVar()
            entry = ttk.Entry(row, textvariable=url_var)
            entry.grid(row=0, column=2, sticky="ew", padx=(0, 6))
            entry.bind("<FocusOut>", partial(self._on_change_event, dir_key))

            if base_url:
                ttk.Button(
                    row, text="Oeffnen", width=8,
                    command=partial(webbrowser.open, base_url),
                ).grid(row=0, column=3)

            self.rows[dir_key] = {"var": var, "url_var": url_var}

    def _on_change_event(self, dir_key, _event=None):
        self._on_change(dir_key)

    def _on_change(self, dir_key):
        if self.client is None:
            return
        row = self.rows[dir_key]
        self.app.db.set_directory_item(
            self.client["id"], dir_key, row["var"].get(), profil_url=row["url_var"].get()
        )
        self.progress_row.set_value(self.app.db.directory_progress(self.client["id"]))
        self.app.on_client_updated(self.client["id"])

    def load_client(self, client):
        super().load_client(client)
        if client is None:
            for row in self.rows.values():
                row["var"].set(False)
                row["url_var"].set("")
            self.progress_row.set_value(0)
            return
        status = self.app.db.get_directory_status(client["id"])
        for dir_key, row in self.rows.items():
            entry = status.get(dir_key, {"eingetragen": False, "profil_url": ""})
            row["var"].set(entry["eingetragen"])
            row["url_var"].set(entry["profil_url"])
        self.progress_row.set_value(self.app.db.directory_progress(client["id"]))


class KeywordTab(BaseTab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.keywords = []
        self._build()

    def _build(self):
        self.info_label = ttk.Label(self, text="", style="Muted.TLabel", wraplength=560, justify="left")
        self.info_label.pack(fill="x", pady=(0, 8))

        zusatz_frame = ttk.Frame(self)
        zusatz_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(zusatz_frame, text="Zusaetzliche Leistungen (kommagetrennt):").pack(side="left")
        self.zusatz_var = tk.StringVar()
        ttk.Entry(zusatz_frame, textvariable=self.zusatz_var, width=36).pack(side="left", padx=8)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=(0, 8))
        ttk.Button(
            btn_frame, text="Keywords generieren", style="Primary.TButton", command=self.generate
        ).pack(side="left")
        ttk.Button(btn_frame, text="In Zwischenablage kopieren", command=self.copy_to_clipboard).pack(
            side="left", padx=8
        )
        ttk.Button(btn_frame, text="Als CSV exportieren", command=self.export_csv).pack(side="left")

        self.count_label = ttk.Label(self, text="", style="Muted.TLabel")
        self.count_label.pack(fill="x")

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, pady=(8, 0))
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 10), activestyle="none"
        )
        scrollbar.config(command=self.listbox.yview)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def load_client(self, client):
        super().load_client(client)
        self.keywords = []
        self.listbox.delete(0, "end")
        self.zusatz_var.set("")
        if client is None:
            self.info_label.config(text="")
            self.count_label.config(text="")
            return
        gewerk = client.get("gewerk", "")
        gebiet = client.get("einzugsgebiet", "")
        self.info_label.config(
            text=f"Gewerk: {gewerk or '(nicht gesetzt)'}  |  Einzugsgebiet: {gebiet or '(nicht gesetzt, bitte in Stammdaten eintragen)'}"
        )
        self.count_label.config(text="")

    def generate(self):
        if self.client is None:
            return
        gebiet = self.client.get("einzugsgebiet", "")
        if not gebiet.strip():
            messagebox.showinfo(
                "Einzugsgebiet fehlt",
                "Bitte zuerst im Tab 'Stammdaten' ein Einzugsgebiet (Orte, kommagetrennt) hinterlegen.",
            )
            return
        zusatz = [z for z in self.zusatz_var.get().split(",") if z.strip()]
        self.keywords = generate_keywords(self.client.get("gewerk", ""), gebiet, zusatz_leistungen=zusatz)
        self.listbox.delete(0, "end")
        for kw in self.keywords:
            self.listbox.insert("end", kw)
        self.count_label.config(text=f"{len(self.keywords)} Keyword-Vorschlaege generiert.")

    def copy_to_clipboard(self):
        if not self.keywords:
            messagebox.showinfo("Keine Keywords", "Bitte zuerst Keywords generieren.")
            return
        self.clipboard_clear()
        self.clipboard_append("\n".join(self.keywords))
        messagebox.showinfo("Kopiert", f"{len(self.keywords)} Keywords in die Zwischenablage kopiert.")

    def export_csv(self):
        if not self.keywords:
            messagebox.showinfo("Keine Keywords", "Bitte zuerst Keywords generieren.")
            return
        firma = (self.client or {}).get("firma", "keywords")
        default_name = f"{firma}-keywords.csv".replace(" ", "_")
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV-Datei", "*.csv")],
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Keyword"])
            for kw in self.keywords:
                writer.writerow([kw])
        messagebox.showinfo("Export erfolgreich", f"Keywords wurden gespeichert unter:\n{path}")


class ReportTab(BaseTab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.last_report_path = None
        self._build()

    def _build(self):
        ttk.Label(
            self,
            text="Erstellt einen uebersichtlichen HTML-Statusbericht fuer diesen Kunden\n"
                 "(Fortschritt, offene To-Dos, Verzeichnisstatus, Keyword-Vorschlaege).",
            style="Muted.TLabel",
            justify="left",
        ).pack(fill="x", pady=(0, 16))

        self.summary_label = ttk.Label(self, text="", justify="left", font=FONT_BOLD)
        self.summary_label.pack(fill="x", pady=(0, 16))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x")
        ttk.Button(
            btn_frame, text="Report erstellen", style="Primary.TButton", command=self.create_report
        ).pack(side="left")
        self.open_button = ttk.Button(
            btn_frame, text="Report im Browser oeffnen", command=self.open_report, state="disabled"
        )
        self.open_button.pack(side="left", padx=8)

        self.path_label = ttk.Label(self, text="", style="Muted.TLabel")
        self.path_label.pack(fill="x", pady=(12, 0))

    def load_client(self, client):
        super().load_client(client)
        self.last_report_path = None
        self.open_button.config(state="disabled")
        self.path_label.config(text="")
        if client is None:
            self.summary_label.config(text="")
            return
        gesamt, teilbereiche = self.app.db.gesamt_score(client["id"])
        teile = "   |   ".join(f"{name}: {wert}%" for name, wert in teilbereiche.items())
        self.summary_label.config(
            text=f"{client['firma']}  –  Gesamt-SEO-Score: {gesamt}/100\n{teile}"
        )

    def create_report(self):
        if self.client is None:
            return
        client = self.app.db.get_client(self.client["id"])
        path = save_report(client, self.app.db)
        self.last_report_path = os.path.abspath(path)
        self.path_label.config(text=f"Gespeichert unter: {self.last_report_path}")
        self.open_button.config(state="normal")
        messagebox.showinfo("Report erstellt", f"Report wurde erstellt:\n{self.last_report_path}")

    def open_report(self):
        if self.last_report_path:
            webbrowser.open(f"file://{self.last_report_path}")
