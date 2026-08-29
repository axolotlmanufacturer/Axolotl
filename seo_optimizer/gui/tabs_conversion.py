"""Tabs zur Conversion-Maximierung: Trichter/ROI-Rechner und A/B-Test-Auswertung."""

import tkinter as tk
from tkinter import ttk, messagebox

from seo_optimizer.conversion import (
    trichter, roi, break_even_auftraege, ab_test, benoetigte_stichprobe,
    ctr_fuer_position, geschaetzte_besucher, potenzial_durch_verbesserung,
)
from seo_optimizer.gui.base import BaseTab
from seo_optimizer.gui.style import FONT_BOLD
from seo_optimizer.gui.widgets import StatTile


def _zahl(stringvar, standard=0.0):
    """Liest ein Eingabefeld als Zahl.

    Akzeptiert deutsche Schreibweise: enthaelt der Wert ein Komma, gilt dieses
    als Dezimaltrenner und Punkte gelten als Tausenderpunkte ("1.234,5").
    Ohne Komma bleibt der Punkt der Dezimaltrenner ("1234.5").
    """
    rohwert = stringvar.get().strip()
    if not rohwert:
        return standard
    if "," in rohwert:
        rohwert = rohwert.replace(".", "").replace(",", ".")
    try:
        return float(rohwert)
    except ValueError:
        raise ValueError(f"\"{stringvar.get()}\" ist keine gueltige Zahl.")


class TrichterTab(BaseTab):
    """Rechnet von Sichtbarkeit ueber Anfragen bis zu Umsatz und ROI."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        ttk.Label(
            self,
            text="Zeigt, welchen Umsatz die SEO-Massnahmen erwartbar bringen - "
                 "die Grundlage fuer das Verkaufsgespraech mit dem Handwerksbetrieb.",
            style="Muted.TLabel", wraplength=760, justify="left",
        ).pack(fill="x", pady=(0, 12))

        eingaben = ttk.Frame(self)
        eingaben.pack(fill="x")

        # Linke Spalte: Sichtbarkeit
        links = ttk.Labelframe(eingaben, text="Sichtbarkeit", padding=10)
        links.pack(side="left", fill="both", expand=True)
        links.columnconfigure(1, weight=1)

        self.suchvolumen_var = tk.StringVar(value="2000")
        self.position_var = tk.StringVar(value="8")
        self.zielposition_var = tk.StringVar(value="3")
        self._feld(links, 0, "Suchvolumen pro Monat", self.suchvolumen_var)
        self._feld(links, 1, "Aktuelle Position", self.position_var)
        self._feld(links, 2, "Zielposition", self.zielposition_var)

        # Rechte Spalte: Wirtschaftlichkeit
        rechts = ttk.Labelframe(eingaben, text="Wirtschaftlichkeit", padding=10)
        rechts.pack(side="left", fill="both", expand=True, padx=(10, 0))
        rechts.columnconfigure(1, weight=1)

        self.anfrage_rate_var = tk.StringVar(value="3")
        self.abschluss_var = tk.StringVar(value="40")
        self.auftragswert_var = tk.StringVar(value="2500")
        self.marge_var = tk.StringVar(value="25")
        self.kosten_var = tk.StringVar(value="900")
        self._feld(rechts, 0, "Anfragerate der Besucher (%)", self.anfrage_rate_var)
        self._feld(rechts, 1, "Abschlussquote der Anfragen (%)", self.abschluss_var)
        self._feld(rechts, 2, "Durchschnittlicher Auftragswert (EUR)", self.auftragswert_var)
        self._feld(rechts, 3, "Deckungsbeitrag (%)", self.marge_var)
        self._feld(rechts, 4, "SEO-Kosten pro Monat (EUR)", self.kosten_var)

        ttk.Button(self, text="Berechnen", style="Primary.TButton",
                   command=self.berechne).pack(anchor="w", pady=(12, 10))

        kacheln = ttk.Frame(self)
        kacheln.pack(fill="x")
        self.kachel_besucher = StatTile(kacheln, "Besucher/Monat (Ziel)")
        self.kachel_besucher.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.kachel_anfragen = StatTile(kacheln, "Anfragen/Monat")
        self.kachel_anfragen.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_auftraege = StatTile(kacheln, "Auftraege/Monat")
        self.kachel_auftraege.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_umsatz = StatTile(kacheln, "Umsatz/Monat")
        self.kachel_umsatz.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_roi = StatTile(kacheln, "ROI der Massnahme")
        self.kachel_roi.pack(side="left", fill="x", expand=True, padx=(6, 0))

        ergebnis = ttk.Labelframe(self, text="Auswertung", padding=10)
        ergebnis.pack(fill="both", expand=True, pady=(12, 0))
        self.ergebnis_text = tk.Text(ergebnis, wrap="word", font=("Segoe UI", 10),
                                     height=10, state="disabled")
        self.ergebnis_text.pack(fill="both", expand=True)

    def _feld(self, parent, zeile, beschriftung, variable):
        ttk.Label(parent, text=beschriftung).grid(row=zeile, column=0, sticky="w", pady=3, padx=(0, 8))
        ttk.Entry(parent, textvariable=variable, width=12).grid(row=zeile, column=1, sticky="e", pady=3)

    def load_client(self, client):
        super().load_client(client)
        self._setze_ergebnis("")
        for kachel in (self.kachel_besucher, self.kachel_anfragen, self.kachel_auftraege,
                       self.kachel_umsatz, self.kachel_roi):
            kachel.set_wert("-")

    def _setze_ergebnis(self, inhalt):
        self.ergebnis_text.config(state="normal")
        self.ergebnis_text.delete("1.0", "end")
        self.ergebnis_text.insert("1.0", inhalt)
        self.ergebnis_text.config(state="disabled")

    def berechne(self):
        try:
            suchvolumen = _zahl(self.suchvolumen_var)
            aktuelle_position = int(_zahl(self.position_var, 10))
            zielposition = int(_zahl(self.zielposition_var, 3))
            anfrage_rate = _zahl(self.anfrage_rate_var)
            abschluss = _zahl(self.abschluss_var)
            auftragswert = _zahl(self.auftragswert_var)
            marge = _zahl(self.marge_var)
            kosten = _zahl(self.kosten_var)
        except ValueError as fehler:
            messagebox.showwarning("Ungueltige Eingabe", str(fehler))
            return

        if aktuelle_position < 1 or zielposition < 1:
            messagebox.showwarning("Ungueltige Eingabe", "Positionen muessen mindestens 1 sein.")
            return

        potenzial = potenzial_durch_verbesserung(suchvolumen, aktuelle_position, zielposition)
        jetzt = trichter(potenzial["besucher_aktuell"], anfrage_rate, abschluss, auftragswert)
        ziel = trichter(potenzial["besucher_ziel"], anfrage_rate, abschluss, auftragswert)
        wirtschaftlichkeit = roi(ziel["umsatz"], marge, kosten)
        break_even = break_even_auftraege(kosten, auftragswert, marge)

        self.kachel_besucher.set_wert(ziel["besucher"], f"heute: {jetzt['besucher']}")
        self.kachel_anfragen.set_wert(ziel["anfragen"], f"heute: {jetzt['anfragen']}")
        self.kachel_auftraege.set_wert(ziel["auftraege"], f"heute: {jetzt['auftraege']}")
        self.kachel_umsatz.set_wert(f"{ziel['umsatz']:,.0f} EUR".replace(",", "."),
                                    f"heute: {jetzt['umsatz']:,.0f} EUR".replace(",", "."))
        roi_text = f"{wirtschaftlichkeit['roi_prozent']} %" if wirtschaftlichkeit["roi_prozent"] is not None else "-"
        self.kachel_roi.set_wert(roi_text, "rentabel" if wirtschaftlichkeit["rentabel"] else "nicht rentabel")

        mehrumsatz = ziel["umsatz"] - jetzt["umsatz"]
        zeilen = [
            f"Ausgangslage: Position {aktuelle_position} bei {suchvolumen:.0f} Suchanfragen/Monat",
            f"  Klickrate (Richtwert): {ctr_fuer_position(aktuelle_position) * 100:.1f} %"
            f"  ->  {jetzt['besucher']} Besucher, {jetzt['anfragen']} Anfragen, "
            f"{jetzt['auftraege']} Auftraege, {jetzt['umsatz']:,.0f} EUR Umsatz".replace(",", "."),
            "",
            f"Ziel: Position {zielposition}",
            f"  Klickrate (Richtwert): {ctr_fuer_position(zielposition) * 100:.1f} %"
            f"  ->  {ziel['besucher']} Besucher, {ziel['anfragen']} Anfragen, "
            f"{ziel['auftraege']} Auftraege, {ziel['umsatz']:,.0f} EUR Umsatz".replace(",", "."),
            "",
            f"Zusaetzliche Besucher pro Monat: {potenzial['zusaetzlich']}",
            f"Zusaetzlicher Umsatz pro Monat : {mehrumsatz:,.0f} EUR".replace(",", "."),
            f"Zusaetzlicher Umsatz pro Jahr  : {mehrumsatz * 12:,.0f} EUR".replace(",", "."),
            "",
            f"Deckungsbeitrag bei Zielposition: {wirtschaftlichkeit['deckungsbeitrag']:,.0f} EUR/Monat".replace(",", "."),
            f"SEO-Kosten                      : {wirtschaftlichkeit['kosten']:,.0f} EUR/Monat".replace(",", "."),
            f"Gewinn                          : {wirtschaftlichkeit['gewinn']:,.0f} EUR/Monat".replace(",", "."),
        ]
        if break_even is not None:
            zeilen.append(f"Break-even: ab {break_even} Auftrag/Auftraegen pro Monat tragen sich die Kosten.")
        zeilen += [
            "",
            "Hinweis: Die Klickraten sind branchenuebliche Richtwerte. Tatsaechliche Werte",
            "aus der Google Search Console liefern genauere Prognosen.",
        ]
        self._setze_ergebnis("\n".join(zeilen))


class ABTestTab(BaseTab):
    """Wertet A/B-Tests statistisch aus und plant die noetige Stichprobe."""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        ttk.Label(
            self,
            text="Prueft, ob eine Variante (z. B. neue Headline oder kuerzeres Formular) "
                 "wirklich besser konvertiert oder ob der Unterschied Zufall ist.",
            style="Muted.TLabel", wraplength=760, justify="left",
        ).pack(fill="x", pady=(0, 12))

        eingaben = ttk.Frame(self)
        eingaben.pack(fill="x")

        variante_a = ttk.Labelframe(eingaben, text="Variante A (Original)", padding=10)
        variante_a.pack(side="left", fill="both", expand=True)
        variante_a.columnconfigure(1, weight=1)
        self.besucher_a_var = tk.StringVar(value="1000")
        self.conversions_a_var = tk.StringVar(value="30")
        self._feld(variante_a, 0, "Besucher", self.besucher_a_var)
        self._feld(variante_a, 1, "Anfragen / Conversions", self.conversions_a_var)

        variante_b = ttk.Labelframe(eingaben, text="Variante B (Test)", padding=10)
        variante_b.pack(side="left", fill="both", expand=True, padx=(10, 0))
        variante_b.columnconfigure(1, weight=1)
        self.besucher_b_var = tk.StringVar(value="1000")
        self.conversions_b_var = tk.StringVar(value="45")
        self._feld(variante_b, 0, "Besucher", self.besucher_b_var)
        self._feld(variante_b, 1, "Anfragen / Conversions", self.conversions_b_var)

        ttk.Button(self, text="Test auswerten", style="Primary.TButton",
                   command=self.werte_aus).pack(anchor="w", pady=(12, 10))

        kacheln = ttk.Frame(self)
        kacheln.pack(fill="x")
        self.kachel_a = StatTile(kacheln, "Conversion-Rate A")
        self.kachel_a.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.kachel_b = StatTile(kacheln, "Conversion-Rate B")
        self.kachel_b.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_uplift = StatTile(kacheln, "Veraenderung")
        self.kachel_uplift.pack(side="left", fill="x", expand=True, padx=6)
        self.kachel_konfidenz = StatTile(kacheln, "Statistische Sicherheit")
        self.kachel_konfidenz.pack(side="left", fill="x", expand=True, padx=(6, 0))

        ergebnis = ttk.Labelframe(self, text="Ergebnis & Stichprobenplanung", padding=10)
        ergebnis.pack(fill="both", expand=True, pady=(12, 0))
        self.ergebnis_text = tk.Text(ergebnis, wrap="word", font=("Segoe UI", 10),
                                     height=9, state="disabled")
        self.ergebnis_text.pack(fill="both", expand=True)

    def _feld(self, parent, zeile, beschriftung, variable):
        ttk.Label(parent, text=beschriftung).grid(row=zeile, column=0, sticky="w", pady=3, padx=(0, 8))
        ttk.Entry(parent, textvariable=variable, width=12).grid(row=zeile, column=1, sticky="e", pady=3)

    def load_client(self, client):
        super().load_client(client)
        self._setze_ergebnis("")
        for kachel in (self.kachel_a, self.kachel_b, self.kachel_uplift, self.kachel_konfidenz):
            kachel.set_wert("-")

    def _setze_ergebnis(self, inhalt):
        self.ergebnis_text.config(state="normal")
        self.ergebnis_text.delete("1.0", "end")
        self.ergebnis_text.insert("1.0", inhalt)
        self.ergebnis_text.config(state="disabled")

    def werte_aus(self):
        try:
            besucher_a = int(_zahl(self.besucher_a_var))
            conversions_a = int(_zahl(self.conversions_a_var))
            besucher_b = int(_zahl(self.besucher_b_var))
            conversions_b = int(_zahl(self.conversions_b_var))
        except ValueError as fehler:
            messagebox.showwarning("Ungueltige Eingabe", str(fehler))
            return

        try:
            ergebnis = ab_test(besucher_a, conversions_a, besucher_b, conversions_b)
        except ValueError as fehler:
            messagebox.showwarning("Ungueltige Eingabe", str(fehler))
            return

        self.kachel_a.set_wert(f"{ergebnis['rate_a']} %", f"{conversions_a} von {besucher_a}")
        self.kachel_b.set_wert(f"{ergebnis['rate_b']} %", f"{conversions_b} von {besucher_b}")
        uplift = ergebnis["uplift_prozent"]
        self.kachel_uplift.set_wert(
            f"{uplift:+.1f} %" if uplift is not None else "-",
            "relativ zu Variante A")
        self.kachel_konfidenz.set_wert(
            f"{ergebnis['konfidenz']} %",
            "signifikant" if ergebnis["signifikant"] else "nicht signifikant")

        stichprobe = benoetigte_stichprobe(ergebnis["rate_a"], 10)
        zeilen = [
            f"Ergebnis: {ergebnis['gewinner']}",
            "",
            f"Conversion-Rate A : {ergebnis['rate_a']} %",
            f"Conversion-Rate B : {ergebnis['rate_b']} %",
            f"Relative Veraenderung: {uplift:+.1f} %" if uplift is not None else "Relative Veraenderung: -",
            f"z-Wert: {ergebnis['z_wert']}   p-Wert: {ergebnis['p_wert']}",
            "",
        ]
        if ergebnis["signifikant"]:
            zeilen.append(
                "Der Unterschied ist auf dem 95-%-Niveau statistisch signifikant. "
                "Die bessere Variante kann dauerhaft uebernommen werden.")
        else:
            zeilen.append(
                "Der Unterschied ist statistisch nicht abgesichert - er kann Zufall sein. "
                "Test weiterlaufen lassen oder groesseren Effekt testen.")
        if stichprobe:
            zeilen += [
                "",
                f"Stichprobenplanung: Um bei einer Basisrate von {ergebnis['rate_a']} % eine "
                f"Verbesserung von 10 % nachzuweisen, werden rund {stichprobe:,} Besucher "
                f"je Variante benoetigt (95 % Konfidenz, 80 % Power).".replace(",", "."),
            ]
        self._setze_ergebnis("\n".join(zeilen))
