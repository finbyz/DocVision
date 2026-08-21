"""Restricted, non-sensitive AI agent configuration diagnostics."""

import frappe


def check():
    frappe.only_for("System Manager")
    setting = frappe.get_single("Telegram Setting")
    agents = []
    for agent_name in {
        setting.ai_agent,
        setting.company_research_agent,
        setting.person_research_agent,
        setting.email_agent,
    }:
        if not agent_name or not frappe.db.exists("AI Agent", agent_name):
            continue
        agent = frappe.get_doc("AI Agent", agent_name)
        agents.append(
            {
                "name": agent.name,
                "llm_provider": agent.llm_provider,
                "llm": agent.llm,
                "agent_type": agent.agent_type,
            }
        )
    return {"agents": agents}
