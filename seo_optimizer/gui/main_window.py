"""Hauptfenster des Lokal-SEO Managers fuer Handwerksbetriebe."""

import tkinter as tk
from tkinter import ttk, messagebox

from seo_optimizer.gui.style import apply_style, COLORS, FONT_HEADER
from seo_optimizer.gui.dialogs import NeuerKundeDialog
from seo_optimizer.gui.tabs import StammdatenTab, ChecklistTab, KeywordTab, DirectoryTab, ReportTab

APP_TITEL = "Lokal-SEO Manager fuer Handwerksbetriebe"


class MainWindow(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_client_id = None

        self.title(APP_TITEL)
        self.geometry("1180x760")
        self.minsize(980, 640)

        apply_style(self)
        self._build_layout()
        self.refresh_client_list()

    # -- Layout -------------------------------------------------------

    def _build_layout(self):
        header = tk.Frame(self, bg=COLORS["primary"], height=54)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(
            header, text=APP_TITEL, bg=COLORS["primary"], fg="white", font=FONT_HEADER,
        ).pack(side="left", padx=20)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_detail_area(body)

        self.status_bar = ttk.Label(self, text=f"Datenbank: {self.db.db_path}", style="Muted.TLabel", anchor="w")
        self.status_bar.pack(fill="x", side="bottom", padx=10, pady=4)

    def _build_sidebar(self, parent):
        sidebar = ttk.Frame(parent, style="Sidebar.TFrame", width=300)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        inner = ttk.Frame(sidebar, style="Sidebar.TFrame", padding=12)
        inner.pack(fill="both", expand=True)

        ttk.Label(inner, text="Kunden", style="Sidebar.TLabel", font=("Segoe UI", 11, "bold")).pack(
            anchor="w", pady=(0, 6)
        )

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(inner, textvariable=self.search_var)
        search_entry.pack(fill="x", pady=(0, 8))
        self._set_placeholder(search_entry, "Kunde suchen...")

        columns = ("firma", "fortschritt")
        self.tree = ttk.Treeview(inner, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("firma", text="Firma / Gewerk")
        self.tree.heading("fortschritt", text="SEO %")
        self.tree.column("firma", width=200, anchor="w")
        self.tree.column("fortschritt", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_client)

        # Trace erst binden, nachdem self.tree existiert, da refresh_client_list()
        # bei jeder Aenderung des Suchfelds (auch beim Setzen des Platzhaltertexts) darauf zugreift.
        self.search_var.trace_add("write", lambda *a: self.refresh_client_list())

        btn_frame = ttk.Frame(inner, style="Sidebar.TFrame")
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="Neuer Kunde", style="Primary.TButton", command=self.neuer_kunde).pack(
            side="left"
        )
        ttk.Button(btn_frame, text="Loeschen", style="Danger.TButton", command=self.kunde_loeschen).pack(
            side="left", padx=(8, 0)
        )

    def _set_placeholder(self, entry, text):
        entry.insert(0, text)
        entry.config(foreground=COLORS["muted"])

        def on_focus_in(_event):
            if entry.get() == text:
                entry.delete(0, "end")
                entry.config(foreground=COLORS["text"])

        def on_focus_out(_event):
            if not entry.get():
                entry.insert(0, text)
                entry.config(foreground=COLORS["muted"])

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        self._placeholder_text = text

    def _build_detail_area(self, parent):
        detail = ttk.Frame(parent, padding=(16, 12))
        detail.pack(side="left", fill="both", expand=True)

        self.client_title = ttk.Label(detail, text="Bitte einen Kunden auswaehlen oder anlegen", font=FONT_HEADER)
        self.client_title.pack(anchor="w", pady=(0, 10))

        self.notebook = ttk.Notebook(detail)
        self.notebook.pack(fill="both", expand=True)

        self.tabs = {
            "Stammdaten": StammdatenTab(self.notebook, self),
            "SEO-Checkliste": ChecklistTab(self.notebook, self),
            "Keyword-Generator": KeywordTab(self.notebook, self),
            "Verzeichnisse": DirectoryTab(self.notebook, self),
            "Report": ReportTab(self.notebook, self),
        }
        for name, tab in self.tabs.items():
            self.notebook.add(tab, text=name)

        self._set_tabs_state(disabled=True)

    def _set_tabs_state(self, disabled):
        state = "disabled" if disabled else "normal"
        for i in range(len(self.tabs)):
            self.notebook.tab(i, state=state)

    # -- Datenlogik -----------------------------------------------------

    def refresh_client_list(self):
        selected_id = self.current_client_id
        for row in self.tree.get_children():
            self.tree.delete(row)

        query = self.search_var.get().strip().lower()
        if query == self._placeholder_text.lower():
            query = ""

        clients = self.db.get_clients()
        for client in clients:
            label = f"{client['firma']} ({client.get('gewerk') or '–'})"
            if query and query not in label.lower():
                continue
            gesamt, _ = self.db.checklist_progress(client["id"])
            self.tree.insert("", "end", iid=str(client["id"]), values=(label, f"{gesamt}%"))

        if selected_id is not None and self.tree.exists(str(selected_id)):
            self.tree.selection_set(str(selected_id))

    def _on_select_client(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        client_id = int(selection[0])
        if client_id == self.current_client_id:
            # Treeview wurde nur neu aufgebaut (z. B. nach Checkliste-Toggle) und die
            # bisherige Auswahl erneut gesetzt - kein echter Kundenwechsel, also nicht
            # neu laden (sonst gingen z. B. generierte Keywords/Report-Status verloren).
            return
        self.load_client(client_id)

    def load_client(self, client_id):
        client = self.db.get_client(client_id)
        if client is None:
            return
        self.current_client_id = client_id
        self.client_title.config(text=f"{client['firma']}  ·  {client.get('gewerk') or 'kein Gewerk gesetzt'}")
        self._set_tabs_state(disabled=False)
        for tab in self.tabs.values():
            tab.load_client(client)
        self.status_bar.config(text=f"Datenbank: {self.db.db_path}  |  Kunde geladen: {client['firma']}")

    def on_client_updated(self, client_id):
        self.refresh_client_list()
        if client_id == self.current_client_id:
            client = self.db.get_client(client_id)
            if client:
                self.client_title.config(
                    text=f"{client['firma']}  ·  {client.get('gewerk') or 'kein Gewerk gesetzt'}"
                )

    def neuer_kunde(self):
        dialog = NeuerKundeDialog(self)
        if not dialog.result:
            return
        client_id = self.db.add_client(dialog.result)
        self.refresh_client_list()
        self.tree.selection_set(str(client_id))
        self.load_client(client_id)

    def kunde_loeschen(self):
        if self.current_client_id is None:
            messagebox.showinfo("Kein Kunde ausgewaehlt", "Bitte zuerst einen Kunden auswaehlen.")
            return
        client = self.db.get_client(self.current_client_id)
        if not client:
            return
        if not messagebox.askyesno(
            "Kunde loeschen",
            f"Soll '{client['firma']}' inklusive aller Checklisten- und Verzeichnisdaten "
            "endgueltig geloescht werden?",
        ):
            return
        self.db.delete_client(self.current_client_id)
        self.current_client_id = None
        self.client_title.config(text="Bitte einen Kunden auswaehlen oder anlegen")
        self._set_tabs_state(disabled=True)
        for tab in self.tabs.values():
            tab.load_client(None)
        self.refresh_client_list()
