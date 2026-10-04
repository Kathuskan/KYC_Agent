# Agent Akshaya — local Tesseract ID text extraction

Reads JPEG, PNG and WebP images locally using Tesseract. Returns raw text and conservative field suggestions for human review. No Gemini API, API key, face matching, liveness, document authentication or automatic seller approval. `identity_verified` is always `false`.

## Install and run

Python 3.10+ and Tesseract 5 are required.

macOS:
```sh
brew install tesseract tesseract-lang
```
Ubuntu/Debian:
```sh
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-sin tesseract-ocr-tam
```
Then:
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```
Open http://127.0.0.1:8000. Choose an image, confirm permission, extract, inspect recognized text, correct suggestions and optionally export JSON. **Load sample image** runs genuine OCR; **Try a sample result** is a clearly labeled preset, not an OCR test.

Default language is English. For multilingual text, set `OCR_LANGUAGES=eng+sin+tam` before starting the server or CLI. All selected language packs must be installed (`tesseract --list-langs`). OCR language coverage does not guarantee document accuracy. Field parsing currently recognizes English labels with Unicode values; Sinhala/Tamil-only labels and unfamiliar card layouts require manual transcription from raw text. No NIC or licence layout has been certified.

CLI:
```sh
python kyc_agent.py static/sample-document.png
OCR_LANGUAGES=eng+sin+tam python kyc_agent.py static/sample-document.png
```
CLI prints sensitive extracted text to stdout: do not redirect real IDs into shared logs.

## API contract (local prototype)

`GET /api/status` returns engine availability, configured and installed languages.

`POST /api/extract` accepts raw image bytes, an image Content-Type and `X-Consent: process-locally`. Response: nullable `name`, `dob`, `id_number`, boolean `readable`, `notes`, `raw_text`, `engine`, `languages`, and `identity_verified: false`. `readable` means all three labeled fields were extracted, not that their contents are correct. Ambiguous dates or conflicting field values become null. ISO YYYY-MM-DD is the only parsed date format.

Errors: 400 invalid image/consent; 413 over 10 MB; 415 unsupported Content-Type; 429 OCR already busy; 503 missing engine/languages; 502 OCR error/60-second timeout. One OCR process per application process. Image limit is 20 megapixels. EXIF orientation is applied; images are flattened onto white and converted to grayscale in memory. Tesseract receives PNG bytes through stdin and returns UTF-8 through stdout; there are no application-created temporary image files.

This localhost app has no user authentication or durable storage. The consent header is a UI acknowledgement, not authentication or a compliance record. Do not expose it publicly. Browser previews are held in memory; downloaded JSON persists on the user's device. OS swap/crash dumps remain an operating-system concern. No external AI requests are made.

## Verification and documentation

```sh
python -m unittest discover -s tests -v
```
Tests use only fictional images. Real Tesseract integration tests are mandatory and fail if the engine is missing. GitHub Actions installs Tesseract and runs the suite on Linux. Passing the sample proves wiring, not accuracy on genuine NICs/licences.

- [Shelv integration specification](docs/shelv-integration.md)
- [ID and selfie information security plan](docs/information-security.md)
- [Acceptance and rollout plan](docs/acceptance.md)
- [Change history](CHANGELOG.md)

These documents distinguish implemented extraction from proposed marketplace work. Every upgrade must update the API documentation, relevant integration/security sections, acceptance checks and change history in the same pull request.

### Current local validation (2026-10-04)

12 unit/API checks passed; the two mandatory real OCR checks failed because Tesseract could not be installed (download host DNS resolution failed). Python and JavaScript syntax checks passed. End-to-end extraction and Linux CI are not yet verified. This is an implementation awaiting engine installation and real OCR validation, not a verified production release.
