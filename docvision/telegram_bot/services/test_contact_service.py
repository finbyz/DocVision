from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from docvision.telegram_bot.services.contact_service import process_contact_or_lead


class TestContactService(TestCase):
    @patch("docvision.telegram_bot.services.contact_service.find_customer_by_company_name")
    @patch("docvision.telegram_bot.services.contact_service.format_existing_party_message")
    @patch("docvision.telegram_bot.services.contact_service.format_existing_contact_message")
    @patch("docvision.telegram_bot.services.contact_service.get_contact_with_domain_or_email")
    def test_existing_contact_with_incomplete_party_uses_contact_message(
        self, get_contact, format_contact_message, format_party_message, find_customer
    ):
        contact = SimpleNamespace(name="CONTACT-0001")
        data = SimpleNamespace(core_company_name="Example", company_name="Example")
        incomplete_parties = (
            (None, None),
            (None, "CUSTOMER-0001"),
            ("Customer", None),
            ("", "CUSTOMER-0001"),
            ("Customer", ""),
        )

        for party_type, party_name in incomplete_parties:
            with self.subTest(party_type=party_type, party_name=party_name):
                get_contact.return_value = {
                    "status": "success",
                    "with_domain": True,
                    "contact": contact,
                    "party_type": party_type,
                    "party_name": party_name,
                }
                format_contact_message.return_value = "existing contact"

                result = process_contact_or_lead(data)

                self.assertEqual(
                    result, {
                        "success": True,
                        "message": "existing contact",
                        "contact_name": "CONTACT-0001",
                        "party_type": None,
                        "party_name": None,
                    }
                )
                format_contact_message.assert_called_once_with(contact)
                format_party_message.assert_not_called()
                find_customer.assert_not_called()
                format_contact_message.reset_mock()

    @patch("docvision.telegram_bot.services.contact_service.format_existing_party_message")
    @patch("docvision.telegram_bot.services.contact_service.get_contact_with_domain_or_email")
    def test_existing_linked_contact_uses_party_message(self, get_contact, format_message):
        contact = SimpleNamespace(name="CONTACT-0001")
        data = SimpleNamespace(core_company_name="Example", company_name="Example")
        linked_parties = (
            ("Customer", "CUSTOMER-0001", "Example", "existing customer"),
            ("Lead", "LEAD-0001", "Example Lead", "existing lead"),
        )

        for party_type, party_name, party_display, expected_message in linked_parties:
            with self.subTest(party_type=party_type):
                get_contact.return_value = {
                    "status": "success",
                    "with_domain": True,
                    "contact": contact,
                    "party_type": party_type,
                    "party_name": party_name,
                    "party_display": party_display,
                }
                format_message.return_value = expected_message

                result = process_contact_or_lead(data)

                self.assertEqual(
                    result, {
                        "success": True,
                        "message": expected_message,
                        "contact_name": "CONTACT-0001",
                        "party_type": party_type,
                        "party_name": party_name,
                    }
                )
                format_message.assert_called_once_with(
                    party_type, party_name, party_display, contact
                )
                format_message.reset_mock()


    @patch("docvision.telegram_bot.services.contact_service.find_customer_by_company_name")
    @patch("docvision.telegram_bot.services.contact_service.get_contact_with_domain_or_email")
    def test_contact_lookup_error_stops_party_creation(self, get_contact, find_customer):
        get_contact.return_value = {"status": "error"}
        data = SimpleNamespace(core_company_name="Example", company_name="Example")

        result = process_contact_or_lead(data)

        self.assertFalse(result["success"])
        find_customer.assert_not_called()
