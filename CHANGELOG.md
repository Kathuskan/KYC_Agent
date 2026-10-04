# Change history

## 2026-10-04 — Tesseract extraction and manual-review design

- Replaced Gemini extraction and Apple Vision runtime with local Tesseract, stdin/stdout processing, language availability checks and bounded OCR concurrency.
- Preserved image limits, local consent acknowledgement, conservative field parsing and review/export UI. Added a non-verification flag and conflicting-field handling.
- Added mandatory real OCR tests and Linux CI.
- Documented proposed ID/selfie applications, manual decisions, pending seller listings and private document protection for Shelv. These marketplace features are not implemented by this release.
