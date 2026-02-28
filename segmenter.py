"""
Section Segmentation Module
============================
Splits cleaned resume text into logical sections using keyword-based
heuristics. Handles variations in heading style (ALL CAPS, Title Case, etc.).
"""

import re
from typing import Dict, List, Tuple

# ─── Section Heading Definitions ────────────────────────────────────────────

# Each key is a canonical section name; values are keyword patterns that may
# appear as headings in real resumes (case-insensitive matching).

SECTION_KEYWORDS: Dict[str, List[str]] = {
    "contact": [
        "contact", "contact info", "contact information", "personal info",
        "personal information", "personal details",
    ],
    "summary": [
        "summary", "profile", "professional profile", "about me", "objective", 
        "career objective", "summary of experience", "technical summary", "executive summary"
    ],
    "skills": [
        "skills", "technical skills", "tech skills", "competencies", "core competencies", 
        "expertise", "areas of expertise", "it skills", "functional skills", 
        "professional skills", "key skills", "specialties", "proficiencies", "skill set"
    ],
    "experience": [
        "experience", "work experience", "employment history", "professional experience", 
        "work history", "career history", "professional background", "experience history", "positions held"
    ],
    "education": [
        "education", "academic background", "academic history", "qualification", 
        "qualifications", "academic credentials", "academic qualifications", "academics"
    ],
    "projects": [
        "projects", "key projects", "personal projects", "academic projects", 
        "professional projects", "technical projects", "selected projects", "notable projects"
    ],
    "certifications": [
        "certifications", "certificates", "professional certifications",
        "licenses", "licenses and certifications", "training",
        "professional development",
    ],
    "publications": [
        "publications", "papers", "research", "research papers",
        "conferences",
    ],
    "awards": [
        "awards", "honors", "achievements", "accomplishments",
        "awards and honors",
    ],
    "languages": [
        "languages", "language proficiency", "language skills",
    ],
    "interests": [
        "interests", "hobbies", "hobbies and interests",
        "extracurricular", "extracurricular activities", "activities",
    ],
    "references": [
        "references",
    ],
    "frameworks": [
        "frameworks", "tools", "technologies", "frameworks & tools", 
        "technical environment", "tools & technologies", "it environment"
    ],
    "volunteer": [
        "volunteer", "volunteer experience", "volunteering",
        "community service", "social work",
    ],
}


def _build_heading_pattern() -> re.Pattern:
    """
    Build a compiled regex pattern that matches any of the known section
    headings. The pattern matches lines that:
      - Start at the beginning of a line (after optional whitespace)
      - Contain a known heading keyword
      - Are optionally followed by a colon
      - Appear on their own line (no significant trailing text)
    """
    all_keywords = []
    for keywords in SECTION_KEYWORDS.values():
        all_keywords.extend(keywords)

    # Sort by length descending so longer phrases match first
    all_keywords.sort(key=len, reverse=True)

    # Escape special regex chars and join with alternation
    escaped = [re.escape(kw) for kw in all_keywords]
    
    # Relaxed pattern: Heading must be at the start of a line,
    # followed by optional colon, and either newline or extra space.
    # This helps catch "EXPERIENCE: ..." even if there is trailing text on the same line.
    pattern = r'^\s*(?:' + '|'.join(escaped) + r')\s*(?::\s*|\n|$)'

    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


HEADING_PATTERN = _build_heading_pattern()


def _normalize_section_name(heading_text: str) -> str:
    """
    Map a detected heading string back to its canonical section name.
    """
    cleaned = heading_text.strip().lower()

    # Sort all keywords by length descending to match longest first
    all_kw_flat = []
    for section_name, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            all_kw_flat.append((kw, section_name))
    
    all_kw_flat.sort(key=lambda x: len(x[0]), reverse=True)

    for kw, section_name in all_kw_flat:
        if kw.lower() in cleaned:
            return section_name

    # Fallback: return the cleaned heading itself
    return cleaned.rstrip(":").strip()

def _find_headings(text: str) -> List[Tuple[int, int, str]]:
    """
    Find all section headings in the text.

    Returns:
        List of (start_position, end_position, canonical_section_name) tuples,
        sorted by position in the text.
    """
    headings = []

    for match in HEADING_PATTERN.finditer(text):
        raw = match.group().strip()
        canonical = _normalize_section_name(raw)
        headings.append((match.start(), match.end(), canonical))

    return headings


def segment_resume(text: str) -> Dict[str, str]:
    """
    Segment a cleaned resume text into logical sections.

    The function identifies section headings using keyword heuristics and
    splits the text between consecutive headings. Any text before the first
    detected heading is stored under the "header" key (typically contains
    the candidate's name and contact info).

    Args:
        text: Cleaned resume text.

    Returns:
        Dictionary mapping section names (str) to section content (str).
        Example keys: "header", "summary", "experience", "education", "skills"
    """
    if not text:
        return {"header": ""}

    headings = _find_headings(text)

    sections: Dict[str, str] = {}

    if not headings:
        # No headings found — return the entire text as header
        sections["header"] = text.strip()
        return sections

    # Text before the first heading = header (name, contact, etc.)
    header_text = text[: headings[0][0]].strip()
    if header_text:
        sections["header"] = header_text

    # Extract content between consecutive headings
    for i, (start, end, section_name) in enumerate(headings):
        # Content starts after the heading line
        content_start = end

        # Content ends at the start of the next heading (or end of text)
        if i + 1 < len(headings):
            content_end = headings[i + 1][0]
        else:
            content_end = len(text)

        content = text[content_start:content_end].strip()

        # If the same section appears twice, merge content
        if section_name in sections:
            sections[section_name] += "\n\n" + content
        else:
            sections[section_name] = content

    return sections
