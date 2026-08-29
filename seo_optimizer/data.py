"""Statische Fachdaten fuer den Lokal-SEO Manager.

Enthaelt die unterstuetzten Handwerks-Gewerke samt typischer Leistungen,
den Katalog der lokalen SEO-Checkliste sowie die Liste der wichtigsten
deutschen Branchenverzeichnisse (Citations) fuer Handwerksbetriebe.
"""

# Gewerk -> typische Leistungen/Suchbegriffe, die fuer die
# Keyword-Generierung als Basis dienen.
GEWERKE = {
    "Elektriker": [
        "Elektriker", "Elektroinstallation", "Elektrofirma", "E-Check",
        "Zaehlerschrank", "Smart Home Installation", "Notdienst Elektriker",
    ],
    "Sanitaer & Heizung (SHK)": [
        "Heizungsbauer", "Sanitaerinstallation", "Badsanierung",
        "Heizungsnotdienst", "Klempner", "Rohrreinigung", "Waermepumpe",
    ],
    "Dachdecker": [
        "Dachdecker", "Dachsanierung", "Dachreparatur",
        "Flachdachabdichtung", "Dachrinnenreinigung", "Solaranlage Montage",
    ],
    "Maler & Lackierer": [
        "Malerbetrieb", "Malerarbeiten", "Fassadenanstrich",
        "Tapezieren", "Waermedaemmung Fassade", "Lackierarbeiten",
    ],
    "Tischler & Schreiner": [
        "Tischlerei", "Moebeltischler", "Einbaukueche",
        "Innenausbau", "Fenster aus Holz",
    ],
    "Fliesenleger": [
        "Fliesenleger", "Fliesen verlegen", "Badsanierung Fliesen",
    ],
    "Garten- & Landschaftsbau": [
        "Gartenbau", "Landschaftsgaertner", "Pflasterarbeiten",
        "Gartenpflege", "Baumfaellung",
    ],
    "Maurer & Betonbauer": [
        "Maurerbetrieb", "Betonarbeiten", "Mauerwerksanierung",
    ],
    "Zimmerer": [
        "Zimmerei", "Dachstuhl", "Holzhausbau", "Carport Bau",
    ],
    "Metallbau & Schlosserei": [
        "Metallbau", "Schlosserei", "Schweissarbeiten",
        "Gelaender Herstellung", "Torbau",
    ],
    "Fenster & Tuerenbau": [
        "Fensterbau", "Tuerenbau", "Fenster einbauen", "Rollladenbau",
    ],
    "Kfz-Werkstatt": [
        "Autowerkstatt", "Kfz-Meisterbetrieb", "Reifenwechsel",
        "Inspektion", "Unfallreparatur",
    ],
    "Reinigungsservice": [
        "Gebaeudereinigung", "Fensterreinigung", "Bueroreinigung",
    ],
    "Sonstiges Handwerk": [
        "Handwerksbetrieb",
    ],
}

# Suchmuster ("Modifikatoren"), die mit Leistung und Ort kombiniert
# werden, um typische lokale Suchanfragen abzubilden.
KEYWORD_MODIFIERS = [
    "{leistung} {ort}",
    "{leistung} in {ort}",
    "{leistung} {ort} in der Naehe",
    "{leistung} {ort} Notdienst",
    "{leistung} {ort} Preise",
    "{leistung} {ort} Kosten",
    "{leistung} Firma {ort}",
    "bester {leistung} {ort}",
    "{leistung} {ort} 24h",
    "was kostet {leistung} in {ort}",
]

# Checkliste fuer lokale SEO-Optimierung, gegliedert nach Kategorien.
# Jeder Eintrag ist ein Tupel (eindeutiger_key, Beschreibungstext).
CHECKLIST_CATALOG = {
    "Google Unternehmensprofil": [
        ("gmb_claimed", "Eintrag beansprucht und verifiziert"),
        ("gmb_name", "Firmenname exakt wie im Impressum (kein Keyword-Spam)"),
        ("gmb_kategorien", "Primaere & sekundaere Kategorien korrekt gewaehlt"),
        ("gmb_adresse", "Vollstaendige Adresse & Servicegebiet hinterlegt"),
        ("gmb_telefon", "Lokale Telefonnummer hinterlegt"),
        ("gmb_website", "Website-URL verlinkt"),
        ("gmb_oeffnungszeiten", "Oeffnungszeiten inkl. Feiertage gepflegt"),
        ("gmb_beschreibung", "Unternehmensbeschreibung mit lokalen Keywords verfasst"),
        ("gmb_fotos", "Mind. 10 aktuelle Fotos (Team, Fahrzeuge, Projekte)"),
        ("gmb_logo", "Logo & Titelbild hinterlegt"),
        ("gmb_posts", "Google-Beitraege werden regelmaessig veroeffentlicht"),
        ("gmb_qa", "Fragen & Antworten (Q&A) Bereich gepflegt"),
        ("gmb_produkte", "Dienstleistungen mit Beschreibung/Preisen angelegt"),
        ("gmb_attribute", "Attribute (z. B. Notdienst, Kostenvoranschlag) gesetzt"),
    ],
    "Website & On-Page SEO": [
        ("web_title", "Title-Tags enthalten Leistung + Ort"),
        ("web_meta", "Meta-Descriptions mit Call-to-Action & Ort optimiert"),
        ("web_h1", "H1 pro Seite eindeutig mit lokalem Bezug"),
        ("web_landingpages", "Eigene Landingpage je Einzugsgebiet/Stadtteil"),
        ("web_schema", "LocalBusiness-Schema (JSON-LD) eingebunden"),
        ("web_nap", "NAP (Name, Adresse, Telefon) im Footer konsistent"),
        ("web_responsive", "Mobile Darstellung optimiert (Responsive Design)"),
        ("web_speed", "Ladezeit unter 3 Sekunden (PageSpeed geprueft)"),
        ("web_ssl", "SSL-Zertifikat (https) aktiv"),
        ("web_cta", "Kontaktformular & Klick-to-Call auf Mobilgeraeten"),
        ("web_rechtliches", "Impressum & Datenschutzerklaerung DSGVO-konform"),
        ("web_searchconsole", "Google Search Console eingerichtet & Sitemap eingereicht"),
        ("web_analytics", "Datenschutzkonformes Tracking eingerichtet"),
    ],
    "Bewertungen & Reputation": [
        ("rev_prozess", "Aktiver Prozess zur Bewertungsanfrage nach Auftrag"),
        ("rev_anzahl", "Mind. 15 Google-Rezensionen mit Schnitt ab 4,5 Sternen"),
        ("rev_antworten", "Alle Rezensionen werden zeitnah beantwortet"),
        ("rev_widget", "Bewertungs-Widget auf der Website eingebunden"),
        ("rev_plattformen", "Rezensionen auch auf weiteren Plattformen gesammelt"),
    ],
    "Lokaler Content & Linkbuilding": [
        ("content_referenzen", "Referenzprojekte mit Ortsangabe & Fotos veroeffentlicht"),
        ("content_blog", "Regelmaessige Blogbeitraege zu lokalen Themen"),
        ("content_backlinks", "Backlinks von lokalen Partnern (IHK, Lieferanten, Vereine)"),
        ("content_presse", "Erwaehnung in lokaler Presse angestrebt"),
        ("content_events", "Teilnahme an lokalen Events/Sponsoring dokumentiert"),
        ("content_faq", "FAQ-Seite mit lokalen Suchfragen"),
    ],
}

# Wichtige deutsche Branchenverzeichnisse fuer NAP-Citations.
# Tupel: (eindeutiger_key, Anzeigename, Basis-URL)
DIRECTORIES = [
    ("google_gmb", "Google Unternehmensprofil", "https://business.google.com"),
    ("bing_places", "Bing Places for Business", "https://www.bingplaces.com"),
    ("das_oertliche", "Das Oertliche", "https://www.dasoertliche.de"),
    ("gelbeseiten", "Gelbe Seiten", "https://www.gelbeseiten.de"),
    ("elf1880", "11880.com", "https://www.11880.com"),
    ("golocal", "GoLocal.de", "https://www.golocal.de"),
    ("firmenwissen", "Firmenwissen.de", "https://www.firmenwissen.de"),
    ("meinestadt", "Meinestadt.de", "https://www.meinestadt.de"),
    ("cylex", "Cylex Deutschland", "https://www.cylex.de"),
    ("yelp", "Yelp", "https://www.yelp.de"),
    ("werkenntdenbesten", "Werkenntdenbesten.de", "https://www.werkenntdenbesten.de"),
    ("myhammer", "MyHammer Profil", "https://www.my-hammer.de"),
    ("ihk", "IHK/Handwerkskammer-Verzeichnis", ""),
]


def alle_checklisten_keys():
    """Liefert eine flache Liste aller Checklisten-Keys (fuer Validierung/Tests)."""
    return [key for items in CHECKLIST_CATALOG.values() for key, _ in items]


def anzahl_checklisten_items():
    return len(alle_checklisten_keys())
