import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.providers import get_provider
from app.services.extraction_service import ExtractionService, resolve_date_and_time


CASES_PATH = Path(__file__).with_name("eval_cases.json")
FROZEN_NOW = datetime(2026, 10, 22, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
FIELDS = ("intent", "title", "date", "time", "missing_fields")


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        if tz is None:
            return FROZEN_NOW.replace(tzinfo=None)
        return FROZEN_NOW.astimezone(tz)


def normalize_text(value):
    if value is None:
        return None
    return " ".join(value.split()).casefold()


def actual_fields(item):
    if item is None:
        return {
            "intent": None,
            "title": None,
            "date": None,
            "time": None,
            "missing_fields": [],
        }

    date_value, time_value, _ = resolve_date_and_time(
        item.date_phrase,
        item.time_phrase,
        item.duration_minutes,
    )
    return {
        "intent": item.intent,
        "title": item.title,
        "date": date_value,
        "time": time_value,
        "missing_fields": item.missing_fields,
    }


def fields_match(field, actual, expected):
    if field == "title":
        return normalize_text(actual) == normalize_text(expected)
    if field == "missing_fields":
        return set(actual or []) == set(expected or [])
    return actual == expected


async def evaluate():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    service = ExtractionService(provider=get_provider())
    correct = {field: 0 for field in FIELDS}
    complete_matches = 0

    with patch("app.services.extraction_service.datetime", FrozenDateTime):
        for index, case in enumerate(cases, start=1):
            item = await service.extract(case["message"])
            actual = actual_fields(item)
            expected = case["expected"]
            matches = {
                field: fields_match(field, actual[field], expected[field])
                for field in FIELDS
            }
            for field, matched in matches.items():
                correct[field] += matched
            complete_matches += all(matches.values())

            print(
                f"[{index:02d}/{len(cases)}] "
                f"{'PASS' if all(matches.values()) else 'FAIL'} "
                f"{case['message']}"
            )
            for field, matched in matches.items():
                if not matched:
                    print(
                        f"    {field}: expected={expected[field]!r}, "
                        f"actual={actual[field]!r}"
                    )

    print("\nAccuracy")
    for field in FIELDS:
        print(f"{field:16} {correct[field]}/{len(cases)} ({correct[field] / len(cases):.1%})")
    print(
        f"{'overall':16} {complete_matches}/{len(cases)} "
        f"({complete_matches / len(cases):.1%})"
    )


if __name__ == "__main__":
    asyncio.run(evaluate())
