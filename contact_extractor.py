"""
Contact Information Extractor
==============================
Uses Regular Expressions to extract and normalize email addresses,
phone numbers, LinkedIn URLs, GitHub URLs, and portfolio/website links.
"""

import re
from typing import Dict, List, Optional


# ─── Regex Patterns ─────────────────────────────────────────────────────────

# Email: standard RFC-5322-ish pattern
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE,
)

# Phone: international and domestic formats
# Matches: +1-234-567-8901, (234) 567-8901, 234.567.8901,
#          +91 98765 43210, 9876543210, etc.
PHONE_PATTERN = re.compile(
    r'(?:\+?\d{1,3}[\s\-.]?)?\(?\d{2,4}\)?[\s\-.]?\d{3,5}[\s\-.]?\d{3,5}',
)

# LinkedIn profile URL
LINKEDIN_PATTERN = re.compile(
    r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+/?',
    re.IGNORECASE,
)

# GitHub profile URL
GITHUB_PATTERN = re.compile(
    r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9\-_]+/?',
    re.IGNORECASE,
)

# General website / portfolio URL
WEBSITE_PATTERN = re.compile(
    r'https?://[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)+(?:/[^\s]*)?',
    re.IGNORECASE,
)


# ─── Phone Normalization ────────────────────────────────────────────────────

def _normalize_phone(raw_phone: str) -> str:
    """
    Normalize a phone number to a cleaner format.
    Strips extraneous characters and ensures consistent formatting.

    Args:
        raw_phone: Raw phone string from regex match.

    Returns:
        Normalized phone string.
    """
    # Remove all non-digit characters except leading +
    digits = re.sub(r'[^\d+]', '', raw_phone)

    # If it already starts with +, keep it
    if digits.startswith('+'):
        return digits

    # If 10 digits (likely US/India domestic), leave as-is
    if len(digits) == 10:
        return digits

    # If 11+ digits and doesn't start with +, add +
    if len(digits) >= 11:
        return '+' + digits

    return digits


def _is_valid_phone(phone: str) -> bool:
    """
    Basic validation: phone should have at least 7 digits.
    Filters out false positives like dates (2020-2024) or zip codes.
    """
    digits = re.sub(r'\D', '', phone)
    return 7 <= len(digits) <= 15


# ─── Public API ──────────────────────────────────────────────────────────────

def extract_contact_info(text: str) -> Dict[str, object]:
    """
    Extract all contact information from resume text.

    Args:
        text: Full resume text (ideally the header/contact section,
              but can also be the full text).

    Returns:
        Dictionary with keys:
            - "emails": list of email addresses
            - "phones": list of normalized phone numbers
            - "linkedin": LinkedIn URL or None
            - "github": GitHub URL or None
            - "websites": list of other URLs (excluding LinkedIn/GitHub)
    """
    result: Dict[str, object] = {
        "emails": [],
        "phones": [],
        "linkedin": None,
        "github": None,
        "websites": [],
    }

    # ── Emails ──
    emails = EMAIL_PATTERN.findall(text)
    # Deduplicate while preserving order
    seen = set()
    for email in emails:
        lower = email.lower()
        if lower not in seen:
            seen.add(lower)
            result["emails"].append(email)

    # ── Phone Numbers ──
    phones = PHONE_PATTERN.findall(text)
    for phone in phones:
        if _is_valid_phone(phone):
            normalized = _normalize_phone(phone)
            if normalized not in result["phones"]:
                result["phones"].append(normalized)

    # ── LinkedIn ──
    linkedin_match = LINKEDIN_PATTERN.search(text)
    if linkedin_match:
        url = linkedin_match.group()
        if not url.startswith("http"):
            url = "https://" + url
        result["linkedin"] = url

    # ── GitHub ──
    github_match = GITHUB_PATTERN.search(text)
    if github_match:
        url = github_match.group()
        if not url.startswith("http"):
            url = "https://" + url
        result["github"] = url

    # ── Other Websites ──
    all_urls = WEBSITE_PATTERN.findall(text)
    linkedin_str = result["linkedin"] or ""
    github_str = result["github"] or ""
    for url in all_urls:
        if "linkedin.com" not in url.lower() and "github.com" not in url.lower():
            if url not in result["websites"]:
                result["websites"].append(url)

    return result
