"""
Named Entity Extractor
=======================
Extracts candidate names, organizations, degree titles, and universities
from resume text. Uses spaCy NER when available, with a robust regex/heuristic
fallback for environments where spaCy is not installed.
"""

import re
from typing import Dict, List, Optional

# ─── spaCy Loading (Optional) ───────────────────────────────────────────────

_nlp = None
_SPACY_AVAILABLE = False

try:
    import spacy
    try:
        _nlp = spacy.load("en_core_web_sm")
        _SPACY_AVAILABLE = True
    except OSError:
        # Model not downloaded — fall back to heuristics
        pass
except ImportError:
    # spaCy not installed — fall back to heuristics
    pass


# ─── Degree Detection ───────────────────────────────────────────────────────

DEGREE_PATTERNS = [
    # Full degree names
    r"(?:Bachelor|Master|Doctor)(?:'?s)?(?:\s+of\s+\w+(?:\s+\w+)?)?",
    # Abbreviated degrees — require dots to avoid matching "Be", "Ma", "Ms"
    r"B\.\s?(?:Tech|Eng|Sc|A|S|Com|Ed|Arch|Des|Pharm)",
    r"M\.\s?(?:Tech|Eng|Sc|A|S|Com|Ed|BA|Phil|Des|Pharm)",
    r"B\.E\.",
    r"M\.E\.",
    r"B\.?B\.?A\.?",
    r"M\.?B\.?A\.?",
    r"B\.?C\.?A\.?",
    r"M\.?C\.?A\.?",
    r"Ph\.?\s?D\.?",
    r"Diploma(?:\s+in\s+\w+(?:\s+\w+)?)?",
    r"Associate(?:'?s)?(?:\s+(?:of|in)\s+\w+(?:\s+\w+)?)?",
    # Common specific degrees
    r"(?:Computer Science|Information Technology|Electrical Engineering|"
    r"Mechanical Engineering|Civil Engineering|Chemical Engineering|"
    r"Electronics|Data Science|Artificial Intelligence|Business Administration|"
    r"Commerce|Economics|Mathematics|Physics|Chemistry|Biology|"
    r"Liberal Arts|Fine Arts|Communications)",
]

DEGREE_REGEX = re.compile(
    '|'.join(f'(?:{p})' for p in DEGREE_PATTERNS),
    re.IGNORECASE,
)

# ─── University Indicators ──────────────────────────────────────────────────

UNIVERSITY_INDICATORS = [
    "university", "institute", "college", "school", "academy",
    "iit", "nit", "iiit", "bits", "mit", "stanford", "harvard",
    "polytechnic", "conservatory",
]

# ─── Common Title Words (to filter out from name detection) ─────────────────

TITLE_KEYWORDS = [
    "resume", "cv", "curriculum", "vitae", "objective", "summary",
    "address", "phone", "email", "experience", "education", "skills",
    "contact", "profile", "http", "www", "linkedin", "github",
    "@", "certification", "project",
]

JOB_TITLE_INDICATORS = [
    "engineer", "developer", "analyst", "scientist", "manager",
    "designer", "architect", "consultant", "intern", "lead",
    "director", "officer", "specialist", "coordinator", "administrator",
    "senior", "junior", "staff", "principal", "vp", "executive",
]


# ─── Name Extraction ────────────────────────────────────────────────────────

def _extract_name_with_spacy(text: str) -> Optional[str]:
    """Extract candidate name using spaCy PERSON entities."""
    if not _SPACY_AVAILABLE or _nlp is None:
        return None

    header_text = text[:500]
    doc = _nlp(header_text)

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            words = name.split()
            if 1 <= len(words) <= 5 and all(
                w.replace(".", "").replace("-", "").isalpha() for w in words
            ):
                return name
    return None


def _extract_name_with_heuristics(text: str) -> Optional[str]:
    """
    Extract candidate name using heuristics.

    Strategy: The first non-empty line that looks like a personal name.
    """
    lines = text.strip().split("\n")

    for line in lines[:10]:
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Clean line: remove common prefixes
        line = re.sub(r'^(Name|Candidate Name|Full Name)\s*:?\s*', '', line, flags=re.IGNORECASE)
        
        # Strip potential contact info from the same line to avoid skipping the whole line
        clean_name_line = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '', line) # remove email
        clean_name_line = re.sub(r'https?://\S+', '', clean_name_line) # remove urls
        clean_name_line = re.sub(r'\|\s+', ' ', clean_name_line) # remove separators
        clean_name_line = clean_name_line.strip()

        if not clean_name_line or len(clean_name_line) < 3:
            continue

        # Skip lines with high keyword density or special characters
        if any(kw in clean_name_line.lower() for kw in TITLE_KEYWORDS):
            continue
        
        # A name is typically 2-4 words, capitalized
        words = clean_name_line.split()
        if 2 <= len(words) <= 5:
            # Check if majority of words are capitalized and alphabetic
            if all(
                (w[0].isupper() or len(w) <= 2)
                and w.replace(".", "").replace("-", "").replace("'", "").isalpha()
                for w in words
            ):
                # Filter out job titles
                if not any(jt in clean_name_line.lower() for jt in JOB_TITLE_INDICATORS):
                    # Final sanity check: no numbers
                    if not re.search(r'\d', clean_name_line):
                        return clean_name_line

    return None


def extract_candidate_name(text: str) -> Optional[str]:
    """
    Extract the candidate's name from resume text.

    Tries spaCy NER first, then falls back to heuristics.
    """
    # Try spaCy first
    name = _extract_name_with_spacy(text)
    if name:
        return name

    # Fallback: heuristic approach
    return _extract_name_with_heuristics(text)


# ─── Organization Extraction ────────────────────────────────────────────────

def _extract_orgs_with_spacy(text: str) -> List[str]:
    """Extract organization names using spaCy ORG entities."""
    if not _SPACY_AVAILABLE or _nlp is None:
        return []

    doc = _nlp(text)
    orgs = []
    seen = set()

    for ent in doc.ents:
        if ent.label_ == "ORG":
            name = ent.text.strip()
            lower = name.lower()
            if lower not in seen and len(name) > 1:
                seen.add(lower)
                orgs.append(name)

    return orgs


# Common well-known companies for heuristic matching
KNOWN_COMPANIES = [
    "Google", "Microsoft", "Amazon", "Apple", "Meta", "Facebook",
    "Netflix", "Tesla", "IBM", "Oracle", "Intel", "Adobe",
    "Salesforce", "SAP", "Uber", "Airbnb", "Twitter", "LinkedIn",
    "Spotify", "Snap", "Stripe", "Shopify", "Atlassian",
    "Infosys", "TCS", "Wipro", "HCL", "Cognizant", "Accenture",
    "Deloitte", "McKinsey", "BCG", "Goldman Sachs", "JPMorgan",
    "Morgan Stanley", "Cisco", "VMware", "Nvidia", "AMD",
    "Samsung", "Sony", "Huawei", "Qualcomm", "PayPal",
]

COMPANY_SUFFIXES = [
    "Inc", "Inc.", "LLC", "Ltd", "Ltd.", "Corp", "Corp.",
    "Corporation", "Company", "Co.", "Group", "Technologies",
    "Solutions", "Services", "Systems", "Consulting",
    "Labs", "Software", "Tech", "Digital", "Global",
    "Pvt", "Private", "Limited",
]


def _extract_orgs_with_heuristics(text: str) -> List[str]:
    """Extract organization names using pattern matching."""
    orgs = []
    seen = set()

    # Check for known company names
    for company in KNOWN_COMPANIES:
        if re.search(r'\b' + re.escape(company) + r'\b', text, re.IGNORECASE):
            if company.lower() not in seen:
                seen.add(company.lower())
                orgs.append(company)

    # Check for company suffixes pattern: "Name Inc." / "Name LLC"
    # Process line-by-line to avoid newlines leaking into matches
    suffix_pattern = '|'.join(re.escape(s) for s in COMPANY_SUFFIXES)
    company_regex = re.compile(
        r'([A-Z][a-zA-Z &#]+)\s+(?:' + suffix_pattern + r')\b',
    )
    for line in text.split('\n'):
        for match in company_regex.finditer(line):
            full = match.group(0).strip()
            if full.lower() not in seen and len(full) < 80:
                seen.add(full.lower())
                orgs.append(full)

    return orgs


def extract_organizations(text: str) -> List[str]:
    """Extract organization names, trying spaCy then heuristics."""
    orgs = _extract_orgs_with_spacy(text)
    if not orgs:
        orgs = _extract_orgs_with_heuristics(text)
    return orgs


# ─── Degree & University Extraction ─────────────────────────────────────────

def extract_degrees(text: str) -> List[str]:
    """Extract degree titles from text using regex patterns."""
    matches = DEGREE_REGEX.findall(text)
    degrees = []
    seen = set()

    for match in matches:
        cleaned = match.strip()
        # Filter out very short fragments (< 4 chars) that are likely noise
        if cleaned and len(cleaned) >= 4 and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            degrees.append(cleaned)

    return degrees


def extract_universities(text: str) -> List[str]:
    """
    Extract university/institution names from text.

    Uses spaCy ORG entities filtered by university indicators,
    plus line-scanning for institution keywords.
    """
    universities = []
    seen = set()

    # Method 1: spaCy ORG entities with university indicators
    if _SPACY_AVAILABLE and _nlp is not None:
        doc = _nlp(text)
        for ent in doc.ents:
            if ent.label_ == "ORG":
                name = ent.text.strip()
                lower = name.lower()
                if any(ind in lower for ind in UNIVERSITY_INDICATORS):
                    if lower not in seen:
                        seen.add(lower)
                        universities.append(name)

    # Method 2: Line-by-line scan for institution keywords
    for line in text.split("\n"):
        line_clean = line.strip()
        line_lower = line_clean.lower()
        if any(ind in line_lower for ind in UNIVERSITY_INDICATORS):
            if line_lower not in seen and len(line_clean) < 150:
                seen.add(line_lower)
                is_substring = any(line_lower in u.lower() for u in universities)
                is_superstring = any(u.lower() in line_lower for u in universities)
                if not is_substring:
                    if is_superstring:
                        universities = [
                            u for u in universities if u.lower() not in line_lower
                        ]
                    universities.append(line_clean)

    return universities


# ─── High-Level API ──────────────────────────────────────────────────────────

def extract_entities(text: str, sections: dict = None) -> Dict[str, object]:
    """
    Extract all named entities from resume text.

    Args:
        text: Full resume text.
        sections: Optional pre-segmented sections dict.

    Returns:
        Dictionary with: name, organizations, degrees, universities.
    """
    education_text = ""
    if sections:
        education_text = sections.get("education", "")

    return {
        "name": extract_candidate_name(text),
        "organizations": extract_organizations(text),
        "degrees": extract_degrees(education_text or text),
        "universities": extract_universities(education_text or text),
    }
