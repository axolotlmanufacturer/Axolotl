"""Modale Dialoge des Lokal-SEO Managers."""

import tkinter as tk
from tkinter import ttk

from seo_optimizer.data import GEWERKE
from seo_optimizer.gui.style import FONT_BOLD


class NeuerKundeDialog(tk.Toplevel):
    """Modaler Dialog zum Anlegen eines neuen Kunden (Basisdaten)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Neuen Kunden anlegen")
        self.resizable(False, False)
        self.transient(parent)
        self.result = None

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Neuen Kunden anlegen", font=FONT_BOLD).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        ttk.Label(frame, text="Firmenname *").grid(row=1, column=0, sticky="w", pady=4)
        self.firma_var = tk.StringVar()
        firma_entry = ttk.Entry(frame, textvariable=self.firma_var, width=34)
        firma_entry.grid(row=1, column=1, pady=4, sticky="ew")

        ttk.Label(frame, text="Gewerk").grid(row=2, column=0, sticky="w", pady=4)
        self.gewerk_var = tk.StringVar(value=list(GEWERKE.keys())[0])
        gewerk_box = ttk.Combobox(
            frame, textvariable=self.gewerk_var, values=list(GEWERKE.keys()),
            state="readonly", width=32,
        )
        gewerk_box.grid(row=2, column=1, pady=4, sticky="ew")

        ttk.Label(frame, text="Ort").grid(row=3, column=0, sticky="w", pady=4)
        self.ort_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.ort_var, width=34).grid(row=3, column=1, pady=4, sticky="ew")

        self.error_label = ttk.Label(frame, text="", foreground="#b3261e")
        self.error_label.grid(row=4, column=0, columnspan=2, sticky="w")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(16, 0), sticky="e")
        ttk.Button(btn_frame, text="Abbrechen", command=self._abbrechen).pack(side="right", padx=(8, 0))
        ttk.Button(btn_frame, text="Anlegen", style="Primary.TButton", command=self._anlegen).pack(side="right")

        firma_entry.focus_set()
        self.bind("<Return>", lambda e: self._anlegen())
        self.bind("<Escape>", lambda e: self._abbrechen())

        self.grab_set()
        self.wait_window(self)

    def _anlegen(self):
        firma = self.firma_var.get().strip()
        if not firma:
            self.error_label.config(text="Bitte einen Firmennamen eingeben.")
            return
        self.result = {
            "firma": firma,
            "gewerk": self.gewerk_var.get(),
            "ort": self.ort_var.get().strip(),
        }
        self.destroy()

    def _abbrechen(self):
        self.result = None
        self.destroy()
