"""Calendar-day contract for production API filters and output dates.

Keep SQL bounds half-open so every timestamp on the requested end day is
included. These helpers do not change the production scope or TEU/weight rules.
"""

import re
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException


def _parse_day(value: Optional[str], field: str) -> Optional[date]:
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(
        r"(?:[0-9]{8}|[0-9]{4}-[0-9]{2}-[0-9]{2})", value
    ):
        raise HTTPException(
            status_code=422, detail=f"{field} must use YYYYMMDD or YYYY-MM-DD"
        )
    compact = value.replace("-", "")
    try:
        return date(int(compact[:4]), int(compact[4:6]), int(compact[6:8]))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{field} is not a valid date") from exc


def production_date_range(
    start: Optional[str], end: Optional[str]
) -> Tuple[Optional[date], Optional[date]]:
    """Return an inclusive start and exclusive end, suitable for ODBC binding."""
    start_day = _parse_day(start, "startDate")
    end_day = _parse_day(end, "endDate")
    if start_day is not None and end_day is not None and start_day > end_day:
        raise HTTPException(status_code=422, detail="startDate must not exceed endDate")
    try:
        end_exclusive = end_day + timedelta(days=1) if end_day is not None else None
    except OverflowError as exc:
        raise HTTPException(status_code=422, detail="endDate must be before 9999-12-31") from exc
    return start_day, end_exclusive


def production_finish_date(value: object) -> str:
    """Serialize the source calendar day, including ISO strings from database.py.

    Do not apply timezone conversion: shiftDate is the source production day.
    Retain the previous empty value for an absent source date; malformed source
    dates raise an error rather than being silently assigned another day.
    """
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    raise ValueError("Unsupported production finish date")

