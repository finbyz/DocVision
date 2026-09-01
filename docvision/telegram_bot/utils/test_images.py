from unittest import TestCase
from unittest.mock import patch

from docvision.telegram_bot.utils.images import image_bytes_to_data_url, validate_image_size


class TestImages(TestCase):
    def test_png_is_encoded_using_detected_type(self):
        content = b"\x89PNG\r\n\x1a\ncontent"
        result = image_bytes_to_data_url(content, "image/png")
        self.assertTrue(result.startswith("data:image/png;base64,"))

    @patch("docvision.telegram_bot.utils.images.frappe.throw", side_effect=ValueError)
    def test_rejects_mismatched_declared_type(self, _throw):
        with self.assertRaises(ValueError):
            image_bytes_to_data_url(b"\x89PNG\r\n\x1a\ncontent", "image/jpeg")

    def test_allows_application_octet_stream_when_content_valid(self):
        content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        result = image_bytes_to_data_url(content, "application/octet-stream")
        self.assertTrue(result.startswith("data:image/jpeg;base64,"))

    def test_normalizes_image_jpg_declared_type(self):
        content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        result = image_bytes_to_data_url(content, "image/jpg")
        self.assertTrue(result.startswith("data:image/jpeg;base64,"))

    @patch("docvision.telegram_bot.utils.images.frappe.throw", side_effect=ValueError)
    def test_rejects_unsupported_declared_type(self, _throw):
        with self.assertRaises(ValueError):
            image_bytes_to_data_url(b"\x89PNG\r\n\x1a\ncontent", "image/gif")

    @patch("docvision.telegram_bot.utils.images.frappe.throw", side_effect=ValueError)
    def test_rejects_invalid_content_length(self, _throw):
        with self.assertRaises(ValueError):
            validate_image_size("invalid")

