from enum import Enum

from pydantic import BaseModel, Field


class Intent(str, Enum):
    CREATE_TASK = "CREATE_TASK"
    UPDATE_TASK = "UPDATE_TASK"
    DELETE_TASK = "DELETE_TASK"
    COMPLETE_TASK = "COMPLETE_TASK"
    CREATE_EVENT = "CREATE_EVENT"
    RESCHEDULE_EVENT = "RESCHEDULE_EVENT"
    DELETE_EVENT = "DELETE_EVENT"
    TODAY_SCHEDULE = "TODAY_SCHEDULE"
    TOMORROW_SCHEDULE = "TOMORROW_SCHEDULE"
    WEEKLY_SCHEDULE = "WEEKLY_SCHEDULE"
    DAILY_PLANNING = "DAILY_PLANNING"
    GENERAL_CHAT = "GENERAL_CHAT"
    UNKNOWN = "UNKNOWN"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: str | None = Field(
        default=None,
        description="Optional client conversation identifier for multi-turn state",
    )
    provider: str | None = Field(
        default=None,
        description="Optional LLM provider identifier",
    )


class TaskData(BaseModel):
    task_id: int | None = None
    title: str | None = None
    date: str | None = None
    time: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)


class EventData(BaseModel):
    event_id: int | None = None
    title: str | None = None
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None


class ChatResponse(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    message: str
    task: TaskData | None = None
    event: EventData | None = None
    task_id: int | None = None
    event_id: int | None = None
    missing_fields: list[str] = Field(default_factory=list)
    conversation_id: str | None = None
