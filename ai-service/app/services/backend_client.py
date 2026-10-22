import httpx

from app.core.config import settings

SPRING_BOOT_URL = settings.backend_url.rstrip("/")


class BackendClient:

    # =========================================================
    # TASKS
    # =========================================================

    async def create_task(
        self,
        title: str,
        description: str | None = None,
        due_date: str | None = None,
        due_time: str | None = None,
        duration_minutes: int | None = None,
    ):
        payload = {
            "title": title,
            "description": description,
            "dueDate": due_date,
            "dueTime": due_time,
            "durationMinutes": duration_minutes,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{SPRING_BOOT_URL}/api/v1/tasks",
                json=payload,
            )

            response.raise_for_status()

            return response.json()

    # ---------------------------------------------------------
    # GET ALL TASKS
    # ---------------------------------------------------------

    async def get_tasks(self):

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{SPRING_BOOT_URL}/api/v1/tasks"
            )

            response.raise_for_status()

            return response.json()

    # ---------------------------------------------------------
    # GET SINGLE TASK
    # ---------------------------------------------------------

    async def get_task(self, task_id: int):

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.get(
                f"{SPRING_BOOT_URL}/api/v1/tasks/{task_id}"
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()

            return response.json()

    # ---------------------------------------------------------
    # COMPLETE TASK
    # ---------------------------------------------------------

    async def complete_task(self, task_id: int):

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.patch(
                f"{SPRING_BOOT_URL}/api/v1/tasks/{task_id}/complete"
            )

            if response.status_code == 404:
                return {
                    "error": f"Task not found: {task_id}"
                }

            response.raise_for_status()

            return response.json()

            # -------------------------------------------------
            # TASK NOT FOUND
            # -------------------------------------------------

            if response.status_code == 404:
                return {
                    "error": f"Task not found: {task_id}"
                }

            # -------------------------------------------------
            # BACKEND CURRENTLY RETURNS 500 FOR UNKNOWN TASK
            # -------------------------------------------------

            if response.status_code == 500:

                try:
                    error_data = response.json()

                    message = error_data.get("message")

                    if message:
                        return {
                            "error": message
                        }

                except Exception:
                    pass

                return {
                    "error": f"Task not found: {task_id}"
                }

            # -------------------------------------------------
            # OTHER HTTP ERRORS
            # -------------------------------------------------

            if response.status_code >= 400:

                try:
                    error_data = response.json()

                    return {
                        "error": error_data.get(
                            "message",
                            f"Unable to complete task {task_id}"
                        )
                    }

                except Exception:

                    return {
                        "error": f"Unable to complete task {task_id}"
                    }

            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            return response.json()

    # ---------------------------------------------------------
    # UPDATE TASK
    # ---------------------------------------------------------

    async def update_task(
        self,
        task_id: int,
        title: str,
        description: str | None = None,
        due_date: str | None = None,
        due_time: str | None = None,
        duration_minutes: int | None = None,
    ):

        payload = {
            "title": title,
            "description": description,
            "dueDate": due_date,
            "dueTime": due_time,
            "durationMinutes": duration_minutes,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.put(
                f"{SPRING_BOOT_URL}/api/v1/tasks/{task_id}",
                json=payload,
            )

            if response.status_code == 404:
                return {
                    "error": f"Task not found: {task_id}"
                }

            response.raise_for_status()

            return response.json()

    # ---------------------------------------------------------
    # DELETE TASK
    # ---------------------------------------------------------

    async def delete_task(self, task_id: int):

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.delete(
                f"{SPRING_BOOT_URL}/api/v1/tasks/{task_id}"
            )

            if response.status_code == 404:
                return {
                    "error": f"Task not found: {task_id}"
                }

            response.raise_for_status()

            return True

    # ---------------------------------------------------------
    # TODAY'S TASKS
    # ---------------------------------------------------------

    async def get_today_tasks(self):

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.get(
                f"{SPRING_BOOT_URL}/api/v1/tasks/today"
            )

            response.raise_for_status()

            return response.json()

    # ---------------------------------------------------------
    # TOMORROW'S TASKS
    # ---------------------------------------------------------

    async def get_tomorrow_tasks(self):

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.get(
                f"{SPRING_BOOT_URL}/api/v1/tasks/tomorrow"
            )

            response.raise_for_status()

            return response.json()

    # ---------------------------------------------------------
    # WEEK'S TASKS
    # ---------------------------------------------------------

    async def get_week_tasks(self):

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.get(
                f"{SPRING_BOOT_URL}/api/v1/tasks/week"
            )

            response.raise_for_status()

            return response.json()

    # =========================================================
    # EVENTS
    # =========================================================

    # ---------------------------------------------------------
    # CREATE EVENT
    # ---------------------------------------------------------

    async def create_event(
        self,
        title: str,
        description: str | None = None,
        event_date: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ):

        payload = {
            "title": title,
            "description": description,
            "eventDate": event_date,
            "startTime": start_time,
            "endTime": end_time,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.post(
                f"{SPRING_BOOT_URL}/api/v1/events",
                json=payload,
            )

            response.raise_for_status()

            return response.json()

    # ---------------------------------------------------------
    # GET ALL EVENTS
    # ---------------------------------------------------------

    async def get_events(self):

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.get(
                f"{SPRING_BOOT_URL}/api/v1/events"
            )

            response.raise_for_status()

            return response.json()

    # ---------------------------------------------------------
    # GET SINGLE EVENT
    # ---------------------------------------------------------

    async def get_event(self, event_id: int):

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.get(
                f"{SPRING_BOOT_URL}/api/v1/events/{event_id}"
            )

            if response.status_code == 404:
                return None

            response.raise_for_status()

            return response.json()

    # ---------------------------------------------------------
    # UPDATE EVENT
    # ---------------------------------------------------------

    async def update_event(
        self,
        event_id: int,
        title: str,
        description: str | None = None,
        event_date: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ):

        payload = {
            "title": title,
            "description": description,
            "eventDate": event_date,
            "startTime": start_time,
            "endTime": end_time,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.put(
                f"{SPRING_BOOT_URL}/api/v1/events/{event_id}",
                json=payload,
            )

            if response.status_code == 404:
                return {
                    "error": f"Event not found: {event_id}"
                }

            response.raise_for_status()

            return response.json()

    # ---------------------------------------------------------
    # DELETE EVENT
    # ---------------------------------------------------------

    async def delete_event(self, event_id: int):

        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.delete(
                f"{SPRING_BOOT_URL}/api/v1/events/{event_id}"
            )

            if response.status_code == 404:
                return {
                    "error": f"Event not found: {event_id}"
                }

            response.raise_for_status()

            return True


# =============================================================
# SINGLE BACKEND CLIENT INSTANCE
# =============================================================

backend_client = BackendClient()