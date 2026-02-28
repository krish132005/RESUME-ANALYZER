# Automated Resume Analyzer for Job Portals

An intelligent ATS (Applicant Tracking System) core engine that parses resumes in PDF, DOCX, and TXT formats into standardized, structured JSON. Built with Python, spaCy NLP, and FastAPI.

---

## Features

- **Multi-format ingestion** — Reads PDF (via `pdfminer.six`), DOCX (via `python-docx`), and plain text files
- **Text cleaning pipeline** — Normalizes whitespace, strips non-ASCII noise, handles bullet characters
- **Section segmentation** — Identifies 13+ section types (Experience, Education, Skills, Projects, etc.) using keyword heuristics
- **Contact extraction** — Regex-based extraction of emails, phone numbers, LinkedIn, GitHub, and portfolio URLs
- **Named Entity Recognition** — spaCy NER for candidate names and organizations; regex for degree titles
- **Skill matching** — Matches against a 120+ skill knowledge base with variation handling (e.g., "React" ↔ "React.js")
- **Structured output** — Clean nested JSON with typed experience/education entries
- **REST API** — FastAPI wrapper with Swagger UI for file uploads
- **Batch parsing** — Upload and parse multiple resumes at once

---

## Project Structure

```
resume-builder/
├── parser.py               # Main ResumeParser class (entry point)
├── extractors.py           # PDF/DOCX/TXT text extraction + cleaning
├── segmenter.py            # Section segmentation engine
├── contact_extractor.py    # Email, phone, URL regex extraction
├── entity_extractor.py     # spaCy NER (names, orgs, degrees)
├── skill_extractor.py      # Skill matching against knowledge base
├── experience_parser.py    # Experience & education structured parsing
├── skills_db.json          # Skill ontology (120+ skills with variations)
├── app.py                  # FastAPI web API
├── requirements.txt        # Python dependencies
├── samples/                # Sample resumes for testing
│   ├── sample_resume_1.txt
│   └── sample_resume_2.txt
└── README.md               # This file
```

---

## Installation

### 1. Clone / Download the project

```bash
cd "resume builder"
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the spaCy English model

```bash
python -m spacy download en_core_web_sm
```

---

## Usage

### CLI (Command Line)

Parse a single resume and print JSON output:

```bash
python parser.py samples/sample_resume_1.txt
```

Example output (truncated):
```json
{
  "file": "sample_resume_1.txt",
  "candidate_name": "John Michael Anderson",
  "contact": {
    "emails": ["john.anderson@email.com"],
    "phones": ["+14155550198"],
    "linkedin": "https://linkedin.com/in/john-m-anderson",
    "github": "https://github.com/jmanderson",
    "websites": ["https://johnanderson.dev"]
  },
  "skills": {
    "Cloud": ["AWS", "Azure", "GCP"],
    "Programming": ["CSS", "Go", "HTML", "JavaScript", "Python", "SQL", "TypeScript"],
    "Framework": ["Angular", "Django", "Express.js", "FastAPI", "Flask", "Node.js", "React"]
  },
  "experience": [
    {
      "company": "Google LLC",
      "title": "Senior Software Engineer",
      "dates": {"start_date": "Jan 2021", "end_date": "Present"}
    }
  ]
}
```

### REST API

Start the FastAPI server:

```bash
uvicorn app:app --host 0.0.0.0 port 8000 --reload
```--

Then:
- **Swagger UI**: http://localhost:8000/docs
- **Upload endpoint**: `POST /parse` with a file attachment
- **Batch upload**: `POST /parse/batch` with multiple files
- **Health check**: `GET /health`

#### cURL example

```bash
curl -X POST http://localhost:8000/parse \
  -F "file=@samples/sample_resume_1.txt"
```

---

## Section Segmentation Logic

The segmenter identifies section headings using keyword heuristics:

| Canonical Section | Example Headings Detected |
|---|---|
| `experience` | EXPERIENCE, Work Experience, Professional Experience, Employment History |
| `education` | EDUCATION, Academic Background, Qualifications |
| `skills` | SKILLS, Technical Skills, Core Competencies, Technologies |
| `projects` | PROJECTS, Personal Projects, Key Projects |
| `summary` | SUMMARY, Objective, About Me, Professional Profile |
| `certifications` | CERTIFICATIONS, Certificates, Training |
| `awards` | AWARDS, Honors, Achievements |
| `languages` | LANGUAGES, Language Skills |
| `interests` | INTERESTS, Hobbies, Extracurricular Activities |
| `contact` | CONTACT, Contact Information, Personal Details |
| `publications` | PUBLICATIONS, Research, Papers |
| `volunteer` | VOLUNTEER, Volunteering, Community Service |
| `references` | REFERENCES |

Text appearing **before** the first detected heading is stored as `header` (usually contains the candidate's name and contact info).

---

## Architecture

```
Resume File (PDF/DOCX/TXT)
         │
         ▼
┌─────────────────┐
│   extractors.py │  ──► Raw text extraction + cleaning
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  segmenter.py   │  ──► Section segmentation (keyword heuristics)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│              Parallel Extraction            │
│  ┌──────────────────┐  ┌─────────────────┐  │
│  │contact_extractor │  │entity_extractor │  │
│  │  (regex)         │  │  (spaCy NER)    │  │
│  └──────────────────┘  └─────────────────┘  │
│  ┌──────────────────┐  ┌─────────────────┐  │
│  │skill_extractor   │  │experience_parser│  │
│  │  (knowledge-base)│  │  (heuristic)    │  │
│  └──────────────────┘  └─────────────────┘  │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
              Structured JSON Output
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `pdfminer.six` | 20231228 | PDF text extraction |
| `python-docx` | 1.1.0 | DOCX text extraction |
| `spacy` | 3.7.4 | Named Entity Recognition |
| `nltk` | 3.8.1 | NLP utilities |
| `pandas` | 2.2.0 | Data manipulation |
| `fastapi` | 0.109.2 | REST API framework |
| `uvicorn` | 0.27.1 | ASGI server |
| `python-multipart` | 0.0.9 | File upload support |

---

## Skill Knowledge Base

The `skills_db.json` file contains **120+ skills** organized across categories:

- **Programming**: Python, Java, C++, JavaScript, Go, Rust, SQL, etc.
- **Frameworks**: React, Angular, Django, Flask, Spring Boot, Node.js, etc.
- **Data/ML**: TensorFlow, PyTorch, Pandas, Scikit-learn, NLP, etc.
- **Databases**: PostgreSQL, MongoDB, Redis, Elasticsearch, etc.
- **Cloud**: AWS, Azure, GCP
- **DevOps**: Docker, Kubernetes, Jenkins, Terraform, CI/CD
- **Soft Skills**: Leadership, Communication, Problem Solving, etc.

Each skill entry includes a `canonical_name` and a list of `variations` to handle common aliases (e.g., "React.js" → "React", "ML" → "Machine Learning").

---

## License

This project is for educational and research purposes.
