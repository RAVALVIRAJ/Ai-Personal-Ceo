# Deploy the LIVE application

The LIVE deployment uses Vercel for the React frontend, Render for the Spring
Boot and FastAPI services, and Neon for PostgreSQL. The frontend is static;
both API services must be deployed and reachable over HTTPS before chat and
dashboard features can work.

Use [`.env.live.example`](../.env.live.example) as a settings reference only.
It contains placeholders, not deployable credentials. Enter secrets directly
in the relevant hosting dashboard.

## 1. Create the Neon database

1. Create a Neon project and database.
2. In the connection details, select the **direct** (non-pooled) connection
   host for this application. Do not use the `-pooler` host.
3. Build the JDBC URL using the host and database name shown by Neon:

   ```text
   jdbc:postgresql://HOST/DATABASE?sslmode=require
   ```

   If the copied URL contains `channel_binding`, remove that parameter. Store
   the username and password separately in Render as `DB_USERNAME` and
   `DB_PASSWORD`; do not put credentials in `DB_URL`.
4. Keep the direct host, database name, username, password and URL available
   for the backend setup below.

## 2. Configure the Groq model

1. Create an API key in the Groq console. Treat it as a secret.
2. From Groq's current models page, choose a supported chat/completions model.
   Do not choose a guard, safeguard, or Whisper model.
3. Record the model identifier exactly as shown. Set it as `OPENAI_MODEL` in
   the AI service environment. The application uses Groq's OpenAI-compatible
   API; do not use a model name copied from an old example.

## 3. Deploy the backend on Render

Create a **Web Service** connected to this repository:

| Render setting | Value |
|---|---|
| Root Directory | `backend` |
| Runtime | Docker |
| Dockerfile Path | `./Dockerfile` |
| Health Check Path | `/actuator/health` |

Set these environment variables on the backend service:

| Variable | Value |
|---|---|
| `PORT` | Render supplies this value; do not override unless required by the service configuration. |
| `DB_URL` | The Neon direct JDBC URL from step 1. |
| `DB_USERNAME` | Neon database username. |
| `DB_PASSWORD` | Neon database password (**secret**). |
| `DB_POOL_SIZE` | `5` |
| `CORS_ORIGINS` | Exact production Vercel origin, for example `https://your-project.vercel.app`. |
| `APP_TIMEZONE` | `Asia/Kolkata` |
| `JPA_DDL_AUTO` | `update` (the backend currently uses Hibernate schema update). |
| `JPA_SHOW_SQL` | `false` |
| `REMINDERS_ENABLED` | `false` until SMTP has been configured. |
| `MANAGEMENT_HEALTH_MAIL_ENABLED` | `false` |

Leave the SMTP variables unset while reminders are disabled. If enabling email
reminders later, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`,
`SMTP_PASSWORD`, `SMTP_AUTH`, `SMTP_STARTTLS_ENABLE`, `REMINDER_EMAIL_FROM`,
and `REMINDER_EMAIL_TO` in Render. Keep passwords in the dashboard, not in
repository files.

Wait for Render to report the backend as healthy and note its public HTTPS
origin. Do not include `/api/v1` or a trailing slash when using it as a base
URL elsewhere.

## 4. Deploy the AI service on Render

Create a second **Web Service** from the same repository:

| Render setting | Value |
|---|---|
| Root Directory | `ai-service` |
| Runtime | Docker |
| Dockerfile Path | `./Dockerfile` |
| Health Check Path | `/api/v1/health` |

Set these variables on the AI service:

| Variable | Value |
|---|---|
| `PORT` | Render supplies this value. |
| `APP_MODE` | `live` |
| `BACKEND_URL` | Backend public HTTPS origin from step 3, without `/api/v1` or a trailing slash. |
| `CORS_ORIGINS` | Exact production Vercel origin; same value as on the backend. |
| `LLM_PROVIDER` | `openai` |
| `LLM_FALLBACK_PROVIDER` | Leave empty unless you deliberately configure and test a fallback. |
| `OPENAI_API_KEY` | Groq API key (**secret**). |
| `OPENAI_BASE_URL` | `https://api.groq.com/openai/v1` |
| `OPENAI_MODEL` | Current Groq chat model identifier from step 2. |
| `TIMEZONE` | `Asia/Kolkata` |
| `LLM_TIMEOUT_SECONDS` | `60` |
| `STATUS_TIMEOUT_SECONDS` | `20` |
| `RATE_LIMIT_PER_MINUTE` | `20` |

`OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_NUM_CTX`, and `OLLAMA_KEEP_ALIVE`
are local-provider settings and are not used for this LIVE configuration.
Wait for the AI service health check to pass and note its public HTTPS origin.

## 5. Deploy the frontend on Vercel

1. Import the repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Use the Vite build command `npm run build` and output directory `dist`.
   These are already set in `frontend/vercel.json`.
4. Add the following environment variables to the Vercel project for the
   production environment:

   | Variable | Value |
   |---|---|
   | `VITE_BACKEND_URL` | Backend origin only, e.g. `https://your-backend.onrender.com`. |
   | `VITE_AI_SERVICE_URL` | AI service origin only, e.g. `https://your-ai-service.onrender.com`. |

   Do not append `/api`, `/api/v1`, or a trailing slash.
5. If you use a custom Vercel domain, add its exact `https://` origin to
   `CORS_ORIGINS` on **both** Render services. Separate multiple origins with
   commas and no spaces.
6. Redeploy the Vercel project after adding or changing either `VITE_` value;
   Vite embeds them during the build.

The Vercel configuration retains the single-page-app rewrite and gives
content-hashed files in `/assets/` a one-year immutable cache. It intentionally
does not proxy API calls; the browser calls the configured Render origins.

## 6. Verify the deployment

Open these URLs, replacing the hostnames with the deployed service origins:

- `https://<backend-host>/actuator/health`
- `https://<ai-service-host>/api/v1/health`
- `https://<ai-service-host>/api/v1/status/services`
- `https://<ai-service-host>/api/v1/llm/options`

Then open the production Vercel URL and send a test chat message. The status
response should report the backend and Groq as online. A configured cloud
provider does not require Ollama to be running.

## Secrets and operations

- Never commit real environment files, database credentials, or API keys.
  `.env.live.example` is a placeholder reference; use Render and Vercel
  dashboards for actual values.
- To rotate the Groq key, create a replacement key, update `OPENAI_API_KEY` in
  the Render AI service, verify the deployment, then revoke the old key.
- To rotate the Neon password, update it in Neon and update `DB_PASSWORD` in
  Render. Confirm the backend reconnects and passes its health check.
- Free instances may sleep after inactivity and take around a minute to wake.
  The scheduler cannot send reminders while the backend is asleep. Free-tier
  hours/limits can be shared across a workspace and may change; confirm current
  plan details with the hosting providers.
- For a demo, open both health URLs about 15 minutes beforehand, send a test
  message, and present from the production Vercel URL.
- No `render.yaml` Blueprint is included; the deployment guide uses the Render
  dashboard instead of relying on unverified Blueprint field names.

## Troubleshooting

| Symptom | Check |
|---|---|
| Browser reports a CORS error | Set the exact Vercel origin in `CORS_ORIGINS` on both Render services. Include `https://`, omit the trailing slash, and redeploy/restart the services. |
| API returns Not Found | Check the Vercel `VITE_BACKEND_URL` and `VITE_AI_SERVICE_URL`. They must be service origins only, not include `/api/v1`; redeploy Vercel after corrections. |
| Backend or AI returns 500 | Read the relevant Render service logs. Check database connectivity/credentials, model configuration, and missing environment variables. Do not paste secrets into support logs or source files. |
| Groq reports an invalid model | Verify `OPENAI_MODEL` against Groq's current chat-model list; avoid guard, safeguard, or speech-to-text models. |
| Chat returns 429 | Wait before retrying; `RATE_LIMIT_PER_MINUTE` is an in-memory per-client limit on the AI service. |
| First request is slow | The free service may be waking from sleep. Allow up to about a minute, then retry. |

## Acceptance checklist

- [ ] Neon direct (non-pooled) database host is used.
- [ ] Backend health check passes at `/actuator/health`.
- [ ] AI service health check passes at `/api/v1/health`.
- [ ] Both Render services allow the exact production Vercel origin.
- [ ] AI status reports the backend and configured cloud LLM accurately.
- [ ] Vercel Root Directory is `frontend` and production build succeeds.
- [ ] Vercel API variables contain only the Render service origins.
- [ ] A test chat message succeeds from the production Vercel URL.
- [ ] No real secrets were added to the repository.
