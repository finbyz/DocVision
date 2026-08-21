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


def html_to_safe_telegram_text(value: str) -> str:
    parser = _PlainTextParser()
    parser.feed(value or "")
    parser.close()
    return "".join(parser.parts).strip()


class _PlainTextParser(HTMLParser):
    BREAK_TAGS = {"br", "div", "li", "p"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.BREAK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(escape_telegram(data))
