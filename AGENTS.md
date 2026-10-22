# AI Personal CEO

Chat-based personal assistant. The user types natural language ("remind me to
submit the report next Friday at 5pm"); the system turns it into tasks and
events stored in PostgreSQL and shown in a React dashboard.

## Architecture (3 services)

| Service | Path | Tech | Port |
|---|---|---|---|
| Frontend | `frontend/` | React + Vite, plain CSS | 5173 |
| Backend | `backend/` | Spring Boot (Java), Spring Data JPA, PostgreSQL | 8080 |
| AI service | `ai-service/` | Python FastAPI, httpx, pydantic v2 | 8000 |

Flow: React -> `POST /api/v1/ai/chat` (AI service) -> AI service calls the
backend REST API (`app/services/backend_client.py`) to create/update/list
tasks and events -> reply goes back to React.

## Key files

- `ai-service/app/services/ai_service.py`: main message router (`process_message`).
- `ai-service/app/services/intent_service.py`: CURRENT intent/date/time/title
  extraction. It is regex-based, and `extract_date` only knows
  today / tomorrow / day after tomorrow.
- `ai-service/app/providers/`: `base.py` (LLMProvider), `ollama.py`,
  `openai_provider.py`, `mock.py`. The provider is currently hard-coded at the
  bottom of `ai_service.py` (Ollama, `llama3.2:3b`).
- `ai-service/app/schemas/chat.py`: `Intent` enum, `ChatRequest`,
  `TaskData`, `EventData`, `ChatResponse`.
- `ai-service/app/core/config.py`: pydantic-settings, reads `.env`.
- Backend REST: `/api/v1/tasks` (CRUD, `/{id}/complete`, `/today`,
  `/tomorrow`, `/week`) and `/api/v1/events` (CRUD).
- Entities: `Task(title, description, dueDate, dueTime, durationMinutes,
  status)` and `Event(title, description, eventDate, startTime, endTime)`.
- Frontend chat: `frontend/src/pages/ChatPage.jsx`, `services/aiApi.js`.

## Conventions and rules

- Timezone is Asia/Kolkata. Never use `date.today()` or naive datetimes;
  use `datetime.now(ZoneInfo("Asia/Kolkata"))`.
- Never guess missing information. Ask a follow-up question instead.
- Do not claim an action succeeded unless the backend call succeeded.
- LLM output is untrusted. Validate it with pydantic before using it.
- Keep the LLM provider configurable through `.env` / `config.py`
  (`LLM_PROVIDER=ollama|openai|mock`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`).
  No hard-coded URLs or model names.
- Existing explicit commands (`complete task 17`, `delete event 5`) must keep
  working exactly as they do now.
- Do not change the database schema without telling me first.
  `ddl-auto=update` is on, so entity edits alter tables.
- Never commit secrets. `.env` and `application.properties` credentials should
  come from environment variables.
- Make small, reviewable changes. Before editing, show a plan listing the
  files you will touch. After editing, list changed files and how to test.
- Do not rewrite working code or reformat unrelated files.

## How to run

- AI service: `cd ai-service && uvicorn app.main:app --reload --port 8000`
- Backend: `cd backend && ./mvnw spring-boot:run`
- Frontend: `cd frontend && npm install && npm run dev`
- Ollama must be running locally (`ollama serve`) with the model pulled.

## Known gaps (not bugs to silently "fix")

- No recurrence, no reminder offsets, no alert firing yet.
- `README.md`, `docker-compose.yml`, `routes/scheduling.py`,
  `routes/suggestions.py` and `clients/backend_client.py` are empty files.
- `ChatRequest` only has `message`; there is no conversation state yet.
