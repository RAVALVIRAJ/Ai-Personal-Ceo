import {
  AI_SERVICE_API_URL,
  BACKEND_API_URL,
} from "./apiConfig";

const SPRING_API_URL = `${BACKEND_API_URL}/api/v1`;
const AI_API_URL = `${AI_SERVICE_API_URL}/api/v1/ai/chat`;


export async function getTasks() {
  const response = await fetch(
    `${SPRING_API_URL}/tasks`
  );

  if (!response.ok) {
    throw new Error("Failed to load tasks.");
  }

  return response.json();
}


export async function getEvents() {
  const response = await fetch(
    `${SPRING_API_URL}/events`
  );

  if (!response.ok) {
    throw new Error("Failed to load events.");
  }

  return response.json();
}


export async function getTodayFocus() {
  const response = await fetch(
    AI_API_URL,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        message: "What should I focus on today?",
      }),
    }
  );

  if (!response.ok) {
    throw new Error(
      "Failed to load today's AI plan."
    );
  }

  return response.json();
}