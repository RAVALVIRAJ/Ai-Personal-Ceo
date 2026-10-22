import re
from datetime import date, datetime, timedelta

from app.schemas.chat import (
    ChatResponse,
    EventData,
    Intent,
    TaskData,
)


class IntentService:

    def analyze(self, message: str) -> ChatResponse:
        text = message.strip()
        lower = text.lower()

        # =========================================================
        # DELETE EVENT
        # =========================================================

        delete_event_match = re.search(
            r"\b(?:delete|remove|cancel)\s+"
            r"(?:the\s+)?event\s*#?\s*(\d+)\b",
            lower,
            re.IGNORECASE,
        )

        if delete_event_match:

            event_id = int(delete_event_match.group(1))

            return ChatResponse(
                intent=Intent.DELETE_EVENT,
                confidence=0.95,
                message="I understood this as a request to delete an event.",
                event=EventData(
                    event_id=event_id,
                ),
            )
        delete_event_without_id = re.search(
            r"\b(?:delete|remove|cancel)\s+"
            r"(?:the\s+)?event\b",
            lower,
            re.IGNORECASE,
        )

        if delete_event_without_id:

            return ChatResponse(
                intent=Intent.DELETE_EVENT,
                confidence=0.90,
                message="Please provide the event ID you want to delete.",
                event=EventData(),
            )

        # -------------------------
        # TODAY'S SCHEDULE
        # -------------------------
        if (
            "what do i have today" in lower
            or "what's on my schedule today" in lower
            or "what is on my schedule today" in lower
            or "show me today's tasks" in lower
            or "show me todays tasks" in lower
            or "what are my tasks today" in lower
            or "do i have anything today" in lower
        ):
            return ChatResponse(
                intent=Intent.TODAY_SCHEDULE,
                confidence=0.95,
                message="I'll check your schedule for today.",
            )

        # -------------------------
        # TOMORROW'S SCHEDULE
        # -------------------------
        if (
            "what do i have tomorrow" in lower
            or "what's on my schedule tomorrow" in lower
            or "what is on my schedule tomorrow" in lower
            or "show me tomorrow's tasks" in lower
            or "show me tomorrows tasks" in lower
            or "what are my tasks tomorrow" in lower
            or "do i have anything tomorrow" in lower
        ):
            return ChatResponse(
                intent=Intent.TOMORROW_SCHEDULE,
                confidence=0.95,
                message="I'll check your schedule for tomorrow.",
            )


        # -------------------------
        # WEEKLY SCHEDULE
        # -------------------------
        if (
            "what do i have this week" in lower
            or "what's on my schedule this week" in lower
            or "what is on my schedule this week" in lower
            or "show me this week's schedule" in lower
            or "show me this weeks schedule" in lower
            or "show me my schedule this week" in lower
            or "what are my tasks this week" in lower
        ):
            return ChatResponse(
                intent=Intent.WEEKLY_SCHEDULE,
                confidence=0.95,
                message="I'll check your schedule for this week.",
            )

        # -------------------------
        # DAILY PLANNING
        # -------------------------
        if (
            "what should i do today" in lower
            or "what should i focus on today" in lower
            or "plan my day" in lower
        ):
            return ChatResponse(
                intent=Intent.DAILY_PLANNING,
                confidence=0.95,
                message="I can help you plan your day.",
            )

        # -------------------------
        # COMPLETE TASK
        # -------------------------

        complete_match = re.search(
            r"\b(complete|finish|done|mark)\b.*\b(task|todo|to-do)\b",
            lower,
            re.IGNORECASE,
        )

        if complete_match:

            task_id = self.extract_task_id(text)

            if task_id is not None:
                return ChatResponse(
                    intent=Intent.COMPLETE_TASK,
                    confidence=0.95,
                    message="I understood this as a request to complete a task.",
                    task=TaskData(
                        task_id=task_id,
                    ),
                )

            return ChatResponse(
                intent=Intent.COMPLETE_TASK,
                confidence=0.90,
                message="Please provide the task ID you want to complete.",
                task=TaskData(),
            )
        # -------------------------
        # DELETE TASK
        # -------------------------
        delete_match = re.search(
            r"\b(delete|remove|cancel)\b.*\b(task|todo|to-do)\b"
            r"|\b(delete|remove|cancel)\s+my\s+(task|todo|to-do)\b",
            lower,
            re.IGNORECASE,
        )

        if delete_match:
            task_id = self.extract_task_id(text)

            if task_id is not None:
                return ChatResponse(
                    intent=Intent.DELETE_TASK,
                    confidence=0.95,
                    message="I understood this as a request to delete a task.",
                    task=TaskData(
                        task_id=task_id,
                    ),
                )

            return ChatResponse(
                intent=Intent.DELETE_TASK,
                confidence=0.90,
                message="Please provide the task ID you want to delete.",
                task=TaskData(),
            )

        # -------------------------
        # RESCHEDULE
        # -------------------------
        if (
            "reschedule" in lower
            or "move my" in lower
            or "change my" in lower
        ):
            event_id = self.extract_event_id(text)
            event_date = self.extract_date(lower)
            start_time = self.extract_time(lower)

            return ChatResponse(
                intent=Intent.RESCHEDULE_EVENT,
                confidence=0.90,
                message="I understood this as a request to reschedule an event.",
                event=EventData(
                    event_id=event_id,
                    date=event_date,
                    start_time=start_time,
                    end_time=self.calculate_end_time(
                        start_time,
                        60
                    ),
                ),
            )

        # -------------------------
        # EVENT
        # -------------------------
        if (
            "meeting" in lower
            or "appointment" in lower
            or "schedule a" in lower
        ):
            event_title = self.extract_event_title(text)

            return ChatResponse(
                intent=Intent.CREATE_EVENT,
                confidence=0.90,
                message="I understood this as a request to create an event.",
                event=EventData(
                    title=event_title,
                    date=self.extract_date(lower),
                    start_time=self.extract_time(lower),
                    end_time=self.calculate_end_time(
                        self.extract_time(lower),
                        60,
                    ),
                ),
            )

        # =========================================================
        # UPDATE / RESCHEDULE TASK
        # =========================================================

        update_task_match = re.search(
            r"\b(?:move|reschedule|postpone|change|update|rename)\b"
            r".*\btask\s*#?\s*(\d+)\b",
            lower,
            re.IGNORECASE,
        )

        if update_task_match:

            task_id = int(update_task_match.group(1))

            new_date = self.extract_date(text)
            new_time = self.extract_time(text)
            new_duration = self.extract_duration(text)

            new_title = self.extract_updated_task_title(text)

            return ChatResponse(
                intent=Intent.UPDATE_TASK,
                confidence=0.95,
                message="I understood this as a task update.",
                task=TaskData(
                    task_id=task_id,
                    title=new_title,
                    date=new_date,
                    time=new_time,
                    duration_minutes=new_duration,
                ),
            )

        # -------------------------
        # TASK
        # -------------------------
        if (
            "study" in lower
            or "task" in lower
            or "remind me" in lower
            or "todo" in lower
            or "to-do" in lower
            or "work on" in lower
            or "finish" in lower
        ):
            task_title = self.extract_task_title(text)

            return ChatResponse(
                intent=Intent.CREATE_TASK,
                confidence=0.95,
                message="I understood this as a task creation request.",
                task=TaskData(
                    title=task_title,
                    date=self.extract_date(lower),
                    time=self.extract_time(lower),
                    duration_minutes=self.extract_duration(lower),
                ),
            )

        # =========================================================
        # CREATE EVENT
        # =========================================================

        create_event_match = re.search(
            r"\b(?:create|add|schedule|set|make)\b"
            r".*\b(?:event|meeting|appointment)\b",
            lower,
            re.IGNORECASE,
        )

        if create_event_match:

            event_date = self.extract_date(text)
            start_time = self.extract_time(text)
            duration_minutes = self.extract_duration(text)

            end_time = None

            if start_time and duration_minutes:
                end_time = self.calculate_end_time(
                    start_time,
                    duration_minutes,
                )

            event_title = self.extract_event_title(text)

            return ChatResponse(
                intent=Intent.CREATE_EVENT,
                confidence=0.90,
                message="I understood this as a request to create an event.",
                event=EventData(
                    title=event_title,
                    date=event_date,
                    start_time=start_time,
                    end_time=end_time,
                ),
            )

        # -------------------------
        # GENERAL CHAT
        # -------------------------
        if (
            "hello" in lower
            or "hi" in lower
            or "help" in lower
            or "how are you" in lower
        ):
            return ChatResponse(
                intent=Intent.GENERAL_CHAT,
                confidence=0.80,
                message="I'm ready to help you manage your tasks, schedule, and goals.",
            )

        # -------------------------
        # UNKNOWN
        # -------------------------
        return ChatResponse(
            intent=Intent.UNKNOWN,
            confidence=0.40,
            message="I'm not sure what action you want me to perform.",
        )

    # =========================================================
    # EXTRACTION HELPERS
    # =========================================================

    def extract_updated_task_title(
        self,
        text: str,
    ) -> str | None:

        lower = text.lower().strip()

        # ---------------------------------------------------------
        # Explicit title / rename forms
        #
        # Rename task 16 to Study Spring Boot
        # Change task 16 title to Study Java
        # Update task 16 title to Python revision
        # ---------------------------------------------------------

        match = re.search(
            r"\b(?:rename|change|update)\s+"
            r"task\s*#?\s*\d+\s+"
            r"(?:title\s+)?(?:to|as)\s+(.+)$",
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        candidate = match.group(1).strip()

        # ---------------------------------------------------------
        # Don't mistake rescheduling information for a new title
        #
        # Change task 16 to tomorrow at 6 PM
        # ---------------------------------------------------------

        candidate_lower = candidate.lower()

        date_words = (
            "today",
            "tomorrow",
            "day after tomorrow",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        )

        if candidate_lower.startswith(date_words):
            return None

        # Starts directly with a time:
        # "6 PM", "18:00", etc.
        if re.match(
            r"^\d{1,2}(?::\d{2})?\s*(?:am|pm)?$",
            candidate_lower,
            re.IGNORECASE,
        ):
            return None

        # Looks like a duration rather than a title.
        if re.match(
            r"^\d+\s*(?:minute|minutes|hour|hours)$",
            candidate_lower,
            re.IGNORECASE,
        ):
            return None

        # Clean trailing punctuation.
        candidate = candidate.strip(" .,!")

        if not candidate:
            return None

        return candidate

    def extract_task_id(self, text: str) -> int | None:

        match = re.search(
            r"\b(?:task|todo|to-do)\s*#?\s*(\d+)\b",
            text,
            re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

        return None
    def extract_event_id(self, text: str) -> int | None:

        match = re.search(
            r"\b(?:event|appointment|meeting)\s*#?\s*(\d+)\b",
            text,
            re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

        return None
    def extract_duration(self, text: str) -> int | None:

        number_words = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }

        # Numeric hours: 2 hours, 1.5 hours
        match = re.search(
            r"(\d+(?:\.\d+)?)\s*(hours?|hrs?|h)\b",
            text,
            re.IGNORECASE,
        )

        if match:
            hours = float(match.group(1))
            return int(hours * 60)

        # Written hours: two hours, three hours
        for word, value in number_words.items():
            pattern = rf"\b{word}\s*(hours?|hrs?|h)\b"

            if re.search(pattern, text, re.IGNORECASE):
                return value * 60

        # Numeric minutes: 45 minutes
        match = re.search(
            r"(\d+)\s*(minutes?|mins?|m)\b",
            text,
            re.IGNORECASE,
        )

        if match:
            return int(match.group(1))

        # Written minutes: thirty minutes etc.
        minute_words = {
            "one": 1,
            "two": 2,
            "three": 3,
            "five": 5,
            "ten": 10,
            "fifteen": 15,
            "twenty": 20,
            "thirty": 30,
            "forty": 40,
            "forty-five": 45,
            "sixty": 60,
        }

        for word, value in minute_words.items():
            pattern = rf"\b{word}\s*(minutes?|mins?|m)\b"

            if re.search(pattern, text, re.IGNORECASE):
                return value

        return None

    def extract_date(self, text: str) -> str | None:

        # Check longer phrase first
        if "day after tomorrow" in text:
            return (date.today() + timedelta(days=2)).isoformat()

        if "tomorrow" in text:
            return (date.today() + timedelta(days=1)).isoformat()

        if "today" in text:
            return date.today().isoformat()

        return None

    def extract_time(self, text: str) -> str | None:
        """
        Extract time from natural language.

        Examples:
        6 PM       -> 18:00
        6:30 PM    -> 18:30
        9 AM       -> 09:00
        12 PM      -> 12:00
        12 AM      -> 00:00
        18:00      -> 18:00
        at 7 pm    -> 19:00
        """

        # =========================================================
        # 12-HOUR FORMAT
        # =========================================================

        match = re.search(
            r"\b(?:at\s+)?"
            r"(\d{1,2})"
            r"(?::(\d{2}))?"
            r"\s*(am|pm)\b",
            text,
            re.IGNORECASE,
        )

        if match:

            hour = int(match.group(1))
            minute = int(match.group(2) or 0)
            period = match.group(3).lower()

            # Validate
            if hour < 1 or hour > 12:
                return None

            if minute < 0 or minute > 59:
                return None

            # Convert to 24-hour format
            if period == "am":

                if hour == 12:
                    hour = 0

            elif period == "pm":

                if hour != 12:
                    hour += 12

            return f"{hour:02d}:{minute:02d}"

        # =========================================================
        # 24-HOUR FORMAT
        # =========================================================

        match = re.search(
            r"\b(?:at\s+)?"
            r"([01]?\d|2[0-3])"
            r":"
            r"([0-5]\d)"
            r"\b",
            text,
            re.IGNORECASE,
        )

        if match:

            hour = int(match.group(1))
            minute = int(match.group(2))

            return f"{hour:02d}:{minute:02d}"

        return None

    def extract_task_title(self, text: str) -> str | None:

            title = text.strip()

            # Remove command prefixes
            prefix_patterns = [
                r"^\s*(?:please\s+)?"
                r"(?:create|add|make|schedule|set)\s+"
                r"(?:a\s+)?(?:new\s+)?task\s+"
                r"(?:to\s+)?",

                r"^\s*(?:please\s+)?"
                r"remind\s+me\s+to\s+",

                r"^\s*(?:please\s+)?"
                r"(?:add|create)\s+"
                r"(?:a\s+)?(?:todo|to-do)\s+"
                r"(?:to\s+)?",
            ]

            for pattern in prefix_patterns:
                title = re.sub(
                    pattern,
                    "",
                    title,
                    count=1,
                    flags=re.IGNORECASE,
                )

            # ---------------------------------------------------------
            # Remove scheduling information from the end
            # ---------------------------------------------------------

            scheduling_patterns = [

                # today / tomorrow / day after tomorrow
                r"\s+\b(?:today|tomorrow|day\s+after\s+tomorrow)\b.*$",

                # weekdays
                r"\s+(?:on\s+)?"
                r"(?:monday|tuesday|wednesday|thursday|friday|"
                r"saturday|sunday)\b.*$",

                # time: at 6 PM, at 6:30 PM
                r"\s+at\s+"
                r"\d{1,2}(?::\d{2})?\s*(?:am|pm)\b.*$",

                # 24-hour time
                r"\s+at\s+"
                r"(?:[01]?\d|2[0-3]):[0-5]\d\b.*$",

                # duration
                r"\s+for\s+"
                r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|"
                r"seven|eight|nine|ten|half)\s*"
                r"(?:minutes?|mins?|hours?|hrs?)\b.*$",
            ]

            for pattern in scheduling_patterns:
                title = re.sub(
                    pattern,
                    "",
                    title,
                    count=1,
                    flags=re.IGNORECASE,
                )

            title = title.strip(" .,!:-")

            if not title:
                return None

            # Capitalize first character without destroying things
            # like DBMS, Python, Java, etc.
            title = title[0].upper() + title[1:]

            return title

    def extract_event_title(self, text: str) -> str | None:

            title = text.strip()

            # ---------------------------------------------------------
            # Remove event command prefixes
            # ---------------------------------------------------------

            prefix_patterns = [
                r"^\s*(?:please\s+)?"
                r"(?:create|add|make|schedule|set)\s+"
                r"(?:a\s+|an\s+)?(?:new\s+)?"
                r"(?:event|meeting|appointment)\s+"
                r"(?:for\s+|to\s+)?",

                r"^\s*(?:please\s+)?"
                r"(?:book|schedule)\s+"
                r"(?:a\s+|an\s+)?"
                r"(?:meeting|appointment)\s+"
                r"(?:for\s+)?",
            ]

            for pattern in prefix_patterns:
                title = re.sub(
                    pattern,
                    "",
                    title,
                    count=1,
                    flags=re.IGNORECASE,
                )

            # ---------------------------------------------------------
            # Remove date/time/duration information
            # ---------------------------------------------------------

            scheduling_patterns = [

                r"\s+\b(?:today|tomorrow|day\s+after\s+tomorrow)\b.*$",

                r"\s+(?:on\s+)?"
                r"(?:monday|tuesday|wednesday|thursday|friday|"
                r"saturday|sunday)\b.*$",

                r"\s+at\s+"
                r"\d{1,2}(?::\d{2})?\s*(?:am|pm)\b.*$",

                r"\s+at\s+"
                r"(?:[01]?\d|2[0-3]):[0-5]\d\b.*$",

                r"\s+for\s+"
                r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|"
                r"seven|eight|nine|ten|half)\s*"
                r"(?:minutes?|mins?|hours?|hrs?)\b.*$",
            ]

            for pattern in scheduling_patterns:
                title = re.sub(
                    pattern,
                    "",
                    title,
                    count=1,
                    flags=re.IGNORECASE,
                )

            title = title.strip(" .,!:-")

            if not title:
                return None

            title = title[0].upper() + title[1:]

            return title

    def calculate_end_time(self, start_time: str | None, duration_minutes: int = 60) -> str | None:
        if not start_time:
            return None

        try:
            start = datetime.strptime(start_time, "%H:%M")
            end = start + timedelta(minutes=duration_minutes)
            return end.strftime("%H:%M")
        except ValueError:
            return None

intent_service = IntentService()