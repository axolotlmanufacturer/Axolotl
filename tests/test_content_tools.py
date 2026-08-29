import unittest

from seo_optimizer.content_tools import (
    zaehle_silben, zaehle_saetze, flesch_reading_ease, lesbarkeit_label,
    keyword_dichte, dichte_bewertung, haeufigste_begriffe, lange_saetze,
    analysiere_text, empfehlungen_zum_text, erstelle_briefing, briefing_als_text,
)

EINFACHER_TEXT = "Wir sind Ihr Elektriker. Wir kommen schnell. Der Preis ist fair."
SCHWERER_TEXT = (
    "Die Durchfuehrung der elektrotechnischen Installationsmassnahmen erfordert unter "
    "Beruecksichtigung der einschlaegigen Normenwerke eine vorausschauende "
    "Projektierungsleistung, welche die Dimensionierung der Leitungsquerschnitte "
    "sowie die Selektivitaetsbetrachtung der Schutzorgane dokumentiert."
)


class TestHilfsfunktionen(unittest.TestCase):
    def test_silben(self):
        self.assertEqual(zaehle_silben("Haus"), 1)
        self.assertEqual(zaehle_silben("Elektriker"), 4)
        self.assertGreaterEqual(zaehle_silben("x"), 1)

    def test_saetze(self):
        self.assertEqual(zaehle_saetze("Eins. Zwei! Drei?"), 3)
        self.assertEqual(zaehle_saetze("Ohne Satzzeichen"), 1)

    def test_lange_saetze(self):
        self.assertEqual(lange_saetze("Kurz und knapp."), [])
        self.assertEqual(len(lange_saetze(SCHWERER_TEXT)), 1)


class TestLesbarkeit(unittest.TestCase):
    def test_einfacher_text_ist_besser_lesbar(self):
        self.assertGreater(flesch_reading_ease(EINFACHER_TEXT), flesch_reading_ease(SCHWERER_TEXT))

    def test_wertebereich(self):
        for text in (EINFACHER_TEXT, SCHWERER_TEXT, ""):
            self.assertTrue(0 <= flesch_reading_ease(text) <= 100)

    def test_leerer_text(self):
        self.assertEqual(flesch_reading_ease(""), 0.0)

    def test_label_stufen(self):
        self.assertIn("leicht", lesbarkeit_label(85).lower())
        self.assertIn("schwer", lesbarkeit_label(10).lower())


class TestKeywordDichte(unittest.TestCase):
    def test_dichte_wird_berechnet(self):
        text = "Elektriker Muenchen " * 10  # 20 Woerter, 10 Treffer fuer "Elektriker"
        treffer, dichte = keyword_dichte(text, "Elektriker")
        self.assertEqual(treffer, 10)
        self.assertAlmostEqual(dichte, 50.0, places=1)

    def test_keyword_nicht_vorhanden(self):
        treffer, dichte = keyword_dichte("Ein Text ohne Treffer", "Dachdecker")
        self.assertEqual(treffer, 0)
        self.assertEqual(dichte, 0.0)

    def test_leeres_keyword(self):
        self.assertEqual(keyword_dichte("Irgendein Text", ""), (0, 0.0))

    def test_bewertungsstufen(self):
        self.assertEqual(dichte_bewertung(0), "Keyword fehlt im Text")
        self.assertEqual(dichte_bewertung(1.5), "Optimal")
        self.assertIn("Ueberoptimiert", dichte_bewertung(8))


class TestBegriffe(unittest.TestCase):
    def test_stoppwoerter_werden_gefiltert(self):
        text = "und der die das Badsanierung Badsanierung Badsanierung"
        begriffe = dict(haeufigste_begriffe(text))
        self.assertIn("badsanierung", begriffe)
        self.assertNotIn("und", begriffe)
        self.assertNotIn("der", begriffe)


class TestTextanalyse(unittest.TestCase):
    def test_vollstaendige_analyse(self):
        analyse = analysiere_text(EINFACHER_TEXT, "Elektriker")
        self.assertEqual(analyse["saetze"], 3)
        self.assertGreater(analyse["woerter"], 0)
        self.assertEqual(analyse["keyword_treffer"], 1)
        self.assertGreaterEqual(analyse["lesezeit_minuten"], 1)

    def test_empfehlungen_bei_schwerem_text(self):
        analyse = analysiere_text(SCHWERER_TEXT, "Dachdecker")
        tipps = empfehlungen_zum_text(analyse, wortziel=800)
        self.assertTrue(any("erweitern" in t for t in tipps))
        self.assertTrue(any("verstaendlich" in t or "kuerzen" in t.lower() for t in tipps))

    def test_empfehlungen_bei_gutem_text(self):
        guter_text = ("Wir sanieren Ihr Bad. Das Team kommt puenktlich. " * 40) + "Die Badsanierung gelingt."
        analyse = analysiere_text(guter_text, "Badsanierung")
        tipps = empfehlungen_zum_text(analyse, wortziel=100)
        self.assertTrue(len(tipps) >= 1)


class TestBriefing(unittest.TestCase):
    def test_briefing_enthaelt_alle_bausteine(self):
        briefing = erstelle_briefing("Badsanierung", "Sanitaer & Heizung (SHK)", "Leipzig")
        self.assertEqual(briefing["fokus_keyword"], "Badsanierung")
        self.assertIn("Leipzig", briefing["title_vorschlag"])
        self.assertIn("badsanierung", briefing["url_vorschlag"])
        self.assertTrue(briefing["gliederung"])
        self.assertTrue(briefing["w_fragen"])
        self.assertTrue(briefing["semantische_begriffe"])

    def test_title_wird_gekuerzt(self):
        briefing = erstelle_briefing("Photovoltaikanlage installieren lassen",
                                     "Elektriker", "Fuerstenfeldbruck")
        self.assertLessEqual(len(briefing["title_vorschlag"]), 75)

    def test_meta_maximal_160_zeichen(self):
        briefing = erstelle_briefing("Dachsanierung mit Waermedaemmung", "Dachdecker", "Muenchen")
        self.assertLessEqual(len(briefing["meta_vorschlag"]), 160)

    def test_ohne_keyword_kein_briefing(self):
        self.assertIsNone(erstelle_briefing("", "Elektriker", "Berlin"))
        self.assertIsNone(erstelle_briefing("   ", "Elektriker", "Berlin"))

    def test_ohne_ort_funktioniert(self):
        briefing = erstelle_briefing("Elektroinstallation", "Elektriker", "")
        self.assertIsNotNone(briefing)
        self.assertTrue(briefing["url_vorschlag"].startswith("/"))

    def test_umlaute_im_slug(self):
        briefing = erstelle_briefing("Tueren einbauen", "Tischler & Schreiner", "Koeln")
        self.assertNotIn(" ", briefing["url_vorschlag"])

    def test_textausgabe(self):
        briefing = erstelle_briefing("Heizungswartung", "Sanitaer & Heizung (SHK)", "Kiel")
        text = briefing_als_text(briefing)
        self.assertIn("CONTENT-BRIEFING", text)
        self.assertIn("GLIEDERUNG", text)
        self.assertIn("Heizungswartung", text)
        self.assertEqual(briefing_als_text(None), "")


if __name__ == "__main__":
    unittest.main()
