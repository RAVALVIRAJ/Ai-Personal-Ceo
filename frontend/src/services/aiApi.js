import { AI_SERVICE_API_URL } from "./apiConfig";

const AI_API_URL = `${AI_SERVICE_API_URL}/api/v1/ai/chat`;

export async function sendMessage(message) {
  const response = await fetch(AI_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: message,
    }),
  });

  if (!response.ok) {
    let errorMessage = "Failed to communicate with AI service.";

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        errorMessage =
          typeof errorData.detail === "string"
            ? errorData.detail
            : JSON.stringify(errorData.detail);
      }
    } catch {
      // Ignore JSON parsing failure.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}