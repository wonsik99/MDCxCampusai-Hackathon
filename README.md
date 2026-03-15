# StruggleSense (MDC x Campus AI Hackathon)

StruggleSense is an AI-powered adaptive study support system for struggling learners. It turns lecture materials into concept-tagged quizzes, tracks answers, updates per-concept mastery, detects prerequisite-aware gaps, and returns ordered study recommendations. A Unity WebGL game (e.g. meteorite quiz) can run in the browser and use the same backend APIs.

## Stack

- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS. Unity WebGL builds are served from `frontend/public/unity/`.
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic.
- **Database**: SQLAlchemy schema (SQLite by default; PostgreSQL-compatible).
- **AI**: OpenAI Python SDK (Responses API, structured JSON). No fallback provider; `OPENAI_API_KEY` is required for summaries, concept extraction, and quiz generation.

## Repo layout

```text
backend/
  app/
    api/routes/     # lectures, quiz-sessions, users
    core/           # config, dependencies, exceptions
    db/             # session, seed
    models/
    schemas/
    services/       # lecture, quiz, analytics, recommendation, star_jar, ai
    utils/
  alembic/
frontend/
  app/              # pages (upload, lectures, quiz, dashboard, recommendations, games)
  components/
  lib/              # API client
  public/
    unity/          # WebGL build (index.html, Build/, TemplateData/)
tools/              # e.g. unity_launcher_helper
.env.example
requirements.txt
```

## Backend API overview

- **Lectures**
  - `POST /lectures/upload` — Upload raw text or PDF; extract/clean text, store lecture, run AI summary and concept extraction.
  - `POST /lectures/{lecture_id}/generate-quiz` — Generate concept-tagged multiple-choice questions and wrong-answer explanations (idempotent unless `force_regenerate=true`).
- **Quiz sessions** (used by the web quiz and by Unity)
  - `POST /quiz-sessions/start` — Start a session (body: `lecture_id`, optional `question_limit`).
  - `GET /quiz-sessions/{session_id}` — Session status.
  - `GET /quiz-sessions/{session_id}/questions` — Question payloads (no correct answers).
  - `POST /quiz-sessions/{session_id}/submit-answer` — Submit one answer; server grades, stores attempt, updates mastery, returns feedback.
  - `POST /quiz-sessions/{session_id}/finish` — Close session, award stars, refresh recommendations.
- **Users & analytics**
  - `GET /demo-users` — List seeded demo users (for web app user selector).
  - `GET /users/{user_id}/concept-mastery` — Per-concept mastery.
  - `GET /users/{user_id}/recommendations` — Ordered study recommendations.
  - `GET /users/{user_id}/star-jars` — Weekly star-jar progress (motivation).

Lecture and quiz routes require the **`X-User-Id`** header (UUID of the current user). Demo users are seeded on startup.

## OpenAI

- The backend uses the official `openai` Python SDK and the Responses API for structured JSON (summaries, concepts, quiz generation, wrong-answer explanations, recommendation wording).
- All AI outputs are validated with Pydantic before use.
- **`OPENAI_API_KEY`** must be set for upload and quiz generation. No fallback provider.
- Optional env: `OPENAI_MODEL` (default `gpt-4.1-mini`), `OPENAI_TIMEOUT_SECONDS` (default 45).

## Prerequisite reasoning

A seeded linear algebra dependency chain is used so that if an extracted concept matches part of it, missing prerequisites can be inferred for mastery and recommendations:

```text
matrix multiplication → determinant → eigenvalues → eigenvectors
```

## Local setup

### 1. Backend

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Set OPENAI_API_KEY and optionally DATABASE_URL
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --app-dir backend --reload
```

Default is SQLite (`sqlite:///./strugglesense.db`). For PostgreSQL, set `DATABASE_URL` and run the migration again.

### 2. Frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local   # Or set NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The app expects the API at `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`).

## Running tests

- **Backend**: `pytest backend/tests` (from repo root).
- **Frontend**: `cd frontend && npm test`.

## Web app pages

- `/` — Overview and current learner state.
- `/upload` — Lecture upload and AI analysis.
- `/lectures/[lectureId]` — Lecture summary, concepts, quiz generation, and links to start quiz or game.
- `/quiz/[sessionId]` — Browser quiz runner (same APIs as Unity).
- `/game/[lectureId]` — Entry point for game mode for a lecture.
- `/games/meteorite` — Meteorite game (Unity WebGL) with `?lectureId=...`.
- `/dashboard` — Concept mastery and weak-concept analytics.
- `/recommendations` — Ordered study steps.
- `/users/[userId]/star-jars` (or via dashboard) — Weekly star jars.

## Unity integration

- **WebGL build**: The built Unity game is placed under `frontend/public/unity/` (e.g. `index.html`, `Build/`, `TemplateData/`). The Next.js page `/games/meteorite` loads it in an iframe with `?lectureId=...`.
- **Backend**: Unity should call the same quiz-session APIs as the web app:
  - `POST /quiz-sessions/start`
  - `GET /quiz-sessions/{session_id}/questions`
  - `POST /quiz-sessions/{session_id}/submit-answer`
  - `POST /quiz-sessions/{session_id}/finish`
- Send **`X-User-Id`** (user UUID) on every request. No file upload; all communication is JSON over HTTP.
- A detailed **Unity integration guide** (request/response shapes, flow) is in `docs/unity-integration-guide.md` if present.

## Notes

- **Server-side grading**: Correct answers are never exposed in question delivery; only submit-answer returns correctness and explanation.
- **Quiz generation**: One-time per lecture unless `force_regenerate=true` (and no existing quiz sessions).
- **Recommendations**: Order is deterministic and prerequisite-aware; the LLM helps phrase the wording.
- **Star jars**: Completed quiz sessions award stars and update the weekly jar; see `GET /users/{user_id}/star-jars`.
- **Demo users**: Seeded on backend startup via `backend/app/db/seed.py`.
