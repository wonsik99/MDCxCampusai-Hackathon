# StruggleSense MVP

StruggleSense is an AI-powered adaptive study support system for struggling learners. This MVP converts lecture materials into concept-tagged quiz content, tracks answer history, updates per-concept mastery, detects prerequisite-aware gaps, and returns ordered study recommendations.

## Stack

- Frontend: Next.js App Router, TypeScript, Tailwind CSS
- Backend: FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic
- Database: PostgreSQL-compatible SQLAlchemy schema, SQLite-friendly dev default
- AI: Official OpenAI Python SDK with the Responses API and structured JSON validation

## Repo layout

```text
backend/
  app/
    api/routes/
    core/
    db/
    models/
    schemas/
    services/
    utils/
  alembic/
frontend/
  app/
  components/
  lib/
requirements.txt
.env.example
```

## Backend overview

- `POST /lectures/upload`: accepts raw text or a PDF, extracts and cleans text, stores the lecture, summarizes content, and extracts core concepts
- `POST /lectures/{lecture_id}/generate-quiz`: generates concept-tagged multiple-choice questions and wrong-answer explanations
- `POST /quiz-sessions/start`: creates a quiz session for the active student
- `GET /quiz-sessions/{session_id}/questions`: returns safe question payloads without correct answers
- `POST /quiz-sessions/{session_id}/submit-answer`: grades server-side, stores the attempt, updates mastery, and returns feedback
- `POST /quiz-sessions/{session_id}/finish`: closes the session and refreshes recommendations
- `GET /users/{user_id}/concept-mastery`: returns mastery analytics
- `GET /users/{user_id}/recommendations`: returns ordered study recommendations
- `GET /demo-users`: returns the seeded demo students used by the web app selector

Lecture and quiz routes expect `X-User-Id` so the current demo student is resolved in one place. A future auth layer can replace that resolver without changing route contracts.

## OpenAI behavior

- When `OPENAI_API_KEY` is present, the backend uses the official `openai` Python SDK and the Responses API to request structured JSON outputs for summaries, concept extraction, quiz generation, explanations, and recommendation wording.
- All AI outputs are validated with Pydantic before persistence.
- When `OPENAI_API_KEY` is missing, the app still runs with a deterministic fallback provider that generates heuristic summaries, concepts, quiz items, and recommendation copy. The API metadata reports whether fallback mode was used.

## Prerequisite reasoning

The MVP includes a seeded linear algebra dependency chain:

```text
matrix multiplication -> determinant -> eigenvalues -> eigenvectors
```

If an extracted concept matches part of that chain, StruggleSense automatically inserts missing prerequisites as inferred lecture concepts so mastery and recommendations can still reason about what the student needs first.

## Local setup

### 1. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --app-dir backend --reload
```

The default `DATABASE_URL` uses SQLite for easy local startup. For PostgreSQL, replace it with your Postgres connection string and rerun the migration command.

### 2. Frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local
npm run dev
```

The frontend expects `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.

## Running tests

Backend:

```bash
pytest backend/tests
```

Frontend:

```bash
cd frontend
npm test
```

## Web app pages

- `/`: project overview and Unity handoff explanation
- `/upload`: lecture upload and AI analysis
- `/lectures/[lectureId]`: lecture summary, concepts, quiz generation, and quiz start
- `/quiz/[sessionId]`: lightweight browser quiz runner over the same backend APIs Unity will call later
- `/dashboard`: concept mastery and weak concept analytics
- `/recommendations`: ordered study steps

## Unity integration point

Unity is intentionally not implemented in this repo. It should connect to the backend by calling the same endpoints already used by the browser quiz:

- `POST /quiz-sessions/start`
- `GET /quiz-sessions/{session_id}`
- `GET /quiz-sessions/{session_id}/questions`
- `POST /quiz-sessions/{session_id}/submit-answer`
- `POST /quiz-sessions/{session_id}/finish`
- `GET /users/{user_id}/recommendations`

Unity should send `X-User-Id` for demo mode today. Later, that header can be replaced by auth token resolution on the backend without changing the session payload shapes.

## Notes

- Server-side grading is enforced; correct answers never appear in question delivery endpoints.
- Quiz generation is idempotent unless `force_regenerate=true`.
- Recommendation order is deterministic and prerequisite-aware; the LLM only helps phrase the wording.
- Demo users are seeded automatically on backend startup for SQLite development and via `backend/app/db/seed.py` for other environments.
