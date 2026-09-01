"""Safe Telegram HTML formatting helpers."""

import html
from html.parser import HTMLParser
from urllib.parse import quote


def escape_telegram(value) -> str:
    return html.escape(str(value or ""), quote=True)


def telegram_form_link(doctype: str, name: str, label: str) -> str:
    import frappe

    base_url = frappe.utils.get_url().rstrip("/")
    route = f"/app/{quote(doctype.lower(), safe='')}/{quote(str(name), safe='')}"
    return f'<a href="{escape_telegram(base_url + route)}">{escape_telegram(label)}</a>'


import re


def html_to_safe_telegram_text(value: str) -> str:
    if not value:
        return ""
    parser = _PlainTextParser()
    parser.feed(value)
    parser.close()
    text = "".join(parser.parts)
    # Collapse multiple blank lines (3 or more \n -> \n\n)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip()


class _PlainTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._last_was_newline = False

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.parts.append("\n")
            self._last_was_newline = True

    def handle_endtag(self, tag):
        if tag in {"p", "div"}:
            self.parts.append("\n\n")
            self._last_was_newline = True
        elif tag in {"li", "tr"}:
            self.parts.append("\n")
            self._last_was_newline = True

    def handle_data(self, data):
        if not data:
            return
        # If preceding element was a line break, strip leading newlines from literal HTML data
        if self._last_was_newline:
            data = data.lstrip("\r\n")
        if data:
            self.parts.append(escape_telegram(data))
            self._last_was_newline = data.endswith("\n")

