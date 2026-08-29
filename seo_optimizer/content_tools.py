"""Werkzeuge fuer die Content-Produktion: Textanalyse und Content-Briefings."""

import re
from collections import Counter

from seo_optimizer.data import GEWERKE
from seo_optimizer.data_seo import (
    STOPWORDS_DE, W_FRAGEN, WORTZIEL_JE_TYP, SUCHINTENTIONEN,
)

_SATZ_RE = re.compile(r"[.!?]+(?:\s|$)")
_WORT_RE = re.compile(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß\-]*", re.UNICODE)
_VOKALGRUPPEN_RE = re.compile(r"[aeiouyäöü]+", re.IGNORECASE)


def zaehle_silben(wort):
    """Naeherung der Silbenzahl eines deutschen Wortes ueber Vokalgruppen."""
    treffer = _VOKALGRUPPEN_RE.findall(wort.lower())
    return max(1, len(treffer))


def zaehle_saetze(text):
    """Anzahl der Saetze; ein Text ohne Satzzeichen gilt als ein Satz."""
    saetze = [s for s in _SATZ_RE.split(text) if s.strip()]
    return max(1, len(saetze))


def flesch_reading_ease(text):
    """Flesch-Reading-Ease in der deutschen Fassung nach Amstad.

    Formel: 180 - ASL - (58,5 * ASW)
    ASL = Woerter je Satz, ASW = Silben je Wort.
    Ergebnis 0 (sehr schwer) bis 100 (sehr leicht).
    """
    woerter = _WORT_RE.findall(text)
    if not woerter:
        return 0.0
    saetze = zaehle_saetze(text)
    asl = len(woerter) / saetze
    asw = sum(zaehle_silben(w) for w in woerter) / len(woerter)
    wert = 180 - asl - (58.5 * asw)
    return round(max(0.0, min(100.0, wert)), 1)


def lesbarkeit_label(wert):
    """Ordnet einen Flesch-Wert einer Verstaendlichkeitsstufe zu."""
    if wert >= 80:
        return "Sehr leicht (Grundschule)"
    if wert >= 70:
        return "Leicht - gut fuer Kundentexte"
    if wert >= 60:
        return "Mittel - gut verstaendlich"
    if wert >= 50:
        return "Anspruchsvoll"
    if wert >= 30:
        return "Schwer (Fachtext)"
    return "Sehr schwer - dringend vereinfachen"


def keyword_dichte(text, keyword):
    """Vorkommen und Dichte (in Prozent) eines Keywords im Text."""
    woerter = _WORT_RE.findall(text)
    if not woerter or not keyword.strip():
        return 0, 0.0
    treffer = len(re.findall(re.escape(keyword.strip()), text, flags=re.IGNORECASE))
    dichte = treffer / len(woerter) * 100
    return treffer, round(dichte, 2)


def dichte_bewertung(dichte):
    """Bewertet die Keyword-Dichte nach gaengiger SEO-Praxis."""
    if dichte == 0:
        return "Keyword fehlt im Text"
    if dichte < 0.5:
        return "Sehr niedrig - Keyword haeufiger einbauen"
    if dichte <= 2.5:
        return "Optimal"
    if dichte <= 4:
        return "Erhoeht - etwas reduzieren"
    return "Ueberoptimiert - Keyword-Stuffing vermeiden"


def haeufigste_begriffe(text, anzahl=12, min_laenge=4):
    """Haeufigste inhaltstragende Begriffe (ohne Stoppwoerter)."""
    woerter = [w.lower() for w in _WORT_RE.findall(text)]
    gefiltert = [
        w for w in woerter
        if len(w) >= min_laenge and w not in STOPWORDS_DE
    ]
    return Counter(gefiltert).most_common(anzahl)


def lange_saetze(text, grenze=20):
    """Liefert Saetze, die mehr als `grenze` Woerter enthalten."""
    rohsaetze = [s.strip() for s in _SATZ_RE.split(text) if s.strip()]
    return [s for s in rohsaetze if len(_WORT_RE.findall(s)) > grenze]


def analysiere_text(text, fokus_keyword=""):
    """Vollstaendige Textanalyse fuer die Content-Produktion."""
    woerter = _WORT_RE.findall(text)
    anzahl_woerter = len(woerter)
    anzahl_saetze = zaehle_saetze(text) if anzahl_woerter else 0
    flesch = flesch_reading_ease(text)
    treffer, dichte = keyword_dichte(text, fokus_keyword)
    zu_lang = lange_saetze(text)

    return {
        "woerter": anzahl_woerter,
        "saetze": anzahl_saetze,
        "zeichen": len(text),
        "woerter_je_satz": round(anzahl_woerter / anzahl_saetze, 1) if anzahl_saetze else 0,
        "lesbarkeit": flesch,
        "lesbarkeit_label": lesbarkeit_label(flesch),
        "keyword_treffer": treffer,
        "keyword_dichte": dichte,
        "dichte_bewertung": dichte_bewertung(dichte) if fokus_keyword.strip() else "Kein Fokus-Keyword angegeben",
        "lange_saetze": len(zu_lang),
        "lange_saetze_beispiele": zu_lang[:3],
        "begriffe": haeufigste_begriffe(text),
        "lesezeit_minuten": max(1, round(anzahl_woerter / 200)) if anzahl_woerter else 0,
    }


def empfehlungen_zum_text(analyse, wortziel=None):
    """Leitet konkrete Handlungsempfehlungen aus einer Textanalyse ab."""
    tipps = []
    if wortziel and analyse["woerter"] < wortziel:
        fehlend = wortziel - analyse["woerter"]
        tipps.append(f"Text um rund {fehlend} Woerter erweitern, um das Ziel von {wortziel} zu erreichen.")
    if analyse["lesbarkeit"] < 50:
        tipps.append("Saetze kuerzen und Fachbegriffe erklaeren - der Text ist schwer verstaendlich.")
    if analyse["woerter_je_satz"] > 20:
        tipps.append(f"Durchschnittlich {analyse['woerter_je_satz']} Woerter je Satz - auf unter 20 senken.")
    if analyse["lange_saetze"]:
        tipps.append(f"{analyse['lange_saetze']} sehr lange Saetze aufteilen.")
    if analyse["dichte_bewertung"] == "Keyword fehlt im Text":
        tipps.append("Fokus-Keyword in Ueberschrift, Einleitung und Fliesstext einbauen.")
    elif analyse["keyword_dichte"] > 2.5:
        tipps.append("Keyword-Dichte senken und stattdessen Synonyme verwenden.")
    elif 0 < analyse["keyword_dichte"] < 0.5:
        tipps.append("Fokus-Keyword etwas haeufiger verwenden (Ziel: 0,5-2,5 %).")
    if analyse["woerter"] < 300:
        tipps.append("Unter 300 Woerter ranken Seiten selten - Inhalt vertiefen.")
    if not tipps:
        tipps.append("Text erfuellt die wichtigsten Qualitaetskriterien.")
    return tipps


# ---------------------------------------------------------------------------
# Content-Briefing
# ---------------------------------------------------------------------------

def erstelle_briefing(fokus_keyword, gewerk="", ort="", typ="Leistungsseite"):
    """Erstellt ein vollstaendiges Content-Briefing fuer einen Redakteur."""
    keyword = fokus_keyword.strip()
    if not keyword:
        return None

    ortszusatz = f" {ort.strip()}" if ort.strip() else ""
    wortziel = WORTZIEL_JE_TYP.get(typ, 800)
    leistungen = GEWERKE.get(gewerk, GEWERKE["Sonstiges Handwerk"])

    title = f"{keyword.capitalize()}{ortszusatz} - Meisterbetrieb mit Festpreis"
    if len(title) > 60:
        title = f"{keyword.capitalize()}{ortszusatz} - Meisterbetrieb"

    meta = (
        f"{keyword.capitalize()}{ortszusatz} vom Meisterbetrieb: Beratung, Festpreis und "
        f"schnelle Termine. Jetzt kostenloses Angebot anfordern."
    )[:160]

    gliederung = [
        f"H1: {keyword.capitalize()}{ortszusatz} vom Meisterbetrieb",
        "H2: Unsere Leistungen im Ueberblick",
        f"H2: Was kostet {keyword}? - Preisbeispiele und Einflussfaktoren",
        "H2: So laeuft die Zusammenarbeit ab (in 4 Schritten)",
        "H2: Referenzen aus der Region mit Vorher-Nachher-Bildern",
        "H2: Haeufige Fragen (FAQ)",
        "H2: Jetzt unverbindliches Angebot anfordern",
    ]
    if ort.strip():
        gliederung.insert(5, f"H2: Warum Kunden in {ort.strip()} uns waehlen")

    semantische_begriffe = sorted({
        *[l.lower() for l in leistungen[:6]],
        "meisterbetrieb", "festpreis", "kostenvoranschlag", "beratung",
        "termin", "garantie", "innung", "referenzen",
    })

    w_fragen = [muster.format(keyword=keyword) for muster in W_FRAGEN]

    return {
        "fokus_keyword": keyword,
        "typ": typ,
        "wortziel": wortziel,
        "suchintention": _intention_zu_typ(typ),
        "title_vorschlag": title,
        "meta_vorschlag": meta,
        "url_vorschlag": "/" + _slug(keyword + ortszusatz),
        "gliederung": gliederung,
        "semantische_begriffe": semantische_begriffe,
        "w_fragen": w_fragen,
        "interne_links": [
            "Von der Startseite auf diese Seite verlinken",
            "Aus passenden Ratgeberbeitraegen hierher verlinken",
            "Auf Kontakt-/Angebotsseite verlinken",
            "Auf zwei thematisch verwandte Leistungsseiten verlinken",
        ],
        "medien": [
            "Mindestens 3 eigene Projektfotos mit Alt-Text",
            "Ein Foto des Teams oder des Inhabers",
            "Optional: kurzes Video zur Arbeitsweise",
        ],
        "cta": f"Jetzt kostenloses Angebot fuer {keyword}{ortszusatz} anfordern - Rueckmeldung innerhalb von 24 Stunden.",
        "hinweise": [
            f"Fokus-Keyword \"{keyword}\" in Title, H1, Einleitung und Meta-Description verwenden.",
            "Keyword-Dichte zwischen 0,5 und 2,5 % halten, Synonyme einsetzen.",
            "Kurze Absaetze (max. 4 Zeilen) und Zwischenueberschriften nutzen.",
            "FAQ-Bereich mit FAQPage-Schema auszeichnen.",
            "Telefonnummer und Formular oberhalb des Falzes platzieren.",
        ],
    }


def _intention_zu_typ(typ):
    zuordnung = {
        "Leistungsseite": "Kommerziell (Vergleich)",
        "Standort-Landingpage": "Transaktional (Auftrag)",
        "Ratgeber / Blogbeitrag": "Informativ (Wissen)",
        "Referenz / Projektbericht": "Kommerziell (Vergleich)",
        "FAQ-Seite": "Informativ (Wissen)",
        "Pillar-Page": "Informativ (Wissen)",
        "Video / Bildstrecke": "Informativ (Wissen)",
        "Pressemitteilung": "Navigational (Marke)",
    }
    intention = zuordnung.get(typ, "Kommerziell (Vergleich)")
    return f"{intention} - {SUCHINTENTIONEN.get(intention, '')}"


def _slug(text):
    text = text.lower().strip()
    ersetzungen = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}
    for alt, neu in ersetzungen.items():
        text = text.replace(alt, neu)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def briefing_als_text(briefing):
    """Formatiert ein Briefing als reinen Text (fuer Export/Zwischenablage)."""
    if not briefing:
        return ""
    zeilen = [
        "CONTENT-BRIEFING",
        "=" * 60,
        f"Fokus-Keyword : {briefing['fokus_keyword']}",
        f"Inhaltstyp    : {briefing['typ']}",
        f"Suchintention : {briefing['suchintention']}",
        f"Wortziel      : ca. {briefing['wortziel']} Woerter",
        f"URL-Vorschlag : {briefing['url_vorschlag']}",
        "",
        "TITLE-VORSCHLAG",
        f"  {briefing['title_vorschlag']} ({len(briefing['title_vorschlag'])} Zeichen)",
        "",
        "META-DESCRIPTION",
        f"  {briefing['meta_vorschlag']} ({len(briefing['meta_vorschlag'])} Zeichen)",
        "",
        "GLIEDERUNG",
    ]
    zeilen += [f"  {eintrag}" for eintrag in briefing["gliederung"]]
    zeilen += ["", "ZU BEANTWORTENDE FRAGEN"]
    zeilen += [f"  - {frage}" for frage in briefing["w_fragen"]]
    zeilen += ["", "SEMANTISCHE BEGRIFFE"]
    zeilen += ["  " + ", ".join(briefing["semantische_begriffe"])]
    zeilen += ["", "INTERNE VERLINKUNG"]
    zeilen += [f"  - {eintrag}" for eintrag in briefing["interne_links"]]
    zeilen += ["", "MEDIEN"]
    zeilen += [f"  - {eintrag}" for eintrag in briefing["medien"]]
    zeilen += ["", "HANDLUNGSAUFFORDERUNG (CTA)", f"  {briefing['cta']}"]
    zeilen += ["", "REDAKTIONELLE HINWEISE"]
    zeilen += [f"  - {eintrag}" for eintrag in briefing["hinweise"]]
    return "\n".join(zeilen)
