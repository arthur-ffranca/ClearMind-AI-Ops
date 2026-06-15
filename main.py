from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from typing import Literal
from urllib import error, request
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine, func
from sqlalchemy.orm import Session, declarative_base, sessionmaker


DATABASE_URL = "sqlite:///./clearmind.db"
AUTH_SECRET = os.getenv("CLEARMIND_AUTH_SECRET", "clearmind-demo-secret-change-before-production")
TOKEN_TTL_SECONDS = 60 * 60 * 8
AI_PROVIDER = os.getenv("CLEARMIND_AI_PROVIDER", "structured").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


app = FastAPI(
    title="ClearMind AI Ops Pilot API",
    description="Persistent clinical-operations API for therapist-reviewed intake workflows.",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PatientRecord(Base):
    __tablename__ = "patients"

    id = Column(String(40), primary_key=True)
    name = Column(String(120), nullable=False)
    age = Column(Integer, nullable=False)
    pronouns = Column(String(40), nullable=False, default="not captured")
    therapist = Column(String(120), nullable=False, default="Unassigned")
    status = Column(String(60), nullable=False, default="New intake")
    queue = Column(String(60), nullable=False, default="Needs review")
    priority = Column(String(60), nullable=False, default="Routine")
    next_step = Column(String(120), nullable=False, default="Therapist review")
    last_check_in = Column(String(80), nullable=False, default="No check-in yet")
    intake_complete = Column(Integer, nullable=False, default=100)
    consent = Column(Boolean, nullable=False, default=False)
    reviewed = Column(Boolean, nullable=False, default=False)
    follow_up_active = Column(Boolean, nullable=False, default=False)
    review_note = Column(Text, nullable=False, default="")
    follow_up_cadence = Column(String(40), nullable=False, default="")
    follow_up_owner = Column(String(120), nullable=False, default="")
    next_check_in = Column(String(40), nullable=False, default="")

    chief_concern = Column(Text, nullable=False)
    duration = Column(String(120), nullable=False)
    functional_impact = Column(Text, nullable=False)
    reported_symptoms_json = Column(Text, nullable=False, default="[]")
    support = Column(Text, nullable=False)
    free_text = Column(Text, nullable=False)
    ai_summary_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UserRecord(Base):
    __tablename__ = "users"

    id = Column(String(40), primary_key=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, index=True, nullable=False)
    role = Column(String(40), nullable=False)
    password_salt = Column(String(120), nullable=False)
    password_hash = Column(String(160), nullable=False)
    linked_patient_id = Column(String(40), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(40), nullable=False, index=True)
    patient_name = Column(String(120), nullable=False)
    event = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SummaryVersion(Base):
    __tablename__ = "summary_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(40), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    status = Column(String(40), nullable=False, default="draft")
    provider = Column(String(80), nullable=False)
    model = Column(String(120), nullable=False)
    summary_json = Column(Text, nullable=False)
    quality_json = Column(Text, nullable=False)
    created_by = Column(String(120), nullable=False)
    reviewed_by = Column(String(120), nullable=True)
    review_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)


class ReviewRequest(BaseModel):
    reviewer: str = Field(min_length=2)
    decision: Literal["approved", "needs_changes"]
    note: str = Field(min_length=2)


class FollowUpRequest(BaseModel):
    cadence: Literal["weekly", "twice_weekly", "monthly"]
    owner: str = Field(min_length=2)
    nextCheckIn: str = Field(min_length=4)


class IntakeCreate(BaseModel):
    name: str = Field(min_length=2)
    age: int = Field(ge=1, le=120)
    pronouns: str = "not captured"
    therapist: str = "Unassigned"
    chiefConcern: str = Field(min_length=4)
    duration: str = Field(min_length=2)
    functionalImpact: str = Field(min_length=4)
    reportedSymptoms: list[str] = Field(default_factory=list)
    support: str = Field(min_length=2)
    freeText: str = Field(min_length=12)
    consent: bool


class LoginRequest(BaseModel):
    email: str
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def dated_event(label: str) -> str:
    return f"{utc_stamp()} - {label}"


def json_loads(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def json_dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True)


def b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 180_000)
    return b64encode(salt), b64encode(digest)


def verify_password(password: str, salt_value: str, expected_hash: str) -> bool:
    salt = b64decode(salt_value)
    _, computed_hash = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, expected_hash)


def public_user(user: UserRecord) -> dict:
    return {
        "id": user.id,
        "fullName": user.full_name,
        "email": user.email,
        "role": user.role,
        "linkedPatientId": user.linked_patient_id,
    }


def create_token(user: UserRecord) -> str:
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.full_name,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    encoded_payload = b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(AUTH_SECRET.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded_payload}.{b64encode(signature)}"


def decode_token(token: str) -> dict:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    expected_signature = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(b64encode(expected_signature), encoded_signature):
        raise HTTPException(status_code=401, detail="Invalid token")

    payload = json.loads(b64decode(encoded_payload).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Session expired")
    return payload


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> UserRecord:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_token(authorization.removeprefix("Bearer ").strip())
    user = db.get(UserRecord, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_roles(*roles: str):
    def dependency(user: UserRecord = Depends(get_current_user)) -> UserRecord:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return dependency


def can_access_patient(user: UserRecord, patient: PatientRecord) -> bool:
    if user.role == "admin":
        return True
    if user.role == "therapist":
        return patient.therapist == user.full_name
    if user.role == "patient":
        return user.linked_patient_id == patient.id
    return False


def assert_patient_access(user: UserRecord, patient: PatientRecord) -> None:
    if not can_access_patient(user, patient):
        raise HTTPException(status_code=403, detail="Patient is outside this user's scope")


def infer_priority(patient: PatientRecord) -> str:
    text = " ".join(
        [
            patient.chief_concern,
            patient.functional_impact,
            patient.free_text,
            " ".join(json_loads(patient.reported_symptoms_json, [])),
        ]
    ).lower()
    high_markers = ["self-harm", "burnout", "panic", "chest tightness", "hopeless", "unsafe"]
    if any(marker in text for marker in high_markers):
        return "High attention"
    if patient.intake_complete < 80 or not patient.consent:
        return "Missing data"
    return "Routine"


def audit(db: Session, patient: PatientRecord, event: str) -> None:
    db.add(AuditEvent(patient_id=patient.id, patient_name=patient.name, event=dated_event(event)))


def build_structured_summary(patient: PatientRecord) -> dict:
    symptoms = json_loads(patient.reported_symptoms_json, [])
    priority_signal = (
        "therapist review recommended"
        if patient.priority == "High attention"
        else "routine therapist review"
    )
    return {
        "chiefConcern": patient.chief_concern,
        "timeline": patient.duration,
        "functionalImpact": patient.functional_impact,
        "attentionSignals": [*symptoms[:3], priority_signal],
        "suggestedQuestions": [
            "What would make the next session feel most useful?",
            "Which symptoms are creating the biggest day-to-day burden?",
            "What support can be safely included in the care plan?",
        ],
        "recommendedOps": (
            "Prioritize therapist review before assigning routine monitoring."
            if patient.priority == "High attention"
            else "Proceed with standard therapist review and check-in cadence."
        ),
        "safetyBoundary": "AI output is a draft and is not a diagnosis.",
        "provider": "structured",
        "model": "deterministic-summary-v1",
    }


def ollama_prompt(patient: PatientRecord) -> str:
    symptoms = json_loads(patient.reported_symptoms_json, [])
    return f"""
You are a clinical operations assistant for a mental health clinic.
You do not diagnose. You only organize intake information for therapist review.

Return strict JSON with exactly these keys:
chiefConcern, timeline, functionalImpact, attentionSignals, suggestedQuestions, recommendedOps, safetyBoundary.

Rules:
- Do not mention diagnoses.
- Use neutral operational language.
- attentionSignals must be an array of short strings.
- suggestedQuestions must be an array of therapist-facing questions.
- safetyBoundary must say the output is a draft and not a diagnosis.

Patient intake:
Name: {patient.name}
Therapist: {patient.therapist}
Priority: {patient.priority}
Chief concern: {patient.chief_concern}
Duration: {patient.duration}
Functional impact: {patient.functional_impact}
Reported symptoms: {", ".join(symptoms)}
Support: {patient.support}
Free text: {patient.free_text}
""".strip()


def parse_json_object(raw_text: str) -> dict | None:
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(raw_text[start : end + 1])
    except json.JSONDecodeError:
        return None


def normalize_summary(candidate: dict, fallback: dict, provider: str, model: str) -> dict:
    def string_value(key: str) -> str:
        value = candidate.get(key)
        return value.strip() if isinstance(value, str) and value.strip() else fallback[key]

    def list_value(key: str) -> list[str]:
        value = candidate.get(key)
        if not isinstance(value, list):
            return fallback[key]
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return cleaned[:6] or fallback[key]

    return {
        "chiefConcern": string_value("chiefConcern"),
        "timeline": string_value("timeline"),
        "functionalImpact": string_value("functionalImpact"),
        "attentionSignals": list_value("attentionSignals"),
        "suggestedQuestions": list_value("suggestedQuestions"),
        "recommendedOps": string_value("recommendedOps"),
        "safetyBoundary": string_value("safetyBoundary"),
        "provider": provider,
        "model": model,
    }


def build_ollama_summary(patient: PatientRecord, fallback: dict) -> dict:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": ollama_prompt(patient),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
    candidate = parse_json_object(data.get("response", ""))
    if not candidate:
        raise ValueError("Ollama response did not contain valid JSON")
    return normalize_summary(candidate, fallback, provider="ollama", model=OLLAMA_MODEL)


def build_summary(patient: PatientRecord) -> dict:
    fallback = build_structured_summary(patient)
    if AI_PROVIDER != "ollama":
        return fallback

    try:
        return build_ollama_summary(patient, fallback)
    except (OSError, TimeoutError, ValueError, error.URLError, json.JSONDecodeError):
        fallback["provider"] = "structured-fallback"
        fallback["model"] = f"fallback-after-{OLLAMA_MODEL}"
        return fallback


def summary_to_text(summary: dict) -> str:
    parts: list[str] = []
    for value in summary.values():
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
    return " ".join(parts).lower()


def evaluate_summary(summary: dict) -> dict:
    required_fields = [
        "chiefConcern",
        "timeline",
        "functionalImpact",
        "attentionSignals",
        "suggestedQuestions",
        "recommendedOps",
        "safetyBoundary",
    ]
    text = summary_to_text(summary)
    diagnostic_text = summary_to_text(
        {key: value for key, value in summary.items() if key != "safetyBoundary"}
    )
    diagnostic_phrases = [
        "diagnosed with",
        "final diagnosis",
        "primary diagnosis",
        "confirmed diagnosis",
        "meets criteria for",
        "suffers from",
        "has major depressive disorder",
        "has bipolar disorder",
        "has generalized anxiety disorder",
        "patient has depression",
        "patient has anxiety disorder",
        "the patient is depressed",
        "is clinically",
    ]

    checks = [
        {
            "id": "required_fields",
            "label": "Required fields present",
            "passed": all(summary.get(field) for field in required_fields),
            "detail": "Summary includes the expected structured fields.",
        },
        {
            "id": "attention_signals",
            "label": "Attention signals included",
            "passed": isinstance(summary.get("attentionSignals"), list) and len(summary.get("attentionSignals", [])) >= 1,
            "detail": "At least one attention signal is available for therapist review.",
        },
        {
            "id": "suggested_questions",
            "label": "Therapist questions included",
            "passed": isinstance(summary.get("suggestedQuestions"), list) and len(summary.get("suggestedQuestions", [])) >= 2,
            "detail": "The draft suggests follow-up questions instead of clinical conclusions.",
        },
        {
            "id": "operational_recommendation",
            "label": "Operational recommendation present",
            "passed": bool(str(summary.get("recommendedOps", "")).strip()),
            "detail": "The output gives an operational next step.",
        },
        {
            "id": "safety_boundary",
            "label": "Safety boundary present",
            "passed": "draft" in str(summary.get("safetyBoundary", "")).lower()
            and "diagnos" in str(summary.get("safetyBoundary", "")).lower(),
            "detail": "The output states it is a draft and not a diagnosis.",
        },
        {
            "id": "no_diagnostic_language",
            "label": "No diagnostic language",
            "passed": not any(phrase in diagnostic_text for phrase in diagnostic_phrases),
            "detail": "The draft avoids diagnostic or deterministic clinical claims.",
        },
    ]
    passed_count = sum(1 for check in checks if check["passed"])
    score = round((passed_count / len(checks)) * 100)
    hard_failures = {
        check["id"]
        for check in checks
        if not check["passed"] and check["id"] in {"safety_boundary", "no_diagnostic_language"}
    }
    return {
        "score": score,
        "status": "pass" if score >= 80 and not hard_failures else "needs_review",
        "checks": checks,
        "evaluatedAt": utc_stamp(),
    }


def create_summary_version(db: Session, patient: PatientRecord, summary: dict, user: UserRecord) -> dict:
    last_version = (
        db.query(SummaryVersion)
        .filter(SummaryVersion.patient_id == patient.id)
        .order_by(SummaryVersion.version.desc())
        .first()
    )
    next_version = (last_version.version if last_version else 0) + 1
    quality = evaluate_summary(summary)
    enriched_summary = {
        **summary,
        "version": next_version,
        "status": "draft",
        "quality": quality,
    }
    db.add(
        SummaryVersion(
            patient_id=patient.id,
            version=next_version,
            status="draft",
            provider=str(summary.get("provider", "structured")),
            model=str(summary.get("model", "unknown")),
            summary_json=json_dumps(enriched_summary),
            quality_json=json_dumps(quality),
            created_by=user.full_name,
        )
    )
    return enriched_summary


def latest_summary_version(db: Session, patient_id: str) -> SummaryVersion | None:
    return (
        db.query(SummaryVersion)
        .filter(SummaryVersion.patient_id == patient_id)
        .order_by(SummaryVersion.version.desc())
        .first()
    )


def serialize_summary_version(version: SummaryVersion) -> dict:
    return {
        "id": version.id,
        "version": version.version,
        "status": version.status,
        "provider": version.provider,
        "model": version.model,
        "quality": json_loads(version.quality_json, {}),
        "createdBy": version.created_by,
        "reviewedBy": version.reviewed_by,
        "reviewNote": version.review_note,
        "createdAt": version.created_at.isoformat() if version.created_at else None,
        "reviewedAt": version.reviewed_at.isoformat() if version.reviewed_at else None,
    }


def get_summary_versions(db: Session, patient_id: str) -> list[SummaryVersion]:
    return (
        db.query(SummaryVersion)
        .filter(SummaryVersion.patient_id == patient_id)
        .order_by(SummaryVersion.version.desc())
        .limit(5)
        .all()
    )


def serialize_patient(
    patient: PatientRecord,
    audit_events: list[AuditEvent] | None = None,
    summary_versions: list[SummaryVersion] | None = None,
) -> dict:
    summary = json_loads(patient.ai_summary_json, None)
    events = audit_events or []
    versions = summary_versions or []
    return {
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "pronouns": patient.pronouns,
        "therapist": patient.therapist,
        "status": patient.status,
        "queue": patient.queue,
        "priority": patient.priority,
        "nextStep": patient.next_step,
        "lastCheckIn": patient.last_check_in,
        "intakeComplete": patient.intake_complete,
        "consent": patient.consent,
        "summaryGenerated": summary is not None,
        "reviewed": patient.reviewed,
        "followUpActive": patient.follow_up_active,
        "reviewNote": patient.review_note,
        "followUp": {
            "cadence": patient.follow_up_cadence,
            "owner": patient.follow_up_owner,
            "nextCheckIn": patient.next_check_in,
        },
        "intake": {
            "chiefConcern": patient.chief_concern,
            "duration": patient.duration,
            "functionalImpact": patient.functional_impact,
            "reportedSymptoms": json_loads(patient.reported_symptoms_json, []),
            "support": patient.support,
            "freeText": patient.free_text,
        },
        "aiSummary": summary,
        "summaryVersions": [serialize_summary_version(version) for version in versions],
        "audit": [event.event for event in events],
    }


def get_patient_or_404(db: Session, patient_id: str) -> PatientRecord:
    patient = db.get(PatientRecord, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def get_patient_audit(db: Session, patient_id: str) -> list[AuditEvent]:
    return (
        db.query(AuditEvent)
        .filter(AuditEvent.patient_id == patient_id)
        .order_by(AuditEvent.id.desc())
        .limit(12)
        .all()
    )


def create_patient_from_intake(payload: IntakeCreate) -> PatientRecord:
    completeness = 100 if payload.consent else 72
    patient = PatientRecord(
        id=f"pt-{uuid4().hex[:8]}",
        name=payload.name,
        age=payload.age,
        pronouns=payload.pronouns,
        therapist=payload.therapist,
        status="New intake" if payload.consent else "Draft intake",
        queue="Needs review" if payload.consent else "Incomplete",
        priority="Routine",
        next_step="Therapist review" if payload.consent else "Capture consent",
        last_check_in="No check-in yet",
        intake_complete=completeness,
        consent=payload.consent,
        chief_concern=payload.chiefConcern,
        duration=payload.duration,
        functional_impact=payload.functionalImpact,
        reported_symptoms_json=json_dumps(payload.reportedSymptoms),
        support=payload.support,
        free_text=payload.freeText,
    )
    patient.priority = infer_priority(patient)
    return patient


def seed_data(db: Session) -> None:
    if db.query(PatientRecord).count() > 0:
        return

    seed_payloads = [
        IntakeCreate(
            name="Mariana Costa",
            age=32,
            pronouns="she/her",
            therapist="Dr. Ana Ribeiro",
            chiefConcern="Persistent anxiety around work performance and sleep disruption.",
            duration="About six weeks",
            functionalImpact="Sleep reduced to 4-5 hours. Avoiding meetings and delaying decisions.",
            reportedSymptoms=["racing thoughts", "chest tightness", "fatigue", "difficulty concentrating"],
            support="Partner is aware and supportive. Has not contacted clinician before this intake.",
            freeText=(
                "Patient reports escalating work-related anxiety, poor sleep, and reduced concentration. "
                "Denies immediate intent to self-harm but says she feels close to burnout."
            ),
            consent=True,
        ),
        IntakeCreate(
            name="Lucas Ferreira",
            age=24,
            pronouns="he/him",
            therapist="Dr. Miguel Alves",
            chiefConcern="Low mood after academic stress and social withdrawal.",
            duration="Three months",
            functionalImpact="Missing classes twice a week and avoiding friends.",
            reportedSymptoms=["low motivation", "sleep changes", "isolation"],
            support="Close friend and sister available.",
            freeText=(
                "Patient wants support building routine and managing academic pressure. "
                "No acute safety statement reported in the intake."
            ),
            consent=True,
        ),
        IntakeCreate(
            name="Renato Lima",
            age=41,
            pronouns="he/him",
            therapist="Unassigned",
            chiefConcern="Relationship stress and irritability.",
            duration="Not captured",
            functionalImpact="Partial response only.",
            reportedSymptoms=["irritability"],
            support="Not captured",
            freeText="Draft intake was started but consent and required fields are not complete.",
            consent=False,
        ),
    ]

    for payload in seed_payloads:
        patient = create_patient_from_intake(payload)
        if patient.name == "Lucas Ferreira":
            patient.status = "In monitoring"
            patient.queue = "Stable"
            patient.priority = "Routine"
            patient.next_step = "Weekly check-in"
            patient.last_check_in = "Yesterday, 18:40"
            patient.reviewed = True
            patient.follow_up_active = True
            patient.review_note = "Reviewed. Keep weekly monitoring and ask about academic load next session."
            patient.follow_up_cadence = "weekly"
            patient.follow_up_owner = patient.therapist
            patient.next_check_in = "2026-06-19"
            patient.ai_summary_json = json_dumps(
                {
                    "chiefConcern": "Academic stress with low mood and social withdrawal.",
                    "timeline": "Three months with gradual functional impact.",
                    "functionalImpact": patient.functional_impact,
                    "attentionSignals": ["class avoidance", "sleep changes", "social withdrawal"],
                    "suggestedQuestions": [
                        "What changed around the start of this three-month period?",
                        "Which routines still feel manageable?",
                        "How often is the patient able to access social support?",
                    ],
                    "recommendedOps": "Continue weekly check-ins and therapist-led treatment planning.",
                    "safetyBoundary": "AI output is a draft and is not a diagnosis.",
                    "provider": "structured",
                    "model": "deterministic-summary-v1",
                }
            )
        db.add(patient)
        db.flush()

        audit(db, patient, "Patient intake submitted")
        if patient.consent:
            audit(db, patient, "Consent captured for AI-assisted summarization")
        audit(db, patient, f"Assigned to {patient.therapist}")
        if patient.reviewed:
            summary = json_loads(patient.ai_summary_json, {})
            quality = evaluate_summary(summary)
            approved_summary = {
                **summary,
                "version": 1,
                "status": "approved",
                "quality": quality,
            }
            patient.ai_summary_json = json_dumps(approved_summary)
            db.add(
                SummaryVersion(
                    patient_id=patient.id,
                    version=1,
                    status="approved",
                    provider=str(summary.get("provider", "structured")),
                    model=str(summary.get("model", "deterministic-summary-v1")),
                    summary_json=json_dumps(approved_summary),
                    quality_json=json_dumps(quality),
                    created_by=patient.therapist,
                    reviewed_by=patient.therapist,
                    review_note=patient.review_note,
                    reviewed_at=datetime.now(timezone.utc),
                )
            )
            audit(db, patient, "AI-assisted summary generated")
            audit(db, patient, "Therapist reviewed summary")
            audit(db, patient, "Monitoring plan activated")

    db.commit()


def upsert_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    role: Literal["admin", "therapist", "patient"],
    password: str,
    linked_patient_id: str | None = None,
) -> None:
    user = db.query(UserRecord).filter(UserRecord.email == email).first()
    salt, password_digest = hash_password(password)
    if not user:
        user = UserRecord(
            id=f"user-{uuid4().hex[:8]}",
            full_name=full_name,
            email=email,
            role=role,
            password_salt=salt,
            password_hash=password_digest,
            linked_patient_id=linked_patient_id,
        )
        db.add(user)
        return

    user.full_name = full_name
    user.role = role
    user.linked_patient_id = linked_patient_id


def seed_users(db: Session) -> None:
    lucas = db.query(PatientRecord).filter(PatientRecord.name == "Lucas Ferreira").first()
    demo_password = "clearmind123"
    upsert_user(
        db,
        full_name="Arthur Clinic Admin",
        email="admin@clearmind.local",
        role="admin",
        password=demo_password,
    )
    upsert_user(
        db,
        full_name="Dr. Ana Ribeiro",
        email="ana@clearmind.local",
        role="therapist",
        password=demo_password,
    )
    upsert_user(
        db,
        full_name="Dr. Miguel Alves",
        email="miguel@clearmind.local",
        role="therapist",
        password=demo_password,
    )
    upsert_user(
        db,
        full_name="Lucas Ferreira",
        email="lucas.patient@clearmind.local",
        role="patient",
        password=demo_password,
        linked_patient_id=lucas.id if lucas else None,
    )
    db.commit()


def backfill_summary_versions(db: Session) -> None:
    patients = db.query(PatientRecord).filter(PatientRecord.ai_summary_json.isnot(None)).all()
    changed = False
    for patient in patients:
        has_version = (
            db.query(SummaryVersion)
            .filter(SummaryVersion.patient_id == patient.id)
            .first()
        )
        if has_version:
            continue

        summary = json_loads(patient.ai_summary_json, {})
        if not summary:
            continue

        quality = summary.get("quality") or evaluate_summary(summary)
        version_number = int(summary.get("version", 1) or 1)
        status = str(summary.get("status") or ("approved" if patient.reviewed else "draft"))
        enriched_summary = {
            **summary,
            "version": version_number,
            "status": status,
            "quality": quality,
        }
        patient.ai_summary_json = json_dumps(enriched_summary)
        db.add(
            SummaryVersion(
                patient_id=patient.id,
                version=version_number,
                status=status,
                provider=str(summary.get("provider", "structured")),
                model=str(summary.get("model", "deterministic-summary-v1")),
                summary_json=json_dumps(enriched_summary),
                quality_json=json_dumps(quality),
                created_by=patient.therapist or "System",
                reviewed_by=patient.therapist if patient.reviewed else "",
                review_note=patient.review_note if patient.reviewed else "",
                reviewed_at=datetime.now(timezone.utc) if patient.reviewed else None,
            )
        )
        changed = True

    if changed:
        db.commit()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_data(db)
        seed_users(db)
        backfill_summary_versions(db)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "clearmind-ai-ops-pilot",
        "version": "0.4.0",
        "ai": {"provider": AI_PROVIDER, "ollamaModel": OLLAMA_MODEL},
    }


@app.get("/ai/status")
def ai_status() -> dict:
    return {
        "provider": AI_PROVIDER,
        "configuredProvider": AI_PROVIDER,
        "ollamaBaseUrl": OLLAMA_BASE_URL if AI_PROVIDER == "ollama" else None,
        "ollamaModel": OLLAMA_MODEL if AI_PROVIDER == "ollama" else None,
        "fallback": "structured",
        "clinicalBoundary": "AI summaries are drafts for therapist review, not diagnoses.",
    }


@app.get("/auth/demo-users")
def demo_users() -> list[dict]:
    return [
        {
            "role": "admin",
            "label": "Clinic admin",
            "email": "admin@clearmind.local",
            "password": "clearmind123",
        },
        {
            "role": "therapist",
            "label": "Therapist",
            "email": "ana@clearmind.local",
            "password": "clearmind123",
        },
        {
            "role": "patient",
            "label": "Patient",
            "email": "lucas.patient@clearmind.local",
            "password": "clearmind123",
        },
    ]


@app.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.query(UserRecord).filter(UserRecord.email == req.email.lower().strip()).first()
    if not user or not verify_password(req.password, user.password_salt, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"token": create_token(user), "user": public_user(user)}


@app.get("/auth/me")
def me(user: UserRecord = Depends(get_current_user)) -> dict:
    return public_user(user)


@app.get("/patients")
def list_patients(
    db: Session = Depends(get_db),
    user: UserRecord = Depends(get_current_user),
) -> list[dict]:
    query = db.query(PatientRecord)
    if user.role == "therapist":
        query = query.filter(PatientRecord.therapist == user.full_name)
    elif user.role == "patient":
        query = query.filter(PatientRecord.id == user.linked_patient_id)
    patients = query.order_by(PatientRecord.created_at.asc()).all()
    return [
        serialize_patient(patient, get_patient_audit(db, patient.id), get_summary_versions(db, patient.id))
        for patient in patients
    ]


@app.get("/patients/{patient_id}")
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    user: UserRecord = Depends(get_current_user),
) -> dict:
    patient = get_patient_or_404(db, patient_id)
    assert_patient_access(user, patient)
    return serialize_patient(patient, get_patient_audit(db, patient.id), get_summary_versions(db, patient.id))


@app.post("/intakes", status_code=201)
def create_intake(
    payload: IntakeCreate,
    db: Session = Depends(get_db),
    user: UserRecord = Depends(require_roles("admin", "therapist")),
) -> dict:
    if user.role == "therapist":
        payload.therapist = user.full_name
    patient = create_patient_from_intake(payload)
    db.add(patient)
    db.flush()
    audit(db, patient, "Patient intake submitted")
    if patient.consent:
        audit(db, patient, "Consent captured for AI-assisted summarization")
    audit(db, patient, f"Assigned to {patient.therapist}")
    db.commit()
    db.refresh(patient)
    return serialize_patient(patient, get_patient_audit(db, patient.id), get_summary_versions(db, patient.id))


@app.post("/patients/{patient_id}/ai-summary")
def generate_ai_summary(
    patient_id: str,
    db: Session = Depends(get_db),
    user: UserRecord = Depends(require_roles("admin", "therapist")),
) -> dict:
    patient = get_patient_or_404(db, patient_id)
    assert_patient_access(user, patient)
    if not patient.consent:
        raise HTTPException(status_code=409, detail="Consent is required before AI summarization")
    if patient.intake_complete < 80:
        raise HTTPException(status_code=409, detail="Intake is not complete enough for summarization")

    summary = create_summary_version(db, patient, build_summary(patient), user)
    patient.ai_summary_json = json_dumps(summary)
    patient.queue = "Needs review"
    patient.next_step = "Therapist approval"
    audit(db, patient, f"AI-assisted summary v{summary['version']} generated; quality {summary['quality']['score']}%")
    db.commit()
    db.refresh(patient)
    return serialize_patient(patient, get_patient_audit(db, patient.id), get_summary_versions(db, patient.id))


@app.post("/patients/{patient_id}/review")
def review_summary(
    patient_id: str,
    req: ReviewRequest,
    db: Session = Depends(get_db),
    user: UserRecord = Depends(require_roles("admin", "therapist")),
) -> dict:
    patient = get_patient_or_404(db, patient_id)
    assert_patient_access(user, patient)
    if not patient.ai_summary_json:
        raise HTTPException(status_code=409, detail="AI summary must exist before review")

    patient.reviewed = req.decision == "approved"
    patient.status = "Reviewed" if patient.reviewed else "Needs changes"
    patient.queue = "Ready for care plan" if patient.reviewed else "Needs revision"
    patient.next_step = "Create monitoring plan" if patient.reviewed else "Update summary"
    patient.review_note = req.note
    current_summary = json_loads(patient.ai_summary_json, {})
    current_summary["status"] = req.decision
    patient.ai_summary_json = json_dumps(current_summary)
    summary_version = latest_summary_version(db, patient.id)
    if summary_version:
        summary_version.status = req.decision
        summary_version.reviewed_by = user.full_name
        summary_version.review_note = req.note
        summary_version.reviewed_at = datetime.now(timezone.utc)
        summary_version.summary_json = json_dumps(current_summary)
    audit(db, patient, f"{req.reviewer} marked summary as {req.decision}: {req.note}")
    db.commit()
    db.refresh(patient)
    return serialize_patient(patient, get_patient_audit(db, patient.id), get_summary_versions(db, patient.id))


@app.post("/patients/{patient_id}/follow-up")
def create_follow_up(
    patient_id: str,
    req: FollowUpRequest,
    db: Session = Depends(get_db),
    user: UserRecord = Depends(require_roles("admin", "therapist")),
) -> dict:
    patient = get_patient_or_404(db, patient_id)
    assert_patient_access(user, patient)
    if not patient.reviewed:
        raise HTTPException(status_code=409, detail="Therapist review is required before monitoring")

    patient.follow_up_active = True
    patient.status = "In monitoring"
    patient.queue = "Monitoring active"
    patient.next_step = "First check-in scheduled"
    patient.follow_up_cadence = req.cadence
    patient.follow_up_owner = req.owner
    patient.next_check_in = req.nextCheckIn
    audit(db, patient, f"Monitoring plan activated: {req.cadence}, owner {req.owner}, next {req.nextCheckIn}")
    db.commit()
    db.refresh(patient)
    return serialize_patient(patient, get_patient_audit(db, patient.id), get_summary_versions(db, patient.id))


@app.get("/audit")
def audit_events(
    db: Session = Depends(get_db),
    user: UserRecord = Depends(require_roles("admin", "therapist")),
) -> list[dict]:
    query = db.query(AuditEvent)
    if user.role == "therapist":
        visible_patients = db.query(PatientRecord.id).filter(PatientRecord.therapist == user.full_name).all()
        visible_ids = [row[0] for row in visible_patients]
        query = query.filter(AuditEvent.patient_id.in_(visible_ids))
    events = query.order_by(AuditEvent.id.desc()).limit(100).all()
    return [
        {
            "patientId": event.patient_id,
            "patient": event.patient_name,
            "event": event.event,
            "createdAt": event.created_at.isoformat() if event.created_at else None,
        }
        for event in events
    ]


@app.post("/dev/reset")
def reset_demo_data(db: Session = Depends(get_db)) -> dict:
    db.query(AuditEvent).delete()
    db.query(SummaryVersion).delete()
    db.query(PatientRecord).delete()
    db.query(UserRecord).delete()
    db.commit()
    seed_data(db)
    seed_users(db)
    return {"status": "reset", "patients": db.query(PatientRecord).count()}
