import json
import logging
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import dateparser
from pydantic import BaseModel, Field

from app.core.config import settings
from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)


def get_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(settings.timezone)
    except Exception:
        return ZoneInfo("Asia/Kolkata")


class ExtractedItem(BaseModel):
    intent: str | None = Field(
        default=None,
        description="Intent of the request (e.g. CREATE_TASK, CREATE_EVENT, RESCHEDULE_EVENT, GENERAL_CHAT, UNKNOWN)",
    )
    title: str | None = Field(
        default=None,
        description="Title or description of the task or event",
    )
    date_phrase: str | None = Field(
        default=None,
        description="Extracted date phrase verbatim from user message, e.g. 'next friday', '3rd Nov', 'tomorrow'",
    )
    time_phrase: str | None = Field(
        default=None,
        description="Extracted time phrase verbatim from user message, e.g. '5pm', 'evening', 'in 2 hours', '3pm to 4pm'",
    )
    duration_minutes: int | None = Field(
        default=None,
        description="Duration in minutes if mentioned in the message",
    )
    priority: str | None = Field(
        default=None,
        description="Priority if mentioned (e.g. HIGH, MEDIUM, LOW)",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="List of strings denoting missing required or expected fields",
    )


def build_extraction_system_prompt() -> str:
    tz = get_timezone()
    now = datetime.now(tz)
    current_date = now.strftime("%Y-%m-%d")
    current_weekday = now.strftime("%A")
    current_time = now.strftime("%H:%M:%S")

    return f"""You are an expert entity extraction engine for an AI Personal Assistant.
Your task is to analyze user requests and extract scheduling entities into a JSON object matching the requested schema.

Current context (timezone: {settings.timezone}):
- Current Date: {current_date}
- Current Weekday: {current_weekday}
- Current Time: {current_time}

EXTRACTION RULES:
1. Extract PHRASES ONLY for `date_phrase` and `time_phrase` ("next friday", "5pm", "3rd Nov", "in 2 hours", "evening"). DO NOT compute or resolve dates or ISO timestamps yourself.
2. If the user request is creating a task, reminder, or to-do, set intent to "CREATE_TASK".
3. If the user request is scheduling a meeting, appointment, or calendar event, set intent to "CREATE_EVENT".
4. If the user request is rescheduling or moving an existing event, set intent to "RESCHEDULE_EVENT".
5. If the user message is casual conversation or greeting without scheduling intent, set intent to "GENERAL_CHAT".
6. If the intent cannot be determined, set intent to "UNKNOWN".
7. Extract durations in integer minutes into `duration_minutes` (e.g. "for 2 hours" -> 120, "for 30 mins" -> 30).
8. If an actionable request is missing an expected field (such as time for a specific task/meeting, or a title), list that field name in `missing_fields` (e.g. ["time"]).
9. Return ONLY a valid JSON object matching the schema.

Few-Shot Examples:

Example 1 (Relative date / time):
User: "remind me to check the oven in 2 hours"
Output:
{{
  "intent": "CREATE_TASK",
  "title": "Check the oven",
  "date_phrase": "today",
  "time_phrase": "in 2 hours",
  "duration_minutes": null,
  "priority": null,
  "missing_fields": []
}}

Example 2 (Weekday):
User: "remind me to submit the report next Friday at 5pm"
Output:
{{
  "intent": "CREATE_TASK",
  "title": "Submit the report",
  "date_phrase": "next Friday",
  "time_phrase": "5pm",
  "duration_minutes": null,
  "priority": null,
  "missing_fields": []
}}

Example 3 (Missing time):
User: "buy groceries tomorrow"
Output:
{{
  "intent": "CREATE_TASK",
  "title": "Buy groceries",
  "date_phrase": "tomorrow",
  "time_phrase": null,
  "duration_minutes": null,
  "priority": null,
  "missing_fields": ["time"]
}}

Example 4 (Duration):
User: "study physics tomorrow at 4pm for 2 hours"
Output:
{{
  "intent": "CREATE_TASK",
  "title": "Study physics",
  "date_phrase": "tomorrow",
  "time_phrase": "4pm",
  "duration_minutes": 120,
  "priority": null,
  "missing_fields": []
}}

Example 5 (Event with start and end time):
User: "dentist appointment next Monday from 3pm to 4pm"
Output:
{{
  "intent": "CREATE_EVENT",
  "title": "Dentist appointment",
  "date_phrase": "next Monday",
  "time_phrase": "3pm to 4pm",
  "duration_minutes": 60,
  "priority": null,
  "missing_fields": []
}}

Example 6 (Message with no actionable intent):
User: "how is the weather today?"
Output:
{{
  "intent": "GENERAL_CHAT",
  "title": null,
  "date_phrase": null,
  "time_phrase": null,
  "duration_minutes": null,
  "priority": null,
  "missing_fields": []
}}
"""


def resolve_date_and_time(
    date_phrase: str | None,
    time_phrase: str | None,
    duration_minutes: int | None = None,
) -> tuple[str | None, str | None, str | None]:
    """
    Resolve date_phrase and time_phrase to real values in Python using dateparser.
    Settings: TIMEZONE=Asia/Kolkata, PREFER_DATES_FROM=future.

    Returns: (resolved_date: 'YYYY-MM-DD', resolved_start_time: 'HH:MM', resolved_end_time: 'HH:MM')
    """
    tz = get_timezone()
    now = datetime.now(tz)
    dateparser_settings = {
        "TIMEZONE": settings.timezone,
        "TO_TIMEZONE": settings.timezone,
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": now.replace(tzinfo=None),
    }

    resolved_date: str | None = None
    resolved_time: str | None = None
    resolved_end_time: str | None = None

    # 1. Resolve date_phrase
    if date_phrase:
        dp = date_phrase.strip()
        dt = dateparser.parse(dp, settings=dateparser_settings)
        if dt is None:
            # Handle 'next <weekday>' or 'this <weekday>' which dateparser can struggle with directly
            m = re.match(
                r"^(?:next|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$",
                dp,
                re.IGNORECASE,
            )
            if m:
                dt = dateparser.parse(m.group(1), settings=dateparser_settings)
        if dt is not None:
            resolved_date = dt.date().isoformat()

    # 2. Resolve time_phrase
    if time_phrase:
        tp = time_phrase.strip()
        # Range check: e.g. "3pm to 4pm", "3pm - 4pm", "from 10am to 11am"
        range_match = re.search(
            r"(?:from\s+)?(.*?)\s+(?:to|-)\s+(.*)",
            tp,
            re.IGNORECASE,
        )
        if range_match:
            start_str = range_match.group(1).strip()
            end_str = range_match.group(2).strip()
            s_dt = dateparser.parse(start_str, settings=dateparser_settings)
            e_dt = dateparser.parse(end_str, settings=dateparser_settings)
            if s_dt is not None:
                resolved_time = s_dt.strftime("%H:%M")
            if e_dt is not None:
                resolved_end_time = e_dt.strftime("%H:%M")
        else:
            # Standalone hour format: e.g. "5", "at 5", "5pm", "5:30 pm", "9"
            standalone_match = re.match(
                r"^(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$",
                tp,
                re.IGNORECASE,
            )
            if standalone_match:
                h = int(standalone_match.group(1))
                m_val = int(standalone_match.group(2) or 0)
                p_val = standalone_match.group(3)
                if p_val:
                    if p_val.lower() == "pm" and h != 12:
                        h += 12
                    elif p_val.lower() == "am" and h == 12:
                        h = 0
                else:
                    # Bare hour like '5' or 'at 5': 1 to 6 is typically afternoon/evening (PM)
                    if 1 <= h <= 6:
                        h += 12
                resolved_time = f"{h:02d}:{m_val:02d}"
            else:
                t_dt = dateparser.parse(tp, settings=dateparser_settings)
                if t_dt is not None:
                    resolved_time = t_dt.strftime("%H:%M")
                    # If date_phrase wasn't provided, relative phrases like "in 2 hours" supply the date
                    if not resolved_date and any(
                        kw in tp.lower() for kw in ["in ", "hour", "minute", "day", "tomorrow"]
                    ):
                        resolved_date = t_dt.date().isoformat()
                else:
                    # Named times of day
                    tod_map = {
                        "morning": "09:00",
                        "afternoon": "14:00",
                        "evening": "18:00",
                        "night": "20:00",
                        "noon": "12:00",
                        "midday": "12:00",
                        "midnight": "00:00",
                    }
                    for kw, val in tod_map.items():
                        if kw in tp.lower():
                            resolved_time = val
                            break

    # Calculate end_time if start_time & duration exist but end_time is not set
    if resolved_time and duration_minutes and not resolved_end_time:
        try:
            st = datetime.strptime(resolved_time, "%H:%M")
            resolved_end_time = (st + timedelta(minutes=duration_minutes)).strftime("%H:%M")
        except ValueError:
            pass

    return resolved_date, resolved_time, resolved_end_time


class ExtractionService:

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def extract(self, message: str) -> ExtractedItem | None:
        """
        Extract structured entities from user message using LLMProvider.generate_json.
        Validates with Pydantic. On invalid JSON retries once, then returns None for fallback.
        """
        system_prompt = build_extraction_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]
        schema = ExtractedItem.model_json_schema()

        last_raw_response = ""
        for attempt in range(2):
            try:
                raw_response = await self.provider.generate_json(
                    messages=messages,
                    schema=schema,
                )
                last_raw_response = raw_response or ""
                if not last_raw_response.strip():
                    raise ValueError("Empty response received from LLM")

                # Validate with Pydantic
                item = ExtractedItem.model_validate_json(last_raw_response)
                return item

            except Exception as exc:
                logger.warning(
                    f"Extraction attempt {attempt + 1} failed: {exc}. "
                    f"Raw response: {last_raw_response!r}"
                )
                if attempt == 0:
                    messages.append({
                        "role": "assistant",
                        "content": last_raw_response,
                    })
                    messages.append({
                        "role": "user",
                        "content": (
                            "Your previous output was not valid JSON conforming to the schema. "
                            "Please output ONLY valid JSON matching the schema."
                        ),
                    })
                else:
                    logger.error("Extraction retry attempt also failed. Falling back to regex flow.")
                    return None

        return None
