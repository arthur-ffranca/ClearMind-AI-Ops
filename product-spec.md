# Product Spec

## Core User Roles

- Clinic admin: manages queue, therapists, and operational metrics.
- Therapist: reviews summaries, edits notes, and owns follow-up plans.
- Patient: submits intake and scheduled check-ins.

## Demo Access Model

- Admin sees all seeded patients and can create intake, generate summary, approve, and schedule monitoring.
- Therapist sees only patients assigned to their full name.
- Patient sees only the linked patient record and cannot run clinical operations.
- Tokens are signed for the pilot and stored in browser local storage.

## MVP Objects

- Clinic
- User
- Patient
- Intake
- AI summary draft
- AI summary version
- Therapist review
- Monitoring plan
- Audit event

## MVP States

- Draft intake
- New intake
- Needs review
- Reviewed
- Ready for care plan
- In monitoring
- Escalated for clinical review

## API Surface

- `GET /patients`
- `GET /patients/{id}`
- `GET /ai/status`
- `GET /auth/demo-users`
- `POST /auth/login`
- `GET /auth/me`
- `POST /intakes`
- `POST /patients/{id}/ai-summary`
- `POST /patients/{id}/review`
- `POST /patients/{id}/follow-up`
- `GET /audit`
- `POST /dev/reset`

## Guardrails

- AI outputs are drafts.
- Clinical actions require admin or therapist roles.
- Patient role is read-only in the current workspace.
- Consent is required before AI summarization.
- Incomplete intakes cannot be summarized.
- Monitoring cannot start before therapist review.
- Audit logs record sensitive workflow actions.
- Demo data can be reset without deleting source files.
- AI summary drafts are versioned before review.
- Summary quality checks flag missing structure, weak safety language, or diagnostic wording.

## AI Provider Strategy

- Default provider: deterministic structured summarizer.
- Optional provider: Ollama local open-source model.
- Supported configuration:
  - `CLEARMIND_AI_PROVIDER=ollama`
  - `OLLAMA_BASE_URL=http://127.0.0.1:11434`
  - `OLLAMA_MODEL=llama3.1:8b`
- If the model is unavailable or returns invalid JSON, the API falls back to the structured summarizer.
- Summary metadata includes provider and model so reviewers can see how the draft was produced.

## Summary Quality Evaluation

Each generated summary version stores:

- Draft version and review status.
- Provider and model metadata.
- Quality score.
- Completeness checks for required fields, attention signals, suggested questions, and operational recommendation.
- Safety checks that the output stays a draft and avoids diagnostic claims.
- Reviewer metadata after approval or revision request.

## Later Expansion

- Real patient portal
- Prompt/version comparison and evaluator history
- Check-in trends over time
- Risk signal dashboard reviewed by clinicians
- Integration bridge for existing operational tools
