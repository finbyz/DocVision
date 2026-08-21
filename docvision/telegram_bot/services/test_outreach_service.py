from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch, MagicMock

from docvision.telegram_bot.services.outreach_service import (
    create_and_send_outreach_draft,
    approve_and_send,
    prompt_revision,
    process_revision_reply,
    extract_outreach_name_from_reply,
    _format_outreach_preview_message,
    _invoke_email_agent,
)
from docvision.telegram_bot.webhook import _handle_callback_query


class TestOutreachService(TestCase):
    def test_extract_outreach_name_from_reply(self):
        prompt_text = "Please reply with your changes.\n[outreach:DVO-2026-00001]"
        name = extract_outreach_name_from_reply(prompt_text)
        self.assertEqual(name, "DVO-2026-00001")

        no_name = extract_outreach_name_from_reply("Plain message without marker")
        self.assertIsNone(no_name)

    def test_format_outreach_preview_message(self):
        outreach = SimpleNamespace(
            recipient_email="test@example.com",
            company_name="Test Corp",
            lead="LEAD-0001",
            lead_source="Frappe Verse 2026",
            subject="Welcome to Frappe Verse",
            body="<p>Hello team,<br>Great connecting with you.</p>"
        )
        msg = _format_outreach_preview_message(outreach)
        self.assertIn("Test Corp", msg)
        self.assertIn("test@example.com", msg)
        self.assertIn("Frappe Verse 2026", msg)
        self.assertIn("Welcome to Frappe Verse", msg)

    @patch("docvision.telegram_bot.services.outreach_service.frappe")
    def test_invoke_email_agent_uses_configured_agent_output(self, mock_frappe):
        mock_agent = MagicMock()
        mock_agent.agent_service.invoke.return_value = {
            "subject": "Configured Agent Subject",
            "body": "<p>Configured agent body and signature.</p>",
        }
        mock_frappe.get_doc.return_value = mock_agent

        result = _invoke_email_agent(
            agent_name="Configured Email Agent",
            full_name="Kanu Patel",
            company_name="KANVARTHY ENTERPRISES LLP",
            website="kocoon.in",
            recipient_email="kanu@kocoon.in",
            company_research="KANVARTHY ENTERPRISES LLP works in textile and garment operations.",
            person_research="Kanu is the primary contact for the conversation.",
            research_context="Company: KANVARTHY ENTERPRISES LLP\nCompany research: textile and garment operations",
            industry="Textile",
            lead_source="Frappe Verse 2026",
        )

        self.assertEqual(result["subject"], "Configured Agent Subject")
        self.assertEqual(result["body"], "<p>Configured agent body and signature.</p>")
        self.assertIn("research_context", mock_agent.agent_service.invoke.call_args.kwargs)

    @patch("docvision.telegram_bot.services.outreach_service.send_message_with_inline_buttons")
    @patch("docvision.telegram_bot.services.outreach_service._invoke_email_agent")
    @patch("docvision.telegram_bot.services.outreach_service.research_lead")
    @patch("docvision.telegram_bot.services.outreach_service.frappe")
    def test_create_and_send_outreach_draft(self, mock_frappe, mock_research, mock_invoke, mock_send_buttons):
        mock_setting = SimpleNamespace(
            enable_auto_outreach=1,
            email_agent="DocVision Initial Outreach Agent",
            lead_source="Frappe Verse 2026"
        )
        mock_frappe.get_single.return_value = mock_setting
        mock_frappe.db.get_value.return_value = None

        mock_lead = SimpleNamespace(
            name="LEAD-0001",
            lead_name="John Doe",
            company_name="Acme Corp",
            email_id="john@acme.com",
            website="acme.com",
            source="Frappe Verse 2026",
            designation="VP of Engineering"
        )
        mock_research.return_value = {
            "company_overview": "Acme Corp is a leader in widget manufacturing.",
            "person_overview": "John oversees core systems.",
            "industry": "Manufacturing",
            "website": "acme.com"
        }

        mock_invoke.return_value = {
            "subject": "Great meeting you at Frappe Verse 2026 — Collaboration with Acme Corp",
            "body": "<p>Hi John, it was great connecting at Frappe Verse 2026.</p>"
        }

        mock_outreach = MagicMock()
        mock_outreach.name = "DVO-2026-00001"
        mock_outreach.recipient_email = "john@acme.com"
        mock_outreach.company_name = "Acme Corp"
        mock_outreach.lead = "LEAD-0001"
        mock_outreach.lead_source = "Frappe Verse 2026"
        mock_outreach.subject = "Great meeting you at Frappe Verse 2026"
        mock_outreach.body = "<p>Hi John...</p>"
        def get_doc(doctype_or_values, name=None):
            if doctype_or_values == "Lead":
                return mock_lead
            if isinstance(doctype_or_values, dict):
                return mock_outreach
            return None

        mock_frappe.get_doc.side_effect = get_doc
        mock_send_buttons.return_value = {"message_id": 12345}

        result = create_and_send_outreach_draft("LEAD-0001", None, "chat_123")
        self.assertIsNotNone(result)
        mock_send_buttons.assert_called_once()
        # Verify button callback data format
        args, kwargs = mock_send_buttons.call_args
        self.assertEqual(args[0], "chat_123")
        self.assertEqual(args[2][0][0]["callback_data"], "dov:app:DVO-2026-00001")
        self.assertEqual(args[2][0][1]["callback_data"], "dov:rev:DVO-2026-00001")

    @patch("docvision.telegram_bot.services.outreach_service._invoke_email_agent")
    @patch("docvision.telegram_bot.services.outreach_service.send_telegram_message")
    @patch("docvision.telegram_bot.services.outreach_service.evaluate_outreach_condition")
    @patch("docvision.telegram_bot.services.outreach_service.research_lead")
    @patch("docvision.telegram_bot.services.outreach_service.frappe")
    def test_false_outreach_condition_skips_ai_draft(
        self,
        mock_frappe,
        mock_research,
        mock_condition,
        mock_send_message,
        mock_invoke,
    ):
        mock_frappe.get_single.return_value = SimpleNamespace(
            enable_auto_outreach=1,
            email_agent="Email Agent",
            lead_source="Conference",
            outreach_draft_condition='doc.country == "India"',
        )
        mock_frappe.db.get_value.return_value = None
        lead = MagicMock(
            lead_name="Ada Lovelace",
            company_name="Analytical Engines",
            email_id="ada@example.com",
            website="example.com",
            source="Conference",
        )
        mock_frappe.get_doc.return_value = lead
        mock_research.return_value = {
            "company_overview": "Research",
            "person_overview": "Person",
            "industry": "Technology",
            "website": "example.com",
        }
        mock_condition.return_value = False

        result = create_and_send_outreach_draft("LEAD-0001", chat_id="chat_123")

        self.assertIsNone(result)
        mock_condition.assert_called_once_with(
            'doc.country == "India"', lead, None
        )
        mock_invoke.assert_not_called()
        self.assertIn(
            "condition was not met",
            mock_send_message.call_args.args[1],
        )

    @patch("docvision.telegram_bot.services.outreach_service.edit_message_text")
    @patch("docvision.telegram_bot.services.outreach_service.frappe")
    def test_approve_and_send(self, mock_frappe, mock_edit_msg):
        mock_frappe.db.exists.return_value = True

        mock_outreach = MagicMock()
        mock_outreach.name = "DVO-2026-00001"
        mock_outreach.status = "Pending Approval"
        mock_outreach.recipient_email = "john@acme.com"
        mock_outreach.subject = "Test Subject"
        mock_outreach.body = "Test Body"
        mock_outreach.lead = "LEAD-0001"
        mock_outreach.lead_source = "Frappe Verse 2026"
        mock_outreach.company_name = "Acme Corp"
        mock_outreach.telegram_chat_id = "chat_123"
        mock_frappe.get_doc.return_value = mock_outreach

        msg, is_error = approve_and_send("DVO-2026-00001", "chat_123", "msg_456", {"first_name": "Alice", "username": "alice_tg"})
        self.assertFalse(is_error)
        mock_outreach.send_outreach_email.assert_called_once()
        mock_edit_msg.assert_called_once()

        # Verify editMessageText hid the buttons
        args, kwargs = mock_edit_msg.call_args
        self.assertEqual(kwargs.get("reply_markup"), {"inline_keyboard": []})

    @patch("docvision.telegram_bot.services.outreach_service.send_force_reply")
    @patch("docvision.telegram_bot.services.outreach_service.frappe")
    def test_prompt_revision(self, mock_frappe, mock_force_reply):
        mock_frappe.db.exists.return_value = True

        mock_outreach = MagicMock()
        mock_outreach.name = "DVO-2026-00001"
        mock_outreach.lead = "LEAD-0001"
        mock_outreach.company_name = "Acme Corp"
        mock_outreach.telegram_chat_id = "chat_123"
        mock_frappe.get_doc.return_value = mock_outreach

        msg, is_error = prompt_revision("DVO-2026-00001", "chat_123", "msg_456")
        self.assertFalse(is_error)
        mock_force_reply.assert_called_once()
        self.assertEqual(mock_outreach.status, "Revision Requested")

    @patch("docvision.telegram_bot.services.outreach_service.send_message_with_inline_buttons")
    @patch("docvision.telegram_bot.services.outreach_service.send_telegram_message")
    @patch("docvision.telegram_bot.services.outreach_service._invoke_email_agent")
    @patch("docvision.telegram_bot.services.outreach_service.frappe")
    def test_process_revision_reply(self, mock_frappe, mock_invoke, mock_send_msg, mock_send_buttons):
        mock_frappe.db.exists.return_value = True

        mock_setting = SimpleNamespace(email_agent="DocVision Initial Outreach Agent")
        mock_frappe.get_single.return_value = mock_setting

        mock_outreach = MagicMock()
        mock_outreach.name = "DVO-2026-00001"
        mock_outreach.lead = "LEAD-0001"
        mock_outreach.contact = None
        mock_outreach.company_name = "Acme Corp"
        mock_outreach.recipient_email = "john@acme.com"
        mock_outreach.website = "acme.com"
        mock_outreach.company_research = "Overview..."
        mock_outreach.person_research = "Person..."
        mock_outreach.industry = "Tech"
        mock_outreach.lead_source = "Frappe Verse 2026"
        mock_outreach.subject = "Old Subject"
        mock_outreach.body = "Old Body"
        mock_outreach.revision_count = 0
        mock_outreach.telegram_chat_id = "chat_123"

        mock_lead = SimpleNamespace(name="LEAD-0001", lead_name="John Doe", designation="VP")

        def get_doc_mock(dt, name):
            if dt == "DocVision Outreach":
                return mock_outreach
            if dt == "Lead":
                return mock_lead
            return None

        mock_frappe.get_doc.side_effect = get_doc_mock

        mock_invoke.return_value = {
            "subject": "Updated Subject - ERPNext Expertise",
            "body": "<p>Updated body with custom focus...</p>"
        }

        mock_send_buttons.return_value = {"message_id": 99999}

        res = process_revision_reply("DVO-2026-00001", "chat_123", "Please mention ERPNext custom apps", {"first_name": "Alice"})
        self.assertIsNotNone(res)
        self.assertEqual(mock_outreach.subject, "Updated Subject - ERPNext Expertise")
        self.assertEqual(mock_outreach.revision_notes, "Please mention ERPNext custom apps")
        self.assertEqual(mock_outreach.revision_count, 1)
        self.assertEqual(mock_outreach.status, "Pending Approval")
        mock_send_buttons.assert_called_once()

    @patch("docvision.telegram_bot.webhook.approve_and_send")
    @patch("docvision.telegram_bot.webhook.answer_callback_query")
    @patch("docvision.telegram_bot.webhook._is_authorized", return_value=True)
    def test_webhook_handle_approve_callback(self, mock_authorized, mock_answer, mock_approve):
        mock_approve.return_value = ("Approved successfully", False)

        callback_query = {
            "id": "cb_123",
            "data": "dov:app:DVO-2026-00001",
            "message": {"chat": {"id": "chat_123"}, "message_id": "msg_456"},
            "from": {"id": 111, "first_name": "Alice"}
        }

        res = _handle_callback_query(callback_query)
        self.assertEqual(res, {"status": "ok"})
        mock_approve.assert_called_once_with("DVO-2026-00001", "chat_123", "msg_456", {"id": 111, "first_name": "Alice"})
        mock_answer.assert_called_once_with("cb_123", text="Approved successfully", show_alert=False)

    @patch("docvision.telegram_bot.webhook.prompt_revision")
    @patch("docvision.telegram_bot.webhook.answer_callback_query")
    @patch("docvision.telegram_bot.webhook._is_authorized", return_value=True)
    def test_webhook_handle_revise_callback(self, mock_authorized, mock_answer, mock_prompt):
        mock_prompt.return_value = ("Type your revision in reply", False)

        callback_query = {
            "id": "cb_124",
            "data": "dov:rev:DVO-2026-00001",
            "message": {"chat": {"id": "chat_123"}, "message_id": "msg_456"},
            "from": {"id": 111, "first_name": "Alice"}
        }

        res = _handle_callback_query(callback_query)
        self.assertEqual(res, {"status": "ok"})
        mock_prompt.assert_called_once_with("DVO-2026-00001", "chat_123", "msg_456")
        mock_answer.assert_called_once_with("cb_124", text="Type your revision in reply", show_alert=False)
