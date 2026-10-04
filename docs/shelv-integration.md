# Shelv integration specification

Status: proposed; AgentAkshaya extraction is implemented, Shelv changes below are not. Updated 2026-10-04. Owner: marketplace engineering. Security companion: [information-security.md](information-security.md).

## Product decision

Buying requires no seller ID check. To sell, an authenticated user submits their legal name, necessary contact details, ID images (front/back according to the document type) and a selfie, with a clear processing notice. Existing verified email is retained; phone verification is a separate planned feature, not something the current application provides. Decide and document seller age eligibility before collecting DOB; collect only what is necessary.

The agent reads ID images only. It does not process the selfie for identity matching, determine authenticity or approve the applicant. An authorized reviewer compares applicant-provided details, extracted text, original ID images and selfie. User-facing status must describe manual review accurately. A static selfie can be stolen, edited or replayed; this flow does not establish liveness. Suspected impersonation needs escalation or resubmission, not an AI confidence score.

After a complete application is submitted, applicants may create and edit listings with pending permission. Listings remain private until seller approval. An applicant may still buy while pending, rejected or restricted.

## States and visibility

Maintain independent application, seller and listing records.

Application: `draft → submitted → processing → pending_review → approved | needs_resubmission | rejected`. OCR failures move to manual review or resubmission with a reason; they never approve or label someone fraudulent. Changed evidence after submission produces a new immutable application version, invalidating any outstanding review of the old version.

Seller: `none | pending | approved | rejected | restricted`. Submitted applicants become pending. Only reviewers can approve/reject/restrict. Rejected applicants may retain private drafts and resubmit; they cannot publish. Restriction hides all listings immediately and blocks new sales while preserving existing order fulfilment access.

Listing: `draft | pending_verification | published | archived`. An applicant must explicitly choose “Publish when approved”; incomplete drafts are never published by approval. On approval, a worker validates each opted-in listing's required fields, price, stock and moderation requirements, then publishes eligible listings. Invalid listings stay private with an actionable message. Repeated approval/jobs must not publish archived listings or duplicate side effects.

Public visibility requires both `listing.status == published` and the current seller being approved, plus all existing marketplace rules. Enforce this in server-side catalog queries, direct detail endpoints, search, recommendations, related listings, feeds, sitemaps and checkout. Never rely on client filters or stale JWT role claims. A hidden direct URL returns a non-disclosing 404 to outsiders. Owners and authorized reviewers use distinct private endpoints. No public stock reservation or order can be created for a pending seller. Publishing and restriction races must fail closed; recheck current seller eligibility when accepting orders using the existing transaction strategy. Invalidate caches/search indexes on approval/restriction; restrict uploads and image delivery for private listings too where those assets reveal private content.

## Data model proposal

`SellerApplication`: userId, version, status, submittedDetails, documentType, country, evidence object references, original extraction results per ID side, corrected review fields separately, extraction engine/language/version, extraction status, reason codes, timestamps, notice/consent version, reviewerId, review decision and evidence deletion deadline. Do not put ID details in the ordinary User profile response.

`Evidence`: opaque object key, applicationId/version, ownerId, type (ID front/back/selfie), detected MIME, byte length, checksum for integrity, upload/scan state and deletion deadline. Never use NIC numbers or names in filenames. IDs and selfies are restricted data.

`ReviewDecision`: applicationId/version, actor, outcome, reason, policy version and timestamp. Write decision/status changes and audit record atomically. Reviewers cannot approve themselves. Use optimistic concurrency so two reviewers or a replacement upload cannot silently overwrite a decision.

Keep the original OCR text distinct from the applicant's statements and reviewer corrections. Never treat browser-exported JSON or `identity_verified` as authoritative approval evidence. Optional duplicate-ID checking needs normalization and keyed HMAC, not plain hashes of enumerable NICs; it requires a documented purpose, restricted access and human review of matches.

## Service integration

React → authenticated Express upload/session endpoint → private quarantine storage → validated evidence → job queue → private Python Tesseract worker → restricted extraction record → review queue → explicit reviewer decision.

Refactor the local Python extraction function into an internal worker; do not expose today's unauthenticated localhost API to the internet. Authenticate service calls, bind each job to the exact application and evidence version, use timeouts/bounded retries/idempotency, and authenticate any callback. Prefer workers reading only specifically authorized object keys. Ignore user-selected URLs and file paths to avoid arbitrary file/network reads. Never send the selfie to OCR.

Suggested application routes: POST /api/seller-applications; POST /:id/evidence-upload; POST /:id/submit; GET /:id/status; POST /api/admin/seller-applications/:id/decision. Exact route names are proposals. Every route enforces ownership or reviewer authorization and explicit allowed transitions. No client-set approval fields.

## Current Shelv touchpoints

- client/src/core/Account.jsx: replace email-only application form with evidence submission/status screens.
- client/src/core/Marketplace.jsx: allow pending sellers a private listing workspace and add reviewer evidence UI.
- server/models/user.js: separate seller state from a restricted application/evidence model.
- server/app.js: current approval checks email and pending/restricted state; require a current eligible reviewed application and audited decision.
- server/services/orders.js and all listing access paths: enforce fresh seller eligibility and listing visibility.
- Existing role middleware: permit narrowly scoped private drafting for pending applicants, without granting approved-seller publication rights.

Do not implement these changes as a broad role bypass. Keep buyer, applicant, approved seller and reviewer capabilities distinct.

## Reviewer experience

Show the submitted identity details, both ID sides, selfie and extracted text side-by-side using temporary authorized delivery. Review legibility, consistency, document completeness and visible portrait similarity; record a reasoned decision. Unfamiliar document versions, transliteration differences, unclear portraits or suspected tampering go to a trained senior reviewer/resubmission. Provide an appeal route. No “100% genuine” labels and no public exposure of ID or selfie.

## Documentation maintenance

Each upgrade updates this specification, security controls, acceptance tests and CHANGELOG.md in the same change. Mark a proposed feature implemented only after tests and rollout evidence exist. Record schema/policy versions so old decisions remain explainable. This is a maintenance requirement, not an unattended background updater.
