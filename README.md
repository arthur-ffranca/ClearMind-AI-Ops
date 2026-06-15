# ClearMind AI Ops Pilot

ClearMind AI Ops is a SaaS pilot for mental health clinics. It focuses on intake operations, AI-assisted summarization, therapist review, monitoring cadence, persistence, and auditability.

This is intentionally positioned as a clinical-operations product, not an AI therapist or diagnostic tool.

Current pilot version: `v0.4`.

## What the Pilot Shows

- Clinic dashboard with fictitious patients
- Intake queue with consent and completeness states
- AI-assisted structured intake summary
- Therapist approval before care-facing use
- Follow-up scheduling after review
- Audit trail for sensitive workflow actions
- Persistent FastAPI backend with SQLite and SQLAlchemy
- Patient intake submission flow
- Role-based demo login for admin, therapist, and patient
- Optional open-source AI adapter through Ollama
- Versioned AI summary drafts with quality checks

## Product Positioning

ClearMind helps a clinic move from scattered intake data to a therapist-reviewed workflow:

1. Patient submits intake.
2. System checks consent and completeness.
3. AI drafts a structured summary.
4. System evaluates the draft against safety and completeness checks.
5. Therapist edits or approves the summary.
6. Clinic activates monitoring cadence.
7. Actions are recorded in an audit trail.

## Quick Start

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

If that port is already in use, Vite will print the next available URL, such as `http://localhost:5174`.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs`.

The backend creates `clearmind.db` automatically and seeds three fictitious patients on first run.

### Optional Open Source AI

By default, summaries use a deterministic structured adapter. To use a local open-source model through Ollama:

```bash
ollama pull llama3.1:8b
set CLEARMIND_AI_PROVIDER=ollama
set OLLAMA_MODEL=llama3.1:8b
uvicorn main:app --reload --port 8000
```

Alternative local models that fit the pilot well: `mistral:7b`, `llama3.1:8b`, or `qwen2.5:7b`.

If Ollama is unavailable or returns invalid JSON, ClearMind falls back to the structured summarizer and marks the summary provider as `structured-fallback`.

### Demo Accounts

All demo accounts use password `clearmind123`.

| Role | Email | Scope |
|------|-------|-------|
| Admin | `admin@clearmind.local` | All patients, intake creation, review, monitoring |
| Therapist | `ana@clearmind.local` | Assigned patients only |
| Patient | `lucas.patient@clearmind.local` | Own record only, read-only |

## Demo Flow

1. Open the dashboard.
2. Select Mariana Costa in the intake queue.
3. Click `Generate` to create the AI-assisted summary.
4. Point out the summary version, quality score, and guardrail checks.
5. Add a therapist note and click `Approve`.
6. Click `Schedule` to activate monitoring.
7. Create a new patient intake from the patient portal panel.
8. Log out and sign in as therapist or patient to show scoped access.
9. Refresh the queue or restart the backend to show persistence.

## Why This Is Different From MindCareAI

MindCareAI is a strong multimodal wellness-assessment reference. ClearMind adapts the idea to a clinic product:

- It prioritizes therapist workflow over self-service counselling.
- It uses AI as an assistant, not as the decision-maker.
- It focuses on operational status, review, monitoring, and auditability.
- It can later add voice, mood, and check-in signals after the core workflow is credible.

## Suggested Roadmap

### Phase 1: Interview Pilot

- Static demo data
- Intake summary mock
- Review and monitoring actions
- Swagger API outline

### Phase 2: Clinical Intake MVP

- Persistent database
- Role-based auth
- Patient intake portal
- AI summarization boundary
- Therapist editable notes
- Monitoring schedule

Current status: the pilot now includes role-based auth, persistence, intake portal, therapist review, monitoring schedule, audit workflow, optional open-source AI adapter, versioned AI summary drafts, and summary quality checks.

### Phase 3: Clinic Product

- Multi-clinic tenancy
- Secure messaging/check-ins
- Reporting and capacity metrics
- Integration bridge for existing tools
- Compliance workflows and retention policies
