# AI Personal CEO

Chat-based personal assistant. The user types natural language ("remind me to
submit the report next Friday at 5pm"); the system turns it into tasks and
events stored in PostgreSQL and shown in a React dashboard.

## ONE codebase, TWO run modes

The same code runs in two modes. The UI must look and behave the same in both.
Only configuration (environment variables) differs. Never fork the code.

| | LIVE mode (website) | LOCAL mode (laptop) |
|---|---|---|
| Frontend | Vercel (static build) | nginx container, or `npm run dev` |
| Backend | Render (Docker) | Docker Compose, or `mvnw spring-boot:run` |
| AI service | Render (Docker) | Docker Compose, or `uvicorn` |
| Database | Neon Postgres | Postgres container, or local Postgres |
| LLM | Groq (`LLM_PROVIDER=openai`, OpenAI-compatible) | Ollama on the host (`LLM_PROVIDER=ollama`) |
| API URLs | `VITE_BACKEND_URL`, `VITE_AI_SERVICE_URL` = Render hosts | empty (relative URLs, same origin via nginx/Vite proxy) |
| Hosting quirks | Free instances sleep (about 1 min cold start), 512 MB RAM, UTC clock | Always on, no internet needed |

`APP_MODE=live|local` (AI service env) is only a label shown in the UI. It must
never change behavior.

## Architecture (3 services)

| Service | Path | Tech | Port |
|---|---|---|---|
| Frontend | `frontend/` | React + Vite | 5173 (dev) / 80 (nginx) |
| Backend | `backend/` | Spring Boot (Java), JPA, PostgreSQL | 8080 |
| AI service | `ai-service/` | Python FastAPI, httpx, pydantic v2 | 8000 |

Flow: React -> `POST {AI}/api/v1/ai/chat` -> AI service extracts intent with
the LLM (and regex for explicit ID commands) -> calls the backend REST API ->
reply returns to React. React also calls the backend directly for the
Tasks, Events, Schedule and Dashboard pages.

## Key files

- `ai-service/app/services/ai_service.py`: message router (`process_message`).
- `ai-service/app/services/extraction_service.py`: LLM JSON extraction.
- `ai-service/app/services/intent_service.py`: regex intent/date/time rules.
- `ai-service/app/services/conversation_service.py`: multi-turn state
  (`conversation_id`) for missing-field follow-ups.
- `ai-service/app/providers/`: `ollama.py`, `openai_provider.py`, `mock.py`,
  and the `get_provider()` factory in `__init__.py`.
- `ai-service/app/routers/status.py`: `GET /api/v1/status/services`.
- `ai-service/app/core/config.py`: pydantic-settings, reads env / `.env`.
- Backend REST: `/api/v1/tasks` (CRUD, `/{id}/complete`, `/today`,
  `/tomorrow`, `/week`) and `/api/v1/events`.
- Backend reminders: `TaskReminderScheduler` (every minute, Asia/Kolkata),
  `TaskReminderService` (email via Spring Mail), `Task.reminderBeforeMinutes`
  and `Task.notified`.
- Frontend: `src/pages/ChatPage.jsx`, `src/services/*Api.js`,
  `src/services/apiConfig.js`, `src/components/Sidebar.jsx` (status panel).
- Deployment files: `docker-compose.yml`, `frontend/vercel.json`,
  `frontend/nginx.conf`, `*/Dockerfile`, `.env.example`.

## Rules (apply in BOTH modes)

- Timezone is Asia/Kolkata everywhere, including on hosts whose clock is UTC.
  Never use `LocalDate.now()`, `LocalDateTime.now()` or `date.today()` without
  an explicit zone.
- Never guess missing information. Ask a follow-up question instead.
- Do not claim an action succeeded unless the backend call succeeded.
- LLM output is untrusted. Validate it before using it. If the LLM fails,
  return a polite message, never a raw 500.
- No hard-coded URLs, model names, ports or credentials. Everything comes from
  environment variables with safe local defaults.
- Never commit secrets. Only `*.example` env files go in Git.
- Existing explicit commands (`complete task 17`, `delete event 5`) must keep
  working.
- Do not change the database schema without telling me first
  (`ddl-auto=update` is on).
- Make small, reviewable changes. Before editing, show a plan listing the
  files you will touch. After editing, list changed files and how to test.
- Do not rewrite working code or reformat unrelated files.

## How to run

- LOCAL (Docker): `docker compose --env-file .env.local up --build`, with
  Ollama running on the host (`ollama serve`).
- LOCAL (dev): three terminals, one each for `ai-service` (`uvicorn`),
  `backend` (`./mvnw spring-boot:run`) and `frontend` (`npm run dev`).
- LIVE: see `docs/DEPLOY_LIVE.md`.
