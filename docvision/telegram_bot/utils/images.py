"""Image validation and encoding helpers."""

import base64

import frappe

MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
GENERIC_BINARY_TYPES = {
    "application/octet-stream",
    "binary/octet-stream",
    "application/x-download",
}


def image_bytes_to_data_url(content: bytes, content_type: str | None) -> str:
    """Return a provider-safe image data URL after validating its real format."""
    if not isinstance(content, bytes):
        frappe.throw("Image content could not be read.")
    if not content or len(content) > MAX_IMAGE_BYTES:
        frappe.throw("Image must be between 1 byte and 10 MB.")

    detected_type = _detect_image_type(content)
    declared_type = (content_type or "").split(";", 1)[0].strip().lower()
    if declared_type == "image/jpg":
        declared_type = "image/jpeg"

    if detected_type not in ALLOWED_IMAGE_TYPES:
        frappe.throw("Only JPEG, PNG, and WebP images are supported.")

    if declared_type and declared_type not in GENERIC_BINARY_TYPES:
        if declared_type not in ALLOWED_IMAGE_TYPES:
            frappe.throw("Only JPEG, PNG, and WebP images are supported.")
        if declared_type != detected_type:
            frappe.throw("The image content does not match its declared file type.")

    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{detected_type};base64,{encoded}"


def validate_image_size(content_length: str | None) -> None:
    if not content_length:
        return
    try:
        size = int(content_length)
    except (TypeError, ValueError):
        frappe.throw("Invalid image size.")
    if size < 0 or size > MAX_IMAGE_BYTES:
        frappe.throw("Image must not exceed 10 MB.")


def _detect_image_type(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    return None
