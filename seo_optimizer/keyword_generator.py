"""Generierung lokaler SEO-Keyword-Vorschlaege.

Kombiniert die typischen Leistungen eines Gewerks mit dem Einzugsgebiet
(Staedte/Orte) des Kunden und gaengigen lokalen Suchmustern.
"""

from seo_optimizer.data import GEWERKE, KEYWORD_MODIFIERS

# Begrenzung, wie viele Leistungen pro Gewerk in die Kombinatorik
# einfliessen, damit die Ergebnisliste uebersichtlich bleibt.
MAX_LEISTUNGEN = 6


def parse_einzugsgebiet(text):
    """Wandelt eine kommagetrennte Ortsliste in eine bereinigte Liste um."""
    if not text:
        return []
    orte = [ort.strip() for ort in text.split(",")]
    return [ort for ort in orte if ort]


def leistungen_fuer_gewerk(gewerk):
    return GEWERKE.get(gewerk, GEWERKE["Sonstiges Handwerk"])[:MAX_LEISTUNGEN]


def generate_keywords(gewerk, einzugsgebiet_text, zusatz_leistungen=None):
    """Erstellt eine sortierte, deduplizierte Liste lokaler Keyword-Vorschlaege.

    :param gewerk: Name des Gewerks (Schluessel aus GEWERKE)
    :param einzugsgebiet_text: kommagetrennte Staedte/Orte als Freitext
    :param zusatz_leistungen: optionale Liste weiterer Leistungsbegriffe
    :return: sortierte Liste eindeutiger Keyword-Strings
    """
    orte = parse_einzugsgebiet(einzugsgebiet_text)
    if not orte:
        return []

    leistungen = list(leistungen_fuer_gewerk(gewerk))
    if zusatz_leistungen:
        for leistung in zusatz_leistungen:
            leistung = leistung.strip()
            if leistung and leistung not in leistungen:
                leistungen.append(leistung)

    keywords = set()
    for ort in orte:
        for leistung in leistungen:
            for muster in KEYWORD_MODIFIERS:
                keyword = muster.format(leistung=leistung, ort=ort)
                keywords.add(keyword)

    return sorted(keywords, key=str.lower)
