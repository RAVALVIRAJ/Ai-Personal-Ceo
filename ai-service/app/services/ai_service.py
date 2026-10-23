from datetime import datetime, timedelta
import logging
import re

from fastapi import HTTPException
from app.core.config import settings
from app.providers import LLMProvider, get_provider

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    Intent,
    TaskData,
    EventData,
)

from app.services.backend_client import backend_client
from app.services.intent_service import intent_service
from app.services.extraction_service import (
    ExtractionService,
    get_timezone,
    resolve_date_and_time,
)

logger = logging.getLogger(__name__)


class AIService:

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.extraction_service = ExtractionService(provider=provider)

    # =========================================================
    # ID EXTRACTION
    # =========================================================

    def extract_task_id(self, text: str) -> int | None:
        """
        Extract task ID from messages such as:

        Complete task 17
        Complete Task #17
        finish task 25
        mark task 10 as done
        task 42
        """

        match = re.search(
            r"\btask\s*#?\s*(\d+)\b",
            text,
            re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

        return None

    def extract_event_id(self, text: str) -> int | None:
        """
        Extract event ID from messages such as:

        Reschedule event 12
        Reschedule event #12
        Delete event 5
        event 20
        """

        match = re.search(
            r"\bevent\s*#?\s*(\d+)\b",
            text,
            re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

        return None

    # =========================================================
    # HELPERS & FORMATTING
    # =========================================================

    def sort_tasks_by_time(
        self,
        tasks: list[dict],
    ) -> list[dict]:
        return sorted(
            tasks,
            key=lambda task: (
                task.get("dueTime") is None,
                task.get("dueTime") or "99:99:99",
                task.get("id") or 0,
            ),
        )

    def sort_events_by_time(
        self,
        events: list[dict],
    ) -> list[dict]:
        return sorted(
            events,
            key=lambda event: (
                event.get("startTime") is None,
                event.get("startTime") or "99:99:99",
                event.get("id") or 0,
            ),
        )

    def format_time(self, value):
        if not value:
            return "no time specified"

        value = str(value)

        # Convert 18:00:00 -> 18:00
        if len(value) >= 5:
            return value[:5]

        return value

    def format_task(self, task: dict) -> str:
        title = task.get("title") or "Untitled task"
        due_time = task.get("dueTime")
        duration = task.get("durationMinutes")
        status = task.get("status")

        parts = [title]

        if due_time:
            parts.append(f"at {self.format_time(due_time)}")
        else:
            parts.append("with no time specified")

        if duration:
            parts.append(f"for {duration} minutes")

        if status:
            parts.append(f"[{status}]")

        return " ".join(parts)

    def format_event(self, event: dict) -> str:
        title = event.get("title") or "Untitled event"

        start = event.get("startTime")
        end = event.get("endTime")

        if start and end:
            return (
                f"{title} "
                f"({self.format_time(start)} - {self.format_time(end)})"
            )

        if start:
            return f"{title} at {self.format_time(start)}"

        return title

    # =========================================================
    # MAIN MESSAGE PROCESSOR
    # =========================================================

    async def process_message(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        message = request.message
        provider = self.provider

        # -----------------------------------------------------
        # 0. PROVIDER OVERRIDE VALIDATION
        # -----------------------------------------------------
        # If the client specifies a provider, validate it against the
        # configured, usable providers and switch the service accordingly.
        # This must happen before any other intent handling.
        if request.provider:
            usable_providers: list[str] = []
            if settings.app_mode.lower() == "local":
                usable_providers.append("ollama")
            if settings.openai_api_key.strip():
                usable_providers.append("openai")
            if request.provider not in usable_providers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Provider '{request.provider}' is not configured or unavailable.",
                )
            provider = get_provider(request.provider)

        extraction_service = ExtractionService(provider=provider)

        lower = message.lower()

        # -----------------------------------------------------
        # 1. EXPLICIT ID COMMANDS & SCHEDULE QUERIES (REGEX PATH)
        # -----------------------------------------------------

        # =====================================================
        # COMPLETE TASK (e.g. "complete task 17")
        # =====================================================

        if self._looks_like_complete_task(lower):

            task_id = self.extract_task_id(message)

            if task_id is None:

                return ChatResponse(
                    intent=Intent.COMPLETE_TASK,
                    confidence=0.95,
                    message=(
                        "Please provide the task ID you want "
                        "to complete."
                    ),
                )

            completed_task = await backend_client.complete_task(
                task_id
            )

            # Backend returned an error
            if isinstance(completed_task, dict):

                error = completed_task.get("error")

                if error:

                    return ChatResponse(
                        intent=Intent.COMPLETE_TASK,
                        confidence=1.0,
                        message=error,
                        task_id=task_id,
                    )

            # Success
            return ChatResponse(
                intent=Intent.COMPLETE_TASK,
                confidence=1.0,
                message=(
                    f"Task {task_id} completed successfully."
                ),
                task_id=task_id,
            )

        # Analyze regex intent
        result = intent_service.analyze(message)

        # =====================================================
        # DELETE TASK (e.g. "delete task 17")
        # =====================================================

        if result.intent == Intent.DELETE_TASK:

            task_id = None

            if result.task is not None:
                task_id = result.task.task_id

            if task_id is None:
                task_id = self.extract_task_id(message)

            if task_id is None:

                return ChatResponse(
                    intent=Intent.DELETE_TASK,
                    confidence=result.confidence,
                    message=(
                        "Please provide the task ID you want "
                        "to delete."
                    ),
                )

            deleted_task = await backend_client.delete_task(
                task_id
            )

            # Backend error
            if isinstance(deleted_task, dict):

                error = deleted_task.get("error")

                if error:

                    return ChatResponse(
                        intent=Intent.DELETE_TASK,
                        confidence=result.confidence,
                        message=error,
                        task_id=task_id,
                    )

            return ChatResponse(
                intent=Intent.DELETE_TASK,
                confidence=result.confidence,
                message=(
                    f"Task {task_id} deleted successfully."
                ),
                task_id=task_id,
            )

        # =====================================================
        # UPDATE TASK (e.g. "update task 16 ...")
        # =====================================================

        if (
            result.intent == Intent.UPDATE_TASK
            and result.task is not None
        ):

            task = result.task
            task_id = task.task_id

            if task_id is None:
                task_id = self.extract_task_id(message)

            if task_id is None:

                return ChatResponse(
                    intent=Intent.UPDATE_TASK,
                    confidence=result.confidence,
                    message=(
                        "Please provide the task ID "
                        "you want to update."
                    ),
                )

            existing_task = await backend_client.get_task(
                task_id
            )

            if existing_task is None:

                return ChatResponse(
                    intent=Intent.UPDATE_TASK,
                    confidence=result.confidence,
                    message=f"Task {task_id} was not found.",
                    task_id=task_id,
                )

            updated_title = (
                task.title
                if task.title is not None
                else existing_task.get("title")
            )

            updated_description = existing_task.get(
                "description"
            )

            updated_date = (
                task.date
                if task.date is not None
                else existing_task.get("dueDate")
            )

            updated_time = (
                task.time
                if task.time is not None
                else existing_task.get("dueTime")
            )

            updated_duration = (
                task.duration_minutes
                if task.duration_minutes is not None
                else existing_task.get("durationMinutes")
            )

            if (
                task.title is None
                and task.date is None
                and task.time is None
                and task.duration_minutes is None
            ):

                return ChatResponse(
                    intent=Intent.UPDATE_TASK,
                    confidence=result.confidence,
                    message=(
                        f"What would you like to change "
                        f"about task {task_id}?"
                    ),
                    task_id=task_id,
                )

            updated_task = await backend_client.update_task(
                task_id=task_id,
                title=updated_title,
                description=updated_description,
                due_date=updated_date,
                due_time=updated_time,
                duration_minutes=updated_duration,
            )

            if (
                isinstance(updated_task, dict)
                and updated_task.get("error")
            ):

                return ChatResponse(
                    intent=Intent.UPDATE_TASK,
                    confidence=result.confidence,
                    message=updated_task["error"],
                    task_id=task_id,
                )

            return ChatResponse(
                intent=Intent.UPDATE_TASK,
                confidence=result.confidence,
                message=f"Task {task_id} updated successfully.",
                task=TaskData(
                    task_id=task_id,
                    title=updated_title,
                    date=updated_date,
                    time=(
                        str(updated_time)[:5]
                        if updated_time
                        else None
                    ),
                    duration_minutes=updated_duration,
                ),
                task_id=task_id,
            )

        # =====================================================
        # DELETE EVENT (e.g. "delete event 5")
        # =====================================================

        if result.intent == Intent.DELETE_EVENT:

            event_id = None

            if result.event is not None:
                event_id = result.event.event_id

            if event_id is None:
                event_id = self.extract_event_id(message)

            if event_id is None:

                return ChatResponse(
                    intent=Intent.DELETE_EVENT,
                    confidence=result.confidence,
                    message=(
                        "Please provide the event ID "
                        "you want to delete."
                    ),
                )

            existing_event = await backend_client.get_event(
                event_id
            )

            if existing_event is None:

                return ChatResponse(
                    intent=Intent.DELETE_EVENT,
                    confidence=result.confidence,
                    message=f"Event {event_id} was not found.",
                    event=EventData(
                        event_id=event_id,
                    ),
                )

            deleted_event = await backend_client.delete_event(
                event_id
            )

            if (
                isinstance(deleted_event, dict)
                and deleted_event.get("error")
            ):

                return ChatResponse(
                    intent=Intent.DELETE_EVENT,
                    confidence=result.confidence,
                    message=deleted_event["error"],
                    event=EventData(
                        event_id=event_id,
                    ),
                )

            return ChatResponse(
                intent=Intent.DELETE_EVENT,
                confidence=result.confidence,
                message=f"Event {event_id} deleted successfully.",
                event=EventData(
                    event_id=event_id,
                ),
            )

        # =====================================================
        # TODAY'S SCHEDULE
        # =====================================================

        if result.intent == Intent.TODAY_SCHEDULE:

            tasks = await backend_client.get_tasks()
            events = await backend_client.get_events()

            today = datetime.now(get_timezone()).date().isoformat()

            today_tasks = [
                task
                for task in tasks
                if (
                    task.get("dueDate") == today
                    and task.get("status") not in (
                        "COMPLETED",
                        "CANCELLED",
                    )
                )
            ]

            today_events = [
                event
                for event in events
                if event.get("eventDate") == today
            ]

            today_tasks = self.sort_tasks_by_time(
                today_tasks
            )

            today_events = self.sort_events_by_time(
                today_events
            )

            lines = [
                f"Schedule for {today}:",
                "",
                "Tasks:",
            ]

            if today_tasks:
                for task in today_tasks:
                    lines.append(
                        f"- {self.format_task(task)}"
                    )
            else:
                lines.append("- No tasks scheduled.")

            lines.extend([
                "",
                "Events:",
            ])

            if today_events:
                for event in today_events:
                    lines.append(
                        f"- {self.format_event(event)}"
                    )
            else:
                lines.append("- No events scheduled.")

            return ChatResponse(
                intent=Intent.TODAY_SCHEDULE,
                confidence=result.confidence,
                message="\n".join(lines),
            )

        # =====================================================
        # TOMORROW'S SCHEDULE
        # =====================================================

        if result.intent == Intent.TOMORROW_SCHEDULE:

            tasks = await backend_client.get_tasks()
            events = await backend_client.get_events()

            tomorrow = (
                datetime.now(get_timezone()).date()
                + timedelta(days=1)
            ).isoformat()

            tomorrow_tasks = [
                task
                for task in tasks
                if (
                    task.get("dueDate") == tomorrow
                    and task.get("status") not in (
                        "COMPLETED",
                        "CANCELLED",
                    )
                )
            ]

            tomorrow_events = [
                event
                for event in events
                if event.get("eventDate") == tomorrow
            ]

            tomorrow_tasks = self.sort_tasks_by_time(
                tomorrow_tasks
            )

            tomorrow_events = self.sort_events_by_time(
                tomorrow_events
            )

            lines = [
                f"Schedule for {tomorrow}:",
                "",
                "Tasks:",
            ]

            if tomorrow_tasks:
                for task in tomorrow_tasks:
                    lines.append(
                        f"- {self.format_task(task)}"
                    )
            else:
                lines.append("- No tasks scheduled.")

            lines.extend([
                "",
                "Events:",
            ])

            if tomorrow_events:
                for event in tomorrow_events:
                    lines.append(
                        f"- {self.format_event(event)}"
                    )
            else:
                lines.append("- No events scheduled.")

            return ChatResponse(
                intent=Intent.TOMORROW_SCHEDULE,
                confidence=result.confidence,
                message="\n".join(lines),
            )

        # =====================================================
        # WEEKLY SCHEDULE
        # =====================================================

        if result.intent == Intent.WEEKLY_SCHEDULE:

            tasks = await backend_client.get_tasks()
            events = await backend_client.get_events()

            today_date = datetime.now(get_timezone()).date()

            week_start = (
                today_date
                - timedelta(days=today_date.weekday())
            )

            week_end = week_start + timedelta(days=6)

            lines = [
                (
                    f"Schedule for {week_start.isoformat()} "
                    f"to {week_end.isoformat()}:"
                )
            ]

            anything_scheduled = False

            for offset in range(7):

                current_date = week_start + timedelta(days=offset)
                date_string = current_date.isoformat()

                day_tasks = [
                    task
                    for task in tasks
                    if (
                        task.get("dueDate") == date_string
                        and task.get("status") not in (
                            "COMPLETED",
                            "CANCELLED",
                        )
                    )
                ]

                day_events = [
                    event
                    for event in events
                    if event.get("eventDate") == date_string
                ]

                day_tasks = self.sort_tasks_by_time(
                    day_tasks
                )

                day_events = self.sort_events_by_time(
                    day_events
                )

                if not day_tasks and not day_events:
                    continue

                anything_scheduled = True

                lines.append("")
                lines.append(
                    f"{current_date.strftime('%A')} "
                    f"({date_string}):"
                )

                for task in day_tasks:
                    lines.append(
                        f"- Task: {self.format_task(task)}"
                    )

                for event in day_events:
                    lines.append(
                        f"- Event: {self.format_event(event)}"
                    )

            if not anything_scheduled:
                lines.append("")
                lines.append(
                    "No tasks or events scheduled this week."
                )

            return ChatResponse(
                intent=Intent.WEEKLY_SCHEDULE,
                confidence=result.confidence,
                message="\n".join(lines),
            )

        # =====================================================
        # DAILY PLANNING
        # =====================================================

        if result.intent == Intent.DAILY_PLANNING:

            tasks = await backend_client.get_tasks()
            events = await backend_client.get_events()

            today = datetime.now(get_timezone()).date().isoformat()

            today_tasks = [
                task
                for task in tasks
                if (
                    task.get("dueDate") == today
                    and task.get("status")
                    not in ("COMPLETED", "CANCELLED")
                )
            ]

            today_events = [
                event
                for event in events
                if event.get("eventDate") == today
            ]

            unique_tasks = []
            seen_task_ids = set()

            for task in today_tasks:

                task_id = task.get("id")

                if task_id in seen_task_ids:
                    continue

                seen_task_ids.add(task_id)
                unique_tasks.append(task)

            fixed_time_tasks = [
                task
                for task in unique_tasks
                if task.get("dueTime")
            ]

            flexible_tasks = [
                task
                for task in unique_tasks
                if not task.get("dueTime")
            ]

            fixed_time_tasks = self.sort_tasks_by_time(
                fixed_time_tasks
            )

            today_events = self.sort_events_by_time(
                today_events
            )

            timeline_items = []

            for task in fixed_time_tasks:
                timeline_items.append({
                    "type": "TASK",
                    "time": task.get("dueTime"),
                    "id": task.get("id") or 0,
                    "data": task,
                })

            for event in today_events:
                timeline_items.append({
                    "type": "EVENT",
                    "time": event.get("startTime"),
                    "id": event.get("id") or 0,
                    "data": event,
                })

            timeline_items.sort(
                key=lambda item: (
                    item.get("time") is None,
                    item.get("time") or "99:99:99",
                    item.get("id") or 0,
                )
            )

            if (
                not timeline_items
                and not flexible_tasks
            ):

                return ChatResponse(
                    intent=Intent.DAILY_PLANNING,
                    confidence=result.confidence,
                    message=(
                        f"You have no active tasks or events "
                        f"scheduled for today ({today})."
                    ),
                )

            focus_items = []

            for item in timeline_items:

                if item["type"] == "TASK":

                    task = item["data"]
                    title = task.get("title") or "Untitled task"
                    due_time = task.get("dueTime")

                    focus_items.append(
                        f"{title} at {self.format_time(due_time)}"
                    )

                else:

                    event = item["data"]
                    title = event.get("title") or "Untitled event"
                    start = event.get("startTime")

                    if start:
                        focus_items.append(
                            f"{title} at {self.format_time(start)}"
                        )
                    else:
                        focus_items.append(title)

            for task in flexible_tasks:

                title = task.get("title") or "Untitled task"
                duration = task.get("durationMinutes")

                if duration:
                    focus_items.append(
                        f"{title} ({duration} minutes, flexible)"
                    )
                else:
                    focus_items.append(
                        f"{title} (flexible)"
                    )

            lines = [
                "Today's focus:"
            ]

            for index, item in enumerate(
                focus_items[:3],
                start=1,
            ):
                lines.append(
                    f"{index}. {item}"
                )

            lines.extend([
                "",
                "Schedule:",
            ])

            if timeline_items:

                for item in timeline_items:

                    if item["type"] == "TASK":

                        task = item["data"]

                        title = task.get("title") or "Untitled task"
                        due_time = task.get("dueTime")
                        duration = task.get("durationMinutes")

                        line = (
                            f"- {self.format_time(due_time)} "
                            f"Task: {title}"
                        )

                        if duration:
                            line += f" ({duration} minutes)"

                        lines.append(line)

                    else:

                        event = item["data"]

                        title = event.get("title") or "Untitled event"
                        start = event.get("startTime")
                        end = event.get("endTime")

                        if start and end:
                            lines.append(
                                f"- {self.format_time(start)} "
                                f"Event: {title} "
                                f"({self.format_time(start)} - "
                                f"{self.format_time(end)})"
                            )

                        elif start:
                            lines.append(
                                f"- {self.format_time(start)} "
                                f"Event: {title}"
                            )

                        else:
                            lines.append(
                                f"- Event: {title}"
                            )

            else:
                lines.append(
                    "- No fixed-time tasks or events."
                )

            lines.extend([
                "",
                "Flexible work:",
            ])

            if flexible_tasks:

                for task in flexible_tasks:

                    title = task.get("title") or "Untitled task"
                    duration = task.get("durationMinutes")

                    if duration:

                        lines.append(
                            f"- {title} ({duration} minutes)"
                        )

                    else:

                        lines.append(
                            f"- {title}"
                        )

            else:

                lines.append(
                    "- No flexible tasks."
                )

            return ChatResponse(
                intent=Intent.DAILY_PLANNING,
                confidence=result.confidence,
                message="\n".join(lines),
            )

        # -----------------------------------------------------
        # 2. LLM EXTRACTION STEP FOR CREATE_TASK, CREATE_EVENT,
        #    RESCHEDULE_EVENT
        # -----------------------------------------------------

        extracted = await extraction_service.extract(message)

        if extracted is not None and extracted.intent:
            extracted_intent = extracted.intent.upper()

            # -------------------------------------------------
            # CREATE TASK via LLM
            # -------------------------------------------------
            if extracted_intent == Intent.CREATE_TASK.value:
                resolved_date, resolved_time, _ = resolve_date_and_time(
                    extracted.date_phrase,
                    extracted.time_phrase,
                    extracted.duration_minutes,
                )
                title = extracted.title or message

                created_task = await backend_client.create_task(
                    title=title,
                    description=None,
                    due_date=resolved_date,
                    due_time=resolved_time,
                    duration_minutes=extracted.duration_minutes,
                )

                if isinstance(created_task, dict) and created_task.get("error"):
                    return ChatResponse(
                        intent=Intent.CREATE_TASK,
                        confidence=1.0,
                        message=created_task["error"],
                    )

                created_task_id = None
                if isinstance(created_task, dict):
                    created_task_id = created_task.get("id")

                task_data = TaskData(
                    task_id=created_task_id,
                    title=title,
                    date=resolved_date,
                    time=resolved_time,
                    duration_minutes=extracted.duration_minutes,
                )

                return ChatResponse(
                    intent=Intent.CREATE_TASK,
                    confidence=0.95,
                    message=(
                        f"Task {created_task_id} created successfully."
                        if created_task_id
                        else "Task created successfully."
                    ),
                    task=task_data,
                    task_id=created_task_id,
                )

            # -------------------------------------------------
            # CREATE EVENT via LLM
            # -------------------------------------------------
            if extracted_intent == Intent.CREATE_EVENT.value:
                resolved_date, resolved_start, resolved_end = resolve_date_and_time(
                    extracted.date_phrase,
                    extracted.time_phrase,
                    extracted.duration_minutes,
                )
                if resolved_start and not resolved_end:
                    resolved_end = intent_service.calculate_end_time(
                        resolved_start,
                        extracted.duration_minutes or 60,
                    )

                title = extracted.title or message

                created_event = await backend_client.create_event(
                    title=title,
                    description=None,
                    event_date=resolved_date,
                    start_time=resolved_start,
                    end_time=resolved_end,
                )

                if isinstance(created_event, dict) and created_event.get("error"):
                    return ChatResponse(
                        intent=Intent.CREATE_EVENT,
                        confidence=1.0,
                        message=created_event["error"],
                    )

                event_id = None
                if isinstance(created_event, dict):
                    event_id = created_event.get("id")

                event_data = EventData(
                    event_id=event_id,
                    title=title,
                    date=resolved_date,
                    start_time=resolved_start,
                    end_time=resolved_end,
                )

                return ChatResponse(
                    intent=Intent.CREATE_EVENT,
                    confidence=0.95,
                    message="Event created successfully.",
                    event=event_data,
                )

            # -------------------------------------------------
            # RESCHEDULE EVENT via LLM
            # -------------------------------------------------
            if extracted_intent == Intent.RESCHEDULE_EVENT.value:
                event_id = self.extract_event_id(message)

                if event_id is None:
                    return ChatResponse(
                        intent=Intent.RESCHEDULE_EVENT,
                        confidence=0.90,
                        message="Please provide the event ID you want to reschedule.",
                        event=EventData(),
                    )

                resolved_date, resolved_start, resolved_end = resolve_date_and_time(
                    extracted.date_phrase,
                    extracted.time_phrase,
                    extracted.duration_minutes,
                )

                if resolved_date is None:
                    return ChatResponse(
                        intent=Intent.RESCHEDULE_EVENT,
                        confidence=0.90,
                        message="Please provide the new date for the event.",
                        event=EventData(event_id=event_id),
                    )

                if resolved_start is None:
                    return ChatResponse(
                        intent=Intent.RESCHEDULE_EVENT,
                        confidence=0.90,
                        message="Please provide the new start time for the event.",
                        event=EventData(event_id=event_id, date=resolved_date),
                    )

                existing_event = await backend_client.get_event(event_id)
                if existing_event is None:
                    return ChatResponse(
                        intent=Intent.RESCHEDULE_EVENT,
                        confidence=0.90,
                        message=f"Event {event_id} was not found.",
                        event=EventData(
                            event_id=event_id,
                            date=resolved_date,
                            start_time=resolved_start,
                        ),
                    )

                if not resolved_end:
                    resolved_end = intent_service.calculate_end_time(
                        resolved_start,
                        extracted.duration_minutes or 60,
                    )

                updated_event = await backend_client.update_event(
                    event_id=event_id,
                    title=existing_event.get(
                        "title",
                        extracted.title or "Event",
                    ),
                    description=existing_event.get("description"),
                    event_date=resolved_date,
                    start_time=resolved_start,
                    end_time=(
                        resolved_end
                        if resolved_end is not None
                        else existing_event.get("endTime")
                    ),
                )

                if isinstance(updated_event, dict) and updated_event.get("error"):
                    return ChatResponse(
                        intent=Intent.RESCHEDULE_EVENT,
                        confidence=1.0,
                        message=updated_event["error"],
                        event=EventData(
                            event_id=event_id,
                            date=resolved_date,
                            start_time=resolved_start,
                        ),
                    )

                return ChatResponse(
                    intent=Intent.RESCHEDULE_EVENT,
                    confidence=0.95,
                    message=f"Event {event_id} rescheduled successfully.",
                    event=EventData(
                        event_id=event_id,
                        title=existing_event.get("title"),
                        date=resolved_date,
                        start_time=resolved_start,
                        end_time=resolved_end or existing_event.get("endTime"),
                    ),
                )

            # -------------------------------------------------
            # GENERAL CHAT via LLM
            # -------------------------------------------------
            if extracted_intent == Intent.GENERAL_CHAT.value:
                llm_response = await provider.generate(message)
                return ChatResponse(
                    intent=Intent.GENERAL_CHAT,
                    confidence=0.85,
                    message=llm_response,
                )

        # -----------------------------------------------------
        # 3. REGEX FALLBACK
        # (Used when LLM extraction fails, times out, or returns None)
        # -----------------------------------------------------

        # =====================================================
        # CREATE TASK (REGEX FALLBACK)
        # =====================================================

        if (
            result.intent == Intent.CREATE_TASK
            and result.task is not None
        ):

            task = result.task
            title = task.title or message

            created_task = await backend_client.create_task(
                title=title,
                description=None,
                due_date=task.date,
                due_time=task.time,
                duration_minutes=task.duration_minutes,
            )

            created_task_id = None
            if isinstance(created_task, dict):
                created_task_id = created_task.get("id")

            task.task_id = created_task_id

            return ChatResponse(
                intent=Intent.CREATE_TASK,
                confidence=result.confidence,
                message=(
                    f"Task {created_task_id} "
                    "created successfully."
                ),
                task=task,
                task_id=created_task_id,
            )

        # =====================================================
        # CREATE EVENT (REGEX FALLBACK)
        # =====================================================

        if (
            result.intent == Intent.CREATE_EVENT
            and result.event is not None
        ):

            event = result.event

            created_event = await backend_client.create_event(
                title=event.title or message,
                description=None,
                event_date=event.date,
                start_time=event.start_time,
                end_time=event.end_time,
            )

            event_id = None
            if isinstance(created_event, dict):
                event_id = created_event.get("id")

            event.event_id = event_id

            return ChatResponse(
                intent=Intent.CREATE_EVENT,
                confidence=result.confidence,
                message="Event created successfully.",
                event=event,
            )

        # =====================================================
        # RESCHEDULE EVENT (REGEX FALLBACK)
        # =====================================================

        if result.intent == Intent.RESCHEDULE_EVENT:

            event = result.event

            if event is None:
                event = EventData()

            event_id = event.event_id

            if event_id is None:
                event_id = self.extract_event_id(message)

            if event_id is None:

                return ChatResponse(
                    intent=Intent.RESCHEDULE_EVENT,
                    confidence=result.confidence,
                    message=(
                        "Please provide the event ID "
                        "you want to reschedule."
                    ),
                    event=event,
                )

            event.event_id = event_id

            if event.date is None:

                return ChatResponse(
                    intent=Intent.RESCHEDULE_EVENT,
                    confidence=result.confidence,
                    message=(
                        "Please provide the new date "
                        "for the event."
                    ),
                    event=event,
                )

            if event.start_time is None:

                return ChatResponse(
                    intent=Intent.RESCHEDULE_EVENT,
                    confidence=result.confidence,
                    message=(
                        "Please provide the new start time "
                        "for the event."
                    ),
                    event=event,
                )

            existing_event = await backend_client.get_event(
                event_id
            )

            if existing_event is None:

                return ChatResponse(
                    intent=Intent.RESCHEDULE_EVENT,
                    confidence=result.confidence,
                    message=(
                        f"Event {event_id} was not found."
                    ),
                    event=event,
                )

            await backend_client.update_event(
                event_id=event_id,
                title=existing_event.get(
                    "title",
                    event.title or "Event",
                ),
                description=existing_event.get(
                    "description"
                ),
                event_date=event.date,
                start_time=event.start_time,
                end_time=(
                    event.end_time
                    if event.end_time is not None
                    else existing_event.get("endTime")
                ),
            )

            return ChatResponse(
                intent=Intent.RESCHEDULE_EVENT,
                confidence=result.confidence,
                message=(
                    f"Event {event_id} "
                    "rescheduled successfully."
                ),
                event=event,
            )

        # =====================================================
        # GENERAL CHAT (FALLBACK)
        # =====================================================

        if result.intent == Intent.GENERAL_CHAT:

            llm_response = await provider.generate(
                message
            )

            return ChatResponse(
                intent=Intent.GENERAL_CHAT,
                confidence=result.confidence,
                message=llm_response,
            )

        # =====================================================
        # UNKNOWN (FALLBACK)
        # =====================================================

        safe_prompt = f"""
        You are an AI Personal Manager.

        User message:
        "{message}"

        The system did NOT execute any task or event action.

        Rules:
        - Do not claim that you created, updated, deleted, completed,
        scheduled, or rescheduled anything.
        - Do not pretend an action succeeded.
        - If the user appears to be requesting an action that you
        cannot reliably identify, ask them to rephrase it.
        - You may answer normal informational questions.

        Respond concisely.
        """

        llm_response = await provider.generate(
            safe_prompt
        )

        return ChatResponse(
            intent=Intent.UNKNOWN,
            confidence=result.confidence,
            message=llm_response,
        )

    # =========================================================
    # COMPLETE TASK DETECTION
    # =========================================================

    def _looks_like_complete_task(
        self,
        lower: str,
    ) -> bool:
        """
        Detect explicit task-completion commands.

        Examples:

        complete task 17
        complete Task #17
        finish task 10
        mark task 5 as done
        mark task 5 completed
        done task 8
        """

        pattern = (
            r"\b"
            r"(?:complete|finish|done|mark)"
            r"\s+"
            r"(?:task|todo|to-do)"
            r"\s*#?\s*\d+"
            r"(?:"
            r"\s+(?:as\s+)?"
            r"(?:complete|completed|done)"
            r")?"
            r"\b"
        )

        return re.search(
            pattern,
            lower,
            re.IGNORECASE,
        ) is not None


# =============================================================
# AI SERVICE INSTANCE
# =============================================================

ai_service = AIService(
    provider=get_provider()
)
