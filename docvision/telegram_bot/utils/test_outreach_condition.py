from types import SimpleNamespace
from unittest.mock import patch

from frappe.tests import UnitTestCase

from docvision.telegram_bot.utils.outreach_condition import evaluate_outreach_condition


class TestOutreachCondition(UnitTestCase):
    def test_blank_condition_always_matches(self):
        self.assertTrue(evaluate_outreach_condition("", SimpleNamespace()))

    @patch("docvision.telegram_bot.utils.outreach_condition.frappe.safe_eval")
    def test_condition_receives_lead_and_contact(self, safe_eval):
        safe_eval.return_value = True
        lead = SimpleNamespace(country="India")
        contact = SimpleNamespace(designation="Director")

        result = evaluate_outreach_condition(
            'doc.country == "India" and contact.designation == "Director"',
            lead,
            contact,
        )

        self.assertTrue(result)
        context = safe_eval.call_args.args[2]
        self.assertIs(context["doc"], lead)
        self.assertIs(context["contact"], contact)

    @patch("docvision.telegram_bot.utils.outreach_condition.frappe.safe_eval")
    def test_false_condition_skips_draft(self, safe_eval):
        safe_eval.return_value = False
        self.assertFalse(
            evaluate_outreach_condition('doc.country == "India"', SimpleNamespace())
        )
