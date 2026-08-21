"""Permission-gated business-card image extraction endpoints."""

import json
import mimetypes

import frappe
from frappe import _

from docvision.telegram_bot.services.ai_service import process_business_card_with_context
from docvision.telegram_bot.utils.images import image_bytes_to_data_url


@frappe.whitelist(methods=["POST"])
def extract_data_from_image(file_id: str):
    return _extract_for_doctype(file_id, "Contact")


@frappe.whitelist(methods=["POST"])
def extract_customer_from_image(file_id: str):
    return _extract_for_doctype(file_id, "Customer")


@frappe.whitelist(methods=["POST"])
def extract_supplier_from_image(file_id: str):
    return _extract_for_doctype(file_id, "Supplier")


@frappe.whitelist(methods=["POST"])
def extract_lead_from_image(file_id: str):
    return _extract_for_doctype(file_id, "Lead")


def _extract_for_doctype(file_id: str, target_doctype: str) -> dict:
    if not isinstance(file_id, str) or not file_id.strip():
        frappe.throw(_("An uploaded image is required."))

    frappe.has_permission(target_doctype, "create", throw=True)
    file_name = frappe.db.get_value("File", {"file_url": file_id.strip()}, "name")
    if not file_name:
        frappe.throw(_("The uploaded image was not found."))
    file_doc = frappe.get_doc("File", file_name)
    file_doc.check_permission("read")

    content_type = mimetypes.guess_type(file_doc.file_name or file_doc.file_url)[0]
    image_data_url = image_bytes_to_data_url(file_doc.get_content(), content_type)
    extracted = _result_as_dict(
        process_business_card_with_context(
            image_data_url,
            f"Return fields suitable for a new {target_doctype} document.",
        )
    )
    return _map_result(extracted, target_doctype)


def _result_as_dict(result) -> dict:
    if hasattr(result, "model_dump"):
        result = result.model_dump()
    elif hasattr(result, "as_dict"):
        result = result.as_dict()
    elif isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            frappe.throw(_("The card extraction agent returned invalid data."))

    if not isinstance(result, dict):
        frappe.throw(_("The card extraction agent returned invalid data."))
    return result


def _map_result(data: dict, target_doctype: str) -> dict:
    if target_doctype == "Contact":
        allowed_fields = {
            "salutation",
            "first_name",
            "last_name",
            "designation",
            "gender",
            "company_name",
            "email_ids",
            "phone_nos",
        }
        return {key: value for key, value in data.items() if key in allowed_fields}

    company_name = data.get("company_name") or data.get("organization") or ""
    full_name = " ".join(
        part for part in (data.get("first_name"), data.get("last_name")) if part
    ) or data.get("lead_name") or ""
    email = _first_child_value(data.get("email_ids"), "email_id") or data.get("email_id")
    phone = (
        _first_child_value(data.get("phone_nos"), "phone")
        or data.get("mobile_no")
        or data.get("phone")
    )
    website = data.get("website") or data.get("company_domain")

    if target_doctype == "Customer":
        return {
            "customer_name": data.get("customer_name") or company_name or full_name,
            "customer_type": "Company" if company_name else "Individual",
        }
    if target_doctype == "Supplier":
        return {
            "supplier_name": data.get("supplier_name") or company_name or full_name,
            "supplier_type": "Company" if company_name else "Individual",
        }

    return {
        key: value
        for key, value in {
            "lead_name": full_name or company_name,
            "company_name": company_name,
            "email_id": email,
            "mobile_no": phone,
            "website": website,
        }.items()
        if value
    }


def _first_child_value(rows, fieldname: str):
    if not isinstance(rows, list):
        return None
    for row in rows:
        if isinstance(row, dict) and row.get(fieldname):
            return row[fieldname]
    return None
