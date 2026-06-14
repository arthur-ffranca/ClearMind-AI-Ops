# 🧠 ClearMind AI Ops

> An intelligent mental health clinic operations platform combining NLP-driven patient intake assessment, continuous monitoring, and clinical dashboards for therapists and administrators.

**Status:** MVP ✅ Fully Functional | **Stack:** FastAPI + React + PostgreSQL + Docker

---

## 🚀 Quick Start (30 seconds)

```bash
# Clone
git clone https://github.com/yourusername/ClearMind-AI-Ops.git
cd ClearMind-AI-Ops

# Copy env
cp .env.example .env

# Run everything
docker-compose up

# Open browser
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

**First time?** Create account → log in → see dashboard!

For detailed setup, see [SETUP.md](SETUP.md).

---

## 📋 What You Get

✅ **Full-stack MVP** - Register, login, dashboard  
✅ **Production-ready code** - Type-safe FastAPI + React  
✅ **PostgreSQL database** - 12 tables with audit logs  
✅ **JWT authentication** - Secure token-based auth  
✅ **Docker setup** - One command to run everything  
✅ **API documentation** - Swagger UI included  
✅ **Beautiful design** - Dark glassmorphic UI  

---

## 🏗️ Architecture

**Three Core Pillars:**

1. **Intake & Assessment** - Chat-based NLP patient assessment
2. **Continuous Monitoring** - Scheduled check-ins & sentiment tracking (Phase 2)
3. **Dashboards** - Risk ranking, therapy tracking (Phase 2)

See [docs/01_ARCHITECTURE.md](docs/01_ARCHITECTURE.md) for full design.

---

## 🚢 Getting Started

```bash
# Option 1: Docker (Recommended)
docker-compose up
# Open http://localhost:5173

# Option 2: Local development
# Backend: cd backend && python main.py
# Frontend: cd frontend && npm run dev
```

See [SETUP.md](SETUP.md) for detailed instructions.

---

## 📂 Structure

```
ClearMind-AI-Ops/
├── backend/        # FastAPI + SQLAlchemy
├── frontend/       # React + Vite + TailwindCSS
├── docs/          # Architecture & design
├── api-spec/      # OpenAPI specification
├── docker-compose.yml
└── SETUP.md
```

---

## 📚 Documentation

| Doc | Purpose |
|-----|---------|
| [SETUP.md](SETUP.md) | How to run locally |
| [docs/01_ARCHITECTURE.md](docs/01_ARCHITECTURE.md) | System design |
| [docs/02_ADR/ADRs.md](docs/02_ADR/ADRs.md) | Technical decisions |
| [docs/03_DATA_MODEL.md](docs/03_DATA_MODEL.md) | Database schema |
| [api-spec/openapi.yaml](api-spec/openapi.yaml) | API spec |
| [docs/05_ROADMAP.md](docs/05_ROADMAP.md) | 12-week plan |

---

## 🎯 MVP Features

- [x] User registration & login
- [x] JWT authentication
- [x] User profiles & dashboard
- [x] PostgreSQL database (12 tables)
- [x] API documentation (Swagger)
- [x] Docker setup
- [x] Audit logging
- [x] LGPD compliance ready

---

## 🔄 Next (Phase 2)

- [ ] Chat assessment (OpenRouter LLM)
- [ ] NLP analysis & severity scoring
- [ ] ClickUp integration
- [ ] Email/SMS check-ins
- [ ] Therapist dashboard
- [ ] Compliance reporting

See [docs/05_ROADMAP.md](docs/05_ROADMAP.md) for 12-week timeline.

---

## 💡 Design Philosophy

- **System-first** - Focus on operations, not just accuracy
- **Event-driven** - Decoupled services
- **Scalable** - Ready for 1000+ patients
- **Compliant** - LGPD built-in
- **Production-ready** - No shortcuts

---

## 🔒 Security

- Bcrypt password hashing
- JWT token auth
- CORS configuration
- SQL injection prevention (ORM)
- Audit logging
- LGPD compliance

---

## 📞 Support

- **API Docs:** http://localhost:8000/docs
- **Setup:** [SETUP.md](SETUP.md)
- **Architecture:** [docs/](docs/)
- **Issues:** Open on GitHub

---

**Built by Arthur** | MIT License | Last Updated: June 2026

Get started: `docker-compose up` 🚀
