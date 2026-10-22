import { AI_SERVICE_API_URL } from "./apiConfig";

const STATUS_URL =
  `${AI_SERVICE_API_URL}/api/v1/status/services`;


export async function getServiceStatus() {
  const response = await fetch(
    STATUS_URL,
    {
      method: "GET",
    }
  );

  if (!response.ok) {
    throw new Error(
      "AI service is unavailable."
    );
  }

  return response.json();
}