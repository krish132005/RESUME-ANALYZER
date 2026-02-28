"""
Skill Extractor
================
Matches resume text against a skill knowledge base (skills_db.json).
Handles variations, case-insensitive matching, and word-boundary detection.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set


# ─── Skill Database Loading ─────────────────────────────────────────────────

def load_skill_database(db_path: str = None) -> List[dict]:
    """
    Load the skill ontology from a JSON file.

    Args:
        db_path: Path to the skills_db.json file. If None, looks for it
                 in the same directory as this module.

    Returns:
        List of skill entries, each with canonical_name, category, variations.
    """
    if db_path is None:
        db_path = Path(__file__).parent / "skills_db.json"
    else:
        db_path = Path(db_path)

    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("skills", [])


def _build_variation_map(skills: List[dict]) -> Dict[str, dict]:
    """
    Build a lookup map from every variation string (lowercased)
    to its skill entry (canonical_name, category).

    Args:
        skills: List of skill entries from the database.

    Returns:
        Dict mapping lowercase variation → {canonical_name, category}.
    """
    vmap = {}
    for skill in skills:
        canonical = skill["canonical_name"]
        category = skill["category"]
        info = {"canonical_name": canonical, "category": category}

        # Add the canonical name itself as a variation
        vmap[canonical.lower()] = info

        for var in skill.get("variations", []):
            vmap[var.lower()] = info

    return vmap


# ─── Public API ──────────────────────────────────────────────────────────────

def extract_skills(
    text: str,
    db_path: str = None,
) -> Dict[str, List[str]]:
    """
    Extract skills from resume text by matching against the skill knowledge base.

    Uses word-boundary-aware matching to avoid partial matches (e.g., "Java"
    should not match "JavaScript"). Skills are grouped by category.

    Args:
        text: Resume text (ideally the skills section, but can be full text).
        db_path: Optional path to skills_db.json.

    Returns:
        Dictionary mapping category names to lists of canonical skill names.
        Example:
            {
                "Programming": ["Python", "Java", "SQL"],
                "Framework": ["React", "Django"],
                "Soft Skills": ["Leadership", "Communication"],
            }
    """
    skills_db = load_skill_database(db_path)
    variation_map = _build_variation_map(skills_db)

    text_lower = text.lower()

    found: Dict[str, Set[str]] = {}  # category → set of canonical names

    # Sort variations by length descending so longer phrases match first
    sorted_variations = sorted(variation_map.keys(), key=len, reverse=True)

    matched_canonicals: Set[str] = set()

    for variation in sorted_variations:
        info = variation_map[variation]
        canonical = info["canonical_name"]

        # Skip if we already found this skill
        if canonical in matched_canonicals:
            continue

        # Word-boundary matching to avoid partial matches
        # Special handling for skills with special chars (C++, C#, .NET, etc.)
        escaped = re.escape(variation)
        pattern = r'(?<![a-zA-Z0-9])' + escaped + r'(?![a-zA-Z0-9])'

        if re.search(pattern, text_lower):
            category = info["category"]
            if category not in found:
                found[category] = set()
            found[category].add(canonical)
            matched_canonicals.add(canonical)

    # Convert sets to sorted lists
    result = {
        category: sorted(list(skills))
        for category, skills in sorted(found.items())
    }

    return result


def extract_skills_flat(
    text: str,
    db_path: str = None,
) -> List[str]:
    """
    Extract skills as a flat list (no categorization).

    Args:
        text: Resume text.
        db_path: Optional path to skills_db.json.

    Returns:
        Sorted list of canonical skill names found in the text.
    """
    categorized = extract_skills(text, db_path)
    all_skills = []
    for skills in categorized.values():
        all_skills.extend(skills)
    return sorted(set(all_skills))
