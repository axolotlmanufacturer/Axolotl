import unittest

from seo_optimizer.onpage_analyzer import (
    analysiere_html, berechne_score, lade_seite, AuditFehler,
    KRITISCH, WARNUNG, HINWEIS, OK,
)

GUTE_SEITE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Elektriker Muenchen - Elektroinstallation vom Meisterbetrieb</title>
<meta name="description" content="Ihr Elektriker in Muenchen: Elektroinstallation, E-Check und Notdienst vom Meisterbetrieb. Jetzt kostenloses Angebot anfordern und schnell Termin sichern.">
<link rel="canonical" href="https://example.de/">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Electrician","name":"Mueller Elektro"}
</script>
</head>
<body>
<h1>Elektriker Muenchen fuer Installation und Notdienst</h1>
<p>Rufen Sie uns an unter <a href="tel:+49891234567">089 1234567</a>.</p>
<h2>Leistungen</h2>
<p>WORTFUELLER </p>
<img src="/a.jpg" alt="Team vor Ort">
<form action="/anfrage"><input name="name"></form>
<a href="/leistungen">Leistungen</a>
<a href="/kontakt">Kontakt</a>
<a href="/impressum">Impressum</a>
<a href="/referenzen">Referenzen</a>
</body>
</html>"""

SCHLECHTE_SEITE = """<html>
<head><title>Start</title><meta name="robots" content="noindex"></head>
<body>
<h1>Eins</h1><h1>Zwei</h1><h4>Sprung</h4>
<p>Kurz.</p>
<img src="/a.jpg">
<a href="/x">x</a>
</body>
</html>"""


def _befund(ergebnis, titel):
    for befund in ergebnis["befunde"]:
        if befund["titel"] == titel:
            return befund
    return None


class TestGuteSeite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Text kuenstlich auf ueber 300 Woerter bringen, damit der Umfang passt.
        html = GUTE_SEITE.replace("WORTFUELLER ", "Elektroinstallation Muenchen " * 160)
        cls.ergebnis = analysiere_html(html, "https://example.de/",
                                       fokus_keyword="Elektriker Muenchen")

    def test_hoher_score(self):
        self.assertGreater(self.ergebnis["score"], 85)

    def test_keine_kritischen_maengel(self):
        self.assertEqual(self.ergebnis["anzahl"][KRITISCH], 0)

    def test_wichtige_pruefungen_bestanden(self):
        for titel in ("HTTPS", "Indexierbarkeit", "Canonical-Tag", "Mobile Viewport",
                      "Sprachauszeichnung", "Title-Tag", "Meta-Description",
                      "H1-Ueberschrift", "Alt-Texte", "Klick-to-Call",
                      "Kontaktformular", "Impressum", "Strukturierte Daten"):
            with self.subTest(pruefung=titel):
                self.assertEqual(_befund(self.ergebnis, titel)["schwere"], OK)

    def test_kennzahlen_vorhanden(self):
        self.assertGreater(self.ergebnis["kennzahlen"]["Woerter"], 300)
        self.assertEqual(self.ergebnis["kennzahlen"]["Interne Links"], 4)


class TestSchlechteSeite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ergebnis = analysiere_html(SCHLECHTE_SEITE, "http://example.de/",
                                       fokus_keyword="Dachdecker Leipzig")

    def test_niedriger_score(self):
        self.assertLess(self.ergebnis["score"], 25)

    def test_kritische_maengel_erkannt(self):
        self.assertEqual(_befund(self.ergebnis, "HTTPS")["schwere"], KRITISCH)
        self.assertEqual(_befund(self.ergebnis, "Indexierbarkeit")["schwere"], KRITISCH)
        self.assertEqual(_befund(self.ergebnis, "Mobile Viewport")["schwere"], KRITISCH)
        self.assertEqual(_befund(self.ergebnis, "Meta-Description")["schwere"], KRITISCH)

    def test_mehrere_h1_gemeldet(self):
        befund = _befund(self.ergebnis, "H1-Ueberschrift")
        self.assertEqual(befund["schwere"], WARNUNG)
        self.assertIn("2", befund["hinweis"])

    def test_ebenensprung_gemeldet(self):
        self.assertEqual(_befund(self.ergebnis, "Ueberschriften-Hierarchie")["schwere"], HINWEIS)

    def test_fehlende_alt_texte(self):
        self.assertEqual(_befund(self.ergebnis, "Alt-Texte")["schwere"], WARNUNG)

    def test_fehlendes_impressum(self):
        self.assertEqual(_befund(self.ergebnis, "Impressum")["schwere"], WARNUNG)


class TestParserDetails(unittest.TestCase):
    def test_skript_und_style_zaehlen_nicht_zum_text(self):
        html = ("<html><body><h1>T</h1><script>var geheim = 'wortwortwort';</script>"
                "<style>.a{color:red}</style><p>Sichtbarer Text</p></body></html>")
        ergebnis = analysiere_html(html, "https://example.de/")
        self.assertNotIn("geheim", str(ergebnis["kennzahlen"]))
        self.assertEqual(ergebnis["kennzahlen"]["Woerter"], 3)

    def test_ungueltiges_jsonld_wird_gemeldet(self):
        html = ('<html><head><script type="application/ld+json">{kaputt,,}</script></head>'
                '<body><h1>T</h1></body></html>')
        ergebnis = analysiere_html(html, "https://example.de/")
        self.assertEqual(_befund(ergebnis, "Strukturierte Daten")["schwere"], WARNUNG)

    def test_interne_und_externe_links_unterschieden(self):
        html = ('<html><body><h1>T</h1>'
                '<a href="/intern">i</a><a href="https://www.example.de/auch-intern">i2</a>'
                '<a href="https://fremd.de/x">e</a>'
                '<a href="#anker">a</a><a href="mailto:a@b.de">m</a>'
                '</body></html>')
        ergebnis = analysiere_html(html, "https://example.de/")
        self.assertEqual(ergebnis["kennzahlen"]["Interne Links"], 2)
        self.assertEqual(ergebnis["kennzahlen"]["Externe Links"], 1)

    def test_keyword_stuffing_wird_erkannt(self):
        html = f"<html><body><h1>T</h1><p>{'Dachdecker ' * 100}</p></body></html>"
        ergebnis = analysiere_html(html, "https://example.de/", fokus_keyword="Dachdecker")
        self.assertEqual(_befund(ergebnis, "Keyword-Dichte")["schwere"], WARNUNG)

    def test_langsame_antwortzeit(self):
        ergebnis = analysiere_html(GUTE_SEITE, "https://example.de/", ladezeit=8.0)
        self.assertEqual(_befund(ergebnis, "Antwortzeit")["schwere"], KRITISCH)

    def test_telefonnummer_wird_erkannt(self):
        html = "<html><body><h1>T</h1><p>Rufen Sie 089 1234567 an.</p></body></html>"
        ergebnis = analysiere_html(html, "https://example.de/")
        self.assertEqual(_befund(ergebnis, "Telefonnummer")["schwere"], OK)


class TestScore(unittest.TestCase):
    def test_nur_ok_ergibt_100(self):
        self.assertEqual(berechne_score([{"schwere": OK}] * 5), 100)

    def test_leere_liste(self):
        self.assertEqual(berechne_score([]), 0)

    def test_kritisch_wiegt_schwerer_als_hinweis(self):
        mit_kritisch = berechne_score([{"schwere": OK}] * 9 + [{"schwere": KRITISCH}])
        mit_hinweis = berechne_score([{"schwere": OK}] * 9 + [{"schwere": HINWEIS}])
        self.assertLess(mit_kritisch, mit_hinweis)


class TestAbruf(unittest.TestCase):
    def test_ungueltiges_schema_wird_abgelehnt(self):
        for url in ("ftp://example.de", "file:///etc/passwd", "example.de"):
            with self.subTest(url=url):
                with self.assertRaises(AuditFehler):
                    lade_seite(url)


if __name__ == "__main__":
    unittest.main()
