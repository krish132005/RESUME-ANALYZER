"""
Resume Parser Engine
=====================
Main module containing the ResumeParser class that orchestrates the
full parsing pipeline: ingestion → cleaning → segmentation → extraction
→ structured JSON output.

Usage:
    from parser import ResumeParser

    rp = ResumeParser()
    result = rp.parse_file("path/to/resume.pdf")
    print(json.dumps(result, indent=2))
"""

import json
import sys
from pathlib import Path
from typing import Dict

from extractors import extract_text
from segmenter import segment_resume
from contact_extractor import extract_contact_info
from entity_extractor import extract_entities
from skill_extractor import extract_skills, extract_skills_flat
from experience_parser import parse_experience_section, parse_education_section


class ResumeParser:
    """
    Core ATS resume parsing engine.

    Parses resume files (PDF, DOCX, TXT) into a standardized JSON
    structure containing contact info, summary, skills, experience,
    education, projects, certifications, and more.
    """

    def __init__(self, skills_db_path: str = None):
        """
        Initialize the ResumeParser.

        Args:
            skills_db_path: Optional path to the skills_db.json file.
                            Defaults to skills_db.json in the same directory.
        """
        if skills_db_path is None:
            self.skills_db_path = str(Path(__file__).parent / "skills_db.json")
        else:
            self.skills_db_path = skills_db_path

    def parse_file(self, file_path: str) -> Dict:
        """
        Parse a resume file and return a structured JSON-compatible dict.

        Pipeline:
            1. Extract raw text from the file (PDF/DOCX/TXT)
            2. Clean and normalize the text
            3. Segment into sections (experience, education, skills, etc.)
            4. Extract contact info (emails, phones, URLs)
            5. Extract named entities (name, orgs, degrees, universities)
            6. Extract skills against the knowledge base
            7. Parse experience and education into structured entries
            8. Assemble and return the final JSON object

        Args:
            file_path: Path to the resume file.

        Returns:
            Dictionary with the following structure:
            {
                "file": "resume.pdf",
                "candidate_name": "John Doe",
                "contact": { emails, phones, linkedin, github, websites },
                "summary": "...",
                "skills": { categorized skills },
                "skills_list": [ flat list of skills ],
                "experience": [ { company, title, dates, description }, ... ],
                "education": [ { institution, degree, dates, gpa, details }, ... ],
                "projects": "...",
                "certifications": "...",
                "awards": "...",
                "languages": "...",
                "interests": "...",
                "organizations_detected": [ ... ],
                "raw_sections": { raw section texts }
            }

        Raises:
            FileNotFoundError: If file_path does not exist.
            ValueError: If the file format is unsupported.
        """
        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        # ─── Step 1-2: Extract and clean text ───────────────────────
        cleaned_text = extract_text(file_path)

        if not cleaned_text.strip():
            return {
                "file": path.name,
                "error": "No text could be extracted from the file.",
                "candidate_name": None,
                "contact": {},
                "summary": None,
                "skills": {},
                "skills_list": [],
                "experience": [],
                "education": [],
            }

        # ─── Step 3: Segment into sections ──────────────────────────
        sections = segment_resume(cleaned_text)

        # ─── Step 4: Extract contact info ───────────────────────────
        # Use header + contact section if available, else full text
        contact_text = sections.get("header", "")
        if "contact" in sections:
            contact_text += "\n" + sections["contact"]
        # Also search the first portion of full text (contact info is at top)
        contact_text += "\n" + cleaned_text[:800]
        contact_info = extract_contact_info(contact_text)

        # ─── Step 5: Extract named entities ─────────────────────────
        entities = extract_entities(cleaned_text, sections)

        # ─── Step 6: Extract skills ─────────────────────────────────
        # Use skills section if available, otherwise search full text
        skills_text = sections.get("skills", cleaned_text)
        # Also check experience/projects for implicit skill mentions
        if "experience" in sections:
            skills_text += "\n" + sections["experience"]
        if "projects" in sections:
            skills_text += "\n" + sections["projects"]

        categorized_skills = extract_skills(skills_text, self.skills_db_path)
        flat_skills = extract_skills_flat(skills_text, self.skills_db_path)

        # ─── Step 7: Parse experience & education ───────────────────
        experience = []
        if "experience" in sections:
            experience = parse_experience_section(sections["experience"])

        education = []
        if "education" in sections:
            education = parse_education_section(sections["education"])

        # ─── Step 8: Assemble final output ──────────────────────────
        # Languages fallback
        languages = sections.get("languages", "")
        if not languages or len(str(languages)) < 3:
            # Fallback scan for common languages
            common_languages = [
                "English", "Spanish", "French", "German", "Chinese", "Mandarin",
                "Japanese", "Korean", "Hindi", "Arabic", "Portuguese", "Russian",
                "Italian", "Bengali", "Telugu", "Marathi", "Tamil", "Urdu",
                "Gujarati", "Kannada", "Malayalam", "Odia", "Punjabi"
            ]
            found_langs = []
            for lang in common_languages:
                if re.search(r'\b' + lang + r'\b', cleaned_text, re.I):
                    found_langs.append(lang)
            if found_langs:
                languages = ", ".join(found_langs)
        
        # Frameworks/Tools fallback (if not a separate section, check skills)
        frameworks = sections.get("frameworks", None)

        result = {
            "file": path.name,
            "candidate_name": entities.get("name"),
            "contact": contact_info,
            "summary": sections.get("summary", None),
            "skills": categorized_skills if categorized_skills else {},
            "skills_list": flat_skills if flat_skills else [],
            "experience": experience if experience else [],
            "education": education if education else [],
            "projects": sections.get("projects", None),
            "frameworks": frameworks,
            "certifications": sections.get("certifications", None),
            "awards": sections.get("awards", None),
            "languages": languages if languages else None,
            "interests": sections.get("interests", None),
            "organizations_detected": entities.get("organizations", []),
            "degrees_detected": entities.get("degrees", []),
            "universities_detected": entities.get("universities", []),
            "raw_sections": {
                k: v[:200] + "..." if len(v) > 200 else v
                for k, v in sections.items()
            },
        }

        return result


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    """Command-line interface: parse a resume file and print JSON output."""
    if len(sys.argv) < 2:
        print("Usage: python parser.py <resume_file_path>")
        print("Supported formats: .pdf, .docx, .txt")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"\n{'='*60}")
    print(f"  Resume Parser — Analyzing: {file_path}")
    print(f"{'='*60}\n")

    parser = ResumeParser()

    try:
        result = parser.parse_file(file_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
