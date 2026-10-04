# Acceptance and rollout

Updated 2026-10-04. Automated extraction checks run with `python -m unittest discover -s tests -v`. Required real OCR tests cover fictional labeled document extraction and a blank image; unit/API tests cover malformed images, size/dimension limits, unavailable languages/engine, conflicting fields, busy responses, hidden error details and private file isolation. CI repeats real OCR on Ubuntu.

## Before claiming ID extraction quality

Use explicitly consented, securely handled evaluation examples across old/new Sri Lankan NIC and licence layouts, English/Sinhala/Tamil, glare, rotation, blur and low-end phones. Do not publish those examples. Measure exact character accuracy per ID number, field precision/recall, missed/ambiguous fields, language/layout failures, processing latency and reviewer correction effort. Define acceptance thresholds before evaluation. Synthetic sample success does not establish real-document accuracy. Preserve raw OCR for review only for the approved retention period. No authenticity or face-matching accuracy is claimed.

## Shelv feature acceptance (not implemented yet)

- Buyers can purchase without seller verification.
- Incomplete application cannot enable listing submission.
- Submitted applicants can save/edit private drafts and opt into publication on approval.
- Catalog, search, recommendations, direct URLs and checkout never expose/accept pending or restricted seller listings.
- Owner sees pending listings; unrelated users cannot access them, including through guessed IDs.
- Approval publishes only eligible opted-in listings; draft, invalid and archived listings remain private.
- Repeated approval/publish jobs are idempotent; two reviewers cannot overwrite each other's decisions.
- Replacement evidence invalidates decisions on earlier versions; OCR failures never approve.
- Restriction immediately prevents new sales despite stale sessions/caches; existing orders retain scoped fulfilment access.
- Reviewer can request resubmission/reject with reason and applicant can appeal.
- Self-review denied. Decision history records actor, evidence version and policy.
- Document deletion removes originals, derivatives, object versions and restores respect tombstones.

## Rollout

Start in staging with synthetic evidence and private storage. Complete the information-security release gate before a small consented pilot. Review all applications manually. Roll back ID intake independently of ordinary buying if security or review capacity fails; keep pending listings private. Record measured results and defects in release notes. Upgrade documents and tests in the same PR as behavior changes.

## Recorded local result — 2026-10-04

12 unit/API tests passed. Two real OCR tests failed with EngineUnavailable because package downloads could not resolve ghcr.io. No actual OCR accuracy result was obtained. Python/JavaScript syntax and diff whitespace checks passed. GitHub Actions cannot be confirmed until the branch is published and CI runs.
