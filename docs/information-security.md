# ID and selfie information security plan

Updated 2026-10-04. Status: required design for future Shelv integration, not a claim of deployed protection. Owner: security/data-protection owner appointed by the startup. Applies to ID front/back, selfies, extracted text, identifying metadata, review records and backups.

## Purpose and boundaries

Use identity evidence only for seller application review, appeals and specifically justified fraud handling. Buying should not require these uploads. Do not use evidence for marketing, training AI, public profiles or unrelated analytics. A static selfie is evidence for a human comparison, not a liveness test. Do not create biometric templates in this phase.

AgentAkshaya currently processes images in memory locally, with no application-managed storage or outbound AI calls. It does not yet implement Shelv authentication, cloud storage, review access, durable consent/audit records or deletion jobs. Local exports persist, and OS swap, browser extensions, screen capture and crash dumps are outside the application's in-memory guarantee.

## Threats and mandatory controls

| Threat | Required control | Verification |
|---|---|---|
| Publicly accessible IDs | Separate private bucket, block public access, no public CDN delivery or ordinary book-image upload path | Anonymous object requests fail; storage policy audit |
| Cross-account access | Bind application/evidence to authenticated owner; reviewers receive a narrow explicit role | Owner A cannot read/change B's evidence, even with B's identifiers |
| Stolen reviewer account | MFA, short sessions, reauthentication for sensitive operations, least privilege, prompt access revocation | Test expired/revoked sessions and role changes |
| Leaked evidence URLs | Prefer authenticated proxy with no-store responses; if signed URLs are necessary, short expiry (target ≤60 seconds), no logs/analytics/referrers containing URL | Expired URLs fail; responses never cached publicly |
| Stolen backups or disks | TLS in transit; managed encryption at rest with KMS, separate key permissions, encrypted backups | Inspect settings; test restricted key access and restoration |
| Malicious uploads/OCR exploitation | Size/pixel/type limits, decode/re-encode, reject animated/multipage evidence, quarantine scanning, patched libraries | Invalid/polyglot/oversized images fail; original never reaches browser before validation |
| Worker compromise | Sandboxed non-root workers, read-only runtime, restricted temporary storage, resource limits and no unnecessary egress | Worker cannot list all evidence, reach external services or persist arbitrary data |
| Silent reviewer abuse | Append-only access/decision audit, reviewer cannot approve self, unusual-access alerts | Review access trail; attempted self-approval denied |
| PII in telemetry | Redact bodies, raw OCR, filenames, ID numbers, photos, signed URLs; disable session replay on evidence screens | Inspect error/analytics/log samples with synthetic markers |
| Indefinite retention | Purpose-specific deletion deadlines and deletion jobs including versions/replicas | End-to-end deletion drill including restored backups |
| Corrupted/stale decisions | Immutable evidence versions, integrity hashes, decision concurrency checks | Replacement evidence invalidates old in-flight approval |

All image re-encoding/metadata stripping for the future upload pipeline must preserve readable evidence and document any transformation. Do not advertise forensic authenticity checks after transformations. The current local extractor applies EXIF orientation and normalizes pixels, but is not a production quarantine service.

## Storage design

1. Server creates an opaque evidence identifier and scoped upload authorization for the authenticated application owner.
2. Upload lands in private quarantine with strict size limits and expires if abandoned. Do not accept arbitrary object keys from the client.
3. Validate actual bytes and document type; scan and normalize safely. Store accepted evidence encrypted in restricted storage. Keep rejected/quarantine objects short-lived.
4. Database stores opaque object references and minimal necessary fields, not public URLs or base64 image blobs on User records. Encrypt sensitive extracted fields with application/KMS-managed encryption where feasible; keys never reside in source control or beside ciphertext without independent access controls.
5. OCR worker gets access to the required ID object only. Selfies are never routed to OCR. Keep raw OCR restricted because it may contain more PII than requested fields.
6. Reviewer access passes authorization on every request and is audited. UI masks ID numbers outside the evidence review context. Browser download disabling is not a security boundary; authorized viewers can still photograph screens.

Recommended roles: applicant owns submission access; reviewer reads assigned evidence and decides; support sees status/reason categories without documents; worker reads scoped ID evidence and writes extraction; deletion worker removes expired evidence; infrastructure administrators use audited emergency access. Avoid granting all administrators routine evidence visibility.

## Retention proposal — must be approved before live collection

These are proposed operational defaults, not statutory retention periods:

- Unsubmitted/abandoned uploads: delete within 24 hours.
- Failed/rejected uploads in quarantine: delete within 24 hours.
- Pending complete applications: review promptly; close after 30 days of inactivity after notifying applicant, then apply closed-application retention.
- Approved/rejected/withdrawn application raw IDs, selfies and raw OCR: delete 30 days after closure, allowing a defined appeal window.
- Minimal decision metadata: while seller relationship exists plus a separately justified, bounded dispute period; choose the exact duration before launch. Do not retain full DOB/ID by default merely because decision metadata survives.
- Backups: target maximum 35-day rolling lifetime; record deletions in a tombstone ledger and reapply them before restored backups serve traffic. Delete object versions and replicas too. Do not promise immediate physical deletion from immutable backups.
- Documented, time-limited legal holds can suspend relevant deletions; require owner, scope, reason, expiry and periodic review.

Set actual values in configuration, record deletion deadlines, retry failures and alert on overdue deletion. Test lifecycle policies with storage versioning and backup retention. A database row deletion alone is insufficient.

## Notice, lawful processing and suppliers

Before live collection, appoint the responsible owner and confirm the applicable lawful basis, necessity/proportionality, current Sri Lankan PDPA commencement/obligations and any special rules for biometric processing or minors with qualified local advice. Consent text alone is not the entire legal basis. Explain purpose, mandatory/optional fields, reviewer access, storage location, processors, transfers, retention, appeal and access/correction/deletion request channels. Record notice version and acknowledgement time.

Complete a privacy impact assessment before launch. Review hosting contracts, processor obligations, sub-processors, international transfers, breach assistance and deletion guarantees. No Gemini/unpaid AI forwarding exists in this implementation; any future external processor requires a fresh documented review. If face matching is added later, revisit biometric legal requirements, explicit notice, evaluation and retention before deployment.

Official reference: https://www.dpa.gov.lk/ (PDPA 2022 and 2025 amendment; verify current operative requirements rather than relying on historical announcements).

## Incident response and operations

On suspected evidence exposure: contain access, revoke affected sessions/URLs/keys, preserve non-PII audit evidence, identify affected records and duration, notify the designated owner, assess required regulator/user notices under applicable law, and document remediation. Never attach raw IDs to ordinary support tickets or chat. Reassess access after staff departure and periodically; monitor bulk viewing/download patterns and repeated authorization failures.

Keep secrets in a managed secret store or restricted runtime configuration. Keep real IDs out of Git, tests, CI artifacts, screenshots and developer machines. Use fictional fixtures only. Scan staged files and repository history before publishing; if sensitive material was previously committed, deletion in a new commit is not sufficient—coordinate history cleanup and incident assessment separately.

## Release gate

No live ID collection until access-control tests, private storage policies, encryption/key ownership, reviewer MFA, audit coverage, deletion/restore drills, incident ownership, privacy notice, supplier assessment and legal review are documented. The local prototype must not be mistaken for this production system.
