"""
DocVision Research Service
Performs autonomous lead, company, and person research using FinByz AI agents.
"""
import frappe
from docvision.telegram_bot.utils.logging import log_exception


def research_lead(lead_name: str, contact_name: str = None) -> dict:
    """
    Research a Lead and associated Contact using configured FinByz AI Agents:
    - Company Research Agent: investigates the company domain, firmographics, and overview.
    - Person Research Agent: investigates the individual's role, background, and profile.
    Updates the Lead and Contact documents with discovered details.
    """
    try:
        lead = frappe.get_doc("Lead", lead_name)
        contact = frappe.get_doc("Contact", contact_name) if contact_name else None
        
        full_name = lead.lead_name or ""
        if not full_name and contact:
            full_name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
            
        company_name = lead.company_name or (contact.company_name if contact else "") or ""
        website = getattr(lead, "website", "") or getattr(lead, "company_domain", "") or ""
        email = getattr(lead, "email_id", "") or (contact.email_id if contact else "") or ""
        
        # Derive website from email domain if website is empty
        if not website and email and "@" in email:
            domain_part = email.split("@")[-1].lower().strip()
            free_email_providers = {
                "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
                "icloud.com", "rediffmail.com", "live.com", "proton.me", "aol.com"
            }
            if domain_part not in free_email_providers:
                website = domain_part

        country = getattr(lead, "country", "") or "India"
        city = getattr(lead, "city", "") or ""
        state = getattr(lead, "state", "") or ""
        territory = getattr(lead, "territory", "") or country or "All Territories"
        designation = getattr(contact, "designation", "") if contact else getattr(lead, "designation", "")

        # Dynamically fetch allowed Lead Type and Industry Type options
        lead_meta = frappe.get_meta("Lead")
        lead_type_field = lead_meta.get_field("type")
        allowed_lead_types = [opt.strip() for opt in (lead_type_field.options or "").split("\n") if opt.strip()] if lead_type_field else []
        
        allowed_industries = []
        if frappe.db.exists("DocType", "Industry Type"):
            allowed_industries = frappe.get_all("Industry Type", pluck="name")

        common_info = {
            "full_name": full_name,
            "company": company_name,
            "company_name": company_name,
            "website": website or (f"{company_name.lower().replace(' ', '')}.com" if company_name else ""),
            "country": country,
            "city": city,
            "state": state,
            "territory": territory,
            "email": email,
            "designation": designation or "",
            "lead_source": getattr(lead, "source", None) or "Frappe Verse 2026",
            "allowed_lead_types": allowed_lead_types,
            "allowed_industries": allowed_industries,
            "lead_type_options": ", ".join(allowed_lead_types),
            "industry_options": ", ".join(allowed_industries),
        }


        setting = frappe.get_single("Telegram Setting")
        
        company_overview = getattr(lead, "customer_details", "") or ""
        industry = getattr(lead, "industry", "") or ""
        discovered_website = website

        # 1. Run Company Research if agent is configured
        if setting.company_research_agent:
            try:
                comp_agent = frappe.get_doc("AI Agent", setting.company_research_agent)
                comp_result = comp_agent.agent_service.invoke(**common_info)
                
                raw_lead_type = None
                raw_industry = None

                if hasattr(comp_result, "company_overview"):
                    company_overview = getattr(comp_result, "company_overview", "") or company_overview
                    raw_industry = getattr(comp_result, "industry_type", "") or getattr(comp_result, "industry", "")
                    discovered_website = getattr(comp_result, "website", "") or discovered_website
                    raw_lead_type = getattr(comp_result, "lead_type", "")
                elif isinstance(comp_result, dict):
                    company_overview = comp_result.get("company_overview") or comp_result.get("overview") or comp_result.get("summary") or str(comp_result)
                    raw_industry = comp_result.get("industry") or comp_result.get("industry_type")
                    raw_lead_type = comp_result.get("lead_type")
                    discovered_website = comp_result.get("website") or discovered_website
                else:
                    company_overview = str(comp_result)

                # Set customer_details (Company Details on Lead)
                if company_overview:
                    lead.customer_details = company_overview
                
                # Set website
                if discovered_website and not getattr(lead, "website", None):
                    lead.website = discovered_website

                # Save safe fields first (customer_details, website)
                lead.save(ignore_permissions=True)
                frappe.db.commit()

                # Validate and safely set industry (Link to Industry Type)
                if raw_industry:
                    matched_ind = _match_industry(raw_industry, allowed_industries)
                    if matched_ind and not getattr(lead, "industry", None):
                        lead.industry = matched_ind
                        industry = matched_ind
                    elif not industry:
                        industry = str(raw_industry)

                # Validate and safely set Lead Type (Select field) — in a separate save
                # so a bad type value never kills the research result
                if raw_lead_type and hasattr(lead, "type") and not lead.type:
                    matched_type = _match_lead_type(raw_lead_type, allowed_lead_types)
                    if matched_type:
                        lead.type = matched_type

                try:
                    lead.save(ignore_permissions=True)
                    frappe.db.commit()
                except Exception:
                    log_exception("DocVision Lead Type/Industry Save Error", lead_name=lead_name)
                    frappe.db.rollback()

            except Exception:
                log_exception("DocVision Company Research Error", lead_name=lead_name)

        # 2. Run Person Research if agent is configured
        person_overview = (getattr(contact, "person_details", "") or getattr(contact, "person_research", "")) if contact else ""
        if setting.person_research_agent:
            try:
                person_agent = frappe.get_doc("AI Agent", setting.person_research_agent)
                person_result = person_agent.agent_service.invoke(**common_info)
                
                linkedin = ""
                if hasattr(person_result, "research_summary"):
                    person_overview = getattr(person_result, "research_summary", "")
                    linkedin = getattr(person_result, "linkedin_profile", "")
                elif isinstance(person_result, dict):
                    person_overview = person_result.get("research_summary") or person_result.get("summary") or str(person_result)
                    linkedin = person_result.get("linkedin_profile") or person_result.get("linkedin") or ""
                else:
                    person_overview = str(person_result)

                if contact:
                    if person_overview:
                        if hasattr(contact, "person_details"):
                            contact.person_details = person_overview
                        if hasattr(contact, "person_research"):
                            contact.person_research = person_overview
                    if linkedin and hasattr(contact, "linkedin_profile"):
                        contact.linkedin_profile = linkedin
                    contact.save(ignore_permissions=True)
                    frappe.db.commit()

            except Exception:
                log_exception("DocVision Person Research Error", lead_name=lead_name, contact_name=contact_name)

        has_company_research = bool(company_overview and company_overview.strip())
        has_person_research = bool(person_overview and person_overview.strip())
        company_overview = company_overview or f"Company: {company_name}"
        person_overview = person_overview or f"Contact: {full_name} ({designation or 'Team Member'})"

        return {
            "company_overview": company_overview,
            "person_overview": person_overview,
            "industry": industry,
            "website": discovered_website or website,
            "has_company_research": has_company_research,
            "has_person_research": has_person_research,
            "research_context": _build_research_context(
                company_name=company_name,
                full_name=full_name,
                designation=designation,
                website=discovered_website or website,
                industry=industry,
                company_overview=company_overview,
                person_overview=person_overview,
            ),
        }

    except Exception:
        log_exception("DocVision Lead Research General Error", lead_name=lead_name)
        return {
            "company_overview": f"Company: {lead_name}",
            "person_overview": f"Contact: {contact_name or lead_name}",
            "industry": "",
            "website": "",
            "has_company_research": False,
            "has_person_research": False,
            "research_context": "",
        }


def _build_research_context(
    company_name: str = "",
    full_name: str = "",
    designation: str = "",
    website: str = "",
    industry: str = "",
    company_overview: str = "",
    person_overview: str = "",
) -> str:
    """Compact research packet passed to the email drafting agent."""
    lines = []
    if company_name:
        lines.append(f"Company: {company_name}")
    if full_name:
        contact_line = f"Contact: {full_name}"
        if designation:
            contact_line += f" ({designation})"
        lines.append(contact_line)
    if website:
        lines.append(f"Website: {website}")
    if industry:
        lines.append(f"Industry: {industry}")
    if company_overview:
        lines.append(f"Company research: {company_overview}")
    if person_overview:
        lines.append(f"Person research: {person_overview}")
    return "\n".join(lines)


def _match_lead_type(raw_val: str, allowed_options: list[str]) -> str | None:
    """Safely map raw agent output to allowed Lead Type Select options"""
    if not raw_val or not allowed_options:
        return None
    
    raw = str(raw_val).strip().lower()
    
    # 1. Exact case-insensitive match
    for opt in allowed_options:
        if opt.strip().lower() == raw:
            return opt.strip()

    # 2. Semantic matching
    if "client" in raw or "customer" in raw:
        for opt in allowed_options:
            if "client" in opt.lower() or "customer" in opt.lower():
                return opt.strip()
    if "channel partner" in raw or "partner" in raw or "re-seller" in raw or "reseller" in raw:
        for opt in allowed_options:
            if "partner" in opt.lower() or "channel" in opt.lower():
                return opt.strip()
    if "consultant" in raw or "advisor" in raw:
        for opt in allowed_options:
            if "consultant" in opt.lower():
                return opt.strip()
    if "end user" in raw or "consumer" in raw or "prosumer" in raw:
        for opt in allowed_options:
            if "end user" in opt.lower() or "user" in opt.lower():
                return opt.strip()

    return None


def _match_industry(raw_val: str, allowed_industries: list[str]) -> str | None:
    """Safely map raw industry to existing Industry Type in DB"""
    if not raw_val:
        return None

    raw = str(raw_val).strip()
    
    # 1. Exact DB match
    if frappe.db.exists("Industry Type", raw):
        return raw

    # 2. Case-insensitive search in allowed list
    for ind in allowed_industries:
        if ind.lower() == raw.lower():
            return ind

    # 3. Partial substring search
    for ind in allowed_industries:
        if raw.lower() in ind.lower() or ind.lower() in raw.lower():
            return ind

    return None
