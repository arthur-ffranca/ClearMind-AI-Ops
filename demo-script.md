# Five-Minute Interview Demo Script

## 1. Problem

Clinics often collect intake information across forms, messages, and task tools. The therapist may not see a clean clinical-operational picture before the first session, and administrators lack visibility into what needs review.

## 2. Product Thesis

ClearMind AI Ops turns intake into a therapist-reviewed operational workflow. AI drafts a structured summary, but the clinician remains responsible for review and approval.

## 3. Demo Walkthrough

1. Show the clinic dashboard and intake queue.
2. Sign in as admin and show all visible patients.
3. Select the new patient with high-attention signals.
4. Show consent and intake completeness.
5. Generate the structured intake summary.
6. Point out attention signals, suggested therapist questions, summary version, and quality checks.
7. Explain that the score evaluates the AI draft structure and safety boundary, not the patient.
8. Approve the summary as the therapist/admin reviewer.
9. Schedule monitoring cadence.
10. Submit a new intake from the patient portal panel.
11. Log in as therapist and patient to show scoped access.

## 4. Technical Framing

- React frontend for the clinical workspace.
- FastAPI backend for patient, intake, summary, review, monitoring, and audit endpoints.
- SQLite persistence through SQLAlchemy, with a path to PostgreSQL later.
- Role-based auth with signed demo tokens.
- Open-source AI path through Ollama, with deterministic fallback when local model is unavailable.
- Versioned AI summary drafts with quality gates before therapist approval.
- Future database layer can be PostgreSQL with row-level clinic tenancy.
- Future LLM layer should return structured JSON and require clinician review.

## 5. Closing Line

The goal is not to replace clinical judgment. The goal is to reduce operational friction, organize intake data, and help the clinic act faster with the therapist still in control.
