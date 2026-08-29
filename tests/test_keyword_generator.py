import unittest

from seo_optimizer.keyword_generator import generate_keywords, parse_einzugsgebiet


class TestParseEinzugsgebiet(unittest.TestCase):
    def test_leeres_feld(self):
        self.assertEqual(parse_einzugsgebiet(""), [])
        self.assertEqual(parse_einzugsgebiet(None), [])

    def test_kommagetrennt_mit_leerzeichen(self):
        self.assertEqual(
            parse_einzugsgebiet(" Muenchen, Augsburg ,  Rosenheim"),
            ["Muenchen", "Augsburg", "Rosenheim"],
        )


class TestGenerateKeywords(unittest.TestCase):
    def test_keine_orte_liefert_leere_liste(self):
        self.assertEqual(generate_keywords("Elektriker", ""), [])

    def test_generiert_erwartete_kombination(self):
        keywords = generate_keywords("Elektriker", "Muenchen")
        self.assertIn("Elektriker Muenchen", keywords)
        self.assertIn("Elektriker Muenchen in der Naehe", keywords)
        self.assertIn("was kostet Elektriker in Muenchen", keywords)

    def test_unbekanntes_gewerk_faellt_auf_sonstiges_zurueck(self):
        keywords = generate_keywords("Nicht Vorhanden", "Berlin")
        self.assertTrue(any("Handwerksbetrieb" in k for k in keywords))

    def test_ergebnis_ist_dedupliziert_und_sortiert(self):
        keywords = generate_keywords("Dachdecker", "Koeln, Bonn")
        self.assertEqual(keywords, sorted(set(keywords), key=str.lower))

    def test_zusatz_leistungen_werden_beruecksichtigt(self):
        keywords = generate_keywords("Elektriker", "Kiel", zusatz_leistungen=["Photovoltaik"])
        self.assertTrue(any("Photovoltaik" in k for k in keywords))


if __name__ == "__main__":
    unittest.main()
