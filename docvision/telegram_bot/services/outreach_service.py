"""
DocVision Outreach Service
Handles AI email drafting, Telegram inline review workflow, revisions, and approval execution.
"""
import frappe
from frappe.utils import now_datetime, format_datetime
from docvision.telegram_bot.services.research_service import research_lead
from docvision.telegram_bot.services.telegram_service import (
    send_telegram_message,
    send_message_with_inline_buttons,
    send_force_reply,
    edit_message_text,
)
from docvision.telegram_bot.utils.logging import log_error, log_exception

REVISION_MARKER_PREFIX = "outreach:"

def _clean_email_body(body: str) -> str:
    """Return the agent-generated email body without injecting any hardcoded signature."""
    return (body or "").strip()


def create_and_send_outreach_draft(lead_name: str, contact_name: str = None, chat_id: str = None):
    """
    1. Researches the Lead & Company (Company Research + Person Research).
    2. Drafts an initial welcome outreach email using FinByz AI Email Agent.
    3. Saves record in DocVision Outreach.
    4. Sends preview message to Telegram with Approve and Revise buttons.
    """
    try:
        setting = frappe.get_single("Telegram Setting")
        if not setting.enable_auto_outreach:
            return None

        if not setting.email_agent:
            log_error("DocVision Outreach", "Email Agent not configured in Telegram Setting")
            return None

        lead = frappe.get_doc("Lead", lead_name)
        contact = frappe.get_doc("Contact", contact_name) if contact_name else None
        
        recipient_email = lead.email_id or (contact.email_id if contact else None)
        if not recipient_email:
            # Check contact child emails
            if contact and contact.email_ids and len(contact.email_ids) > 0:
                recipient_email = contact.email_ids[0].email_id

        # Note: we continue even without email — research still runs.
        # The outreach draft will be created for review; email send will be skipped if no recipient.

        # Guard: skip if a non-failed outreach already exists for this lead
        existing = frappe.db.get_value(
            "DocVision Outreach",
            {"lead": lead_name, "status": ["not in", ["Failed", "No Email"]]},
            "name"
        )
        if existing:
            return None

        if chat_id:
            send_telegram_message(chat_id, "🔍 Researching prospect & drafting initial welcome email...")

        # Step 1: Research
        research_data = research_lead(lead_name, contact_name)
        company_overview = research_data.get("company_overview", "")
        person_overview = research_data.get("person_overview", "")
        industry = research_data.get("industry", "")
        website = research_data.get("website", "") or getattr(lead, "website", "")
        research_context = research_data.get("research_context", "")

        # Step 2: Draft initial email
        full_name = lead.lead_name or (f"{contact.first_name or ''} {contact.last_name or ''}".strip() if contact else "Prospect")
        company_name = lead.company_name or (contact.company_name if contact else "")
        designation = getattr(contact, "designation", "") if contact else getattr(lead, "designation", "")
        lead_source = getattr(lead, "source", None) or setting.lead_source or ""

        if not research_context:
            research_context = _build_email_research_context(
                company_name=company_name,
                full_name=full_name,
                designation=designation,
                website=website,
                industry=industry,
                company_research=company_overview,
                person_research=person_overview,
            )

        subject = ""
        body = ""
        outreach_status = "Pending Approval"

        if recipient_email:
            draft_result = _invoke_email_agent(
                agent_name=setting.email_agent,
                full_name=full_name,
                company_name=company_name,
                designation=designation,
                website=website,
                recipient_email=recipient_email,
                company_research=company_overview,
                person_research=person_overview,
                research_context=research_context,
                industry=industry,
                lead_source=lead_source,
                revision_instruction=""
            )
            subject = draft_result.get("subject") or f"Great meeting you at {lead_source} - {company_name or 'your organization'}"
            body = _clean_email_body(draft_result.get("body") or "")
        else:
            outreach_status = "No Email"
            subject = f"[No Email] Research completed for {company_name or full_name}"

        # Step 3: Create DocVision Outreach document
        outreach = frappe.get_doc({
            "doctype": "DocVision Outreach",
            "lead": lead_name,
            "contact": contact_name,
            "company_name": company_name,
            "recipient_email": recipient_email or "",
            "lead_source": lead_source,
            "website": website,
            "industry": industry,
            "company_research": company_overview,
            "person_research": person_overview,
            "subject": subject,
            "body": body,
            "status": outreach_status,
            "telegram_chat_id": str(chat_id) if chat_id else None
        })
        outreach.insert(ignore_permissions=True)
        frappe.db.commit()


        # Step 4: Send preview with inline buttons (or research-only if no email)
        if chat_id:
            if recipient_email:
                msg_text = _format_outreach_preview_message(outreach)
                inline_keyboard = [
                    [
                        {"text": "✅ Approve & Send", "callback_data": f"dov:app:{outreach.name}"},
                        {"text": "✏️ Revise", "callback_data": f"dov:rev:{outreach.name}"}
                    ]
                ]
                sent_msg = send_message_with_inline_buttons(chat_id, msg_text, inline_keyboard)
                if sent_msg and sent_msg.get("message_id"):
                    outreach.telegram_message_id = str(sent_msg["message_id"])
                    outreach.save(ignore_permissions=True)
                    frappe.db.commit()
            else:
                # No email — show research results only
                msg_text = _format_research_only_message(outreach)
                send_telegram_message(chat_id, msg_text)

        return outreach

    except Exception:
        log_exception("DocVision Create Outreach Draft Error", lead_name=lead_name, chat_id=chat_id)
        if chat_id:
            send_telegram_message(chat_id, "⚠️ Failed to generate outreach email draft.")
        return None


def approve_and_send(outreach_name: str, chat_id: str, message_id: str, from_user: dict):
    """Handles Approve button tap: sends email and hides inline buttons on Telegram"""
    try:
        if not frappe.db.exists("DocVision Outreach", outreach_name):
            return "Outreach record not found.", True

        outreach = frappe.get_doc("DocVision Outreach", outreach_name)
        
        if outreach.status == "Sent":
            return "This email has already been sent.", True

        # Send email
        outreach.send_outreach_email()

        # Update Telegram message: Remove buttons and append approval badge
        user_name = _get_user_display_name(from_user)
        timestamp = format_datetime(now_datetime(), "dd-MM-yyyy HH:mm")
        
        updated_text = _format_outreach_preview_message(outreach)
        updated_text += f"\n\n✅ <b>Approved & Sent</b> by {user_name} on {timestamp}"
        
        if chat_id and message_id:
            edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=updated_text,
                reply_markup={"inline_keyboard": []}  # Hide buttons
            )

        return f"Email approved and sent to {outreach.recipient_email}!", False

    except Exception as e:
        log_exception("DocVision Approve and Send Error", outreach_name=outreach_name)
        return f"Failed to send email: {str(e)}", True


def prompt_revision(outreach_name: str, chat_id: str, message_id: str):
    """Handles Revise button tap: sends force-reply prompt asking for revision instructions"""
    try:
        if not frappe.db.exists("DocVision Outreach", outreach_name):
            return "Outreach record not found.", True

        outreach = frappe.get_doc("DocVision Outreach", outreach_name)
        outreach.status = "Revision Requested"
        outreach.save(ignore_permissions=True)
        frappe.db.commit()

        prompt_text = (
            f"✏️ <b>Revision Request</b> for <b>{outreach.company_name or outreach.lead}</b>\n\n"
            f"Please <b>reply to this message</b> with what you would like to change (e.g. tone, key points, length).\n"
            f"[{REVISION_MARKER_PREFIX}{outreach.name}]"
        )

        send_force_reply(
            chat_id=chat_id,
            text=prompt_text,
            placeholder="Type your revision instructions here...",
            reply_to_message_id=message_id
        )

        return "Please type your revision instructions in the reply.", False

    except Exception:
        log_exception("DocVision Prompt Revision Error", outreach_name=outreach_name)
        return "Failed to trigger revision prompt.", True


def process_revision_reply(outreach_name: str, chat_id: str, revision_text: str, from_user: dict):
    """Processes the user's text reply and re-invokes the AI agent to update the email draft"""
    try:
        if not frappe.db.exists("DocVision Outreach", outreach_name):
            return None

        outreach = frappe.get_doc("DocVision Outreach", outreach_name)
        setting = frappe.get_single("Telegram Setting")
        
        if not setting.email_agent:
            send_telegram_message(chat_id, "❌ Email Agent is not configured in Telegram Setting.")
            return None

        send_telegram_message(chat_id, f"⏳ Updating draft based on feedback:\n<i>\"{revision_text}\"</i>...")

        lead = frappe.get_doc("Lead", outreach.lead)
        contact = frappe.get_doc("Contact", outreach.contact) if outreach.contact else None
        full_name = lead.lead_name or (f"{contact.first_name or ''} {contact.last_name or ''}".strip() if contact else "Prospect")
        designation = getattr(contact, "designation", "") if contact else getattr(lead, "designation", "")

        research_context = _build_email_research_context(
            company_name=outreach.company_name,
            full_name=full_name,
            designation=designation,
            website=outreach.website,
            industry=outreach.industry,
            company_research=outreach.company_research,
            person_research=outreach.person_research,
        )

        draft_result = _invoke_email_agent(
            agent_name=setting.email_agent,
            full_name=full_name,
            company_name=outreach.company_name,
            designation=designation,
            website=outreach.website,
            recipient_email=outreach.recipient_email,
            company_research=outreach.company_research,
            person_research=outreach.person_research,
            research_context=research_context,
            industry=outreach.industry,
            lead_source=outreach.lead_source or "",
            revision_instruction=revision_text,
            previous_subject=outreach.subject,
            previous_body=outreach.body
        )

        outreach.subject = draft_result.get("subject") or outreach.subject
        outreach.body = _clean_email_body(draft_result.get("body") or outreach.body)
        outreach.revision_notes = revision_text
        outreach.revision_count = (outreach.revision_count or 0) + 1
        outreach.status = "Pending Approval"
        outreach.save(ignore_permissions=True)
        frappe.db.commit()

        # Send updated preview with inline buttons
        msg_text = _format_outreach_preview_message(outreach, is_revised=True)
        inline_keyboard = [
            [
                {"text": "✅ Approve & Send", "callback_data": f"dov:app:{outreach.name}"},
                {"text": "✏️ Revise Again", "callback_data": f"dov:rev:{outreach.name}"}
            ]
        ]
        sent_msg = send_message_with_inline_buttons(chat_id, msg_text, inline_keyboard)
        if sent_msg and sent_msg.get("message_id"):
            outreach.telegram_message_id = str(sent_msg["message_id"])
            outreach.save(ignore_permissions=True)
            frappe.db.commit()

        return outreach

    except Exception:
        log_exception("DocVision Process Revision Reply Error", outreach_name=outreach_name)
        send_telegram_message(chat_id, "⚠️ Failed to revise email draft. Please try again.")
        return None


def extract_outreach_name_from_reply(prompt_text: str) -> str | None:
    """Extracts outreach docname from embedded marker [outreach:NAME]"""
    token = f"[{REVISION_MARKER_PREFIX}"
    start = prompt_text.find(token)
    if start == -1:
        return None
    end = prompt_text.find("]", start)
    if end == -1:
        return None
    return prompt_text[start + len(token): end].strip() or None


def _invoke_email_agent(agent_name, full_name, company_name, website, recipient_email, company_research="", person_research="", research_context="", designation="", industry="", lead_source="", revision_instruction="", previous_subject="", previous_body=""):
    """Invokes FinByz AI Email Agent and extracts subject and body"""
    agent = frappe.get_doc("AI Agent", agent_name)
    agent_service = agent.agent_service
    
    input_vars = {
        "lead_name": full_name,
        "full_name": full_name,
        "company_name": company_name or "",
        "designation": designation or "",
        "website": website or "",
        "email": recipient_email or "",
        "company_research": company_research or "",
        "person_research": person_research or "",
        "research_context": research_context or _build_email_research_context(
            company_name=company_name,
            full_name=full_name,
            designation=designation,
            website=website,
            industry=industry,
            company_research=company_research,
            person_research=person_research,
        ),
        "industry": industry or "",
        "lead_source": lead_source or "",
        "revision_instruction": revision_instruction or "",
        "previous_subject": previous_subject or "",
        "previous_body": previous_body or "",
    }

    result = agent_service.invoke(**input_vars)
    
    subject = ""
    body = ""

    if hasattr(result, "subject") and hasattr(result, "body"):
        subject = getattr(result, "subject", "")
        body = getattr(result, "body", "")
    elif isinstance(result, dict):
        subject = result.get("subject", "")
        body = result.get("body", "")
    else:
        text = str(result)
        # Fallback parsing if plain text returned
        if "Subject:" in text:
            parts = text.split("Subject:", 1)[1].split("\n", 1)
            subject = parts[0].strip()
            body = parts[1].strip() if len(parts) > 1 else ""
        else:
            body = text

    body = _clean_email_body(body)

    return {
        "subject": subject,
        "body": body
    }


def _build_email_research_context(company_name="", full_name="", designation="", website="", industry="", company_research="", person_research=""):
    parts = []
    if company_name:
        parts.append(f"Company: {company_name}")
    if full_name and full_name != "Prospect":
        contact = f"Contact: {full_name}"
        if designation:
            contact += f" ({designation})"
        parts.append(contact)
    if website:
        parts.append(f"Website: {website}")
    if industry:
        parts.append(f"Industry: {industry}")
    if company_research:
        parts.append(f"Company research: {company_research}")
    if person_research:
        parts.append(f"Person research: {person_research}")
    return "\n".join(parts)


def _html_to_telegram(html: str) -> str:
    """Convert HTML email body to Telegram-compatible text with proper spacing.
    
    Telegram HTML parse_mode supports: <b>, <i>, <u>, <s>, <a href>, <code>, <pre>
    Everything else must be converted to plain-text equivalents.
    """
    import re
    
    text = html or ""
    
    # Paragraph breaks → double newline (visible gap between paragraphs)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "", text, flags=re.IGNORECASE)
    
    # Line breaks → single newline
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    
    # Keep Telegram-safe tags: b, i, u, s, a, code, pre
    # Strip everything else (div, span, h1-h6, ul, li, etc.)
    text = re.sub(r"<(?!/?(?:b|i|u|s|a|code|pre)\b)[^>]+>", "", text, flags=re.IGNORECASE)
    
    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text.strip()


def _format_outreach_preview_message(outreach, is_revised=False):
    """Formats HTML preview of the email draft for Telegram"""
    header = "✏️ <b>Revised Outreach Email Draft</b>" if is_revised else "✉️ <b>Generated Outreach Email Draft</b>"

    msg = f"{header}\n\n"
    msg += f"👤 <b>To:</b> {outreach.recipient_email}\n"
    if outreach.company_name:
        msg += f"🏢 <b>Company:</b> {outreach.company_name}\n"
    if outreach.lead_source:
        msg += f"🏷️ <b>Source:</b> {outreach.lead_source}\n"
    msg += f"📌 <b>Lead:</b> <a href='{frappe.utils.get_url()}/app/lead/{outreach.lead}'>{outreach.lead}</a>\n"
    msg += f"\n📝 <b>Subject:</b> {outreach.subject}\n\n"

    # Convert HTML body to Telegram-friendly text with correct paragraph spacing
    clean_body = _html_to_telegram(outreach.body or "")
    if len(clean_body) > 2500:
        clean_body = clean_body[:2500] + "... [truncated]"

    msg += f"📄 <b>Body:</b>\n{clean_body}"
    return msg


def _format_research_only_message(outreach) -> str:
    """Formats a research-results-only message for leads with no email address."""
    msg = "🔍 <b>Research Completed</b> (No Email Found)\n\n"
    if outreach.company_name:
        msg += f"🏢 <b>Company:</b> {outreach.company_name}\n"
    if outreach.website:
        msg += f"🌐 <b>Website:</b> {outreach.website}\n"
    if outreach.industry:
        msg += f"🏭 <b>Industry:</b> {outreach.industry}\n"
    msg += f"📌 <b>Lead:</b> <a href='{frappe.utils.get_url()}/app/lead/{outreach.lead}'>{outreach.lead}</a>\n"

    if outreach.company_research:
        overview = outreach.company_research
        if len(overview) > 800:
            overview = overview[:800] + "... [truncated]"
        msg += f"\n🏢 <b>Company Research:</b>\n{overview}\n"

    if outreach.person_research:
        person = outreach.person_research
        if len(person) > 600:
            person = person[:600] + "... [truncated]"
        msg += f"\n👤 <b>Person Research:</b>\n{person}\n"

    msg += "\n⚠️ <i>No email on this card — please add an email to the Lead to generate a draft.</i>"
    return msg


def _get_user_display_name(from_user: dict) -> str:
    if not from_user:
        return "User"
    name = from_user.get("first_name") or ""
    if from_user.get("last_name"):
        name = f"{name} {from_user['last_name']}".strip()
    if from_user.get("username"):
        name = f"{name} (@{from_user['username']})".strip()
    return name or str(from_user.get("id") or "User")
