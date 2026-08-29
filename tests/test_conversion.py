import unittest

from seo_optimizer.conversion import (
    ctr_fuer_position, geschaetzte_besucher, potenzial_durch_verbesserung,
    trichter, roi, break_even_auftraege, ab_test, benoetigte_stichprobe,
)


class TestCtrUndPotenzial(unittest.TestCase):
    def test_ctr_bekannte_positionen(self):
        self.assertGreater(ctr_fuer_position(1), ctr_fuer_position(2))
        self.assertGreater(ctr_fuer_position(10), ctr_fuer_position(15))
        self.assertGreater(ctr_fuer_position(15), ctr_fuer_position(30))

    def test_ctr_ungueltige_position(self):
        self.assertEqual(ctr_fuer_position(0), 0.0)
        self.assertEqual(ctr_fuer_position(None), 0.0)

    def test_geschaetzte_besucher(self):
        self.assertEqual(geschaetzte_besucher(1000, 1), 276)
        self.assertEqual(geschaetzte_besucher(0, 1), 0)

    def test_potenzial_bei_verbesserung_ist_positiv(self):
        ergebnis = potenzial_durch_verbesserung(1000, 8, 3)
        self.assertGreater(ergebnis["zusaetzlich"], 0)
        self.assertEqual(
            ergebnis["zusaetzlich"],
            ergebnis["besucher_ziel"] - ergebnis["besucher_aktuell"],
        )


class TestTrichter(unittest.TestCase):
    def test_trichter_rechnet_korrekt_durch(self):
        ergebnis = trichter(besucher=1000, anfrage_rate=3, abschlussquote=50, auftragswert=2000)
        self.assertEqual(ergebnis["anfragen"], 30.0)
        self.assertEqual(ergebnis["auftraege"], 15.0)
        self.assertEqual(ergebnis["umsatz"], 30000.0)

    def test_trichter_ohne_besucher(self):
        ergebnis = trichter(0, 3, 50, 2000)
        self.assertEqual(ergebnis["umsatz"], 0)
        self.assertEqual(ergebnis["umsatz_je_besucher"], 0.0)


class TestRoi(unittest.TestCase):
    def test_roi_positiv(self):
        ergebnis = roi(umsatz=10000, marge_prozent=30, kosten=1000)
        self.assertEqual(ergebnis["deckungsbeitrag"], 3000.0)
        self.assertEqual(ergebnis["gewinn"], 2000.0)
        self.assertEqual(ergebnis["roi_prozent"], 200.0)
        self.assertTrue(ergebnis["rentabel"])

    def test_roi_negativ(self):
        ergebnis = roi(umsatz=1000, marge_prozent=10, kosten=500)
        self.assertFalse(ergebnis["rentabel"])

    def test_roi_ohne_kosten(self):
        self.assertIsNone(roi(1000, 20, 0)["roi_prozent"])

    def test_break_even(self):
        self.assertEqual(break_even_auftraege(1000, 2000, 25), 2)
        self.assertIsNone(break_even_auftraege(1000, 2000, 0))


class TestAbTest(unittest.TestCase):
    def test_signifikanter_unterschied(self):
        # 10 % gegen 13 % bei je 1000 Besuchern ist auf dem 95-%-Niveau signifikant.
        ergebnis = ab_test(1000, 100, 1000, 130)
        self.assertAlmostEqual(ergebnis["z_wert"], 2.103, places=2)
        self.assertLess(ergebnis["p_wert"], 0.05)
        self.assertTrue(ergebnis["signifikant"])
        self.assertEqual(ergebnis["gewinner"], "Variante B")
        self.assertEqual(ergebnis["uplift_prozent"], 30.0)

    def test_kein_signifikanter_unterschied(self):
        ergebnis = ab_test(1000, 100, 1000, 101)
        self.assertFalse(ergebnis["signifikant"])
        self.assertEqual(ergebnis["gewinner"], "Kein signifikanter Unterschied")

    def test_variante_a_gewinnt(self):
        ergebnis = ab_test(1000, 150, 1000, 100)
        self.assertTrue(ergebnis["signifikant"])
        self.assertEqual(ergebnis["gewinner"], "Variante A")

    def test_identische_varianten(self):
        ergebnis = ab_test(500, 50, 500, 50)
        self.assertEqual(ergebnis["z_wert"], 0.0)
        self.assertFalse(ergebnis["signifikant"])

    def test_ungueltige_eingaben(self):
        with self.assertRaises(ValueError):
            ab_test(0, 0, 100, 10)
        with self.assertRaises(ValueError):
            ab_test(100, 200, 100, 10)
        with self.assertRaises(ValueError):
            ab_test(100, -1, 100, 10)

    def test_stichprobenberechnung(self):
        # Referenzwert gaengiger Rechner: ca. 14.000-16.000 je Variante.
        umfang = benoetigte_stichprobe(10, 10)
        self.assertTrue(14000 < umfang < 16000, f"unerwarteter Umfang: {umfang}")

    def test_stichprobe_bei_ungueltigen_werten(self):
        self.assertIsNone(benoetigte_stichprobe(0, 10))
        self.assertIsNone(benoetigte_stichprobe(10, 0))
        self.assertIsNone(benoetigte_stichprobe(95, 20))


if __name__ == "__main__":
    unittest.main()
