"""Erstellung eines HTML-Statusreports je Kunde."""

import os
import re
import html
from datetime import datetime

from seo_optimizer.data import CHECKLIST_CATALOG, DIRECTORIES
from seo_optimizer.keyword_generator import generate_keywords

REPORTS_DIR = "reports"

_STYLE = """
body { font-family: 'Segoe UI', Arial, sans-serif; background:#f4f6f8; color:#1f2937; margin:0; padding:2rem; }
.container { max-width: 860px; margin: 0 auto; background:#fff; border-radius:10px; padding:2rem 2.5rem; box-shadow:0 2px 10px rgba(0,0,0,.08); }
h1 { color:#0f4c81; margin-bottom:.2rem; }
h2 { color:#0f4c81; border-bottom:2px solid #e5e9ef; padding-bottom:.3rem; margin-top:2rem; }
.meta { color:#556; margin-bottom:1.5rem; }
.score { display:inline-block; font-size:2rem; font-weight:700; color:#127a3e; }
.score-bar { background:#e5e9ef; border-radius:6px; height:14px; overflow:hidden; margin:.5rem 0 1.5rem; }
.score-bar > div { background:#1f9d55; height:100%; }
table { width:100%; border-collapse: collapse; margin-top:.5rem; }
th, td { text-align:left; padding:.4rem .6rem; border-bottom:1px solid #eee; font-size:.95rem; }
th { color:#556; font-weight:600; }
.done { color:#127a3e; }
.open { color:#b3261e; }
.tag { display:inline-block; background:#eef3f8; color:#0f4c81; border-radius:5px; padding:.15rem .5rem; margin:.15rem; font-size:.85rem; }
footer { margin-top:2rem; font-size:.8rem; color:#889; }
"""


def _slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "kunde"


def build_report_html(client, db):
    client_id = client["id"]
    gesamt, kategorien = db.checklist_progress(client_id)
    status = db.get_checklist_status(client_id)
    dir_status = db.get_directory_status(client_id)
    dir_progress = db.directory_progress(client_id)

    firma = html.escape(client.get("firma", ""))
    gewerk = html.escape(client.get("gewerk", ""))
    ort = html.escape(client.get("ort", ""))
    heute = datetime.now().strftime("%d.%m.%Y")

    kategorie_html = []
    offene_todos = []
    for kategorie, items in CHECKLIST_CATALOG.items():
        prozent = kategorien.get(kategorie, 0)
        zeilen = []
        for key, text in items:
            erledigt = status.get(key, False)
            css = "done" if erledigt else "open"
            symbol = "&#10003;" if erledigt else "&#9675;"
            zeilen.append(
                f"<tr><td class='{css}'>{symbol}</td><td>{html.escape(text)}</td></tr>"
            )
            if not erledigt:
                offene_todos.append(text)
        kategorie_html.append(
            f"""
            <h2>{html.escape(kategorie)} &mdash; {prozent}%</h2>
            <div class="score-bar"><div style="width:{prozent}%"></div></div>
            <table>{''.join(zeilen)}</table>
            """
        )

    dir_zeilen = []
    for key, name, _ in DIRECTORIES:
        eintrag = dir_status.get(key, {"eingetragen": False})
        css = "done" if eintrag["eingetragen"] else "open"
        symbol = "&#10003;" if eintrag["eingetragen"] else "&#9675;"
        dir_zeilen.append(
            f"<tr><td class='{css}'>{symbol}</td><td>{html.escape(name)}</td></tr>"
        )

    einzugsgebiet = client.get("einzugsgebiet", "")
    keywords = generate_keywords(client.get("gewerk", ""), einzugsgebiet)[:40]
    keyword_tags = "".join(f"<span class='tag'>{html.escape(k)}</span>" for k in keywords)

    todo_liste = "".join(f"<li>{html.escape(t)}</li>" for t in offene_todos[:20]) or "<li>Keine offenen Punkte &#127881;</li>"

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Lokal-SEO Report &ndash; {firma}</title>
<style>{_STYLE}</style>
</head>
<body>
<div class="container">
  <h1>Lokal-SEO Report</h1>
  <div class="meta">{firma} &bull; {gewerk} &bull; {ort} &bull; erstellt am {heute}</div>

  <div class="score">{gesamt}%</div> Gesamtfortschritt SEO-Checkliste
  <div class="score-bar"><div style="width:{gesamt}%"></div></div>

  <h2>Wichtigste offene To-Dos</h2>
  <ul>{todo_liste}</ul>

  {''.join(kategorie_html)}

  <h2>Branchenverzeichnisse (Citations) &mdash; {dir_progress}%</h2>
  <div class="score-bar"><div style="width:{dir_progress}%"></div></div>
  <table>{''.join(dir_zeilen)}</table>

  <h2>Vorgeschlagene lokale Keywords</h2>
  <div>{keyword_tags or '<em>Kein Einzugsgebiet hinterlegt.</em>'}</div>

  <footer>Erstellt mit Lokal-SEO Manager fuer Handwerksbetriebe</footer>
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
