import { AI_SERVICE_API_URL } from "./apiConfig";

// ------------------------------------------------------------
// Helper: fetch with retry on network errors and HTTP 5xx (502, 503, 504)
// Retries up to 2 times with delays 5s then 10s
// ------------------------------------------------------------
async function fetchWithRetry(url, options, attempt = 1) {
  const maxAttempts = 2;
  const delays = [5000, 10000];
  try {
    const response = await fetch(url, options);
    if (!response.ok && [502, 503, 504].includes(response.status) && attempt < maxAttempts) {
      await new Promise((r) => setTimeout(r, delays[attempt - 1]));
      return fetchWithRetry(url, options, attempt + 1);
    }
    return response;
  } catch (err) {
    // network error (e.g., DNS failure, connection refused)
    if (attempt < maxAttempts) {
      await new Promise((r) => setTimeout(r, delays[attempt - 1]));
      return fetchWithRetry(url, options, attempt + 1);
    }
    throw err;
  }
}

// ------------------------------------------------------------
// Fetch available LLM provider options from the backend
// ------------------------------------------------------------
export async function getOptions() {
  const response = await fetchWithRetry(`${AI_SERVICE_API_URL}/api/v1/llm/options`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    throw new Error("Failed to fetch LLM options");
  }
  return response.json();
}

// ------------------------------------------------------------
// Main exported function used by the frontend to send a chat message
// ------------------------------------------------------------
export async function sendMessage(message, conversationId) {
  const body = { message };
  if (conversationId) {
    body.conversation_id = conversationId;
  }
  // Include selected LLM provider if set in localStorage
  const provider = localStorage.getItem("selectedProvider");
  if (provider) {
    body.provider = provider;
  }
  const response = await fetchWithRetry(`${AI_SERVICE_API_URL}/api/v1/ai/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let errorMessage = "Failed to communicate with AI service.";
    try {
      const errorData = await response.json();
      if (errorData && errorData.detail) {
        errorMessage = typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      /* ignore parsing errors */
    }
    // Forward specific 429 messages (rate limit)
    // 4xx other than 429 are not retried and should be shown as-is
    throw new Error(errorMessage);
  }
  return response.json();
}
