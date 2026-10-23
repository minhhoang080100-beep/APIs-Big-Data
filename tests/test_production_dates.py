"""Offline production-date regressions; never load the configured database.

These checks validate the date contract, not the numerical impact on MISBI.
The live number of non-midnight source records must be measured separately.
"""

import re
import sqlite3
from datetime import date, datetime

import pytest

from test_vietsun_scope import GATE_PATHS, QUAY_PATHS, api


PATHS = QUAY_PATHS + GATE_PATHS


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize(
    "params,bounds",
    [
        ({}, []),
        ({"startDate": "20260101"}, [date(2026, 1, 1)]),
        ({"startDate": "2026-01-01"}, [date(2026, 1, 1)]),
        ({"endDate": "20260131"}, [date(2026, 2, 1)]),
        ({"endDate": "2026-01-31"}, [date(2026, 2, 1)]),
        ({"startDate": "20260131", "endDate": "2026-01-31"},
         [date(2026, 1, 31), date(2026, 2, 1)]),
        ({"startDate": "2024-02-29", "endDate": "20240229"},
         [date(2024, 2, 29), date(2024, 3, 1)]),
        ({"startDate": "2026-12-31", "endDate": "20261231"},
         [date(2026, 12, 31), date(2027, 1, 1)]),
    ],
)
def test_calendar_filters_bind_dates_with_exclusive_end(api, path, params, bounds):
    client, execute = api
    response = client.get(path, params=params)
    assert response.status_code == 200
    sql, bound = execute.call_args.args
    assert bound == tuple(bounds + [0, 20])
    assert sql.count("?") == len(bound)
    assert ("t.shiftDate >= ?" in sql) == ("startDate" in params)
    assert ("t.shiftDate < ?" in sql) == ("endDate" in params)
    assert "t.shiftDate <= ?" not in sql


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize(
    "params",
    [
        {"startDate": ""},
        {"endDate": ""},
        {"startDate": "20260229"},
        {"endDate": "2026-02-29"},
        {"startDate": "20261301"},
        {"endDate": "20260132"},
        {"startDate": "2026-1-01"},
        {"endDate": "31/01/2026"},
        {"startDate": "2026-01-01T00:00:00"},
        {"endDate": "20260131 "},
        {"startDate": "20260101 OR 1=1"},
        {"endDate": "0000-01-01"},
        {"endDate": "9999-12-31"},
        {"startDate": "20260201", "endDate": "20260131"},
        {"startDate": "2026-02-01", "endDate": "2026-01-31"},
    ],
)
def test_invalid_date_filters_return_422_before_database(api, path, params):
    client, execute = api
    response = client.get(path, params=params)
    assert response.status_code == 422
    execute.assert_not_called()


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize(
    "source,expected",
    [
        (datetime(2026, 1, 31), "2026-01-31"),
        (datetime(2026, 1, 31, 23, 59, 59, 999999), "2026-01-31"),
        (date(2026, 1, 31), "2026-01-31"),
        ("2026-01-31", "2026-01-31"),
        ("2026-01-31T23:59:59.999999", "2026-01-31"),
        ("2026-01-31 23:59:59", "2026-01-31"),
        ("2026-01-31T23:59:59Z", "2026-01-31"),
        ("2026-01-31T23:59:59-07:00", "2026-01-31"),
        (None, ""),
        ("", ""),
    ],
)
def test_finish_date_uses_source_calendar_day_for_real_database_strings(api, path, source, expected):
    client, execute = api
    execute.return_value = [{
        "shiftDate": source, "cargoCode": "20F", "quantityTotalSum": 1,
        "weightNetSum": 25,
    }]
    response = client.get(path)
    assert response.status_code == 200
    assert response.json()["data"][0]["finishDate"] == expected


@pytest.mark.parametrize("path", PATHS)
def test_invalid_source_date_is_not_silently_changed(api, path):
    client, execute = api
    execute.return_value = [{
        "shiftDate": "not-a-date", "cargoCode": "20F", "quantityTotalSum": 1,
        "weightNetSum": 25,
    }]
    response = client.get(path)
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "0"


@pytest.mark.parametrize("path", PATHS)
def test_actual_sql_date_predicates_include_last_day_and_exclude_next_day(api, path):
    client, execute = api
    client.get(path, params={"startDate": "20260131", "endDate": "20260131"})
    sql, bound = execute.call_args.args
    predicates = re.findall(r"t\.shiftDate (?:>=|<) \?", sql)
    assert predicates == ["t.shiftDate >= ?", "t.shiftDate < ?"]
    with sqlite3.connect(":memory:") as connection:
        connection.execute("CREATE TABLE sample (shiftDate TEXT)")
        connection.executemany(
            "INSERT INTO sample VALUES (?)",
            [("2026-01-30T23:59:59",), ("2026-01-31T00:00:00",),
             ("2026-01-31T23:59:59.999999",), ("2026-02-01T00:00:00",)],
        )
        selected = connection.execute(
            "SELECT shiftDate FROM sample t WHERE " + " AND ".join(predicates)
            + " ORDER BY shiftDate", tuple(day.isoformat() for day in bound[:2]),
        ).fetchall()
    assert selected == [("2026-01-31T00:00:00",), ("2026-01-31T23:59:59.999999",)]

