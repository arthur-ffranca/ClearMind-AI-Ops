# 🚀 ClearMind AI Ops - Quick Start Guide

## Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (if running without Docker)
- **Node.js 18+** (if running without Docker)
- **PostgreSQL 15+** (if running without Docker)

---

## Option 1: Docker Compose (Recommended) ⚡

**Everything runs in containers with one command:**

```bash
# 1. Clone and navigate
git clone https://github.com/yourusername/ClearMind-AI-Ops.git
cd ClearMind-AI-Ops

# 2. Create .env from example
cp .env.example .env

# 3. Start services
docker-compose up

# 4. Open in browser
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**That's it!** The database is created automatically.

### First Time Usage:
1. Go to http://localhost:5173
2. Click "Sign Up"
3. Fill in form (role can be: patient, therapist, or admin)
4. Submit
5. Go to "Sign In" and log in with your credentials
6. You should see the Dashboard!

---

## Option 2: Local Development (Without Docker)

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env (at project root)
cp ../.env.example ../.env

# 5. Set DATABASE_URL in .env
DATABASE_URL=postgresql://clearmind:clearmind@localhost:5432/clearmind

# 6. Run backend
python main.py
# API will be available at http://localhost:8000
```

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start dev server
npm run dev
# Frontend will be available at http://localhost:5173
```

### Database Setup

```bash
# 1. Install PostgreSQL locally

# 2. Create database
createdb -U postgres clearmind

# 3. Or use Docker just for database
docker run --name clearmind-postgres \
  -e POSTGRES_USER=clearmind \
  -e POSTGRES_PASSWORD=clearmind \
  -e POSTGRES_DB=clearmind \
  -p 5432:5432 \
  -d postgres:15-alpine
```

---

## Testing the API

### Using Swagger UI (Built-in)
1. Navigate to http://localhost:8000/docs
2. Try "Try it out" on any endpoint
3. For protected endpoints, click "Authorize" and paste your JWT token

### Using curl

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password123",
    "full_name": "Test User",
    "role": "patient",
    "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password123"
  }'

# Get current user (replace TOKEN with your actual token)
curl -X GET http://localhost:8000/me \
  -H "Authorization: Bearer TOKEN"
```

---

## Project Structure

```
ClearMind-AI-Ops/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── models.py            # SQLAlchemy ORM
│   ├── schemas.py           # Pydantic validators
│   ├── database.py          # DB config
│   ├── jwt_handler.py       # Auth utilities
│   ├── requirements.txt
│   ├── Dockerfile
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── store/           # Zustand state
│   │   ├── App.jsx          # Router
│   │   └── main.jsx         # Entry point
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── ...
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Common Issues & Solutions

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port:
# Docker: edit docker-compose.yml
# Local: python main.py --port 8001
```

### Database connection error
```bash
# Check PostgreSQL is running
psql -U postgres -d postgres -c "SELECT version();"

# Check DATABASE_URL in .env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

### Frontend can't reach backend
```bash
# Check backend is running on 8000
curl http://localhost:8000/health

# Update frontend API URL in src/api.js
VITE_API_BASE_URL=http://localhost:8000
```

### JWT token expired
```bash
# Just log in again - fresh token will be issued
# Token TTL is 8 hours by default
```

---

## Environment Variables

See `.env.example` for all available options:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT
SECRET_KEY=your-secret-key (change in production!)

# API Keys (optional for MVP)
OPENROUTER_API_KEY=your-key-here
SENDGRID_API_KEY=your-key-here
TWILIO_ACCOUNT_SID=your-sid

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

---

## Next Steps

After getting it running:

1. **Review Architecture**: Read `/docs/01_ARCHITECTURE.md`
2. **Add Features**: See `/docs/05_ROADMAP.md` for what to build next
3. **API Reference**: Check `/api-spec/openapi.yaml` for all endpoints
4. **Database**: See `/docs/03_DATA_MODEL.md` for schema details

---

## Deployment

To deploy to production:

1. **Backend**: Railway, Heroku, AWS, or any Docker-compatible host
2. **Frontend**: Vercel, Netlify, GitHub Pages
3. **Database**: RDS, Supabase, Heroku Postgres

See `/docs/06_DEPLOYMENT.md` for detailed instructions (coming soon).

---

## Getting Help

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Architecture**: `/docs/` folder
- **Code Issues**: Check `/docs/02_ADR/` for design decisions

---

**Happy building!** 🚀

For issues, questions, or contributions, open an issue on GitHub.
