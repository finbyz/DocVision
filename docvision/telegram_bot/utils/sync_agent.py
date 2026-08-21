"""Synchronize packaged DocVision AI Agent fixtures."""

import json

import frappe


def sync_agent():
    frappe.only_for("System Manager")
    fixture_path = frappe.get_app_path("docvision", "fixtures", "ai_agent.json")
    with open(fixture_path, encoding="utf-8") as fixture_file:
        agents = json.load(fixture_file)

    updated = []
    for agent_data in agents:
        name = agent_data["name"]
        if frappe.db.exists("AI Agent", name):
            agent = frappe.get_doc("AI Agent", name)
            agent.messages = []
            for message in agent_data.get("messages", []):
                agent.append(
                    "messages",
                    {"type": message.get("type"), "content": message.get("content")},
                )
            agent.output_schema = agent_data.get("output_schema")
            agent.temperature = agent_data.get("temperature", 0.3)
            agent.save()
        else:
            frappe.get_doc(agent_data).insert()
        updated.append(name)
    return updated
