"""Wiederverwendbare kleine GUI-Bausteine."""

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    """Ein ttk.Frame mit vertikalem Scrollbalken fuer laengere Inhalte."""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.canvas = tk.Canvas(self, highlightthickness=0, background="#f4f6f8")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self._window, width=e.width),
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

    def _bind_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(3, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class ProgressRow(ttk.Frame):
    """Eine Zeile mit Beschriftung, Fortschrittsbalken und Prozentanzeige."""

    def __init__(self, parent, label_text, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text=label_text, style="Bold.TLabel").grid(row=0, column=0, sticky="w")
        self.percent_var = tk.StringVar(value="0%")
        ttk.Label(self, textvariable=self.percent_var, style="Muted.TLabel").grid(
            row=0, column=2, sticky="e", padx=(8, 0)
        )

        self.progress = ttk.Progressbar(
            self, style="Green.Horizontal.TProgressbar", maximum=100, value=0
        )
        self.progress.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 0))

    def set_value(self, prozent):
        prozent = max(0, min(100, prozent))
        self.progress["value"] = prozent
        self.percent_var.set(f"{prozent}%")
