from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

from docvision.telegram_bot.services.create_service import create_address_for_party


class TestCreateAddressForParty(TestCase):
    @patch("docvision.telegram_bot.services.create_service.frappe.get_doc")
    def test_ignores_validation_for_indian_address_without_state(self, get_doc):
        address_doc = MagicMock()
        address_doc.flags = SimpleNamespace()
        get_doc.return_value = address_doc
        data = SimpleNamespace(
            address=SimpleNamespace(
                address_line1="12 Example Road",
                city="Mumbai",
                state=None,
                pincode="400001",
                country="India",
            )
        )

        result = create_address_for_party(data, "Lead", "LEAD-0001", "Example")

        self.assertIs(result, address_doc)
        self.assertTrue(address_doc.flags.ignore_validate)
        address_doc.insert.assert_called_once_with(ignore_permissions=True)

    @patch("docvision.telegram_bot.services.create_service.frappe.get_doc")
    def test_defaults_missing_country_to_india_and_ignores_validation(self, get_doc):
        address_doc = MagicMock()
        address_doc.flags = SimpleNamespace()
        get_doc.return_value = address_doc
        data = SimpleNamespace(
            address=SimpleNamespace(
                address_line1="12 Example Road",
                city="Mumbai",
                state="   ",
                pincode="400001",
                country=None,
            )
        )

        result = create_address_for_party(data, "Lead", "LEAD-0001", "Example")

        self.assertIs(result, address_doc)
        self.assertEqual(get_doc.call_args.args[0]["country"], "India")
        self.assertTrue(address_doc.flags.ignore_validate)
        address_doc.insert.assert_called_once_with(ignore_permissions=True)

    @patch("docvision.telegram_bot.services.create_service.frappe.get_doc")
    def test_creates_indian_address_with_state(self, get_doc):
        address_doc = MagicMock()
        address_doc.flags = SimpleNamespace()
        get_doc.return_value = address_doc
        data = SimpleNamespace(
            address=SimpleNamespace(
                address_line1="12 Example Road",
                address_line2=None,
                city="Mumbai",
                state="Maharashtra",
                pincode="400001",
                country="India",
            )
        )

        result = create_address_for_party(data, "Lead", "LEAD-0001", "Example")

        self.assertIs(result, address_doc)
        self.assertEqual(get_doc.call_args.args[0]["state"], "Maharashtra")
        self.assertFalse(hasattr(address_doc.flags, "ignore_validate"))
        address_doc.insert.assert_called_once_with(ignore_permissions=True)

    @patch("docvision.telegram_bot.services.create_service.frappe.get_doc")
    def test_allows_international_address_without_state(self, get_doc):
        address_doc = MagicMock()
        address_doc.flags = SimpleNamespace()
        get_doc.return_value = address_doc
        data = SimpleNamespace(
            address=SimpleNamespace(
                address_line1="1 Example Street",
                address_line2=None,
                city="Singapore",
                state=None,
                pincode="018989",
                country="Singapore",
            )
        )

        result = create_address_for_party(data, "Lead", "LEAD-0001", "Example")

        self.assertIs(result, address_doc)
        self.assertIsNone(get_doc.call_args.args[0]["state"])
        self.assertFalse(hasattr(address_doc.flags, "ignore_validate"))
        address_doc.insert.assert_called_once_with(ignore_permissions=True)
