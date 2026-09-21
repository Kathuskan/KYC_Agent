# Agent Akshaya
A local document upload, transcription, review, and JSON-export workspace.

## Current verification status
The upload controls, consent gating, API validation, and field parsing pass 10 tests. The real OCR integration test currently FAILS in the Codex execution environment: Apple Vision reports an image-processing failure (nilError / pixel-buffer creation error). Offline extraction is implemented but is not verified operational. No successful extraction should be inferred from the preset demo. Installing an alternative OCR package was blocked by a DNS timeout.

## Run (macOS)
Python 3.9+ and Apple command-line developer tools are required.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p native/cache
swiftc -module-cache-path native/cache native/ocr.swift -o native/akshaya-ocr
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```
Open http://127.0.0.1:8000. The web application uses local Apple Vision, never Gemini. No API key is needed for this mode. The original Gemini extraction script remains available separately through `python kyc_agent.py IMAGE` with GEMINI_API_KEY set; that CLI sends the image to Google.

## Test image
Click **Load sample image**, confirm permission, and click **Extract details** to run actual OCR. **Download sample** saves the same fictional image. Expected text: Alex Morgan; 1994-06-18; DEMO-000123. These are expected values, not a verified OCR result. **Try a sample result** is only a preset interface demonstration.

The parser recognizes English field labels: name/full name, DOB/date of birth, and ID/document/passport number. Dates must be YYYY-MM-DD. Unfamiliar or unlabeled layouts require manual review. All recognized text is available for inspection when OCR succeeds.

## Tests
```sh
python -m unittest discover -s tests -v
```
Tests include real OCR on the synthetic image. Personal images are never used for automated tests.

## Data and scope
No uploaded images or extracted details are stored on disk or in browser storage. JSON exports are saved by the browser. The sample is fictional. The application transcribes text; it does not verify identity, authenticity, fraud, or eligibility. This is a single-user localhost application. Public deployment requires authentication, HTTPS, rate limits, and a deliberate retention policy.
