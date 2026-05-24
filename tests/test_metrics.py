import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from asr_benchmark.metrics import (
    char_error_rate,
    fuzzy_locality_match,
    locality_correct,
    partial_locality_match,
    transliterate_devanagari,
    word_error_rate,
)
from asr_benchmark.locality_matcher import LocalityMatcher


class MetricTests(unittest.TestCase):
    def test_exact_locality_match_ignores_case_and_punctuation(self):
        self.assertTrue(locality_correct("main koramangala mein rehta hoon.", "Koramangala"))

    def test_partial_match_flags_multiword_locality(self):
        self.assertTrue(partial_locality_match("I stay near HSR", "HSR Layout"))

    def test_fuzzy_match_catches_spelling_drift(self):
        self.assertTrue(fuzzy_locality_match("main byatrayanapura mein hoon", "Byatarayanapura"))

    def test_word_error_rate(self):
        self.assertAlmostEqual(word_error_rate("main hebbal mein hoon", "main hebbal hoon"), 0.25)

    def test_char_error_rate_is_zero_for_case_only_difference(self):
        self.assertEqual(char_error_rate("Whitefield", "whitefield"), 0.0)

    def test_devanagari_output_can_match_roman_locality(self):
        self.assertTrue(locality_correct("मेरा एरिया इंदिरानगर है", "Indiranagar"))
        self.assertIn("indiraanagara", transliterate_devanagari("इंदिरानगर"))

    def test_locality_matcher_repairs_common_asr_miss(self):
        matcher = LocalityMatcher(["Koramangala", "Silk Board", "Bellandur"])
        match = matcher.match("haan bhai main core bangla mein rehta hoon")
        self.assertEqual(match.predicted_locality, "Koramangala")


if __name__ == "__main__":
    unittest.main()
