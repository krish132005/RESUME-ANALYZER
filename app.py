"""
FastAPI Resume Parser API
==========================
A web API that accepts resume file uploads (PDF, DOCX, TXT)
and returns the parsed JSON response.

Run:
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload

Then visit http://localhost:8000/docs for the interactive Swagger UI.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from parser import ResumeParser

# ─── App Setup ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Resume Parser API",
    description=(
        "Automated Resume Analyzer for Job Portals. "
        "Upload a resume (PDF, DOCX, or TXT) and receive a structured "
        "JSON response with extracted candidate information."
    ),
    version="1.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the parser
resume_parser = ResumeParser()

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/", tags=["General"])
def serve_ui():
    """Serve the premium frontend UI."""
    return FileResponse("frontend/index.html")


@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "resume-parser"}


@app.post("/parse", tags=["Parser"])
async def parse_resume(file: UploadFile = File(...)) -> Dict:
    """
    Parse an uploaded resume file.

    Accepts PDF, DOCX, or TXT files and returns a structured JSON
    object with extracted candidate information including:
    - Contact details (email, phone, URLs)
    - Skills (categorized)
    - Work experience (structured entries)
    - Education (structured entries)
    - Projects, certifications, and more

    **Supported formats:** `.pdf`, `.docx`, `.txt`
    """
    # Validate file extension
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Unsupported file format: '{ext}'",
                "supported_formats": list(ALLOWED_EXTENSIONS),
            },
        )

    # Save uploaded file to a temporary location
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, filename)

    try:
        # Write the uploaded file to disk
        with open(tmp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Parse the resume
        result = resume_parser.parse_file(tmp_path)

        return JSONResponse(
            content=result,
            status_code=200,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to parse the resume",
                "message": str(e),
            },
        )
    finally:
        # Clean up temporary files
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.post("/parse/batch", tags=["Parser"])
async def parse_resumes_batch(
    files: list[UploadFile] = File(...),
) -> Dict:
    """
    Parse multiple resume files at once.

    Returns a list of parsed results, one per file. Any individual
    failures are included as error entries rather than failing the
    entire batch.
    """
    results = []

    for file in files:
        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            results.append({
                "file": filename,
                "error": f"Unsupported format: {ext}",
            })
            continue

        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, filename)

        try:
            with open(tmp_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            result = resume_parser.parse_file(tmp_path)
            results.append(result)

        except Exception as e:
            results.append({
                "file": filename,
                "error": str(e),
            })
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return JSONResponse(
        content={"total": len(results), "results": results},
        status_code=200,
    )


# Mount the frontend directory to serve CSS and JS
# NOTE: This must be mounted AFTER all other routes so it doesn't shadow them.
app.mount("/", StaticFiles(directory="frontend"), name="frontend")


# ─── Run directly ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
