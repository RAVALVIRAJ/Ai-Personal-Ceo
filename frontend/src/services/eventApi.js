import { BACKEND_API_URL } from "./apiConfig";

const EVENT_API_URL = `${BACKEND_API_URL}/api/v1/events`;


async function getErrorMessage(response, fallback) {
  try {
    const data = await response.json();
    return data.message || data.error || fallback;
  } catch {
    return fallback;
  }
}


export async function getEvents() {
  const response = await fetch(EVENT_API_URL);

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to load events."
      )
    );
  }

  return response.json();
}


export async function createEvent(eventData) {
  const payload = {
    title: eventData.title,
    description: eventData.description || null,
    eventDate: eventData.eventDate || null,
    startTime: eventData.startTime || null,
    endTime: eventData.endTime || null,
  };

  const response = await fetch(
    EVENT_API_URL,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to create event."
      )
    );
  }

  return response.json();
}


export async function updateEvent(
  eventId,
  eventData
) {
  const payload = {
    title: eventData.title,
    description: eventData.description || null,
    eventDate: eventData.eventDate || null,
    startTime: eventData.startTime || null,
    endTime: eventData.endTime || null,
  };

  const response = await fetch(
    `${EVENT_API_URL}/${eventId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        `Failed to update event ${eventId}.`
      )
    );
  }

  return response.json();
}


export async function deleteEvent(eventId) {
  const response = await fetch(
    `${EVENT_API_URL}/${eventId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        `Failed to delete event ${eventId}.`
      )
    );
  }

  return true;
}