# WorkPilot (Full-Stack SaaS MVP)

A multi-tenant workflow/task management SaaS built with:
- Next.js (TypeScript)
- FastAPI (Python)
- Supabase Postgres (hosted)
- JWT auth in HttpOnly cookies

## Features
- Register/Login
- Workspace auto-created on signup
- Create/update/delete tasks
- Task status workflow (todo / in_progress / done)
- Dashboard stats
- Protected routes (frontend + backend auth checks)

## Run locally

### 1) Backend
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # mac/linux
# .venv\Scripts\activate    # windows
pip install -r requirements.txt
cp .env.example .env
# Fill in DATABASE_URL from Supabase
uvicorn app.main:app --reload --port 8000