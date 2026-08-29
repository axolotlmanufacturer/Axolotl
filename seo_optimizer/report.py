"""Erstellung eines HTML-Statusreports je Kunde."""

import os
import re
import html
from datetime import datetime

from seo_optimizer.data import CHECKLIST_CATALOG, DIRECTORIES
from seo_optimizer.data_seo import TECHNICAL_SEO_CATALOG, CRO_CATALOG
from seo_optimizer.keyword_generator import generate_keywords

REPORTS_DIR = "reports"

_STYLE = """
body { font-family: 'Segoe UI', Arial, sans-serif; background:#f4f6f8; color:#1f2937; margin:0; padding:2rem; }
.container { max-width: 900px; margin: 0 auto; background:#fff; border-radius:10px; padding:2rem 2.5rem; box-shadow:0 2px 10px rgba(0,0,0,.08); }
h1 { color:#0f4c81; margin-bottom:.2rem; }
h2 { color:#0f4c81; border-bottom:2px solid #e5e9ef; padding-bottom:.3rem; margin-top:2rem; }
h3 { color:#334155; margin-top:1.4rem; margin-bottom:.3rem; font-size:1rem; }
.meta { color:#556; margin-bottom:1.5rem; }
.score { display:inline-block; font-size:2.4rem; font-weight:700; color:#127a3e; }
.score-bar { background:#e5e9ef; border-radius:6px; height:14px; overflow:hidden; margin:.5rem 0 1.2rem; }
.score-bar > div { background:#1f9d55; height:100%; }
table { width:100%; border-collapse: collapse; margin-top:.5rem; }
th, td { text-align:left; padding:.4rem .6rem; border-bottom:1px solid #eee; font-size:.95rem; }
th { color:#556; font-weight:600; }
.done { color:#127a3e; }
.open { color:#b3261e; }
.tag { display:inline-block; background:#eef3f8; color:#0f4c81; border-radius:5px; padding:.15rem .5rem; margin:.15rem; font-size:.85rem; }
.kacheln { display:flex; flex-wrap:wrap; gap:.8rem; margin:1rem 0; }
.kachel { flex:1 1 150px; border:1px solid #e5e9ef; border-radius:8px; padding:.8rem 1rem; }
.kachel .wert { font-size:1.6rem; font-weight:700; color:#0f4c81; }
.kachel .label { font-size:.8rem; color:#6b7280; }
.hinweis { background:#fff8e6; border-left:4px solid #d99e00; padding:.6rem .9rem; margin:1rem 0; font-size:.9rem; }
footer { margin-top:2rem; font-size:.8rem; color:#889; }
"""


def _slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "kunde"


def _fortschritt_block(titel, prozent):
    return (f"<h3>{html.escape(titel)} &mdash; {prozent}%</h3>"
            f"<div class=\"score-bar\"><div style=\"width:{prozent}%\"></div></div>")


def _checklisten_abschnitt(ueberschrift, catalog, db, client_id):
    """Rendert einen kompletten Checklisten-Katalog inkl. Kategoriefortschritt."""
    gesamt, kategorien = db.checklist_progress(client_id, catalog)
    status = db.get_checklist_status(client_id, catalog)

    teile = [f"<h2>{html.escape(ueberschrift)} &mdash; {gesamt}%</h2>",
             f"<div class=\"score-bar\"><div style=\"width:{gesamt}%\"></div></div>"]
    for kategorie, items in catalog.items():
        zeilen = []
        for key, text in items:
            erledigt = status.get(key, False)
            css = "done" if erledigt else "open"
            symbol = "&#10003;" if erledigt else "&#9675;"
            zeilen.append(f"<tr><td class='{css}' width='24'>{symbol}</td>"
                          f"<td>{html.escape(text)}</td></tr>")
        teile.append(_fortschritt_block(kategorie, kategorien.get(kategorie, 0)))
        teile.append(f"<table>{''.join(zeilen)}</table>")
    return "".join(teile)


def _offene_todos(db, client_id, limit=12):
    """Wichtigste offene Massnahmen ueber alle Kataloge hinweg."""
    eintraege = []
    for bereich, catalog in (
        ("Technik & OnPage", TECHNICAL_SEO_CATALOG),
        ("Lokale SEO", CHECKLIST_CATALOG),
        ("Conversion", CRO_CATALOG),
    ):
        for _, massnahme in db.offene_punkte(client_id, catalog, limit=4):
            eintraege.append((bereich, massnahme))
    if not eintraege:
        return "<li>Alle Checklistenpunkte sind erledigt &#127881;</li>"
    return "".join(
        f"<li><strong>{html.escape(bereich)}:</strong> {html.escape(massnahme)}</li>"
        for bereich, massnahme in eintraege[:limit]
    )


def _ranking_abschnitt(db, client_id):
    uebersicht = db.get_ranking_overview(client_id)
    if not uebersicht:
        return ("<h2>Ranking-Entwicklung</h2>"
                "<p><em>Es sind noch keine Ranking-Messungen erfasst.</em></p>")

    kennzahlen = db.ranking_summary(client_id)
    kacheln = f"""
    <div class="kacheln">
      <div class="kachel"><div class="wert">{kennzahlen['keywords']}</div><div class="label">ueberwachte Keywords</div></div>
      <div class="kachel"><div class="wert">{kennzahlen['top3']}</div><div class="label">in den Top 3</div></div>
      <div class="kachel"><div class="wert">{kennzahlen['top10']}</div><div class="label">in den Top 10</div></div>
      <div class="kachel"><div class="wert">{kennzahlen['durchschnitt']}</div><div class="label">Durchschnittsposition</div></div>
    </div>"""

    zeilen = []
    for eintrag in uebersicht:
        veraenderung = eintrag["veraenderung"]
        if veraenderung is None:
            trend, css = "neu", ""
        elif veraenderung > 0:
            trend, css = f"+{veraenderung}", "done"
        elif veraenderung < 0:
            trend, css = str(veraenderung), "open"
        else:
            trend, css = "0", ""
        zeilen.append(
            f"<tr><td>{html.escape(eintrag['keyword'])}</td>"
            f"<td>{eintrag['aktuell']}</td>"
            f"<td class='{css}'>{trend}</td>"
            f"<td>{eintrag['beste']}</td>"
            f"<td>{html.escape(eintrag['datum'])}</td></tr>"
        )

    return f"""
    <h2>Ranking-Entwicklung</h2>
    {kacheln}
    <table>
      <tr><th>Keyword</th><th>Position</th><th>Trend</th><th>Beste</th><th>Letzte Messung</th></tr>
      {''.join(zeilen)}
    </table>"""


def _content_abschnitt(db, client_id):
    items = db.get_content_items(client_id)
    if not items:
        return ("<h2>Redaktionsplan</h2>"
                "<p><em>Es sind noch keine Inhalte geplant.</em></p>")
    zeilen = "".join(
        f"<tr><td>{html.escape(item['titel'])}</td>"
        f"<td>{html.escape(item.get('typ') or '')}</td>"
        f"<td>{html.escape(item.get('fokus_keyword') or '')}</td>"
        f"<td>{html.escape(item.get('status') or '')}</td>"
        f"<td>{html.escape(item.get('faellig_am') or '')}</td></tr>"
        for item in items
    )
    return f"""
    <h2>Redaktionsplan ({len(items)} Inhalte)</h2>
    <table>
      <tr><th>Titel</th><th>Typ</th><th>Fokus-Keyword</th><th>Status</th><th>Faellig am</th></tr>
      {zeilen}
    </table>"""


def _audit_abschnitt(db, client_id):
    audit = db.get_latest_audit(client_id)
    if not audit:
        return ""
    datum = (audit.get("datum") or "")[:10]
    return f"""
    <h2>Letzte Website-Analyse</h2>
    <div class="kacheln">
      <div class="kachel"><div class="wert">{audit['score']}</div><div class="label">OnPage-Score</div></div>
      <div class="kachel"><div class="wert">{audit['kritisch']}</div><div class="label">kritische Maengel</div></div>
      <div class="kachel"><div class="wert">{audit['warnungen']}</div><div class="label">Warnungen</div></div>
    </div>
    <p class="meta">Geprueft: {html.escape(audit['url'])} (Stand {html.escape(datum)})</p>"""


def build_report_html(client, db):
    client_id = client["id"]
    gesamt_score, teilbereiche = db.gesamt_score(client_id)
    dir_status = db.get_directory_status(client_id)
    dir_progress = db.directory_progress(client_id)

    firma = html.escape(client.get("firma", ""))
    gewerk = html.escape(client.get("gewerk", ""))
    ort = html.escape(client.get("ort", ""))
    heute = datetime.now().strftime("%d.%m.%Y")

    teilbereich_kacheln = "".join(
        f"<div class=\"kachel\"><div class=\"wert\">{wert}%</div>"
        f"<div class=\"label\">{html.escape(name)}</div></div>"
        for name, wert in teilbereiche.items()
    )

    dir_zeilen = "".join(
        f"<tr><td class='{'done' if dir_status.get(key, {}).get('eingetragen') else 'open'}' width='24'>"
        f"{'&#10003;' if dir_status.get(key, {}).get('eingetragen') else '&#9675;'}</td>"
        f"<td>{html.escape(name)}</td></tr>"
        for key, name, _ in DIRECTORIES
    )

    keywords = generate_keywords(client.get("gewerk", ""), client.get("einzugsgebiet", ""))[:40]
    keyword_tags = "".join(f"<span class='tag'>{html.escape(k)}</span>" for k in keywords)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>SEO-Report &ndash; {firma}</title>
<style>{_STYLE}</style>
</head>
<body>
<div class="container">
  <h1>SEO-Statusbericht</h1>
  <div class="meta">{firma} &bull; {gewerk} &bull; {ort} &bull; erstellt am {heute}</div>

  <div class="score">{gesamt_score}</div> <span class="label">von 100 Punkten Gesamt-SEO-Score</span>
  <div class="score-bar"><div style="width:{gesamt_score}%"></div></div>
  <div class="kacheln">{teilbereich_kacheln}</div>

  <h2>Wichtigste naechste Schritte</h2>
  <ul>{_offene_todos(db, client_id)}</ul>

  {_audit_abschnitt(db, client_id)}

  {_ranking_abschnitt(db, client_id)}

  {_content_abschnitt(db, client_id)}

  {_checklisten_abschnitt("Technisches SEO & OnPage", TECHNICAL_SEO_CATALOG, db, client_id)}

  {_checklisten_abschnitt("Lokale SEO", CHECKLIST_CATALOG, db, client_id)}

  {_checklisten_abschnitt("Conversion-Optimierung", CRO_CATALOG, db, client_id)}

  <h2>Branchenverzeichnisse (Citations) &mdash; {dir_progress}%</h2>
  <div class="score-bar"><div style="width:{dir_progress}%"></div></div>
  <table>{dir_zeilen}</table>

  <h2>Vorgeschlagene lokale Keywords</h2>
  <div>{keyword_tags or '<em>Kein Einzugsgebiet hinterlegt.</em>'}</div>

  <footer>Erstellt mit dem SEO-Manager fuer Handwerksbetriebe</footer>
</div>
</body>
</html>"""


def save_report(client, db, output_dir=REPORTS_DIR):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{_slugify(client.get('firma', 'kunde'))}-{timestamp}.html"
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(build_report_html(client, db))
    return path
