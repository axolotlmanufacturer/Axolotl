"""Fachdaten fuer allgemeines (nicht ortsbezogenes) SEO, Content und Conversion.

Ergaenzt data.py, das die rein lokalen SEO-Aspekte abbildet.
"""

# ---------------------------------------------------------------------------
# Checkliste: technisches SEO, OnPage, OffPage, Monitoring
# ---------------------------------------------------------------------------

TECHNICAL_SEO_CATALOG = {
    "Technisches SEO": [
        ("web_ssl", "SSL-Zertifikat (https) aktiv, kein Mixed Content"),
        ("tech_indexierung", "Indexierung geprueft (site:-Abfrage, Coverage-Bericht)"),
        ("tech_robots", "robots.txt vorhanden und gibt wichtige Seiten frei"),
        ("tech_sitemap", "XML-Sitemap aktuell und in der Search Console eingereicht"),
        ("tech_canonical", "Canonical-Tags korrekt gesetzt (keine Duplikate)"),
        ("tech_weiterleitungen", "Weiterleitungen als 301, keine Ketten/Schleifen"),
        ("tech_404", "Individuelle 404-Seite mit Navigation & Suchfunktion"),
        ("web_responsive", "Mobile Darstellung optimiert (Mobile-First-Indexierung)"),
        ("web_speed", "Core Web Vitals im gruenen Bereich (LCP, INP, CLS)"),
        ("tech_bilder", "Bilder komprimiert, moderne Formate (WebP/AVIF), Lazy Loading"),
        ("tech_strukturierte_daten", "Strukturierte Daten (Organization, Service, FAQ, Breadcrumb)"),
        ("tech_url_struktur", "Sprechende, flache URL-Struktur ohne Parameter-Wildwuchs"),
        ("tech_breadcrumb", "Breadcrumb-Navigation vorhanden und ausgezeichnet"),
        ("tech_javascript", "Inhalte auch ohne JavaScript-Rendering crawlbar"),
    ],
    "OnPage-Optimierung": [
        ("web_title", "Title-Tags einzigartig, 30-60 Zeichen, Fokus-Keyword vorn"),
        ("web_meta", "Meta-Descriptions einzigartig mit Call-to-Action"),
        ("web_h1", "Genau eine H1 pro Seite, saubere H2/H3-Hierarchie"),
        ("onpage_keyword_mapping", "Keyword-Mapping: je Keyword genau eine Zielseite"),
        ("onpage_kannibalisierung", "Keine Keyword-Kannibalisierung zwischen Seiten"),
        ("onpage_interne_links", "Interne Verlinkung mit sprechenden Ankertexten"),
        ("onpage_alt_texte", "Alle relevanten Bilder mit beschreibenden Alt-Texten"),
        ("onpage_duplicate", "Kein Duplicate Content (intern & extern)"),
        ("onpage_snippet", "Snippet-Optimierung (Rich Results, FAQ, Bewertungssterne)"),
        ("onpage_orphan", "Keine verwaisten Seiten ohne interne Verlinkung"),
    ],
    "Content & Suchintention": [
        ("ct_suchintention", "Suchintention je Zielseite bestimmt (Info/Kommerziell/Transaktional)"),
        ("ct_keywordrecherche", "Keyword-Recherche mit Suchvolumen & Wettbewerb dokumentiert"),
        ("ct_themencluster", "Themencluster mit Pillar-Page und Unterseiten aufgebaut"),
        ("ct_umfang", "Inhaltstiefe mindestens auf Niveau der Top-10-Wettbewerber"),
        ("ct_eeat", "E-E-A-T: Autorenprofil, Qualifikationen, Meisterbrief sichtbar"),
        ("ct_aktualitaet", "Bestandsinhalte werden regelmaessig aktualisiert"),
        ("ct_medien", "Eigene Fotos/Videos statt Stockmaterial"),
        ("ct_lesbarkeit", "Verstaendliche Sprache, kurze Absaetze, Zwischenueberschriften"),
        ("ct_faq_schema", "FAQ-Bereiche mit FAQPage-Schema ausgezeichnet"),
        ("ct_redaktionsplan", "Redaktionsplan gepflegt und eingehalten"),
    ],
    "OffPage & Autoritaet": [
        ("off_backlinkprofil", "Backlinkprofil analysiert (Anzahl, Qualitaet, Ankertexte)"),
        ("off_linkaufbau", "Aktiver Linkaufbau ueber Partner, Lieferanten, Verbaende"),
        ("off_wettbewerb", "Backlink-Luecken zum Wettbewerb identifiziert"),
        ("off_brand", "Marken-Erwaehnungen ohne Link nachverfolgt & eingesammelt"),
        ("off_digital_pr", "Digitale PR: Fachbeitraege, Interviews, Studien"),
        ("off_toxisch", "Toxische/Spam-Backlinks geprueft und ggf. entwertet"),
        ("off_social", "Social-Media-Profile gepflegt und verlinkt"),
    ],
    "Monitoring & Reporting": [
        ("web_searchconsole", "Google Search Console eingerichtet & Sitemap eingereicht"),
        ("web_analytics", "Datenschutzkonformes Webanalyse-Tool eingerichtet"),
        ("mon_conversion_tracking", "Conversion-Tracking fuer Anrufe & Formulare aktiv"),
        ("mon_rankings", "Ranking-Monitoring fuer die Fokus-Keywords etabliert"),
        ("mon_reporting", "Monatliches Reporting an den Kunden vereinbart"),
        ("mon_ziele", "Messbare Ziele (Anfragen/Monat, Umsatz) definiert"),
    ],
}


# ---------------------------------------------------------------------------
# Checkliste: Conversion-Optimierung (CRO) fuer Handwerksbetriebe
# ---------------------------------------------------------------------------

CRO_CATALOG = {
    "Vertrauen & Nachweise": [
        ("cro_bewertungen", "Kundenbewertungen prominent auf der Startseite"),
        ("cro_meisterbrief", "Meisterbrief, Innungs- & Zertifikatssiegel sichtbar"),
        ("cro_referenzen", "Vorher-Nachher-Galerie echter Projekte"),
        ("cro_team", "Team- und Inhaberfotos mit Namen"),
        ("cro_garantie", "Garantie-/Gewaehrleistungsversprechen ausgewiesen"),
        ("cro_versicherung", "Betriebshaftpflicht & Versicherungsnachweis erwaehnt"),
    ],
    "Kontaktaufnahme & Angebot": [
        ("web_cta", "Kontaktformular & Klick-to-Call auf Mobilgeraeten"),
        ("cro_telefon_sichtbar", "Telefonnummer in jedem Viewport sichtbar (Header/Sticky)"),
        ("cro_formular_kurz", "Anfrageformular mit maximal 5 Pflichtfeldern"),
        ("cro_rueckruf", "Rueckruf-Service oder Terminbuchung angeboten"),
        ("cro_whatsapp", "Messenger-/WhatsApp-Kontakt als Alternative"),
        ("cro_reaktionszeit", "Zugesagte Reaktionszeit kommuniziert (z. B. 24 Std.)"),
        ("cro_notdienst", "Notdienst-Hinweis deutlich hervorgehoben (falls angeboten)"),
    ],
    "Seitenstruktur & Nutzerfuehrung": [
        ("cro_nutzenversprechen", "Klares Nutzenversprechen above the fold"),
        ("cro_leistungsseiten", "Eigene Seite je Hauptleistung statt Sammelseite"),
        ("cro_preistransparenz", "Preisrahmen, Festpreise oder Kostenbeispiele genannt"),
        ("cro_ablauf", "Ablauf der Zusammenarbeit in Schritten erklaert"),
        ("cro_faq", "FAQ beantwortet typische Kaufhindernisse"),
        ("cro_cta_wiederholt", "Handlungsaufforderung mehrfach auf langen Seiten"),
        ("cro_ablenkung", "Keine ablenkenden Elemente im Anfrageprozess"),
    ],
    "Technik & Messung": [
        ("cro_ladezeit", "Ladezeit der Anfrageseite unter 2,5 Sekunden"),
        ("cro_formular_fehler", "Formularvalidierung mit verstaendlichen Fehlermeldungen"),
        ("cro_danke_seite", "Eigene Danke-Seite als Conversion-Ziel eingerichtet"),
        ("cro_ab_tests", "A/B-Tests fuer Headline, CTA und Formular durchgefuehrt"),
        ("cro_heatmap", "Nutzerverhalten per Heatmap/Session-Recording geprueft"),
    ],
}


# ---------------------------------------------------------------------------
# Content-Planung
# ---------------------------------------------------------------------------

CONTENT_TYPES = [
    "Leistungsseite",
    "Standort-Landingpage",
    "Ratgeber / Blogbeitrag",
    "Referenz / Projektbericht",
    "FAQ-Seite",
    "Pillar-Page",
    "Video / Bildstrecke",
    "Pressemitteilung",
]

CONTENT_STATUS = [
    "Idee",
    "Briefing erstellt",
    "In Produktion",
    "Im Lektorat",
    "Veroeffentlicht",
    "Aktualisierung faellig",
]

# Suchintentionen inkl. empfohlenem Inhaltstyp.
SUCHINTENTIONEN = {
    "Informativ (Wissen)": "Ratgeber, Anleitung, Checkliste - Vertrauen aufbauen, spaeter konvertieren",
    "Kommerziell (Vergleich)": "Leistungsseite mit Preisrahmen, Vergleich, Referenzen",
    "Transaktional (Auftrag)": "Landingpage mit Angebot, Formular und Telefonnummer",
    "Navigational (Marke)": "Startseite, Ueber-uns, Kontakt",
}

# W-Fragen-Muster fuer Content-Briefings.
W_FRAGEN = [
    "Was kostet {keyword}?",
    "Wie lange dauert {keyword}?",
    "Wann ist {keyword} noetig?",
    "Wer darf {keyword} durchfuehren?",
    "Welche Foerderung gibt es fuer {keyword}?",
    "Worauf sollte man bei {keyword} achten?",
    "Wie finde ich einen guten Betrieb fuer {keyword}?",
    "Welche Alternativen gibt es zu {keyword}?",
]

# Empfohlener Textumfang je Inhaltstyp (Richtwerte in Woertern).
WORTZIEL_JE_TYP = {
    "Leistungsseite": 800,
    "Standort-Landingpage": 600,
    "Ratgeber / Blogbeitrag": 1200,
    "Referenz / Projektbericht": 400,
    "FAQ-Seite": 700,
    "Pillar-Page": 2000,
    "Video / Bildstrecke": 300,
    "Pressemitteilung": 400,
}


# ---------------------------------------------------------------------------
# Conversion-Kennzahlen
# ---------------------------------------------------------------------------

# Richtwerte fuer die organische Klickrate je Google-Position.
# Quelle: branchenuebliche CTR-Studien - dienen nur als Schaetzgrundlage.
CTR_JE_POSITION = {
    1: 0.276, 2: 0.158, 3: 0.110, 4: 0.084, 5: 0.063,
    6: 0.049, 7: 0.039, 8: 0.033, 9: 0.027, 10: 0.024,
}
CTR_POSITION_11_20 = 0.010
CTR_POSITION_AB_21 = 0.003


# ---------------------------------------------------------------------------
# Sprachdaten fuer die Textanalyse
# ---------------------------------------------------------------------------

# Haeufige deutsche Funktionswoerter, die bei der Termanalyse ignoriert werden.
STOPWORDS_DE = {
    "aber", "alle", "allem", "allen", "aller", "alles", "als", "also", "am", "an",
    "ander", "andere", "anderem", "anderen", "anderer", "anderes", "auch", "auf",
    "aus", "bei", "beim", "bin", "bis", "bist", "da", "damit", "dann", "das",
    "dass", "dem", "den", "denn", "der", "des", "dessen", "die", "dies", "diese",
    "diesem", "diesen", "dieser", "dieses", "doch", "dort", "du", "durch", "ein",
    "eine", "einem", "einen", "einer", "eines", "er", "es", "etwas", "euer",
    "fuer", "für", "ganz", "gegen", "gewesen", "hab", "habe", "haben", "hat",
    "hatte", "hatten", "hier", "hin", "ihr", "ihre", "ihrem", "ihren", "ihrer",
    "im", "in", "ins", "ist", "ja", "jede", "jedem", "jeden", "jeder", "jedes",
    "jetzt", "kann", "kein", "keine", "koennen", "können", "man", "mehr", "mein",
    "meine", "mit", "muss", "muessen", "müssen", "nach", "nicht", "nichts", "noch",
    "nun", "nur", "ob", "oder", "ohne", "schon", "sehr", "sein", "seine", "seit",
    "sich", "sie", "sind", "so", "soll", "sollen", "sondern", "ueber", "über",
    "um", "und", "uns", "unser", "unsere", "unter", "vom", "von", "vor", "waehrend",
    "während", "war", "waren", "was", "weil", "weiter", "welche", "wenn", "werde",
    "werden", "wie", "wieder", "wir", "wird", "wirst", "wo", "wollen", "wurde",
    "wurden", "zu", "zum", "zur", "zwar", "zwischen",
}


def alle_keys(catalog):
    """Liefert alle Item-Keys eines Checklisten-Katalogs."""
    return [key for items in catalog.values() for key, _ in items]
