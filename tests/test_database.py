import os
import tempfile
import unittest

from seo_optimizer.database import Database
from seo_optimizer.data import anzahl_checklisten_items, DIRECTORIES


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


if __name__ == "__main__":
    unittest.main()
