"""
Experience & Education Parser
==============================
Parses the Experience and Education sections of a resume into
structured entries with company/institution, title/degree, dates,
and descriptions.
"""

import re
from typing import Dict, List, Optional, Tuple


# ─── Date Patterns ──────────────────────────────────────────────────────────

MONTH_NAMES = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)"
)

# Matches: "Jan 2020 - Present", "March 2019 – Dec 2021", "2018 - 2022"
DATE_RANGE_PATTERN = re.compile(
    r'(' + MONTH_NAMES + r'[\s,]*\d{4}|\d{4})'
    r'\s*[\-\u2013\u2014to]+\s*'
    r'(' + MONTH_NAMES + r'[\s,]*\d{4}|\d{4}|[Pp]resent|[Cc]urrent|[Nn]ow|[Oo]ngoing)',
    re.IGNORECASE,
)

# Single date: "May 2023" or "2023"
SINGLE_DATE_PATTERN = re.compile(
    r'(' + MONTH_NAMES + r'[\s,]*\d{4}|\d{4})',
    re.IGNORECASE,
)

# GPA pattern: "GPA: 3.8/4.0", "CGPA: 9.2/10", "3.85 GPA"
# Requires a decimal point to avoid matching bare years like "2016"
GPA_PATTERN = re.compile(
    r'(?:(?:C?GPA|Grade)\s*:?\s*(\d+\.\d+)\s*(?:/\s*\d+\.?\d*)?|'
    r'(\d+\.\d+)\s*(?:/\s*\d+\.?\d*)?\s*(?:C?GPA|Grade))',
    re.IGNORECASE,
)


# ─── Experience Parsing ────────────────────────────────────────────────────

def _split_into_entries(text: str) -> List[str]:
    """
    Split a section's text into individual entries.
    Entries are Typically separated by double newlines or date patterns.
    """
    if not text.strip():
        return []

    # Strip excessive leading/trailing whitespace
    text = text.strip()

    # Split on double newlines as the primary separator
    blocks = re.split(r'\n\s*\n', text)
    
    # If we only got one block, try to split by date patterns at the start of lines
    if len(blocks) <= 1:
        # Match lines that START with a date or contain a date range
        # Use a more aggressive split if the section is just one long list
        entries = []
        lines = text.split('\n')
        current = []
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Start a new entry if this line has a date range
            if DATE_RANGE_PATTERN.search(line) and current:
                entries.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            entries.append("\n".join(current))
        return entries

    return blocks


def _extract_date_range(text: str) -> Optional[Dict[str, str]]:
    """Extract start and end dates from text."""
    match = DATE_RANGE_PATTERN.search(text)
    if match:
        return {
            "start_date": match.group(1).strip(),
            "end_date": match.group(2).strip(),
        }
    return None


def parse_experience_entry(entry_text: str) -> Dict[str, object]:
    """
    Parse a single experience entry into structured fields.
    """
    lines = [l.strip() for l in entry_text.strip().split("\n") if l.strip()]
    if not lines:
        return {}

    result = {
        "company": None,
        "title": None,
        "dates": None,
        "description": "",
    }

    # Extract dates from the whole entry first
    dates = _extract_date_range(entry_text)
    if dates:
        result["dates"] = dates

    # Process first line for title and company
    first_line = lines[0]
    
    # 1. Check for inline date range at the END of the first line
    # Format: "Senior Developer                  Jan 2020 - Present"
    date_match = DATE_RANGE_PATTERN.search(first_line)
    if date_match and date_match.start() > 5:
        # We found a date range on the same line. 
        # Title is what's before it.
        result["title"] = first_line[:date_match.start()].strip().rstrip('|').strip()
        description_start = 1
        # Extract company from the next line if it's there
        if len(lines) > 1:
            clean_company = DATE_RANGE_PATTERN.sub('', lines[1]).strip()
            if clean_company:
                result["company"] = clean_company
                description_start = 2
    
    # 2. Check for "Title \n Company + Dates" pattern
    # Format: 
    #   "Software Testing Engineer" (Line 0)
    #   "Online clump Jan 2016 - Mar 2018" (Line 1)
    elif len(lines) > 1 and DATE_RANGE_PATTERN.search(lines[1]):
        # First line is likely the Title
        result["title"] = DATE_RANGE_PATTERN.sub('', lines[0]).strip()
        # Second line contains Company and Dates
        clean_company = DATE_RANGE_PATTERN.sub('', lines[1]).strip()
        if clean_company:
            result["company"] = clean_company
        description_start = 2

    # 3. Existing pipe and "at" split logic if title not found yet
    elif "|" in first_line:
        pipe_split = re.split(r'\s*\|\s*', first_line)
        if len(pipe_split) >= 2:
            non_date_parts = [p for p in pipe_split if not DATE_RANGE_PATTERN.search(p) and not SINGLE_DATE_PATTERN.fullmatch(p)]
            if len(non_date_parts) >= 2:
                result["title"] = non_date_parts[0]
                result["company"] = non_date_parts[1]
                description_start = 1
            else:
                result["title"] = non_date_parts[0] if non_date_parts else first_line
                description_start = 1
    
    elif " at " in first_line.lower():
        parts = re.split(r'\s+at\s+', first_line, maxsplit=1, flags=re.IGNORECASE)
        result["title"] = parts[0].strip()
        result["company"] = DATE_RANGE_PATTERN.sub('', parts[1]).strip()
        description_start = 1
        
    else:
        # Default: first line is title, second is company
        result["title"] = DATE_RANGE_PATTERN.sub('', first_line).strip()
        if len(lines) > 1:
            result["company"] = DATE_RANGE_PATTERN.sub('', lines[1]).strip()
            description_start = 2
        else:
            description_start = 1

    # Final cleanup of title/company fields
    if result["title"]:
        result["title"] = SINGLE_DATE_PATTERN.sub('', result["title"]).strip().rstrip(',').strip()
    if result["company"]:
        result["company"] = SINGLE_DATE_PATTERN.sub('', result["company"]).strip().rstrip(',').strip()

    # Remaining lines are the description
    desc_lines = lines[description_start:]
    desc_lines = [l for l in desc_lines if not DATE_RANGE_PATTERN.search(l) or len(l) > 40]
    result["description"] = "\n".join(desc_lines)

    return result


def parse_experience_section(text: str) -> List[Dict[str, object]]:
    """
    Parse the full Experience section into a list of structured entries.

    Args:
        text: Text content of the Experience section.

    Returns:
        List of experience entry dicts.
    """
    entries = _split_into_entries(text)
    parsed = []

    for entry in entries:
        parsed_entry = parse_experience_entry(entry)
        if parsed_entry and (parsed_entry.get("title") or parsed_entry.get("company")):
            parsed.append(parsed_entry)

    return parsed


# ─── Education Parsing ──────────────────────────────────────────────────────

def parse_education_entry(entry_text: str) -> Dict[str, object]:
    """
    Parse a single education entry.

    Extracts:
        - institution: University/college name
        - degree: Degree title
        - dates: {start_date, end_date}
        - gpa: GPA/CGPA value if found
        - details: Any additional text

    Args:
        entry_text: Text of a single education entry.

    Returns:
        Dictionary with extracted fields.
    """
    lines = [l.strip() for l in entry_text.strip().split("\n") if l.strip()]
    if not lines:
        return {}

    result = {
        "institution": None,
        "degree": None,
        "dates": None,
        "gpa": None,
        "details": "",
    }

    # Extract dates
    dates = _extract_date_range(entry_text)
    if dates:
        result["dates"] = dates

    # Extract GPA
    gpa_match = GPA_PATTERN.search(entry_text)
    if gpa_match:
        result["gpa"] = gpa_match.group(1) or gpa_match.group(2)

    # Heuristic: first line is usually institution or degree
    # Common formats:
    #   "MIT | B.S. Computer Science | 2018 - 2022"
    #   "Massachusetts Institute of Technology"
    #   "B.Tech in Computer Science"
    #   "University of California, Berkeley\nB.S. in EECS\n2016-2020"

    from entity_extractor import UNIVERSITY_INDICATORS, DEGREE_REGEX  # noqa

    for line in lines[:3]:
        clean = line.strip()
        clean_lower = clean.lower()

        # Check if line contains a university indicator
        if not result["institution"] and any(
            ind in clean_lower for ind in UNIVERSITY_INDICATORS
        ):
            # Remove date parts
            inst = DATE_RANGE_PATTERN.sub('', clean).strip()
            inst = SINGLE_DATE_PATTERN.sub('', inst).strip().rstrip(',').strip()
            if inst:
                result["institution"] = inst

        # Check if line contains a degree
        if not result["degree"]:
            degree_match = DEGREE_REGEX.search(clean)
            if degree_match:
                result["degree"] = clean
                # Remove date parts from degree line
                result["degree"] = DATE_RANGE_PATTERN.sub('', result["degree"]).strip()
                result["degree"] = re.sub(r'\s*[\|,]\s*$', '', result["degree"]).strip()

    # If no institution found but we have lines, use first non-degree line
    if not result["institution"] and lines:
        for line in lines[:2]:
            clean = line.strip()
            if clean and clean != result.get("degree"):
                clean = DATE_RANGE_PATTERN.sub('', clean).strip()
                clean = SINGLE_DATE_PATTERN.sub('', clean).strip().rstrip(',').strip()
                if clean:
                    result["institution"] = clean
                    break

    # Remaining text as details
    detail_lines = [l for l in lines[2:] if l.strip()]
    result["details"] = "\n".join(detail_lines)

    return result


def parse_education_section(text: str) -> List[Dict[str, object]]:
    """
    Parse the full Education section into structured entries.

    Args:
        text: Text content of the Education section.

    Returns:
        List of education entry dicts.
    """
    entries = _split_into_entries(text)
    parsed = []

    for entry in entries:
        parsed_entry = parse_education_entry(entry)
        if parsed_entry and (
            parsed_entry.get("institution") or parsed_entry.get("degree")
        ):
            parsed.append(parsed_entry)

    return parsed
