import os
import tempfile
import unittest

from seo_optimizer.database import Database
from seo_optimizer.data import anzahl_checklisten_items, DIRECTORIES, CHECKLIST_CATALOG
from seo_optimizer.data_seo import TECHNICAL_SEO_CATALOG, CRO_CATALOG


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "test.db")
        self.db = Database(self.db_path)

    def tearDown(self):
        self.db.close()
        self.tmpdir.cleanup()

    def test_kunde_anlegen_und_lesen(self):
        client_id = self.db.add_client({"firma": "Mueller Elektro", "gewerk": "Elektriker", "ort": "Muenchen"})
        client = self.db.get_client(client_id)
        self.assertEqual(client["firma"], "Mueller Elektro")
        self.assertEqual(client["gewerk"], "Elektriker")
        self.assertIn("erstellt_am", client)

    def test_kunde_aktualisieren(self):
        client_id = self.db.add_client({"firma": "Alt GmbH"})
        self.db.update_client(client_id, {"firma": "Neu GmbH", "ort": "Berlin"})
        client = self.db.get_client(client_id)
        self.assertEqual(client["firma"], "Neu GmbH")
        self.assertEqual(client["ort"], "Berlin")

    def test_kunde_loeschen(self):
        client_id = self.db.add_client({"firma": "Wird geloescht"})
        self.db.delete_client(client_id)
        self.assertIsNone(self.db.get_client(client_id))

    def test_checkliste_default_alles_offen(self):
        client_id = self.db.add_client({"firma": "Neu"})
        status = self.db.get_checklist_status(client_id)
        self.assertEqual(len(status), anzahl_checklisten_items())
        self.assertTrue(all(v is False for v in status.values()))

    def test_checkliste_item_setzen_und_fortschritt(self):
        client_id = self.db.add_client({"firma": "Fortschritt Test"})
        self.db.set_checklist_item(client_id, "gmb_claimed", True)
        status = self.db.get_checklist_status(client_id)
        self.assertTrue(status["gmb_claimed"])
        gesamt, kategorien = self.db.checklist_progress(client_id)
        self.assertGreater(gesamt, 0)
        self.assertGreater(kategorien["Google Unternehmensprofil"], 0)

    def test_checkliste_item_toggle_idempotent(self):
        client_id = self.db.add_client({"firma": "Toggle Test"})
        self.db.set_checklist_item(client_id, "web_ssl", True)
        self.db.set_checklist_item(client_id, "web_ssl", False)
        status = self.db.get_checklist_status(client_id)
        self.assertFalse(status["web_ssl"])

    def test_verzeichnis_status_default_und_setzen(self):
        client_id = self.db.add_client({"firma": "Verzeichnis Test"})
        status = self.db.get_directory_status(client_id)
        self.assertEqual(len(status), len(DIRECTORIES))
        self.db.set_directory_item(client_id, "google_gmb", True, profil_url="https://g.page/x")
        status = self.db.get_directory_status(client_id)
        self.assertTrue(status["google_gmb"]["eingetragen"])
        self.assertEqual(status["google_gmb"]["profil_url"], "https://g.page/x")
        self.assertEqual(self.db.directory_progress(client_id), round(1 / len(DIRECTORIES) * 100))

    def test_kunden_liste_alphabetisch(self):
        self.db.add_client({"firma": "Zimmerei Zorn"})
        self.db.add_client({"firma": "Anders Bau"})
        clients = self.db.get_clients()
        self.assertEqual([c["firma"] for c in clients], ["Anders Bau", "Zimmerei Zorn"])


class TestKataloge(unittest.TestCase):
    """Die drei Checklisten teilen sich eine Tabelle und muessen getrennt bleiben."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.tmpdir.name, "test.db"))
        self.client_id = self.db.add_client({"firma": "Katalog Test"})

    def tearDown(self):
        self.db.close()
        self.tmpdir.cleanup()

    def test_keys_sind_ueber_kataloge_eindeutig(self):
        alle = []
        for katalog in (CHECKLIST_CATALOG, TECHNICAL_SEO_CATALOG, CRO_CATALOG):
            alle += [key for items in katalog.values() for key, _ in items]
        self.assertEqual(len(alle), len(set(alle)), "Doppelte Checklisten-Keys gefunden")

    def test_fortschritt_je_katalog_getrennt(self):
        self.db.set_checklist_item(self.client_id, "tech_sitemap", True)
        technik, _ = self.db.checklist_progress(self.client_id, TECHNICAL_SEO_CATALOG)
        lokal, _ = self.db.checklist_progress(self.client_id, CHECKLIST_CATALOG)
        cro, _ = self.db.checklist_progress(self.client_id, CRO_CATALOG)
        self.assertGreater(technik, 0)
        self.assertEqual(lokal, 0)
        self.assertEqual(cro, 0)

    def test_status_enthaelt_nur_katalog_keys(self):
        status = self.db.get_checklist_status(self.client_id, CRO_CATALOG)
        self.assertNotIn("tech_sitemap", status)
        self.assertIn("cro_bewertungen", status)

    def test_offene_punkte_respektiert_limit(self):
        offen = self.db.offene_punkte(self.client_id, TECHNICAL_SEO_CATALOG, limit=3)
        self.assertEqual(len(offen), 3)
        self.assertTrue(all(len(eintrag) == 2 for eintrag in offen))

    def test_erledigte_punkte_verschwinden_aus_offenen(self):
        vorher = len(self.db.offene_punkte(self.client_id, CRO_CATALOG))
        self.db.set_checklist_item(self.client_id, "cro_bewertungen", True)
        nachher = len(self.db.offene_punkte(self.client_id, CRO_CATALOG))
        self.assertEqual(nachher, vorher - 1)

    def test_gesamtscore_gewichtet(self):
        leer, _ = self.db.gesamt_score(self.client_id)
        self.assertEqual(leer, 0)
        for katalog in (CHECKLIST_CATALOG, TECHNICAL_SEO_CATALOG, CRO_CATALOG):
            for items in katalog.values():
                for key, _ in items:
                    self.db.set_checklist_item(self.client_id, key, True)
        for key, _, _ in DIRECTORIES:
            self.db.set_directory_item(self.client_id, key, True)
        voll, teilbereiche = self.db.gesamt_score(self.client_id)
        self.assertEqual(voll, 100)
        self.assertEqual(set(teilbereiche), {"Technik & OnPage", "Lokale SEO",
                                             "Conversion", "Verzeichnisse"})


class TestRankings(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.tmpdir.name, "test.db"))
        self.client_id = self.db.add_client({"firma": "Ranking Test"})

    def tearDown(self):
        self.db.close()
        self.tmpdir.cleanup()

    def test_verlauf_chronologisch(self):
        self.db.add_ranking(self.client_id, "kw", 12, datum="2026-03-01")
        self.db.add_ranking(self.client_id, "kw", 20, datum="2026-01-01")
        self.db.add_ranking(self.client_id, "kw", 8, datum="2026-02-01")
        verlauf = self.db.get_ranking_history(self.client_id, "kw")
        self.assertEqual([e["datum"] for e in verlauf],
                         ["2026-01-01", "2026-02-01", "2026-03-01"])

    def test_veraenderung_positiv_bei_verbesserung(self):
        self.db.add_ranking(self.client_id, "kw", 10, datum="2026-01-01")
        self.db.add_ranking(self.client_id, "kw", 4, datum="2026-02-01")
        eintrag = self.db.get_ranking_overview(self.client_id)[0]
        self.assertEqual(eintrag["aktuell"], 4)
        self.assertEqual(eintrag["vorher"], 10)
        self.assertEqual(eintrag["veraenderung"], 6)
        self.assertEqual(eintrag["beste"], 4)

    def test_veraenderung_negativ_bei_verschlechterung(self):
        self.db.add_ranking(self.client_id, "kw", 3, datum="2026-01-01")
        self.db.add_ranking(self.client_id, "kw", 9, datum="2026-02-01")
        self.assertEqual(self.db.get_ranking_overview(self.client_id)[0]["veraenderung"], -6)

    def test_einzelmessung_ohne_veraenderung(self):
        self.db.add_ranking(self.client_id, "kw", 5)
        self.assertIsNone(self.db.get_ranking_overview(self.client_id)[0]["veraenderung"])

    def test_summary_kennzahlen(self):
        for keyword, position in [("a", 2), ("b", 7), ("c", 25)]:
            self.db.add_ranking(self.client_id, keyword, position)
        kennzahlen = self.db.ranking_summary(self.client_id)
        self.assertEqual(kennzahlen["keywords"], 3)
        self.assertEqual(kennzahlen["top3"], 1)
        self.assertEqual(kennzahlen["top10"], 2)
        self.assertAlmostEqual(kennzahlen["durchschnitt"], 11.3, places=1)

    def test_summary_ohne_daten(self):
        kennzahlen = self.db.ranking_summary(self.client_id)
        self.assertEqual(kennzahlen["keywords"], 0)
        self.assertIsNone(kennzahlen["durchschnitt"])

    def test_keyword_loeschen(self):
        self.db.add_ranking(self.client_id, "kw", 5)
        self.db.delete_ranking_keyword(self.client_id, "kw")
        self.assertEqual(self.db.get_ranking_overview(self.client_id), [])


class TestContentUndAudits(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.tmpdir.name, "test.db"))
        self.client_id = self.db.add_client({"firma": "Content Test"})

    def tearDown(self):
        self.db.close()
        self.tmpdir.cleanup()

    def test_content_anlegen_aendern_loeschen(self):
        item_id = self.db.add_content_item(self.client_id, {"titel": "Erst", "status": "Idee"})
        self.assertEqual(self.db.get_content_items(self.client_id)[0]["titel"], "Erst")
        self.db.update_content_item(item_id, {"titel": "Zweit", "status": "Veroeffentlicht",
                                              "wortziel": 900})
        item = self.db.get_content_items(self.client_id)[0]
        self.assertEqual(item["titel"], "Zweit")
        self.assertEqual(item["wortziel"], 900)
        self.db.delete_content_item(item_id)
        self.assertEqual(self.db.get_content_items(self.client_id), [])

    def test_content_summary(self):
        self.db.add_content_item(self.client_id, {"titel": "A", "status": "Idee"})
        self.db.add_content_item(self.client_id, {"titel": "B", "status": "Idee"})
        self.db.add_content_item(self.client_id, {"titel": "C", "status": "Veroeffentlicht"})
        summary = self.db.content_summary(self.client_id)
        self.assertEqual(summary["gesamt"], 3)
        self.assertEqual(summary["Idee"], 2)
        self.assertEqual(summary["Veroeffentlicht"], 1)

    def test_audit_speichern_und_neuesten_lesen(self):
        self.assertIsNone(self.db.get_latest_audit(self.client_id))
        self.db.save_audit(self.client_id, "https://a.de", 60, 2, 3)
        self.db.save_audit(self.client_id, "https://b.de", 80, 0, 1)
        letzter = self.db.get_latest_audit(self.client_id)
        self.assertEqual(letzter["score"], 80)
        self.assertEqual(letzter["url"], "https://b.de")

    def test_loeschen_raeumt_alle_tabellen(self):
        self.db.add_ranking(self.client_id, "kw", 5)
        self.db.add_content_item(self.client_id, {"titel": "A"})
        self.db.save_audit(self.client_id, "https://a.de", 60)
        self.db.set_checklist_item(self.client_id, "tech_sitemap", True)
        self.db.delete_client(self.client_id)
        self.assertEqual(self.db.get_ranking_overview(self.client_id), [])
        self.assertEqual(self.db.get_content_items(self.client_id), [])
        self.assertIsNone(self.db.get_latest_audit(self.client_id))
        gesamt, _ = self.db.gesamt_score(self.client_id)
        self.assertEqual(gesamt, 0)


if __name__ == "__main__":
    unittest.main()
