"""Werkzeuge zur Conversion-Maximierung: Trichterrechnung, ROI und A/B-Tests."""

import math

from seo_optimizer.data_seo import (
    CTR_JE_POSITION, CTR_POSITION_11_20, CTR_POSITION_AB_21,
)


def ctr_fuer_position(position):
    """Richtwert der organischen Klickrate fuer eine Google-Position."""
    if position is None or position < 1:
        return 0.0
    if position in CTR_JE_POSITION:
        return CTR_JE_POSITION[position]
    if position <= 20:
        return CTR_POSITION_11_20
    return CTR_POSITION_AB_21


def geschaetzte_besucher(suchvolumen, position):
    """Schaetzt die monatlichen Besucher aus Suchvolumen und Ranking-Position."""
    return round(max(0, suchvolumen) * ctr_fuer_position(position))


def potenzial_durch_verbesserung(suchvolumen, aktuelle_position, ziel_position):
    """Zusaetzliche Besucher, wenn ein Keyword von A auf B verbessert wird."""
    jetzt = geschaetzte_besucher(suchvolumen, aktuelle_position)
    ziel = geschaetzte_besucher(suchvolumen, ziel_position)
    return {
        "besucher_aktuell": jetzt,
        "besucher_ziel": ziel,
        "zusaetzlich": ziel - jetzt,
    }


def trichter(besucher, anfrage_rate, abschlussquote, auftragswert):
    """Berechnet den Weg vom Besucher zum Umsatz.

    :param besucher: monatliche Besucher der Website
    :param anfrage_rate: Anteil der Besucher, die anfragen (in Prozent)
    :param abschlussquote: Anteil der Anfragen, die zum Auftrag werden (in Prozent)
    :param auftragswert: durchschnittlicher Auftragswert in Euro
    """
    besucher = max(0, besucher)
    anfragen = besucher * max(0.0, anfrage_rate) / 100
    auftraege = anfragen * max(0.0, abschlussquote) / 100
    umsatz = auftraege * max(0.0, auftragswert)
    return {
        "besucher": round(besucher),
        "anfragen": round(anfragen, 1),
        "auftraege": round(auftraege, 1),
        "umsatz": round(umsatz, 2),
        "umsatz_je_besucher": round(umsatz / besucher, 2) if besucher else 0.0,
    }


def roi(umsatz, marge_prozent, kosten):
    """Wirtschaftlichkeit einer SEO-Massnahme.

    :param umsatz: erwarteter Umsatz im Betrachtungszeitraum
    :param marge_prozent: Deckungsbeitrag in Prozent des Umsatzes
    :param kosten: Kosten der SEO-Massnahme im gleichen Zeitraum
    """
    deckungsbeitrag = umsatz * max(0.0, marge_prozent) / 100
    gewinn = deckungsbeitrag - kosten
    roi_prozent = (gewinn / kosten * 100) if kosten > 0 else None
    return {
        "deckungsbeitrag": round(deckungsbeitrag, 2),
        "kosten": round(kosten, 2),
        "gewinn": round(gewinn, 2),
        "roi_prozent": round(roi_prozent, 1) if roi_prozent is not None else None,
        "rentabel": gewinn > 0,
    }


def break_even_auftraege(kosten, auftragswert, marge_prozent):
    """Wie viele Auftraege noetig sind, damit sich die Massnahme traegt."""
    deckungsbeitrag_je_auftrag = auftragswert * max(0.0, marge_prozent) / 100
    if deckungsbeitrag_je_auftrag <= 0:
        return None
    return math.ceil(kosten / deckungsbeitrag_je_auftrag)


# ---------------------------------------------------------------------------
# A/B-Test-Auswertung
# ---------------------------------------------------------------------------

def _normal_cdf(x):
    """Verteilungsfunktion der Standardnormalverteilung."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def ab_test(besucher_a, conversions_a, besucher_b, conversions_b, konfidenz=0.95):
    """Wertet einen A/B-Test mit einem zweiseitigen Z-Test fuer zwei Anteile aus.

    :return: dict mit Conversion-Raten, Uplift, z-Wert, p-Wert und Signifikanz
    :raises ValueError: bei unplausiblen Eingaben
    """
    if besucher_a <= 0 or besucher_b <= 0:
        raise ValueError("Die Besucherzahlen beider Varianten muessen groesser als 0 sein.")
    if not (0 <= conversions_a <= besucher_a) or not (0 <= conversions_b <= besucher_b):
        raise ValueError("Conversions duerfen nicht negativ und nicht groesser als die Besucher sein.")

    rate_a = conversions_a / besucher_a
    rate_b = conversions_b / besucher_b
    gepoolt = (conversions_a + conversions_b) / (besucher_a + besucher_b)

    standardfehler = math.sqrt(gepoolt * (1 - gepoolt) * (1 / besucher_a + 1 / besucher_b))
    if standardfehler == 0:
        z_wert = 0.0
        p_wert = 1.0
    else:
        z_wert = (rate_b - rate_a) / standardfehler
        p_wert = 2 * (1 - _normal_cdf(abs(z_wert)))

    alpha = 1 - konfidenz
    uplift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else None

    return {
        "rate_a": round(rate_a * 100, 2),
        "rate_b": round(rate_b * 100, 2),
        "uplift_prozent": round(uplift, 1) if uplift is not None else None,
        "z_wert": round(z_wert, 3),
        "p_wert": round(p_wert, 4),
        "signifikant": p_wert < alpha,
        "konfidenz": round((1 - p_wert) * 100, 1),
        "gewinner": _gewinner(rate_a, rate_b, p_wert, alpha),
    }


def _gewinner(rate_a, rate_b, p_wert, alpha):
    if p_wert >= alpha:
        return "Kein signifikanter Unterschied"
    return "Variante B" if rate_b > rate_a else "Variante A"


def benoetigte_stichprobe(basis_rate, minimaler_effekt, konfidenz=0.95, power=0.8):
    """Naeherung der noetigen Besucher je Variante fuer einen A/B-Test.

    :param basis_rate: aktuelle Conversion-Rate in Prozent
    :param minimaler_effekt: relativer Mindesteffekt in Prozent (z. B. 10 fuer +10 %)
    :return: benoetigte Besucher je Variante oder None bei unplausiblen Eingaben
    """
    p1 = basis_rate / 100
    if not 0 < p1 < 1 or minimaler_effekt <= 0:
        return None
    p2 = p1 * (1 + minimaler_effekt / 100)
    if p2 >= 1:
        return None

    # z-Werte fuer die gaengigen Schwellen (zweiseitig bzw. einseitig fuer die Power).
    z_alpha = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}.get(round(konfidenz, 2), 1.960)
    z_beta = {0.80: 0.842, 0.90: 1.282}.get(round(power, 2), 0.842)

    differenz = abs(p2 - p1)
    mittel = (p1 + p2) / 2
    zaehler = (z_alpha * math.sqrt(2 * mittel * (1 - mittel))
               + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return math.ceil(zaehler / (differenz ** 2))
