# SEO-Manager fuer Handwerksbetriebe

Eine Python-Desktop-Software mit uebersichtlicher grafischer Oberflaeche (GUI),
mit der SEO-Dienstleistungen fuer Handwerksunternehmen in Deutschland geplant,
umgesetzt, gemessen und dem Kunden gegenueber dokumentiert werden koennen.

Die Software deckt den kompletten Arbeitsablauf einer SEO-Betreuung ab:
**technisches SEO und OnPage-Optimierung, lokale SEO, Ranking-Ueberwachung,
Content-Produktion und Conversion-Maximierung** — je Kunde, mit Gesamtscore
und Kundenreport.

Zielgruppe sind Agenturen und Freelancer, die SEO an Handwerksbetriebe
(Elektriker, SHK, Dachdecker, Maler, Tischler, GaLaBau u. v. m.) verkaufen.

## Funktionsumfang

### Uebersicht (Dashboard)
- Gewichteter **Gesamt-SEO-Score** je Kunde (Technik & OnPage 35 %,
  Lokale SEO 30 %, Conversion 20 %, Verzeichnisse 15 %)
- Fortschrittsbalken je Teilbereich, Ranking- und Content-Kennzahlen
- Automatisch priorisierte Liste der **naechsten empfohlenen Massnahmen**

### Analyse
- **OnPage-Audit**: ruft eine beliebige URL ab und prueft ueber 20 Kriterien —
  Title, Meta-Description, H-Struktur, Alt-Texte, Canonical, Viewport,
  Indexierbarkeit, HTTPS, strukturierte Daten (JSON-LD), Textumfang,
  Keyword-Einsatz, interne Verlinkung, Antwortzeit sowie Conversion-Signale
  (Telefonnummer, Klick-to-Call, Formular, Impressum).
  Jeder Befund erhaelt einen Schweregrad und eine konkrete Empfehlung,
  daraus wird ein Score von 0 bis 100 berechnet. Die Analyse laeuft im
  Hintergrund, die Oberflaeche bleibt bedienbar. Export als CSV.
- **Ranking-Tracker**: Positionen je Keyword ueber die Zeit erfassen, mit
  Trendanzeige, bester Position, Top-3-/Top-10-Kennzahlen und
  Verlaufsdiagramm. CSV-Import und -Export.

### Content-Produktion
- **Redaktionsplan**: Inhalte mit Typ, Fokus-Keyword, Status, Faelligkeit und
  Wortziel planen; ueberfaellige Inhalte werden farblich hervorgehoben.
- **Content-Briefing-Generator**: erstellt aus einem Fokus-Keyword ein
  vollstaendiges Redaktionsbriefing — Title- und Meta-Vorschlag, URL,
  Gliederung, W-Fragen, semantische Begriffe, interne Verlinkung, Medien,
  CTA und redaktionelle Hinweise. Direkt in den Redaktionsplan uebernehmbar.
- **Textanalyse**: Lesbarkeit nach der deutschen Flesch-Formel (Amstad),
  Wortanzahl, Lesezeit, durchschnittliche Satzlaenge, zu lange Saetze,
  Keyword-Dichte mit Bewertung und die haeufigsten inhaltstragenden Begriffe —
  inklusive konkreter Verbesserungsempfehlungen.

### Checklisten (103 Praxispunkte)
- **Technik & OnPage** (47 Punkte): technisches SEO, OnPage-Optimierung,
  Content & Suchintention, OffPage & Autoritaet, Monitoring & Reporting
- **Lokale SEO** (31 Punkte): Google Unternehmensprofil, lokale
  Website-Signale, Bewertungen, lokaler Content & Linkbuilding
- **Conversion/CRO** (25 Punkte): Vertrauen & Nachweise, Kontaktaufnahme,
  Seitenstruktur, Technik & Messung
- **Branchenverzeichnisse**: 13 wichtige deutsche Verzeichnisse (Google,
  Bing Places, Das Oertliche, Gelbe Seiten, 11880.com, GoLocal u. a.) mit
  Direktlink und Feld fuer die eigene Profil-URL (NAP-Konsistenz)

### Conversion-Maximierung
- **Trichter- und ROI-Rechner**: rechnet von Suchvolumen und Ranking-Position
  ueber branchenuebliche Klickraten zu Besuchern, Anfragen, Auftraegen und
  Umsatz — inklusive Deckungsbeitrag, Gewinn, ROI und Break-even. Zeigt den
  Unterschied zwischen aktueller und angestrebter Position (Verkaufsargument).
- **A/B-Test-Auswertung**: zweiseitiger Z-Test fuer zwei Conversion-Raten mit
  z-Wert, p-Wert, Konfidenz und klarer Aussage, ob ein Unterschied statistisch
  abgesichert ist — plus Stichprobenplanung.

### Weitere Werkzeuge
- **Keyword-Generator**: erzeugt lokale Suchbegriffe aus Gewerk und
  Einzugsgebiet (z. B. *"Elektriker Muenchen"*, *"was kostet Dachdecker in
  Leipzig"*), mit CSV-Export.
- **Kundenreport**: erzeugt einen HTML-Statusbericht mit Gesamtscore, offenen
  Massnahmen, Website-Analyse, Rankings, Redaktionsplan, allen Checklisten und
  Keyword-Vorschlaegen — zur Uebergabe an den Kunden.

Alle Daten liegen lokal in einer SQLite-Datenbank (`data/seo_optimizer.db`).
Ausser dem OnPage-Audit, das die zu pruefende Seite abruft, benoetigt die
Software keine Internetverbindung und keinen externen Dienst.

## Voraussetzungen

- Python 3.9 oder neuer
- `tkinter` (in den offiziellen Python-Installationen fuer Windows und macOS
  enthalten; unter Debian/Ubuntu ggf. `sudo apt install python3-tk`)

Es werden **keine zusaetzlichen Pakete** per `pip` benoetigt — die Anwendung
nutzt ausschliesslich die Python-Standardbibliothek.

## Installation & Start

```bash
git clone <repository-url>
cd Axolotl
python main.py
```

Beim ersten Start werden `data/` (Datenbank) und bei Bedarf `reports/`
automatisch angelegt. Bestehende Datenbanken aelterer Versionen werden
weiterverwendet; fehlende Tabellen legt die Anwendung selbst an.

## Projektstruktur

```
main.py                        Einstiegspunkt der Anwendung
seo_optimizer/
    data.py                    Gewerke, lokale Checkliste, Branchenverzeichnisse
    data_seo.py                Technik-/OnPage-/CRO-Katalog, Content- und CTR-Daten
    database.py                SQLite-Zugriff (Kunden, Checklisten, Rankings,
                               Redaktionsplan, Audits, Gesamtscore)
    onpage_analyzer.py         URL-Abruf, HTML-Parser und SEO-Pruefungen
    content_tools.py           Lesbarkeit, Keyword-Dichte, Briefing-Generator
    conversion.py              Trichter, ROI, CTR-Kurve, A/B-Test-Statistik
    keyword_generator.py       Lokale Keyword-Kombinationen
    report.py                  HTML-Report-Erstellung
    gui/
        main_window.py         Hauptfenster, Kundenliste, Navigation
        base.py                Basisklassen fuer Tabs und Tab-Gruppen
        tabs.py                Stammdaten, Checkliste, Keywords, Verzeichnisse, Report
        tabs_overview.py       Dashboard
        tabs_analyse.py        OnPage-Audit und Ranking-Tracker
        tabs_content.py        Redaktionsplan, Briefing, Textanalyse
        tabs_conversion.py     Trichter/ROI und A/B-Test
        dialogs.py             Dialog "Neuer Kunde"
        widgets.py             Scrollbereich, Fortschrittsbalken, Kacheln, Diagramm
        style.py               Farb- und Schriftdefinitionen
tests/                          Unittests (100 Tests)
```

## Tests ausfuehren

```bash
python -m unittest discover -s tests -v
```

## Bedienung (Kurzueberblick)

1. Links ueber **"Neuer Kunde"** einen Handwerksbetrieb anlegen.
2. Im Tab **Stammdaten** Kontaktdaten, Website und Einzugsgebiet (Orte
   kommagetrennt, z. B. *"Muenchen, Dachau, Fuerstenfeldbruck"*) hinterlegen.
3. Unter **Analyse > OnPage-Audit** die Website pruefen — die Befunde zeigen,
   was zuerst zu tun ist. Unter **Rankings** die Startpositionen erfassen.
4. In **Checklisten** die umgesetzten Massnahmen abhaken; der Gesamtscore in
   der Kundenliste aktualisiert sich sofort.
5. Unter **Content** Briefings erzeugen, Inhalte planen und fertige Texte
   vor der Veroeffentlichung pruefen.
6. Unter **Conversion** den Umsatzhebel und die Wirtschaftlichkeit berechnen
   sowie A/B-Tests auswerten.
7. Im Tab **Report** den HTML-Statusbericht fuer den Kunden erzeugen.

## Hinweise zur Methodik

- Die Klickraten je Suchposition sind branchenuebliche **Richtwerte** und
  dienen der Schaetzung. Fuer belastbare Prognosen sollten die tatsaechlichen
  Werte aus der Google Search Console verwendet werden.
- Die Lesbarkeit wird mit der deutschen Fassung des Flesch-Reading-Ease
  (Amstad-Formel) berechnet; die Silbenzaehlung erfolgt naeherungsweise
  ueber Vokalgruppen.
- Der OnPage-Audit prueft die abgerufene HTML-Seite. Vom Browser per
  JavaScript nachgeladene Inhalte werden dabei nicht erfasst.
