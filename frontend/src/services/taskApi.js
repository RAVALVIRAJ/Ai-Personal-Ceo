import { BACKEND_API_URL } from "./apiConfig";

const TASK_API_URL = `${BACKEND_API_URL}/api/v1/tasks`;


async function getErrorMessage(response, fallback) {
  try {
    const data = await response.json();
    return data.message || data.error || fallback;
  } catch {
    return fallback;
  }
}


export async function getTasks() {
  const response = await fetch(TASK_API_URL);

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to load tasks."
      )
    );
  }

  return response.json();
}


export async function completeTask(taskId) {
  const response = await fetch(
    `${TASK_API_URL}/${taskId}/complete`,
    {
      method: "PATCH",
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        `Failed to complete task ${taskId}.`
      )
    );
  }

  return response.json();
}


export async function deleteTask(taskId) {
  const response = await fetch(
    `${TASK_API_URL}/${taskId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        `Failed to delete task ${taskId}.`
      )
    );
  }

  return true;
}
export async function createTask(taskData) {
  const payload = {
    title: taskData.title,
    description:
      taskData.description || null,
    dueDate:
      taskData.dueDate || null,
    dueTime:
      taskData.dueTime || null,
    durationMinutes:
      taskData.durationMinutes !== ""
        ? Number(
            taskData.durationMinutes
          )
        : null,
    reminderBeforeMinutes:
      taskData.reminderBeforeMinutes !== ""
        ? Number(taskData.reminderBeforeMinutes)
        : null,
    recurrence: taskData.recurrence || "NONE",
  };

  const response = await fetch(
    TASK_API_URL,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify(
        payload
      ),
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to create task."
      )
    );
  }

  return response.json();
}
export async function updateTask(taskId, taskData) {
  const payload = {
    title: taskData.title,
    description: taskData.description || null,
    dueDate: taskData.dueDate || null,
    dueTime: taskData.dueTime || null,
    durationMinutes:
      taskData.durationMinutes !== ""
        ? Number(taskData.durationMinutes)
        : null,
    reminderBeforeMinutes:
      taskData.reminderBeforeMinutes !== ""
        ? Number(taskData.reminderBeforeMinutes)
        : null,
    recurrence: taskData.recurrence || "NONE",
  };

  const response = await fetch(
    `${TASK_API_URL}/${taskId}`,
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
        `Failed to update task ${taskId}.`
      )
    );
  }

  return response.json();
}
