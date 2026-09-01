"""Country resolution and dynamic AI prompting for ERPNext DocTypes."""

import json
import os
import re
import frappe

# Common aliases and acronyms to bridge informal names/abbreviations to standard country names
COMMON_COUNTRY_ALIASES = {
    # United States
    "us": "United States",
    "usa": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "u.s.a": "United States",
    "united states of america": "United States",
    "america": "United States",
    # United Kingdom
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "u.k": "United Kingdom",
    "gb": "United Kingdom",
    "gbr": "United Kingdom",
    "great britain": "United Kingdom",
    "britain": "United Kingdom",
    "united kingdom": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    # United Arab Emirates
    "uae": "United Arab Emirates",
    "u.a.e.": "United Arab Emirates",
    "u.a.e": "United Arab Emirates",
    "ae": "United Arab Emirates",
    "are": "United Arab Emirates",
    "emirates": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
    "dubai": "United Arab Emirates",
    "abu dhabi": "United Arab Emirates",
    # India
    "in": "India",
    "ind": "India",
    "india": "India",
    "bharat": "India",
    "hindustan": "India",
    # Germany
    "de": "Germany",
    "deu": "Germany",
    "ger": "Germany",
    "germany": "Germany",
    "deutschland": "Germany",
    # Canada
    "ca": "Canada",
    "can": "Canada",
    "canada": "Canada",
    # Australia
    "au": "Australia",
    "aus": "Australia",
    "australia": "Australia",
    # Singapore
    "sg": "Singapore",
    "sgp": "Singapore",
    "singapore": "Singapore",
    # Saudi Arabia
    "sa": "Saudi Arabia",
    "sau": "Saudi Arabia",
    "ksa": "Saudi Arabia",
    "k.s.a.": "Saudi Arabia",
    "k.s.a": "Saudi Arabia",
    "saudi": "Saudi Arabia",
    "saudi arabia": "Saudi Arabia",
    # Netherlands
    "nl": "Netherlands",
    "nld": "Netherlands",
    "netherlands": "Netherlands",
    "holland": "Netherlands",
    # Switzerland
    "ch": "Switzerland",
    "che": "Switzerland",
    "switzerland": "Switzerland",
    "swiss": "Switzerland",
    # France
    "fr": "France",
    "fra": "France",
    "france": "France",
    # Spain
    "es": "Spain",
    "esp": "Spain",
    "spain": "Spain",
    # Italy
    "it": "Italy",
    "ita": "Italy",
    "italy": "Italy",
    # Japan
    "jp": "Japan",
    "jpn": "Japan",
    "japan": "Japan",
    # China
    "cn": "China",
    "chn": "China",
    "china": "China",
    # Hong Kong
    "hk": "Hong Kong",
    "hkg": "Hong Kong",
    "hong kong": "Hong Kong",
    # New Zealand
    "nz": "New Zealand",
    "nzl": "New Zealand",
    "new zealand": "New Zealand",
    # South Africa
    "za": "South Africa",
    "zaf": "South Africa",
    "south africa": "South Africa",
    # Qatar
    "qa": "Qatar",
    "qat": "Qatar",
    "qatar": "Qatar",
    # Kuwait
    "kw": "Kuwait",
    "kwt": "Kuwait",
    "kuwait": "Kuwait",
    # Oman
    "om": "Oman",
    "omn": "Oman",
    "oman": "Oman",
    # Bahrain
    "bh": "Bahrain",
    "bhr": "Bahrain",
    "bahrain": "Bahrain",
    # Malaysia
    "my": "Malaysia",
    "mys": "Malaysia",
    "malaysia": "Malaysia",
    # Indonesia
    "id": "Indonesia",
    "idn": "Indonesia",
    "indonesia": "Indonesia",
    # Philippines
    "ph": "Philippines",
    "phl": "Philippines",
    "philippines": "Philippines",
    # Thailand
    "th": "Thailand",
    "tha": "Thailand",
    "thailand": "Thailand",
    # Vietnam
    "vn": "Vietnam",
    "vnm": "Vietnam",
    "vietnam": "Vietnam",
    # Bangladesh
    "bd": "Bangladesh",
    "bgd": "Bangladesh",
    "bangladesh": "Bangladesh",
    # Sri Lanka
    "lk": "Sri Lanka",
    "lka": "Sri Lanka",
    "sri lanka": "Sri Lanka",
    # Nepal
    "np": "Nepal",
    "npl": "Nepal",
    "nepal": "Nepal",
    # Pakistan
    "pk": "Pakistan",
    "pak": "Pakistan",
    "pakistan": "Pakistan",
    # Kenya
    "ke": "Kenya",
    "ken": "Kenya",
    "kenya": "Kenya",
    # Nigeria
    "ng": "Nigeria",
    "nga": "Nigeria",
    "nigeria": "Nigeria",
    # Egypt
    "eg": "Egypt",
    "egy": "Egypt",
    "egypt": "Egypt",
    # Brazil
    "br": "Brazil",
    "bra": "Brazil",
    "brazil": "Brazil",
    # Mexico
    "mx": "Mexico",
    "mex": "Mexico",
    "mexico": "Mexico",
    # Ireland
    "ie": "Ireland",
    "irl": "Ireland",
    "ireland": "Ireland",
    # Sweden
    "se": "Sweden",
    "swe": "Sweden",
    "sweden": "Sweden",
    # Norway
    "no": "Norway",
    "nor": "Norway",
    "norway": "Norway",
    # Denmark
    "dk": "Denmark",
    "dnk": "Denmark",
    "denmark": "Denmark",
    # Finland
    "fi": "Finland",
    "fin": "Finland",
    "finland": "Finland",
    # Belgium
    "be": "Belgium",
    "bel": "Belgium",
    "belgium": "Belgium",
    # Austria
    "at": "Austria",
    "aut": "Austria",
    "austria": "Austria",
    # Portugal
    "pt": "Portugal",
    "prt": "Portugal",
    "portugal": "Portugal",
    # Greece
    "gr": "Greece",
    "grc": "Greece",
    "greece": "Greece",
    # Turkey / Turkiye
    "tr": "Turkey",
    "tur": "Turkey",
    "turkey": "Turkey",
    "turkiye": "Turkey",
    "türkiye": "Turkey",
    # Israel
    "il": "Israel",
    "isr": "Israel",
    "israel": "Israel",
    # Russia
    "ru": "Russia",
    "rus": "Russia",
    "russia": "Russia",
    # South Korea
    "kr": "South Korea",
    "kor": "South Korea",
    "south korea": "South Korea",
    "korea": "South Korea",
}


def _load_frappe_country_map() -> dict[str, str]:
    """Load standard country info from Frappe's geo database."""
    country_map = {}
    try:
        frappe_path = frappe.get_app_path("frappe", "geo", "country_info.json")
        if os.path.exists(frappe_path):
            with open(frappe_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for country_name, info in data.items():
                    country_map[country_name.casefold()] = country_name
                    if isinstance(info, dict) and "code" in info:
                        country_map[info["code"].casefold()] = country_name
    except Exception:
        pass
    return country_map


_FRAPPE_COUNTRY_MAP = _load_frappe_country_map()


def get_system_countries() -> list[str]:
    """
    Dynamically retrieve all active Country document names from Frappe.
    Falls back to Frappe geo country_info if database is not initialized.
    """
    try:
        if hasattr(frappe, "db") and frappe.db:
            countries = frappe.db.get_all("Country", pluck="name", order_by="name asc")
            if countries:
                return countries
    except Exception:
        pass
    return sorted(list({name for name in _FRAPPE_COUNTRY_MAP.values()}))


def get_country_extraction_prompt() -> str:
    """
    Generates dynamic system extraction instructions containing the actual
    ERPNext Country list from the database to feed directly to the AI model.
    """
    countries = get_system_countries()
    countries_str = ", ".join(countries)
    return (
        "Extraction Guidelines for Address & Country:\n"
        f"- Valid ERPNext Countries in this system:\n[{countries_str}]\n"
        "- For address.country: You MUST match the extracted country to its exact official Country name from the valid list above.\n"
        "- If the business card shows a country code, state, or abbreviation (e.g., 'US', 'USA', 'CA', 'NY' -> 'United States'; 'UK', 'GB', 'London' -> 'United Kingdom'; 'UAE', 'Dubai' -> 'United Arab Emirates'; 'IN' -> 'India'), map it to the corresponding Country name from the list.\n"
        "- If the country is not specified on the card or is located in India, default to 'India'."
    )


def resolve_country(raw_country: str | None, default: str | None = "India") -> str | None:
    """
    Resolve and normalize a raw country string (e.g. 'US', 'USA', 'u.s.a', 'IN', 'uk')
    to a valid ERPNext Country document name.

    Resolution hierarchy:
    1. Direct alias / acronym match (e.g., 'US' -> 'United States')
    2. Frappe country_info.json lookup (case-insensitive name or 2-letter ISO code)
    3. Dynamic database lookup in `tabCountry` (by name or code)
    4. Safe fallback to default ('India') if valid
    5. None (prevents LinkValidationError)
    """
    if not raw_country or not isinstance(raw_country, str):
        return _validate_against_db(default) if default else None

    cleaned = raw_country.strip()
    if not cleaned:
        return _validate_against_db(default) if default else None

    # Strip surrounding quotes and punctuation
    cleaned_lower = re.sub(r"^[\s\"']+|[\s\"']+$", "", cleaned).casefold()
    cleaned_normalized = re.sub(r"[^\w\s]", "", cleaned_lower).strip()

    # 1. Check known aliases dictionary
    if cleaned_lower in COMMON_COUNTRY_ALIASES:
        candidate = COMMON_COUNTRY_ALIASES[cleaned_lower]
        return _validate_against_db(candidate)

    if cleaned_normalized in COMMON_COUNTRY_ALIASES:
        candidate = COMMON_COUNTRY_ALIASES[cleaned_normalized]
        return _validate_against_db(candidate)

    # 2. Check Frappe country_info map
    if cleaned_lower in _FRAPPE_COUNTRY_MAP:
        candidate = _FRAPPE_COUNTRY_MAP[cleaned_lower]
        return _validate_against_db(candidate)

    if cleaned_normalized in _FRAPPE_COUNTRY_MAP:
        candidate = _FRAPPE_COUNTRY_MAP[cleaned_normalized]
        return _validate_against_db(candidate)

    # 3. Dynamic Database lookup in tabCountry
    db_country = _lookup_in_database(cleaned, cleaned_lower)
    if db_country:
        return db_country

    # 4. Fallback to default
    if default:
        return _validate_against_db(default)

    return None


def _lookup_in_database(cleaned: str, cleaned_lower: str) -> str | None:
    """Lookup country in Frappe tabCountry table dynamically."""
    try:
        if not hasattr(frappe, "db") or not frappe.db:
            return None

        # Check exact name
        if frappe.db.exists("Country", cleaned):
            return cleaned

        # Check case-insensitive name or code
        results = frappe.db.sql(
            """
            SELECT name FROM `tabCountry`
            WHERE LOWER(name) = %s OR LOWER(code) = %s
            LIMIT 1
            """,
            (cleaned_lower, cleaned_lower),
            as_dict=True,
        )
        if results and results[0].get("name"):
            return results[0]["name"]
    except Exception:
        pass
    return None


def _validate_against_db(country_name: str | None) -> str | None:
    """Verify that the resolved country exists in the database if DB is connected."""
    if not country_name:
        return None
    try:
        if hasattr(frappe, "db") and frappe.db and hasattr(frappe.db, "exists"):
            if frappe.db.exists("Country", country_name):
                return country_name
            # If DB exists check fails, try finding by name case-insensitively
            results = frappe.db.sql(
                "SELECT name FROM `tabCountry` WHERE LOWER(name) = %s LIMIT 1",
                (country_name.casefold(),),
                as_dict=True,
            )
            if results and results[0].get("name"):
                return results[0]["name"]
    except Exception:
        pass
    return country_name
