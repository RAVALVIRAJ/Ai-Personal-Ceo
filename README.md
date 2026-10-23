# AI Personal CEO

AI Personal CEO is a chat-based personal assistant with a React frontend,
Spring Boot backend, FastAPI AI service, and PostgreSQL database.

## Run with Docker Compose

Requirements: Docker Desktop (or Docker Engine) with the Compose plugin.

1. Copy `.env.example` to `.env`.
2. Edit `.env` before deployment: change the local-default database password,
   and configure public frontend API URLs, an LLM provider, and SMTP settings
   as needed. Do not use the example credentials in production.
3. Build and start the services:

   ```powershell
   docker compose up --build
   ```

4. Open the frontend at <http://localhost:3000>.

The backend API is at <http://localhost:8080>, AI service at
<http://localhost:8000>, and PostgreSQL is published on port 5432 by default.
The database is persisted in the `postgres_data` Docker volume.

To stop the services, press Ctrl+C and run:

```powershell
docker compose down
```

To remove the database volume as well (this deletes its data):

```powershell
docker compose down --volumes
```

The Compose setup defaults to Ollama running on the host at port 11434. Install
and start Ollama separately and pull the configured model, or update `LLM_PROVIDER`
and the related settings in `.env` to use an OpenAI-compatible provider.
The backend reminder scheduler requires valid SMTP and recipient settings
(`SMTP_*`, `REMINDER_EMAIL_FROM`, and `REMINDER_EMAIL_TO`) to deliver email.

The backend currently uses Hibernate `ddl-auto=update`; first startup may update
the PostgreSQL schema to match the entities.

## Run services locally without Docker

Start PostgreSQL and configure `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`,
and `DB_PASSWORD` in the backend environment (defaults target local PostgreSQL).

Backend:

```powershell
cd backend
.\mvnw.cmd spring-boot:run
```

AI service (from a Python environment with `ai-service/requirements.txt`
installed):

```powershell
cd ai-service
uvicorn app.main:app --reload --port 8000
```

Frontend (from a Node.js environment):

```powershell
cd frontend
npm ci
npm run dev
```

The Vite development server is available at <http://localhost:5173>. API calls
are proxied to the backend and AI service by Vite. For custom deployments,
configure the API proxy or set `VITE_BACKEND_URL` and `VITE_AI_SERVICE_URL`.
The chat transcript is stored in browser local storage and restored when you
return to the chat or reload the page.

## Deploy the frontend to Vercel

Vercel can build and host the React/Vite frontend. The Spring Boot backend,
FastAPI AI service, and PostgreSQL database must be deployed separately to
services that support those runtimes and a persistent database. The frontend
needs publicly reachable HTTPS URLs for both APIs.

1. Import this repository into Vercel.
2. Set the Vercel project **Root Directory** to `frontend`.
3. Keep the detected Vite framework settings, with build command `npm run build`
   and output directory `dist` (also configured in `frontend/vercel.json`).
4. Add these environment variables in Vercel for each deployment environment:
   - `VITE_BACKEND_URL`: base URL of the deployed Spring Boot service, without
     an `/api/v1` suffix (for example, `https://backend.example.com`).
   - `VITE_AI_SERVICE_URL`: base URL of the deployed FastAPI service, without
     an `/api/v1` suffix (for example, `https://ai.example.com`).
5. Redeploy after setting or changing either variable; Vite embeds them during
   the build.
6. Set `CORS_ORIGINS` on both API services to include the exact Vercel frontend
   origin, such as `https://your-project.vercel.app`. On the backend this
   configures browser access to `/api/**`; on the AI service it configures
   FastAPI CORS. Include any Vercel custom domain origins you use.

Deploy and configure the API services before connecting the frontend. The AI
service also needs `BACKEND_URL` set to the deployed Spring Boot base URL, and
an available LLM provider configured with its required credentials. Do not use
localhost URLs for deployed services: they resolve to the visitor's device.

## Configuration

`.env.example` documents Compose settings. Copy it to `.env` and keep real
credentials out of version control. `CORS_ORIGINS` is a comma-separated list
of browser origins allowed by the AI service. Frontend API URL values are
embedded at image build time, so rebuild the frontend after changing them:

```powershell
docker compose build frontend
docker compose up -d frontend
```