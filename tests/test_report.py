import os
import tempfile
import unittest

from seo_optimizer.database import Database
from seo_optimizer.report import build_report_html, save_report


class TestReport(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.tmpdir.name, "test.db"))
        self.client_id = self.db.add_client({
            "firma": "Schmidt Dachdecker", "gewerk": "Dachdecker",
            "ort": "Leipzig", "einzugsgebiet": "Leipzig, Halle",
        })
        self.client = self.db.get_client(self.client_id)

    def tearDown(self):
        self.db.close()
        self.tmpdir.cleanup()

    def test_report_enthaelt_alle_abschnitte(self):
        html = build_report_html(self.client, self.db)
        # Ueberschriften mit "&" stehen HTML-maskiert als "&amp;" im Dokument.
        for abschnitt in ("SEO-Statusbericht", "Gesamt-SEO-Score",
                          "Technisches SEO &amp; OnPage", "Lokale SEO",
                          "Conversion-Optimierung", "Branchenverzeichnisse",
                          "Ranking-Entwicklung", "Redaktionsplan",
                          "Vorgeschlagene lokale Keywords"):
            with self.subTest(abschnitt=abschnitt):
                self.assertIn(abschnitt, html)

    def test_kundendaten_im_report(self):
        html = build_report_html(self.client, self.db)
        self.assertIn("Schmidt Dachdecker", html)
        self.assertIn("Leipzig", html)

    def test_rankings_erscheinen_im_report(self):
        self.db.add_ranking(self.client_id, "dachdecker leipzig", 4)
        html = build_report_html(self.client, self.db)
        self.assertIn("dachdecker leipzig", html)
        self.assertNotIn("noch keine Ranking-Messungen", html)

    def test_hinweis_ohne_rankings(self):
        self.assertIn("noch keine Ranking-Messungen", build_report_html(self.client, self.db))

    def test_content_erscheint_im_report(self):
        self.db.add_content_item(self.client_id, {"titel": "Ratgeber Dachsanierung",
                                                  "status": "Idee"})
        self.assertIn("Ratgeber Dachsanierung", build_report_html(self.client, self.db))

    def test_audit_abschnitt_nur_bei_vorhandenem_audit(self):
        self.assertNotIn("Letzte Website-Analyse", build_report_html(self.client, self.db))
        self.db.save_audit(self.client_id, "https://schmidt-dach.de", 72, 1, 4)
        html = build_report_html(self.client, self.db)
        self.assertIn("Letzte Website-Analyse", html)
        self.assertIn("schmidt-dach.de", html)

    def test_html_wird_maskiert(self):
        gefaehrlich = self.db.add_client({"firma": "<script>alert(1)</script>", "gewerk": "Maler & Lackierer"})
        html = build_report_html(self.db.get_client(gefaehrlich), self.db)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_datei_wird_geschrieben(self):
        pfad = save_report(self.client, self.db, output_dir=os.path.join(self.tmpdir.name, "reports"))
        self.assertTrue(os.path.exists(pfad))
        self.assertTrue(pfad.endswith(".html"))
        with open(pfad, encoding="utf-8") as datei:
            self.assertIn("Schmidt Dachdecker", datei.read())

    def test_erledigte_punkte_erscheinen_nicht_als_offen(self):
        self.db.set_checklist_item(self.client_id, "web_ssl", True)
        html = build_report_html(self.client, self.db)
        naechste_schritte = html.split("Wichtigste naechste Schritte")[1].split("</ul>")[0]
        self.assertNotIn("SSL-Zertifikat", naechste_schritte)


if __name__ == "__main__":
    unittest.main()
