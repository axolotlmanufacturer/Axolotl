"""OnPage-Analyse einer Webseite (technisches SEO + OnPage + Conversion-Signale).

Ruft eine URL ab, parst das HTML mit der Standardbibliothek und prueft
die wichtigsten SEO-Kriterien. Es werden keine externen Pakete benoetigt.
"""

import json
import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

USER_AGENT = "Mozilla/5.0 (compatible; LokalSEOManager/2.0; +Website-Audit)"
TIMEOUT = 15
MAX_BYTES = 3_000_000  # Schutz vor sehr grossen Antworten

# Schweregrade und ihre Gewichtung im Gesamtscore.
KRITISCH = "kritisch"
WARNUNG = "warnung"
HINWEIS = "hinweis"
OK = "ok"

GEWICHTE = {KRITISCH: 3, WARNUNG: 2, HINWEIS: 1}

# Ignorierte Elemente bei der Textextraktion.
_NICHT_TEXT_TAGS = {"script", "style", "noscript", "template", "svg"}

_TELEFON_RE = re.compile(r"(\+49|0)[\s/\-()]?\d[\d\s/\-()]{6,}\d")


class _SeitenParser(HTMLParser):
    """Extrahiert die fuer die SEO-Analyse relevanten Bestandteile einer HTML-Seite."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self._in_title = False
        self.meta = {}
        self.og = {}
        self.canonical = None
        self.lang = None
        self.headings = []           # Liste von (level, text)
        self._heading_level = None
        self._heading_text = []
        self.images = []             # Liste von dicts mit src/alt
        self.links = []              # Liste von dicts mit href/text/rel
        self._link_href = None
        self._link_rel = None
        self._link_text = []
        self.jsonld = []
        self._in_jsonld = False
        self._jsonld_buffer = []
        self._skip_depth = 0
        self._text_parts = []
        self.hat_formular = False
        self.hat_viewport = False

    # -- Tag-Handling ----------------------------------------------------

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in _NICHT_TEXT_TAGS:
            if tag == "script" and attrs.get("type") == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_buffer = []
            self._skip_depth += 1
            return

        if tag == "html":
            self.lang = attrs.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (attrs.get("name") or "").lower()
            prop = (attrs.get("property") or "").lower()
            content = attrs.get("content", "")
            if name:
                self.meta[name] = content
            if prop.startswith("og:"):
                self.og[prop] = content
            if name == "viewport":
                self.hat_viewport = True
        elif tag == "link":
            rel = (attrs.get("rel") or "").lower()
            if "canonical" in rel:
                self.canonical = attrs.get("href")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading_level = int(tag[1])
            self._heading_text = []
        elif tag == "img":
            self.images.append({"src": attrs.get("src", ""), "alt": attrs.get("alt")})
        elif tag == "a":
            self._link_href = attrs.get("href")
            self._link_rel = (attrs.get("rel") or "").lower()
            self._link_text = []
        elif tag == "form":
            self.hat_formular = True

    def handle_endtag(self, tag):
        if tag in _NICHT_TEXT_TAGS:
            if tag == "script" and self._in_jsonld:
                self._speichere_jsonld()
            self._skip_depth = max(0, self._skip_depth - 1)
            return

        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._heading_level:
            text = " ".join("".join(self._heading_text).split())
            self.headings.append((self._heading_level, text))
            self._heading_level = None
        elif tag == "a" and self._link_href is not None:
            text = " ".join("".join(self._link_text).split())
            self.links.append({"href": self._link_href, "text": text, "rel": self._link_rel or ""})
            self._link_href = None

    def handle_data(self, data):
        if self._in_jsonld:
            self._jsonld_buffer.append(data)
            return
        if self._skip_depth:
            return
        if self._in_title:
            self.title = (self.title or "") + data
        if self._heading_level:
            self._heading_text.append(data)
        if self._link_href is not None:
            self._link_text.append(data)
        self._text_parts.append(data)

    def _speichere_jsonld(self):
        self._in_jsonld = False
        rohtext = "".join(self._jsonld_buffer).strip()
        self._jsonld_buffer = []
        if not rohtext:
            return
        try:
            self.jsonld.append(json.loads(rohtext))
        except (ValueError, TypeError):
            # Ungueltiges JSON-LD wird als eigener Befund gemeldet.
            self.jsonld.append({"__ungueltig__": True})

    # -- Ergebnis --------------------------------------------------------

    @property
    def text(self):
        return " ".join(" ".join(self._text_parts).split())


class AuditFehler(Exception):
    """Die Seite konnte nicht abgerufen oder ausgewertet werden."""


def lade_seite(url, timeout=TIMEOUT):
    """Ruft eine URL ab und liefert (html, statuscode, ladezeit, finale_url, groesse)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise AuditFehler("Bitte eine vollstaendige URL mit http:// oder https:// angeben.")

    anfrage = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(anfrage, timeout=timeout) as antwort:
            rohdaten = antwort.read(MAX_BYTES)
            ladezeit = time.monotonic() - start
            finale_url = antwort.geturl()
            status = antwort.status
            zeichensatz = antwort.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as fehler:
        raise AuditFehler(f"Server antwortete mit HTTP {fehler.code} ({fehler.reason}).") from fehler
    except urllib.error.URLError as fehler:
        raise AuditFehler(f"Seite nicht erreichbar: {fehler.reason}") from fehler
    except (TimeoutError, OSError) as fehler:
        raise AuditFehler(f"Abruf fehlgeschlagen: {fehler}") from fehler

    html_text = rohdaten.decode(zeichensatz, errors="replace")
    return html_text, status, ladezeit, finale_url, len(rohdaten)


def _befund(titel, schwere, hinweis="", empfehlung=""):
    return {"titel": titel, "schwere": schwere, "hinweis": hinweis, "empfehlung": empfehlung}


def _pruefe_title(parser, fokus_keyword, befunde):
    title = (parser.title or "").strip()
    if not title:
        befunde.append(_befund(
            "Title-Tag", KRITISCH, "Kein Title-Tag gefunden.",
            "Title mit Fokus-Keyword und Ort ergaenzen (30-60 Zeichen)."))
        return
    laenge = len(title)
    if laenge < 30:
        befunde.append(_befund(
            "Title-Tag", WARNUNG, f"Title ist mit {laenge} Zeichen sehr kurz: \"{title}\"",
            "Auf 30-60 Zeichen erweitern und Leistung + Ort aufnehmen."))
    elif laenge > 60:
        befunde.append(_befund(
            "Title-Tag", WARNUNG, f"Title ist mit {laenge} Zeichen zu lang und wird abgeschnitten.",
            "Auf maximal 60 Zeichen kuerzen, Wichtiges nach vorn."))
    else:
        befunde.append(_befund("Title-Tag", OK, f"{laenge} Zeichen: \"{title}\""))

    if fokus_keyword and fokus_keyword.lower() not in title.lower():
        befunde.append(_befund(
            "Fokus-Keyword im Title", WARNUNG,
            f"\"{fokus_keyword}\" kommt im Title nicht vor.",
            "Fokus-Keyword moeglichst weit vorn im Title platzieren."))
    elif fokus_keyword:
        befunde.append(_befund("Fokus-Keyword im Title", OK, "Keyword ist im Title enthalten."))


def _pruefe_meta_description(parser, befunde):
    beschreibung = (parser.meta.get("description") or "").strip()
    if not beschreibung:
        befunde.append(_befund(
            "Meta-Description", KRITISCH, "Keine Meta-Description vorhanden.",
            "Beschreibung mit Nutzen und Handlungsaufforderung ergaenzen (70-160 Zeichen)."))
        return
    laenge = len(beschreibung)
    if laenge < 70:
        befunde.append(_befund(
            "Meta-Description", HINWEIS, f"Beschreibung ist mit {laenge} Zeichen kurz.",
            "Auf 70-160 Zeichen erweitern und Alleinstellungsmerkmal nennen."))
    elif laenge > 160:
        befunde.append(_befund(
            "Meta-Description", HINWEIS, f"Beschreibung ist mit {laenge} Zeichen zu lang.",
            "Auf 160 Zeichen kuerzen, damit sie nicht abgeschnitten wird."))
    else:
        befunde.append(_befund("Meta-Description", OK, f"{laenge} Zeichen."))


def _pruefe_headings(parser, fokus_keyword, befunde):
    h1 = [text for level, text in parser.headings if level == 1]
    if not h1:
        befunde.append(_befund(
            "H1-Ueberschrift", KRITISCH, "Keine H1 gefunden.",
            "Genau eine H1 mit dem Hauptthema der Seite setzen."))
    elif len(h1) > 1:
        befunde.append(_befund(
            "H1-Ueberschrift", WARNUNG, f"{len(h1)} H1-Ueberschriften gefunden.",
            "Auf genau eine H1 reduzieren, weitere als H2 auszeichnen."))
    else:
        befunde.append(_befund("H1-Ueberschrift", OK, f"\"{h1[0]}\""))
        if fokus_keyword and fokus_keyword.lower() not in h1[0].lower():
            befunde.append(_befund(
                "Fokus-Keyword in H1", HINWEIS,
                f"\"{fokus_keyword}\" kommt in der H1 nicht vor.",
                "Fokus-Keyword natuerlich in die H1 einbauen."))

    ebenen = [level for level, _ in parser.headings]
    spruenge = [
        (ebenen[i - 1], ebenen[i])
        for i in range(1, len(ebenen))
        if ebenen[i] - ebenen[i - 1] > 1
    ]
    if spruenge:
        vorher, nachher = spruenge[0]
        befunde.append(_befund(
            "Ueberschriften-Hierarchie", HINWEIS,
            f"{len(spruenge)} Ebenensprung/-spruenge, z. B. H{vorher} direkt auf H{nachher}.",
            "Ueberschriftenebenen luecken los verschachteln (H1 > H2 > H3)."))
    elif len(parser.headings) > 1:
        befunde.append(_befund("Ueberschriften-Hierarchie", OK,
                               f"{len(parser.headings)} Ueberschriften ohne Ebenenspruenge."))

    if len([1 for level, _ in parser.headings if level == 2]) == 0:
        befunde.append(_befund(
            "Zwischenueberschriften", HINWEIS, "Keine H2-Zwischenueberschriften vorhanden.",
            "Text mit H2 gliedern - verbessert Lesbarkeit und Rankings."))


def _pruefe_bilder(parser, befunde):
    if not parser.images:
        befunde.append(_befund(
            "Bilder", HINWEIS, "Keine Bilder gefunden.",
            "Eigene Projektfotos einbinden - wichtig fuer Vertrauen und Bildersuche."))
        return
    ohne_alt = [b for b in parser.images if not (b["alt"] or "").strip()]
    if ohne_alt:
        befunde.append(_befund(
            "Alt-Texte", WARNUNG,
            f"{len(ohne_alt)} von {len(parser.images)} Bildern ohne Alt-Text.",
            "Beschreibende Alt-Texte ergaenzen (Barrierefreiheit + Bilder-SEO)."))
    else:
        befunde.append(_befund("Alt-Texte", OK,
                               f"Alle {len(parser.images)} Bilder haben einen Alt-Text."))


def _pruefe_links(parser, basis_url, befunde):
    basis_domain = urlparse(basis_url).netloc.lower().removeprefix("www.")
    intern, extern, leere_anker = [], [], 0
    for link in parser.links:
        href = (link["href"] or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        ziel_domain = urlparse(urljoin(basis_url, href)).netloc.lower().removeprefix("www.")
        if ziel_domain == basis_domain:
            intern.append(link)
        else:
            extern.append(link)
        if not link["text"]:
            leere_anker += 1

    if len(intern) < 3:
        befunde.append(_befund(
            "Interne Verlinkung", WARNUNG, f"Nur {len(intern)} interne Links gefunden.",
            "Mehr interne Links mit sprechenden Ankertexten auf Leistungsseiten setzen."))
    else:
        befunde.append(_befund("Interne Verlinkung", OK, f"{len(intern)} interne Links."))

    if leere_anker:
        befunde.append(_befund(
            "Ankertexte", HINWEIS, f"{leere_anker} Links ohne erkennbaren Ankertext.",
            "Verlinkte Grafiken mit Alt-Text bzw. Links mit Text versehen."))

    return len(intern), len(extern)


def _pruefe_technik(parser, url, status, ladezeit, groesse, befunde):
    if urlparse(url).scheme == "https":
        befunde.append(_befund("HTTPS", OK, "Seite wird verschluesselt ausgeliefert."))
    else:
        befunde.append(_befund(
            "HTTPS", KRITISCH, "Seite laeuft ohne SSL-Verschluesselung.",
            "SSL-Zertifikat einrichten und alles per 301 auf https umleiten."))

    robots = (parser.meta.get("robots") or "").lower()
    if "noindex" in robots:
        befunde.append(_befund(
            "Indexierbarkeit", KRITISCH, "Meta-Robots enthaelt 'noindex'.",
            "noindex entfernen, sonst kann die Seite nicht ranken."))
    else:
        befunde.append(_befund("Indexierbarkeit", OK, "Kein noindex gesetzt."))

    if parser.canonical:
        befunde.append(_befund("Canonical-Tag", OK, parser.canonical))
    else:
        befunde.append(_befund(
            "Canonical-Tag", WARNUNG, "Kein Canonical-Tag gesetzt.",
            "Selbstreferenzierendes Canonical setzen, um Duplicate Content zu vermeiden."))

    if parser.hat_viewport:
        befunde.append(_befund("Mobile Viewport", OK, "Viewport-Meta-Tag vorhanden."))
    else:
        befunde.append(_befund(
            "Mobile Viewport", KRITISCH, "Kein Viewport-Meta-Tag - Seite ist nicht mobiloptimiert.",
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> ergaenzen."))

    if parser.lang:
        befunde.append(_befund("Sprachauszeichnung", OK, f"lang=\"{parser.lang}\""))
    else:
        befunde.append(_befund(
            "Sprachauszeichnung", HINWEIS, "Kein lang-Attribut im <html>-Tag.",
            "lang=\"de\" ergaenzen."))

    if ladezeit > 3:
        schwere = KRITISCH if ladezeit > 6 else WARNUNG
        befunde.append(_befund(
            "Antwortzeit", schwere, f"Server-Antwortzeit betrug {ladezeit:.1f} Sekunden.",
            "Hosting, Caching und Bildgroessen pruefen (Ziel unter 1 Sekunde)."))
    else:
        befunde.append(_befund("Antwortzeit", OK, f"{ladezeit:.2f} Sekunden."))

    if groesse > 2_000_000:
        befunde.append(_befund(
            "Seitengroesse", WARNUNG, f"HTML-Dokument ist {groesse / 1_000_000:.1f} MB gross.",
            "HTML verschlanken, Inline-Skripte auslagern."))

    if status and status >= 400:
        befunde.append(_befund(
            "HTTP-Status", KRITISCH, f"Server antwortete mit Status {status}.",
            "Fehlerursache beheben - die Seite ist fuer Nutzer nicht erreichbar."))


def _pruefe_strukturierte_daten(parser, befunde):
    if not parser.jsonld:
        befunde.append(_befund(
            "Strukturierte Daten", WARNUNG, "Kein JSON-LD gefunden.",
            "LocalBusiness-/Organization-Schema einbinden fuer bessere Suchergebnisse."))
        return

    if any(isinstance(b, dict) and b.get("__ungueltig__") for b in parser.jsonld):
        befunde.append(_befund(
            "Strukturierte Daten", WARNUNG, "JSON-LD-Block ist syntaktisch ungueltig.",
            "JSON-LD mit dem Rich-Results-Test von Google pruefen."))
        return

    typen = set()
    for block in parser.jsonld:
        elemente = block if isinstance(block, list) else [block]
        for element in elemente:
            if isinstance(element, dict):
                typ = element.get("@type")
                if isinstance(typ, list):
                    typen.update(str(t) for t in typ)
                elif typ:
                    typen.add(str(typ))

    befunde.append(_befund("Strukturierte Daten", OK,
                           f"Gefundene Typen: {', '.join(sorted(typen)) or 'unbekannt'}"))

    lokale_typen = {"LocalBusiness", "Organization", "HomeAndConstructionBusiness",
                    "Electrician", "Plumber", "RoofingContractor", "GeneralContractor"}
    if not (typen & lokale_typen):
        befunde.append(_befund(
            "LocalBusiness-Schema", HINWEIS, "Kein LocalBusiness-/Organization-Typ ausgezeichnet.",
            "Betriebsdaten (Name, Adresse, Telefon, Oeffnungszeiten) als LocalBusiness auszeichnen."))


def _pruefe_conversion(parser, befunde):
    text = parser.text
    if _TELEFON_RE.search(text):
        befunde.append(_befund("Telefonnummer", OK, "Telefonnummer im Seitentext gefunden."))
    else:
        befunde.append(_befund(
            "Telefonnummer", WARNUNG, "Keine Telefonnummer im Seitentext erkannt.",
            "Telefonnummer gut sichtbar im Header platzieren - wichtigster Kontaktweg im Handwerk."))

    hat_tel_link = any((l["href"] or "").startswith("tel:") for l in parser.links)
    if hat_tel_link:
        befunde.append(_befund("Klick-to-Call", OK, "tel:-Link vorhanden."))
    else:
        befunde.append(_befund(
            "Klick-to-Call", WARNUNG, "Kein tel:-Link gefunden.",
            "Telefonnummer als tel:-Link einbinden, damit Mobilnutzer direkt anrufen koennen."))

    if parser.hat_formular:
        befunde.append(_befund("Kontaktformular", OK, "Formular auf der Seite vorhanden."))
    else:
        befunde.append(_befund(
            "Kontaktformular", HINWEIS, "Kein Formular auf dieser Seite.",
            "Kurzes Anfrageformular ergaenzen (max. 5 Pflichtfelder)."))

    impressum_vorhanden = any(
        "impressum" in ((l["text"] or "") + (l["href"] or "")).lower() for l in parser.links
    )
    if impressum_vorhanden:
        befunde.append(_befund("Impressum", OK, "Impressum ist verlinkt."))
    else:
        befunde.append(_befund(
            "Impressum", WARNUNG, "Kein Impressums-Link gefunden.",
            "Impressum verlinken - in Deutschland gesetzlich vorgeschrieben."))


def _pruefe_textumfang(parser, fokus_keyword, befunde):
    woerter = parser.text.split()
    anzahl = len(woerter)
    if anzahl < 300:
        befunde.append(_befund(
            "Textumfang", WARNUNG, f"Nur {anzahl} Woerter sichtbarer Text.",
            "Inhalt auf mindestens 300-800 Woerter ausbauen, Fragen der Kunden beantworten."))
    else:
        befunde.append(_befund("Textumfang", OK, f"{anzahl} Woerter."))

    if fokus_keyword and anzahl:
        treffer = parser.text.lower().count(fokus_keyword.lower())
        dichte = treffer / anzahl * 100
        if treffer == 0:
            befunde.append(_befund(
                "Fokus-Keyword im Text", WARNUNG,
                f"\"{fokus_keyword}\" kommt im Text nicht vor.",
                "Keyword natuerlich im Flietext verwenden."))
        elif dichte > 4:
            befunde.append(_befund(
                "Keyword-Dichte", WARNUNG, f"Keyword-Dichte betraegt {dichte:.1f} %.",
                "Dichte auf 0,5-2,5 % senken, um Ueberoptimierung zu vermeiden."))
        else:
            befunde.append(_befund(
                "Fokus-Keyword im Text", OK, f"{treffer}x erwaehnt ({dichte:.1f} % Dichte)."))
    return anzahl


def berechne_score(befunde):
    """Score 0-100 aus den Befunden.

    Jede Pruefung geht mit einem Gewicht in die Bewertung ein: eine bestandene
    Pruefung (OK) zaehlt 1 Punkt, eine nicht bestandene erhoeht das Maximum um
    ihr Schweregrad-Gewicht, ohne Punkte einzubringen. Kritische Maengel
    druecken den Score damit staerker als blosse Hinweise.
    """
    maximum = 0
    erreicht = 0
    for befund in befunde:
        if befund["schwere"] == OK:
            maximum += 1
            erreicht += 1
        else:
            maximum += GEWICHTE.get(befund["schwere"], 1)
    if maximum == 0:
        return 0
    return round(erreicht / maximum * 100)


def analysiere_url(url, fokus_keyword="", timeout=TIMEOUT):
    """Ruft eine URL ab und fuehrt die vollstaendige OnPage-Analyse durch.

    :return: dict mit url, score, befunden und Kennzahlen
    :raises AuditFehler: wenn die Seite nicht abgerufen werden kann
    """
    html_text, status, ladezeit, finale_url, groesse = lade_seite(url, timeout=timeout)
    return analysiere_html(html_text, finale_url, fokus_keyword=fokus_keyword,
                           status=status, ladezeit=ladezeit, groesse=groesse)


def analysiere_html(html_text, url, fokus_keyword="", status=200, ladezeit=0.0, groesse=None):
    """Wertet bereits vorliegendes HTML aus (ohne Netzwerkzugriff).

    Von `analysiere_url` genutzt und getrennt aufrufbar, damit die Pruefungen
    unabhaengig vom Abruf testbar sind.
    """
    if groesse is None:
        groesse = len(html_text.encode("utf-8"))

    parser = _SeitenParser()
    parser.feed(html_text)
    parser.close()

    befunde = []
    _pruefe_technik(parser, url, status, ladezeit, groesse, befunde)
    _pruefe_title(parser, fokus_keyword, befunde)
    _pruefe_meta_description(parser, befunde)
    _pruefe_headings(parser, fokus_keyword, befunde)
    wortanzahl = _pruefe_textumfang(parser, fokus_keyword, befunde)
    _pruefe_bilder(parser, befunde)
    intern, extern = _pruefe_links(parser, url, befunde)
    _pruefe_strukturierte_daten(parser, befunde)
    _pruefe_conversion(parser, befunde)

    return {
        "url": url,
        "status": status,
        "score": berechne_score(befunde),
        "befunde": befunde,
        "kennzahlen": {
            "Ladezeit": f"{ladezeit:.2f} s",
            "Woerter": wortanzahl,
            "Ueberschriften": len(parser.headings),
            "Bilder": len(parser.images),
            "Interne Links": intern,
            "Externe Links": extern,
            "Seitengroesse": f"{groesse / 1024:.0f} KB",
        },
        "anzahl": {
            KRITISCH: sum(1 for b in befunde if b["schwere"] == KRITISCH),
            WARNUNG: sum(1 for b in befunde if b["schwere"] == WARNUNG),
            HINWEIS: sum(1 for b in befunde if b["schwere"] == HINWEIS),
            OK: sum(1 for b in befunde if b["schwere"] == OK),
        },
    }
