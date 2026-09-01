from unittest import TestCase
from docvision.telegram_bot.utils.country import resolve_country


class TestCountryResolution(TestCase):
    def test_resolves_us_aliases(self):
        self.assertEqual(resolve_country("US"), "United States")
        self.assertEqual(resolve_country("USA"), "United States")
        self.assertEqual(resolve_country("U.S.A."), "United States")
        self.assertEqual(resolve_country("united states"), "United States")
        self.assertEqual(resolve_country("United States of America"), "United States")

    def test_resolves_uk_aliases(self):
        self.assertEqual(resolve_country("UK"), "United Kingdom")
        self.assertEqual(resolve_country("U.K."), "United Kingdom")
        self.assertEqual(resolve_country("GB"), "United Kingdom")
        self.assertEqual(resolve_country("Great Britain"), "United Kingdom")

    def test_resolves_uae_aliases(self):
        self.assertEqual(resolve_country("UAE"), "United Arab Emirates")
        self.assertEqual(resolve_country("U.A.E."), "United Arab Emirates")
        self.assertEqual(resolve_country("Dubai"), "United Arab Emirates")

    def test_resolves_india_aliases(self):
        self.assertEqual(resolve_country("IN"), "India")
        self.assertEqual(resolve_country("IND"), "India")
        self.assertEqual(resolve_country("Bharat"), "India")
        self.assertEqual(resolve_country("India"), "India")

    def test_resolves_other_countries(self):
        self.assertEqual(resolve_country("Singapore"), "Singapore")
        self.assertEqual(resolve_country("SG"), "Singapore")
        self.assertEqual(resolve_country("DE"), "Germany")
        self.assertEqual(resolve_country("Deutschland"), "Germany")
        self.assertEqual(resolve_country("CA"), "Canada")
        self.assertEqual(resolve_country("AU"), "Australia")
        self.assertEqual(resolve_country("KSA"), "Saudi Arabia")

    def test_defaults_when_empty_or_none(self):
        self.assertEqual(resolve_country(None), "India")
        self.assertEqual(resolve_country(""), "India")
        self.assertEqual(resolve_country("   "), "India")
        self.assertIsNone(resolve_country(None, default=None))

    def test_handles_whitespace_and_punctuation(self):
        self.assertEqual(resolve_country(' "US" '), "United States")
        self.assertEqual(resolve_country("  u.s.a.  "), "United States")

    def test_dynamic_system_countries_and_prompt(self):
        from docvision.telegram_bot.utils.country import get_system_countries, get_country_extraction_prompt
        countries = get_system_countries()
        self.assertTrue(len(countries) > 0)
        self.assertIn("United States", countries)
        self.assertIn("India", countries)

        prompt = get_country_extraction_prompt()
        self.assertIn("United States", prompt)
        self.assertIn("India", prompt)
        self.assertIn("address.country", prompt)

