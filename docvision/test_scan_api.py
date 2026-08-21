from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

from docvision.scan_api import _map_result, _result_as_dict, extract_lead_from_image


class TestScanApi(TestCase):
    def test_contact_result_drops_unexpected_agent_fields(self):
        result = _map_result(
            {"first_name": "Ada", "email_ids": [], "owner": "Administrator"},
            "Contact",
        )
        self.assertEqual(result, {"first_name": "Ada", "email_ids": []})

    def test_lead_result_maps_primary_contact_values(self):
        result = _map_result(
            {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "company_name": "Analytical Engines",
                "email_ids": [{"email_id": "ada@example.com"}],
                "phone_nos": [{"phone": "+44 123"}],
                "company_domain": "example.com",
            },
            "Lead",
        )
        self.assertEqual(result["lead_name"], "Ada Lovelace")
        self.assertEqual(result["email_id"], "ada@example.com")
        self.assertEqual(result["mobile_no"], "+44 123")

    def test_result_accepts_model_dump(self):
        result = SimpleNamespace(model_dump=lambda: {"first_name": "Ada"})
        self.assertEqual(_result_as_dict(result), {"first_name": "Ada"})

    @patch("docvision.scan_api.process_business_card_with_context")
    @patch("docvision.scan_api.image_bytes_to_data_url", return_value="data:image/png;base64,AA==")
    @patch("docvision.scan_api.frappe")
    def test_extract_requires_file_read_and_target_create_permission(
        self, mock_frappe, mock_data_url, mock_process
    ):
        file_doc = MagicMock(file_name="card.png", file_url="/private/files/card.png")
        file_doc.get_content.return_value = b"image"
        mock_frappe.db.get_value.return_value = "FILE-0001"
        mock_frappe.get_doc.return_value = file_doc
        mock_process.return_value = {"first_name": "Ada", "company_name": "Analytical Engines"}

        result = extract_lead_from_image("/private/files/card.png")

        mock_frappe.has_permission.assert_called_once_with("Lead", "create", throw=True)
        file_doc.check_permission.assert_called_once_with("read")
        self.assertEqual(result["lead_name"], "Ada")
