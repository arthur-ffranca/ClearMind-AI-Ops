import {
  Activity,
  AlertTriangle,
  CalendarClock,
  Check,
  ClipboardCheck,
  Database,
  FileText,
  KeyRound,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Plus,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  UserRoundCheck
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const SESSION_KEY = "clearmind-session";

const demoAccounts = [
  {
    role: "admin",
    label: "Clinic admin",
    email: "admin@clearmind.local",
    password: "clearmind123"
  },
  {
    role: "therapist",
    label: "Therapist",
    email: "ana@clearmind.local",
    password: "clearmind123"
  },
  {
    role: "patient",
    label: "Patient",
    email: "lucas.patient@clearmind.local",
    password: "clearmind123"
  }
];

const fallbackPatients = [
  {
    id: "pt-fallback",
    name: "Mariana Costa",
    age: 32,
    pronouns: "she/her",
    therapist: "Dr. Ana Ribeiro",
    status: "New intake",
    queue: "Needs review",
    priority: "High attention",
    nextStep: "Therapist review",
    lastCheckIn: "Today, 09:18",
    intakeComplete: 92,
    consent: true,
    summaryGenerated: false,
    reviewed: false,
    followUpActive: false,
    reviewNote: "",
    followUp: { cadence: "", owner: "", nextCheckIn: "" },
    intake: {
      chiefConcern: "Persistent anxiety around work performance and sleep disruption.",
      duration: "About six weeks",
      functionalImpact: "Sleep reduced to 4-5 hours. Avoiding meetings and delaying decisions.",
      reportedSymptoms: ["racing thoughts", "chest tightness", "fatigue", "difficulty concentrating"],
      support: "Partner is aware and supportive.",
      freeText:
        "Patient reports escalating work-related anxiety, poor sleep, and reduced concentration. Denies immediate intent to self-harm but says she feels close to burnout."
    },
    aiSummary: null,
    audit: ["Local fallback data loaded"]
  }
];

const emptyIntake = {
  name: "Camila Torres",
  age: 29,
  pronouns: "she/her",
  therapist: "Dr. Ana Ribeiro",
  chiefConcern: "Anxiety spikes before work meetings.",
  duration: "Three weeks",
  functionalImpact: "Sleep has worsened and patient is avoiding presentations.",
  reportedSymptoms: "racing thoughts, insomnia, stomach tension",
  support: "Lives with sister and has one close friend available.",
  freeText:
    "Patient reports increased anticipatory anxiety before meetings, reduced sleep, and avoidance at work. Wants structured help before symptoms affect performance further.",
  consent: true
};

async function apiRequest(path, options = {}, token = "") {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    const details = await response.json().catch(() => ({}));
    throw new Error(details.detail || `Request failed with ${response.status}`);
  }

  return response.json();
}

function roleLabel(role) {
  if (role === "admin") return "Clinic admin";
  if (role === "therapist") return "Therapist";
  if (role === "patient") return "Patient";
  return "User";
}

function classForPriority(priority) {
  if (priority === "High attention") return "tag tagCritical";
  if (priority === "Missing data") return "tag tagWarning";
  return "tag tagStable";
}

function cadenceLabel(value) {
  if (value === "twice_weekly") return "Twice weekly check-in";
  if (value === "monthly") return "Monthly check-in";
  return "Weekly check-in";
}

function summaryStatusLabel(value) {
  if (value === "approved") return "Approved";
  if (value === "needs_changes") return "Needs changes";
  if (value === "draft") return "Draft";
  return "Not reviewed";
}

function qualityStatusLabel(value) {
  if (value === "pass") return "Pass";
  if (value === "needs_review") return "Needs review";
  return "Pending";
}

function formatDateTime(value) {
  if (!value) return "No timestamp";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function Stat({ icon: Icon, label, value, tone }) {
  return (
    <section className={`stat ${tone || ""}`}>
      <div className="statIcon">
        <Icon size={18} aria-hidden="true" />
      </div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
      </div>
    </section>
  );
}

function PatientRow({ patient, selected, onSelect }) {
  return (
    <button className={`patientRow ${selected ? "selected" : ""}`} onClick={() => onSelect(patient.id)}>
      <span className="patientAvatar">{patient.name.slice(0, 1)}</span>
      <span className="patientText">
        <strong>{patient.name}</strong>
        <small>{patient.status} - {patient.therapist}</small>
      </span>
      <span className={classForPriority(patient.priority)}>{patient.priority}</span>
    </button>
  );
}

function SummaryBlock({ title, children }) {
  return (
    <div className="summaryBlock">
      <span>{title}</span>
      <p>{children}</p>
    </div>
  );
}

function QualityChecklist({ quality }) {
  if (!quality?.checks?.length) return null;

  return (
    <div className="listBlock qualityBlock">
      <span>Quality checks</span>
      <div className="qualityScoreRow">
        <strong>{quality.score ?? 0}%</strong>
        <small>{qualityStatusLabel(quality.status)}</small>
      </div>
      <ul className="qualityList">
        {quality.checks.map((check) => (
          <li className={`qualityItem ${check.passed ? "pass" : "fail"}`} key={check.id}>
            <i aria-hidden="true" />
            <div>
              <strong>{check.label}</strong>
              <small>{check.detail}</small>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function VersionHistory({ versions = [] }) {
  if (!versions.length) return null;

  return (
    <div className="listBlock versionBlock">
      <span>Summary history</span>
      <div className="versionList">
        {versions.map((version) => (
          <div className="versionItem" key={version.id || version.version}>
            <strong>v{version.version} - {summaryStatusLabel(version.status)}</strong>
            <small>{version.provider} / {version.model}</small>
            <small>{version.quality?.score ?? 0}% quality - {formatDateTime(version.createdAt)}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function TextInput({ label, value, onChange, type = "text" }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function TextArea({ label, value, onChange, rows = 4 }) {
  return (
    <label className="field fullSpan">
      <span>{label}</span>
      <textarea rows={rows} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function LoginScreen({ onLogin }) {
  const [credentials, setCredentials] = useState({
    email: demoAccounts[0].email,
    password: demoAccounts[0].password
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submitLogin(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      const session = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials)
      });
      onLogin(session);
    } catch (loginError) {
      setError(loginError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="loginShell">
      <section className="loginPanel">
        <div className="brandLockup loginBrand">
          <div className="brandMark">
            <Stethoscope size={22} aria-hidden="true" />
          </div>
          <div>
            <strong>ClearMind</strong>
            <span>AI Ops v0.4</span>
          </div>
        </div>

        <div>
          <p className="eyebrow">Role-based access</p>
          <h1>Clinical workspace sign in</h1>
        </div>

        <form className="loginForm" onSubmit={submitLogin}>
          <TextInput
            label="Email"
            value={credentials.email}
            onChange={(value) => setCredentials({ ...credentials, email: value })}
          />
          <TextInput
            label="Password"
            type="password"
            value={credentials.password}
            onChange={(value) => setCredentials({ ...credentials, password: value })}
          />

          {error ? <div className="banner">Login failed: {error}</div> : null}

          <button className="primaryButton loginButton" type="submit" disabled={submitting}>
            <KeyRound size={17} aria-hidden="true" />
            {submitting ? "Signing in" : "Sign in"}
          </button>
        </form>

        <div className="demoAccountGrid">
          {demoAccounts.map((account) => (
            <button
              key={account.email}
              className="demoAccount"
              onClick={() => setCredentials({ email: account.email, password: account.password })}
            >
              <span>{account.label}</span>
              <strong>{account.email}</strong>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}

export function App() {
  const [session, setSession] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(SESSION_KEY));
    } catch {
      return null;
    }
  });
  const [patients, setPatients] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [reviewDraft, setReviewDraft] = useState("");
  const [intakeDraft, setIntakeDraft] = useState(emptyIntake);
  const [loading, setLoading] = useState(Boolean(session));
  const [apiStatus, setApiStatus] = useState("Signed out");
  const [actionError, setActionError] = useState("");
  const [creating, setCreating] = useState(false);

  const selectedPatient = patients.find((patient) => patient.id === selectedId) || patients[0] || fallbackPatients[0];
  const currentRole = session?.user?.role || "";
  const canManageCare = currentRole === "admin" || currentRole === "therapist";
  const canCreateIntake = canManageCare;

  const metrics = useMemo(() => {
    const needsReview = patients.filter((patient) => patient.queue === "Needs review").length;
    const activeMonitoring = patients.filter((patient) => patient.followUpActive).length;
    const highAttention = patients.filter((patient) => patient.priority === "High attention").length;

    return { needsReview, activeMonitoring, highAttention };
  }, [patients]);

  function handleLogin(nextSession) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
    setSession(nextSession);
    setLoading(true);
  }

  function logout() {
    localStorage.removeItem(SESSION_KEY);
    setSession(null);
    setPatients([]);
    setSelectedId("");
    setApiStatus("Signed out");
  }

  async function loadPatients(nextSelectedId = selectedId, activeSession = session) {
    if (!activeSession?.token) return;
    setActionError("");

    try {
      const data = await apiRequest("/patients", {}, activeSession.token);
      setPatients(data);
      setSelectedId(nextSelectedId && data.some((patient) => patient.id === nextSelectedId) ? nextSelectedId : data[0]?.id || "");
      setApiStatus(`${roleLabel(activeSession.user.role)} API`);
    } catch (error) {
      if (
        error.message.includes("Authentication") ||
        error.message.includes("Session") ||
        error.message.includes("Invalid token") ||
        error.message.includes("User not found")
      ) {
        logout();
        return;
      }
      setPatients(fallbackPatients);
      setSelectedId(fallbackPatients[0].id);
      setApiStatus("Local fallback");
      setActionError(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (session?.token) {
      loadPatients("", session);
    }
  }, [session?.token]);

  function replacePatient(nextPatient) {
    setPatients((current) =>
      current.map((patient) => (patient.id === nextPatient.id ? nextPatient : patient))
    );
    setSelectedId(nextPatient.id);
  }

  async function generateSummary() {
    if (!canManageCare || !selectedPatient.consent || selectedPatient.intakeComplete < 80) return;
    setActionError("");
    try {
      const updated = await apiRequest(`/patients/${selectedPatient.id}/ai-summary`, { method: "POST" }, session.token);
      replacePatient(updated);
    } catch (error) {
      setActionError(error.message);
    }
  }

  async function approveReview() {
    if (!canManageCare || !selectedPatient.aiSummary) return;
    const note = reviewDraft.trim() || "Therapist approved AI-assisted summary for care planning.";
    setActionError("");

    try {
      const updated = await apiRequest(
        `/patients/${selectedPatient.id}/review`,
        {
          method: "POST",
          body: JSON.stringify({
            reviewer: session.user.fullName,
            decision: "approved",
            note
          })
        },
        session.token
      );
      replacePatient(updated);
      setReviewDraft("");
    } catch (error) {
      setActionError(error.message);
    }
  }

  async function scheduleFollowUp() {
    if (!canManageCare) return;
    setActionError("");
    try {
      const updated = await apiRequest(
        `/patients/${selectedPatient.id}/follow-up`,
        {
          method: "POST",
          body: JSON.stringify({
            cadence: selectedPatient.priority === "High attention" ? "twice_weekly" : "weekly",
            owner: selectedPatient.therapist || session.user.fullName,
            nextCheckIn: "2026-06-19"
          })
        },
        session.token
      );
      replacePatient(updated);
    } catch (error) {
      setActionError(error.message);
    }
  }

  async function submitIntake(event) {
    event.preventDefault();
    if (!canCreateIntake) return;
    setCreating(true);
    setActionError("");

    try {
      const created = await apiRequest(
        "/intakes",
        {
          method: "POST",
          body: JSON.stringify({
            ...intakeDraft,
            age: Number(intakeDraft.age),
            reportedSymptoms: intakeDraft.reportedSymptoms
              .split(",")
              .map((symptom) => symptom.trim())
              .filter(Boolean)
          })
        },
        session.token
      );

      setPatients((current) => [...current, created]);
      setSelectedId(created.id);
      setIntakeDraft(emptyIntake);
    } catch (error) {
      setActionError(error.message);
    } finally {
      setCreating(false);
    }
  }

  if (!session) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <div className="appShell">
      <aside className="sidebar">
        <div className="brandLockup">
          <div className="brandMark">
            <Stethoscope size={22} aria-hidden="true" />
          </div>
          <div>
            <strong>ClearMind</strong>
            <span>AI Ops v0.4</span>
          </div>
        </div>

        <nav className="navList" aria-label="Main navigation">
          <button className="navItem active" title="Dashboard">
            <LayoutDashboard size={18} aria-hidden="true" />
            Dashboard
          </button>
          <button className="navItem" title="Intake queue">
            <ListChecks size={18} aria-hidden="true" />
            Intake queue
          </button>
          <button className="navItem" title="Clinical review">
            <ClipboardCheck size={18} aria-hidden="true" />
            Review
          </button>
          <button className="navItem" title="Audit trail">
            <ShieldCheck size={18} aria-hidden="true" />
            Audit
          </button>
        </nav>

        <div className="complianceNote">
          <ShieldCheck size={17} aria-hidden="true" />
          <span>AI assists intake organization. Clinicians approve all care-facing notes.</span>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Clinical intake MVP</p>
            <h1>Therapist-reviewed intake workflow</h1>
          </div>
          <div className="statusCluster">
            <span className="apiBadge">
              <Database size={16} aria-hidden="true" />
              {loading ? "Loading" : apiStatus}
            </span>
            <div className="userChip">
              <span>{roleLabel(currentRole)}</span>
              <strong>{session.user.fullName}</strong>
            </div>
            <button className="iconButton" title="Log out" onClick={logout}>
              <LogOut size={18} aria-hidden="true" />
            </button>
          </div>
        </header>

        {actionError ? <div className="banner">API notice: {actionError}</div> : null}

        <section className="statsGrid" aria-label="Clinic metrics">
          <Stat icon={FileText} label="New intakes" value={metrics.needsReview} tone="warm" />
          <Stat icon={Activity} label="Active monitoring" value={metrics.activeMonitoring} tone="cool" />
          <Stat icon={AlertTriangle} label="Attention signals" value={metrics.highAttention} tone="critical" />
          <Stat icon={UserRoundCheck} label="Patients visible" value={patients.length} tone="stable" />
        </section>

        <section className="mainGrid">
          <section className="panel queuePanel">
            <div className="panelHeader">
              <div>
                <p className="eyebrow">Patient queue</p>
                <h2>Intake status</h2>
              </div>
              <button className="iconButton" title="Refresh queue" onClick={() => loadPatients(selectedPatient.id)}>
                <RefreshCw size={18} aria-hidden="true" />
              </button>
            </div>

            <div className="patientList">
              {patients.map((patient) => (
                <PatientRow
                  key={patient.id}
                  patient={patient}
                  selected={patient.id === selectedPatient.id}
                  onSelect={setSelectedId}
                />
              ))}
            </div>
          </section>

          <section className="panel detailPanel">
            <div className="panelHeader">
              <div>
                <p className="eyebrow">Selected patient</p>
                <h2>{selectedPatient.name}</h2>
              </div>
              <span className={classForPriority(selectedPatient.priority)}>
                {selectedPatient.priority}
              </span>
            </div>

            <div className="profileGrid">
              <SummaryBlock title="Profile">
                {selectedPatient.age} years - {selectedPatient.pronouns} - {selectedPatient.therapist}
              </SummaryBlock>
              <SummaryBlock title="Next step">{selectedPatient.nextStep}</SummaryBlock>
              <SummaryBlock title="Last check-in">{selectedPatient.lastCheckIn}</SummaryBlock>
              <div className="progressBlock">
                <span>Intake completeness</span>
                <div className="progressTrack">
                  <div style={{ width: `${selectedPatient.intakeComplete}%` }} />
                </div>
                <strong>{selectedPatient.intakeComplete}%</strong>
              </div>
            </div>

            <div className="intakeText">
              <span>Patient intake</span>
              <p>{selectedPatient.intake.freeText}</p>
            </div>
          </section>
        </section>

        <section className="workflowGrid">
          <section className="panel">
            <div className="panelHeader">
              <div>
                <p className="eyebrow">AI clinical assistant</p>
                <h2>Structured intake summary</h2>
              </div>
              {canManageCare ? (
                <button
                  className="primaryButton"
                  onClick={generateSummary}
                  disabled={!selectedPatient.consent || selectedPatient.intakeComplete < 80}
                  title="Generate summary"
                >
                  <Sparkles size={17} aria-hidden="true" />
                  Generate
                </button>
              ) : (
                <span className="tag tagStable">Read only</span>
              )}
            </div>

            {!selectedPatient.aiSummary ? (
              <div className="emptyState">
                <Sparkles size={24} aria-hidden="true" />
                <p>Summary is available after consent, complete intake, and clinical role access.</p>
              </div>
            ) : (
              <div className="summaryGrid">
                <SummaryBlock title="Chief concern">{selectedPatient.aiSummary.chiefConcern}</SummaryBlock>
                <SummaryBlock title="Timeline">{selectedPatient.aiSummary.timeline}</SummaryBlock>
                <SummaryBlock title="Operational note">{selectedPatient.aiSummary.recommendedOps}</SummaryBlock>
                <SummaryBlock title="Boundary">{selectedPatient.aiSummary.safetyBoundary}</SummaryBlock>
                <SummaryBlock title="AI provider">
                  {(selectedPatient.aiSummary.provider || "structured")} - {(selectedPatient.aiSummary.model || "deterministic-summary-v1")}
                </SummaryBlock>
                <SummaryBlock title="Version">
                  v{selectedPatient.aiSummary.version || selectedPatient.summaryVersions?.[0]?.version || 1} -{" "}
                  {summaryStatusLabel(selectedPatient.aiSummary.status || selectedPatient.summaryVersions?.[0]?.status)}
                </SummaryBlock>
                <div className="listBlock">
                  <span>Attention signals</span>
                  <ul>
                    {selectedPatient.aiSummary.attentionSignals.map((signal) => (
                      <li key={signal}>{signal}</li>
                    ))}
                  </ul>
                </div>
                <div className="listBlock">
                  <span>Suggested therapist questions</span>
                  <ul>
                    {selectedPatient.aiSummary.suggestedQuestions.map((question) => (
                      <li key={question}>{question}</li>
                    ))}
                  </ul>
                </div>
                <QualityChecklist quality={selectedPatient.aiSummary.quality || selectedPatient.summaryVersions?.[0]?.quality} />
                <VersionHistory versions={selectedPatient.summaryVersions || []} />
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panelHeader">
              <div>
                <p className="eyebrow">Human review</p>
                <h2>Therapist approval</h2>
              </div>
              {canManageCare ? (
                <button
                  className="primaryButton"
                  onClick={approveReview}
                  disabled={!selectedPatient.aiSummary}
                  title="Approve summary"
                >
                  <Check size={17} aria-hidden="true" />
                  Approve
                </button>
              ) : null}
            </div>

            <textarea
              value={reviewDraft}
              onChange={(event) => setReviewDraft(event.target.value)}
              placeholder={selectedPatient.reviewNote || "Add a therapist-facing note before approval."}
              aria-label="Therapist review note"
              disabled={!canManageCare}
            />

            <div className="reviewStatus">
              <ClipboardCheck size={18} aria-hidden="true" />
              <span>{selectedPatient.reviewed ? "Reviewed by therapist" : "Awaiting therapist review"}</span>
            </div>
          </section>

          <section className="panel">
            <div className="panelHeader">
              <div>
                <p className="eyebrow">Monitoring</p>
                <h2>Follow-up cadence</h2>
              </div>
              {canManageCare ? (
                <button
                  className="secondaryButton"
                  onClick={scheduleFollowUp}
                  disabled={!selectedPatient.reviewed}
                  title="Schedule follow-up"
                >
                  <CalendarClock size={17} aria-hidden="true" />
                  Schedule
                </button>
              ) : null}
            </div>

            <div className="cadenceGrid">
              <SummaryBlock title="Cadence">
                {selectedPatient.followUp?.cadence
                  ? cadenceLabel(selectedPatient.followUp.cadence)
                  : selectedPatient.priority === "High attention"
                    ? "Twice weekly check-in"
                    : "Weekly check-in"}
              </SummaryBlock>
              <SummaryBlock title="Owner">{selectedPatient.followUp?.owner || selectedPatient.therapist}</SummaryBlock>
              <SummaryBlock title="Status">
                {selectedPatient.followUpActive ? "Monitoring active" : "Not scheduled"}
              </SummaryBlock>
            </div>
          </section>

          <section className="panel">
            <div className="panelHeader">
              <div>
                <p className="eyebrow">Audit trail</p>
                <h2>Recent events</h2>
              </div>
              <ShieldCheck size={19} aria-hidden="true" />
            </div>

            <ol className="auditList">
              {selectedPatient.audit.map((event, index) => (
                <li key={`${event}-${index}`}>{event}</li>
              ))}
            </ol>
          </section>
        </section>

        <section className="panel intakePanel">
          <div className="panelHeader">
            <div>
              <p className="eyebrow">Patient portal</p>
              <h2>New intake submission</h2>
            </div>
            <Plus size={19} aria-hidden="true" />
          </div>

          {canCreateIntake ? (
            <form className="intakeForm" onSubmit={submitIntake}>
              <TextInput label="Patient name" value={intakeDraft.name} onChange={(value) => setIntakeDraft({ ...intakeDraft, name: value })} />
              <TextInput label="Age" type="number" value={intakeDraft.age} onChange={(value) => setIntakeDraft({ ...intakeDraft, age: value })} />
              <TextInput label="Pronouns" value={intakeDraft.pronouns} onChange={(value) => setIntakeDraft({ ...intakeDraft, pronouns: value })} />
              <TextInput label="Therapist" value={intakeDraft.therapist} onChange={(value) => setIntakeDraft({ ...intakeDraft, therapist: value })} />
              <TextInput label="Chief concern" value={intakeDraft.chiefConcern} onChange={(value) => setIntakeDraft({ ...intakeDraft, chiefConcern: value })} />
              <TextInput label="Duration" value={intakeDraft.duration} onChange={(value) => setIntakeDraft({ ...intakeDraft, duration: value })} />
              <TextArea label="Functional impact" value={intakeDraft.functionalImpact} onChange={(value) => setIntakeDraft({ ...intakeDraft, functionalImpact: value })} rows={3} />
              <TextArea label="Reported symptoms" value={intakeDraft.reportedSymptoms} onChange={(value) => setIntakeDraft({ ...intakeDraft, reportedSymptoms: value })} rows={3} />
              <TextArea label="Support available" value={intakeDraft.support} onChange={(value) => setIntakeDraft({ ...intakeDraft, support: value })} rows={3} />
              <TextArea label="Patient notes" value={intakeDraft.freeText} onChange={(value) => setIntakeDraft({ ...intakeDraft, freeText: value })} rows={4} />

              <label className="checkField">
                <input
                  type="checkbox"
                  checked={intakeDraft.consent}
                  onChange={(event) => setIntakeDraft({ ...intakeDraft, consent: event.target.checked })}
                />
                <span>Consent captured for AI-assisted summarization</span>
              </label>

              <button className="primaryButton submitButton" type="submit" disabled={creating}>
                <Plus size={17} aria-hidden="true" />
                {creating ? "Creating" : "Create intake"}
              </button>
            </form>
          ) : (
            <div className="emptyState">
              <UserRoundCheck size={24} aria-hidden="true" />
              <p>Patient role can view only its own intake and monitoring state in this pilot.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
