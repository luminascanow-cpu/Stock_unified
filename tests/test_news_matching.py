import unittest

from src.services.news_matching import canonical_story_key, contains_any, contains_phrase


class NewsMatchingTests(unittest.TestCase):
    def test_short_sector_keyword_does_not_match_inside_word(self):
        self.assertFalse(contains_phrase("Bank profit rises", "IT"))
        self.assertTrue(contains_phrase("IT sector profit rises", "IT"))

    def test_breaking_keyword_does_not_match_inside_company_word(self):
        self.assertFalse(contains_any("Bank profit rises", ["ban", "crash"]))
        self.assertTrue(contains_any("Regulator announces bank ban", ["ban", "crash"]))

    def test_multiword_phrase_keeps_token_boundaries(self):
        self.assertTrue(contains_phrase("RBI announces a rate hike today", "rate hike"))
        self.assertFalse(contains_phrase("Freight hiking demand improves", "rate hike"))

    def test_story_key_ignores_tracking_query(self):
        first = canonical_story_key("RBI holds rates", "https://example.com/story?utm_source=a")
        second = canonical_story_key("RBI holds rates", "https://example.com/story?utm_source=b")
        self.assertEqual(first, second)

    def test_story_key_deduplicates_exact_syndicated_headline(self):
        first = canonical_story_key("RBI keeps repo rate unchanged", "https://one.example/story")
        second = canonical_story_key("RBI keeps repo rate unchanged", "https://two.example/article")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
