from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from docvision.telegram_bot.utils.formatters import (
    format_contact_created_with_party_message,
    format_existing_contact_message,
    format_existing_party_message,
    format_new_lead_and_contact_message,
)


class TestFormatters(TestCase):
    def setUp(self):
        self.contact = SimpleNamespace(
            name="CONTACT-0001",
            first_name="Jane",
            last_name="Doe",
            email_ids=[SimpleNamespace(email_id="jane@example.com")],
            phone_nos=[SimpleNamespace(phone="+1 555 0100")],
            company_name="Example Inc",
        )

    @patch(
        "docvision.telegram_bot.utils.formatters.frappe.utils.get_url",
        return_value="https://erp.example.com",
    )
    def test_existing_contact_message_without_party(self, _get_url):
        message = format_existing_contact_message(self.contact)

        self.assertIn("Contact Already Exists", message)
        self.assertIn("Jane Doe", message)
        self.assertIn("jane@example.com", message)
        self.assertIn("+1 555 0100", message)
        self.assertIn("Example Inc", message)
        self.assertIn(
            "https://erp.example.com/app/contact/CONTACT-0001", message
        )
        self.assertNotIn("Linked to", message)

    @patch(
        "docvision.telegram_bot.utils.formatters.frappe.utils.get_url",
        return_value="https://erp.example.com",
    )
    def test_existing_contact_message_handles_empty_optional_fields(self, _get_url):
        contact = SimpleNamespace(
            name="CONTACT-0002",
            first_name="Jane",
            last_name=None,
            email_ids=[],
            phone_nos=[],
            company_name=None,
        )

        message = format_existing_contact_message(contact)

        self.assertIn("Jane ", message)
        self.assertNotIn("📧", message)
        self.assertNotIn("📞", message)
        self.assertNotIn("🏢", message)
        self.assertIn("/app/contact/CONTACT-0002", message)

    @patch(
        "docvision.telegram_bot.utils.formatters.frappe.utils.get_url",
        return_value="https://erp.example.com",
    )
    def test_existing_contact_message_can_include_party(self, _get_url):
        message = format_existing_contact_message(
            self.contact, "Customer", "Example Inc"
        )

        self.assertIn("Linked to Customer: Example Inc", message)

    @patch(
        "docvision.telegram_bot.utils.formatters.frappe.utils.get_url",
        return_value="https://erp.example.com",
    )
    def test_existing_party_message_for_customer_and_lead(self, _get_url):
        parties = (
            ("Customer", "CUSTOMER-0001", "Example Inc", "customer"),
            ("Lead", "LEAD-0001", "Example Lead", "lead"),
        )

        for party_type, party_name, party_display, route in parties:
            with self.subTest(party_type=party_type):
                message = format_existing_party_message(
                    party_type, party_name, party_display, self.contact
                )

                self.assertIn(f"{party_type} Already Exists", message)
                self.assertIn(f"Linked {party_type}: {party_display}", message)
                self.assertIn(f"/app/{route}/{party_name}", message)
                self.assertIn("/app/contact/CONTACT-0001", message)

    @patch(
        "docvision.telegram_bot.utils.formatters.frappe.utils.get_url",
        return_value="https://erp.example.com",
    )
    def test_contact_created_with_party_message(self, _get_url):
        message = format_contact_created_with_party_message(
            self.contact, "Customer", "CUSTOMER-0001", "Example Inc"
        )

        self.assertIn("Contact Created Successfully", message)
        self.assertIn("Linked to existing Customer: Example Inc", message)
        self.assertIn("/app/customer/CUSTOMER-0001", message)
        self.assertIn("/app/contact/CONTACT-0001", message)

    @patch(
        "docvision.telegram_bot.utils.formatters.frappe.utils.get_url",
        return_value="https://erp.example.com",
    )
    def test_new_lead_and_contact_message(self, _get_url):
        lead = SimpleNamespace(
            name="LEAD-0001",
            lead_name="Jane Doe",
            email_id="jane@example.com",
            phone="+1 555 0100",
            company_name="Example Inc",
        )

        message = format_new_lead_and_contact_message(lead, self.contact)

        self.assertIn("New Lead Created", message)
        self.assertIn("Contact also created and linked", message)
        self.assertIn("/app/lead/LEAD-0001", message)
        self.assertIn("/app/contact/CONTACT-0001", message)

    @patch(
        "docvision.telegram_bot.utils.formatters.frappe.utils.get_url",
        return_value="https://erp.example.com",
    )
    def test_new_lead_with_whatsapp_number_message(self, _get_url):
        lead = SimpleNamespace(
            name="LEAD-0002",
            lead_name="John Doe",
            email_id="john@example.com",
            whatsapp_number="+1 555 0200",
            phone=None,
            company_name="Alcop Inc",
        )

        message = format_new_lead_and_contact_message(lead, self.contact)

        self.assertIn("New Lead Created", message)
        self.assertIn("📞 Phone: +1 555 0200", message)
        self.assertIn("/app/lead/LEAD-0002", message)
