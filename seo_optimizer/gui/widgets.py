"""Wiederverwendbare kleine GUI-Bausteine."""

import tkinter as tk
from tkinter import ttk

from seo_optimizer.gui.style import COLORS, FONT_SMALL, FONT_BOLD


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


class StatTile(ttk.Frame):
    """Kleine Kachel fuer eine einzelne Kennzahl (Wert gross, Beschriftung klein)."""

    def __init__(self, parent, label_text, wert="-", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.wert_var = tk.StringVar(value=str(wert))
        self.hinweis_var = tk.StringVar(value="")

        box = tk.Frame(self, bg="white", highlightbackground=COLORS["border"],
                       highlightthickness=1, padx=14, pady=10)
        box.pack(fill="both", expand=True)

        tk.Label(box, textvariable=self.wert_var, bg="white", fg=COLORS["primary"],
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(box, text=label_text, bg="white", fg=COLORS["muted"],
                 font=FONT_SMALL).pack(anchor="w")
        self._hinweis = tk.Label(box, textvariable=self.hinweis_var, bg="white",
                                 fg=COLORS["muted"], font=FONT_SMALL)
        self._hinweis.pack(anchor="w")

    def set_wert(self, wert, hinweis=""):
        self.wert_var.set(str(wert))
        self.hinweis_var.set(hinweis)


class RankingChart(tk.Canvas):
    """Einfaches Liniendiagramm des Ranking-Verlaufs (Position ueber Zeit).

    Die y-Achse ist invertiert: Position 1 liegt oben, da eine kleinere
    Position ein besseres Ranking bedeutet.
    """

    RAND_LINKS = 42
    RAND_RECHTS = 14
    RAND_OBEN = 16
    RAND_UNTEN = 28

    def __init__(self, parent, hoehe=220, **kwargs):
        super().__init__(parent, height=hoehe, background="white",
                         highlightbackground=COLORS["border"], highlightthickness=1, **kwargs)
        self._punkte = []
        self._titel = ""
        self.bind("<Configure>", lambda e: self._zeichne())

    def set_daten(self, punkte, titel=""):
        """:param punkte: Liste von (datum_string, position)"""
        self._punkte = [(d, p) for d, p in punkte if p is not None]
        self._titel = titel
        self._zeichne()

    def _zeichne(self):
        self.delete("all")
        breite = self.winfo_width()
        hoehe = self.winfo_height()
        if breite < 60 or hoehe < 60:
            return

        if not self._punkte:
            self.create_text(breite / 2, hoehe / 2, text="Keine Ranking-Daten vorhanden",
                             fill=COLORS["muted"], font=FONT_SMALL)
            return

        positionen = [p for _, p in self._punkte]
        max_pos = max(max(positionen), 10)
        min_pos = 1

        plot_breite = breite - self.RAND_LINKS - self.RAND_RECHTS
        plot_hoehe = hoehe - self.RAND_OBEN - self.RAND_UNTEN

        def x_fuer(index):
            if len(self._punkte) == 1:
                return self.RAND_LINKS + plot_breite / 2
            return self.RAND_LINKS + plot_breite * index / (len(self._punkte) - 1)

        def y_fuer(position):
            anteil = (position - min_pos) / (max_pos - min_pos) if max_pos > min_pos else 0
            return self.RAND_OBEN + anteil * plot_hoehe

        # Gitternetz und Achsenbeschriftung
        for position in self._achsenwerte(max_pos):
            y = y_fuer(position)
            self.create_line(self.RAND_LINKS, y, breite - self.RAND_RECHTS, y,
                             fill=COLORS["border"])
            self.create_text(self.RAND_LINKS - 8, y, text=str(position), anchor="e",
                             fill=COLORS["muted"], font=FONT_SMALL)

        # Top-10-Bereich hervorheben
        if max_pos > 10:
            self.create_rectangle(self.RAND_LINKS, y_fuer(1), breite - self.RAND_RECHTS,
                                  y_fuer(10), fill="#eaf6ee", outline="")
            self.tag_lower("all")

        # Linie und Punkte
        koordinaten = []
        for index, (_, position) in enumerate(self._punkte):
            koordinaten.extend([x_fuer(index), y_fuer(position)])
        if len(koordinaten) >= 4:
            self.create_line(*koordinaten, fill=COLORS["primary"], width=2, smooth=False)

        for index, (datum, position) in enumerate(self._punkte):
            x, y = x_fuer(index), y_fuer(position)
            self.create_oval(x - 4, y - 4, x + 4, y + 4,
                             fill=COLORS["accent"], outline="white", width=2)

        # x-Achse: erstes und letztes Datum
        self.create_text(self.RAND_LINKS, hoehe - self.RAND_UNTEN + 14,
                         text=self._punkte[0][0], anchor="w",
                         fill=COLORS["muted"], font=FONT_SMALL)
        if len(self._punkte) > 1:
            self.create_text(breite - self.RAND_RECHTS, hoehe - self.RAND_UNTEN + 14,
                             text=self._punkte[-1][0], anchor="e",
                             fill=COLORS["muted"], font=FONT_SMALL)

        if self._titel:
            self.create_text(self.RAND_LINKS, 8, text=self._titel, anchor="w",
                             fill=COLORS["text"], font=FONT_BOLD)

    @staticmethod
    def _achsenwerte(max_pos):
        """Sinnvolle Positionswerte fuer die y-Achse."""
        kandidaten = [1, 3, 5, 10, 20, 30, 50, 100]
        werte = [k for k in kandidaten if k <= max_pos]
        if max_pos not in werte:
            werte.append(max_pos)
        return werte
