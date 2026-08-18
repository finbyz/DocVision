from unittest import TestCase
from unittest.mock import patch

from docvision.telegram_bot.utils.logging import _sanitize, log_exception


class TestTelegramLogging(TestCase):
    def test_sanitize_redacts_nested_secrets_and_truncates_values(self):
        sanitized = _sanitize({
            "chat_id": 123,
            "settings": {"bot_token": "secret-token"},
            "detail": "x" * 600,
        })

        self.assertEqual(sanitized["chat_id"], 123)
        self.assertEqual(sanitized["settings"]["bot_token"], "[redacted]")
        self.assertEqual(len(sanitized["detail"]), 500)

    @patch("docvision.telegram_bot.utils.logging.frappe.log_error")
    @patch(
        "docvision.telegram_bot.utils.logging.frappe.get_traceback",
        return_value="example traceback",
    )
    def test_log_exception_includes_traceback_and_safe_context(self, _get_traceback, log_error):
        log_exception("Telegram Test Error", chat_id=123, bot_token="secret-token")

        log_error.assert_called_once()
        call = log_error.call_args.kwargs
        self.assertEqual(call["title"], "Telegram Test Error")
        self.assertIn("example traceback", call["message"])
        self.assertIn('"chat_id": 123', call["message"])
        self.assertIn('"bot_token": "[redacted]"', call["message"])
        self.assertNotIn("secret-token", call["message"])
