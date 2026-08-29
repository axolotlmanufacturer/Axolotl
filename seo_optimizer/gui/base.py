"""Basisklassen fuer die Kunden-Tabs."""

from tkinter import ttk


class BaseTab(ttk.Frame):
    """Gemeinsame Basis fuer alle Kunden-Tabs.

    `load_client` wird vom Hauptfenster aufgerufen, sobald ein Kunde
    ausgewaehlt (oder mit None abgewaehlt) wird.
    """

    def __init__(self, parent, app, padding=16):
        super().__init__(parent, padding=padding)
        self.app = app
        self.client = None

    def load_client(self, client):
        self.client = client


class GroupTab(BaseTab):
    """Ein Tab, der mehrere Unter-Tabs in einem eigenen Notebook buendelt.

    Haelt die Zahl der Haupt-Reiter klein und die Oberflaeche uebersichtlich.
    """

    def __init__(self, parent, app):
        super().__init__(parent, app, padding=0)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self.subtabs = {}

    def add_subtab(self, name, tab):
        self.subtabs[name] = tab
        self.notebook.add(tab, text=name)
        return tab

    def load_client(self, client):
        super().load_client(client)
        for tab in self.subtabs.values():
            tab.load_client(client)
