from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch, MagicMock

from docvision.telegram_bot.services.research_service import research_lead


class TestResearchService(TestCase):
    @patch("docvision.telegram_bot.services.research_service.frappe")
    def test_research_lead_with_both_agents(self, mock_frappe):
        mock_setting = SimpleNamespace(
            company_research_agent="Company Research Agent",
            person_research_agent="Person Research Agent"
        )
        mock_frappe.get_single.return_value = mock_setting

        mock_lead = MagicMock()
        mock_lead.name = "LEAD-0001"
        mock_lead.lead_name = "Jane Doe"
        mock_lead.company_name = "Acme Global"
        mock_lead.website = "acme.global"
        mock_lead.email_id = "jane@acme.global"
        mock_lead.designation = "CTO"
        mock_lead.customer_details = None
        mock_lead.industry = None

        mock_contact = MagicMock()
        mock_contact.name = "CONTACT-0001"
        mock_contact.first_name = "Jane"
        mock_contact.last_name = "Doe"
        mock_contact.company_name = "Acme Global"
        mock_contact.email_id = "jane@acme.global"
        mock_contact.designation = "CTO"
        mock_contact.person_research = None
        mock_contact.linkedin_profile = None

        def get_doc_mock(dt, name):
            if dt == "Lead":
                return mock_lead
            if dt == "Contact":
                return mock_contact
            if dt == "AI Agent":
                mock_agent = MagicMock()
                if name == "Company Research Agent":
                    comp_res = SimpleNamespace(
                        company_overview="Acme Global is an enterprise ERP leader.",
                        industry_type="Information Technology",
                        website="acme.global",
                        lead_type="Client"
                    )
                    mock_agent.agent_service.invoke.return_value = comp_res
                elif name == "Person Research Agent":
                    person_res = SimpleNamespace(
                        research_summary="Jane is a veteran CTO specializing in cloud transformations.",
                        linkedin_profile="https://linkedin.com/in/janedoe"
                    )
                    mock_agent.agent_service.invoke.return_value = person_res
                return mock_agent
            return None

        mock_frappe.get_doc.side_effect = get_doc_mock

        result = research_lead("LEAD-0001", "CONTACT-0001")

        self.assertIn("Acme Global is an enterprise ERP leader.", result["company_overview"])
        self.assertIn("veteran CTO", result["person_overview"])
        self.assertEqual(result["industry"], "Information Technology")
        self.assertEqual(result["website"], "acme.global")

        # Verify lead and contact were saved (lead saved via 2-stage safe update)
        self.assertEqual(mock_lead.save.call_count, 2)
        mock_contact.save.assert_called_once()

    @patch("docvision.telegram_bot.services.research_service.frappe")
    def test_research_lead_fallback_when_no_agents(self, mock_frappe):
        mock_setting = SimpleNamespace(
            company_research_agent=None,
            person_research_agent=None
        )
        mock_frappe.get_single.return_value = mock_setting

        mock_lead = MagicMock()
        mock_lead.name = "LEAD-0002"
        mock_lead.lead_name = "Bob Smith"
        mock_lead.company_name = "Beta Ltd"
        mock_lead.website = "beta.com"
        mock_lead.email_id = "bob@beta.com"
        mock_lead.customer_details = None
        mock_lead.industry = "Manufacturing"

        mock_frappe.get_doc.side_effect = lambda dt, name: mock_lead if dt == "Lead" else None

        result = research_lead("LEAD-0002", None)

        self.assertIn("Beta Ltd", result["company_overview"])
        self.assertEqual(result["website"], "beta.com")
