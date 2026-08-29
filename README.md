# Lokal-SEO Manager fuer Handwerksbetriebe

Eine Python-Desktop-Software mit uebersichtlicher grafischer Oberflaeche
(GUI), mit der lokale SEO-Dienstleistungen fuer lokale Handwerksunternehmen
in Deutschland (Elektriker, SHK, Dachdecker, Maler, Tischler, Garten- und
Landschaftsbau, u. v. m.) geplant, umgesetzt und dem Kunden gegenueber als
Report dokumentiert werden koennen.

Die Software richtet sich an Agenturen/Freelancer, die lokale
SEO-Dienstleistungen an Handwerksbetriebe verkaufen, und bildet den
kompletten Optimierungs-Workflow pro Kunde ab.

## Funktionen

- **Kundenverwaltung**: beliebig viele Handwerksbetriebe mit Stammdaten
  (Firma, Gewerk, Adresse, Kontakt, Google-Unternehmensprofil-URL,
  Einzugsgebiet) anlegen, bearbeiten und loeschen.
- **Lokale SEO-Checkliste**: ueber 45 Praxis-Punkte in den Kategorien
  *Google Unternehmensprofil*, *Website & On-Page SEO*, *Bewertungen &
  Reputation* sowie *Lokaler Content & Linkbuilding* — mit Fortschrittsbalken
  je Kategorie und gesamt.
- **Keyword-Generator**: erstellt automatisch lokale Suchbegriffs-Vorschlaege
  aus Gewerk + Einzugsgebiet (z. B. *"Elektriker Muenchen"*, *"Heizungsnotdienst
  in der Naehe Augsburg"*, *"was kostet Dachdecker in Leipzig"*), inkl.
  CSV-Export und Kopieren in die Zwischenablage.
- **Branchenverzeichnisse (Citations)**: Checkliste der wichtigsten
  deutschen Verzeichnisse (Google, Bing Places, Das Oertliche, Gelbe Seiten,
  11880.com, GoLocal, Firmenwissen, Yelp u. a.) inkl. Direktlink und Feld
  fuer die eigene Profil-URL zur NAP-Konsistenzpruefung.
- **Report-Export**: erstellt auf Knopfdruck einen uebersichtlichen
  HTML-Statusbericht je Kunde (Fortschritt, offene To-Dos, Verzeichnisstatus,
  Keyword-Vorschlaege) — ideal zur Praesentation gegenueber dem Kunden.

Alle Daten werden lokal in einer SQLite-Datenbank gespeichert
(`data/seo_optimizer.db`), es ist keine Internetverbindung und kein externer
Dienst noetig.

## Voraussetzungen

- Python 3.9 oder neuer
- `tkinter` (in den offiziellen Python-Installationen fuer Windows und
  macOS bereits enthalten; unter Debian/Ubuntu ggf. nachinstallieren mit
  `sudo apt install python3-tk`)

Es werden **keine zusaetzlichen Pakete** per `pip` benoetigt — die Anwendung
nutzt ausschliesslich die Python-Standardbibliothek.

## Installation & Start

```bash
git clone <repository-url>
cd Axolotl
python main.py
```

Beim ersten Start wird automatisch der Ordner `data/` mit der SQLite-Datenbank
angelegt. Erstellte Reports landen im Ordner `reports/`.

## Projektstruktur

```
main.py                        Einstiegspunkt der Anwendung
seo_optimizer/
    data.py                    Gewerke, Checklisten-Katalog, Verzeichnisse
    database.py                SQLite-Datenzugriff (Kunden, Checkliste, Verzeichnisse)
    keyword_generator.py       Logik zur lokalen Keyword-Generierung
    report.py                  HTML-Report-Erstellung
    gui/
        main_window.py         Hauptfenster (Kundenliste, Navigation)
        tabs.py                 Stammdaten-, Checklisten-, Keyword-, Verzeichnis- und Report-Tab
        dialogs.py              Dialog "Neuer Kunde"
        widgets.py              Wiederverwendbare GUI-Bausteine (Scrollbereich, Fortschrittsbalken)
        style.py                Farb- und Schrift-Definitionen
tests/                          Unittests fuer Datenbank und Keyword-Generator
```

## Tests ausfuehren

```bash
python -m unittest discover -s tests -v
```

## Bedienung (Kurzueberblick)

1. Links ueber **"Neuer Kunde"** einen Handwerksbetrieb anlegen (Firma,
   Gewerk, Ort).
2. Im Tab **Stammdaten** die vollstaendigen Kontaktdaten sowie das
   Einzugsgebiet (Orte, kommagetrennt, z. B. *"Muenchen, Dachau,
   Fuerstenfeldbruck"*) hinterlegen und speichern.
3. Im Tab **SEO-Checkliste** die umgesetzten Massnahmen abhaken — der
   Fortschritt wird live berechnet und in der Kundenliste angezeigt.
4. Im Tab **Keyword-Generator** lokale Suchbegriffe generieren und als CSV
   exportieren oder in die Zwischenablage kopieren.
5. Im Tab **Verzeichnisse** dokumentieren, in welchen Branchenverzeichnissen
   der Kunde bereits eingetragen ist (inkl. eigener Profil-URL).
6. Im Tab **Report** einen HTML-Statusbericht erstellen und direkt im
   Browser oeffnen — z. B. zur Uebergabe an den Kunden.
