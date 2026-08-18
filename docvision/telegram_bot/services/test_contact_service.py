from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from docvision.telegram_bot.services.contact_service import process_contact_or_lead


class TestContactService(TestCase):
    @patch("docvision.telegram_bot.services.contact_service.find_customer_by_company_name")
    @patch("docvision.telegram_bot.services.contact_service.get_contact_with_domain_or_email")
    def test_contact_lookup_error_stops_party_creation(self, get_contact, find_customer):
        get_contact.return_value = {"status": "error"}
        data = SimpleNamespace(core_company_name="Example", company_name="Example")

        result = process_contact_or_lead(data)

        self.assertFalse(result["success"])
        find_customer.assert_not_called()
