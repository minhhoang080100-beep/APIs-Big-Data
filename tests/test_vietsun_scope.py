"""Offline regressions: no configured database, credentials or network are used.

Run only this suite with ``python -m pytest tests/test_vietsun_scope.py -q``.
SQLite checks the actual scope predicate's relational behavior, not SQL Server
query plans or production data. Endpoint checks replace database/auth imports
before loading the application and exercise its HTTP response contract.
"""

import importlib.util
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from production_scope import EXCLUDE_VIETSUN_SQL


EARLY = "2025-12-31T08:00:00"
FIRST = "2026-01-01T08:00:00"
LATER = "2026-01-03T08:00:00"
INVALID_TIME = "1899-12-30T00:00:00"


def event(berth_id, atb=FIRST, ata=None, arrived=1, deleted=0, voyage=100):
    return (voyage, berth_id, atb, ata, arrived, deleted)


@pytest.fixture
def scope_db():
    connection = sqlite3.connect(":memory:")
    connection.execute("ATTACH DATABASE ':memory:' AS dbo")
    context = {"database": "SmartTOS"}
    connection.create_function("DB_NAME", 0, lambda: context["database"])
    connection.executescript(
        """
        CREATE TABLE dbo.TallyShift (
            tallyShiftId INTEGER PRIMARY KEY, vesselVoyageId INTEGER,
            vesselId INTEGER, rowDeleted INTEGER
        );
        CREATE TABLE dbo.DoBerth (
            vesselVoyageId INTEGER, berthId INTEGER, ATB TEXT, ATA TEXT,
            isArrival INTEGER, rowDeleted INTEGER
        );
        CREATE TABLE dbo.Berth (berthId INTEGER PRIMARY KEY, berthCode TEXT);
        INSERT INTO dbo.Berth VALUES (13, 'CAU5'), (2, 'CAU2'), (3, 'CAU3');
        INSERT INTO dbo.TallyShift VALUES (1, 100, 50, NULL);
        """
    )
    try:
        yield connection, context
    finally:
        connection.close()


def selected_ids(connection, suffix=""):
    return [
        row[0]
        for row in connection.execute(
            "SELECT t.tallyShiftId FROM dbo.TallyShift t WHERE 1 = 1 "
            + EXCLUDE_VIETSUN_SQL
            + " ORDER BY t.tallyShiftId "
            + suffix
        )
    ]


@pytest.mark.parametrize(
    "history,removed",
    [
        pytest.param([event(13)], True, id="confirmed-cau5"),
        pytest.param([event(2)], False, id="nghe-tinh"),
        pytest.param([], False, id="no-berth-history"),
        pytest.param([event(13), event(2, LATER)], True, id="cau5-then-move"),
        pytest.param([event(2), event(13, LATER)], False, id="other-then-cau5"),
        pytest.param([event(13, EARLY)], True, id="first-berth-before-report-period"),
        pytest.param([event(13, arrived=0)], True, id="actual-time-without-arrival-flag"),
        pytest.param([event(13, arrived=None)], True, id="actual-time-null-arrival-flag"),
        pytest.param([event(13, atb=None)], False, id="arrival-without-orderable-time"),
        pytest.param([event(13, atb=None, arrived=0)], False, id="planned-only"),
        pytest.param(
            [event(2, atb=None, arrived=0), event(13)], True,
            id="ignore-plan-without-actual-time",
        ),
        pytest.param([event(2, EARLY, deleted=1), event(13)], True, id="ignore-deleted-first"),
        pytest.param([event(13, deleted=1)], False, id="deleted-cau5-not-evidence"),
        pytest.param([event(13, deleted=None)], True, id="null-deleted-is-active"),
        pytest.param(
            [event(13, LATER, ata=EARLY), event(2)], False,
            id="prefer-atb-over-earlier-ata",
        ),
        pytest.param([event(13, atb=None, ata=FIRST)], True, id="ata-fallback"),
        pytest.param([event(13, INVALID_TIME, ata=FIRST)], True, id="sentinel-atb-ata-fallback"),
        pytest.param([event(13, INVALID_TIME, ata=INVALID_TIME)], False, id="sentinel-times"),
        pytest.param(
            [event(13), event(2, atb=None)], False, id="untimed-actual-history-is-ambiguous",
        ),
        pytest.param([event(13), event(2)], False, id="conflicting-earliest-berths"),
        pytest.param([event(13), event(13)], True, id="same-berth-tie-is-not-conflict"),
        pytest.param([event(0, EARLY), event(13)], False, id="invalid-earlier-berth-id"),
        pytest.param([event(999, EARLY), event(13)], False, id="missing-earlier-berth-master"),
        pytest.param([event(None, EARLY), event(13)], False, id="null-earlier-berth"),
        pytest.param([event(None), event(13)], False, id="null-earliest-berth-tie"),
    ],
)
def test_only_confirmed_initial_cau5_is_removed(scope_db, history, removed):
    connection, _ = scope_db
    connection.executemany("INSERT INTO dbo.DoBerth VALUES (?, ?, ?, ?, ?, ?)", history)
    assert selected_ids(connection) == ([] if removed else [1])


@pytest.mark.parametrize("code", [None, "", "   "])
def test_invalid_cau5_master_code_does_not_remove(scope_db, code):
    connection, _ = scope_db
    connection.execute("UPDATE dbo.Berth SET berthCode = ? WHERE berthId = 13", (code,))
    connection.execute("INSERT INTO dbo.DoBerth VALUES (?, ?, ?, ?, ?, ?)", event(13))
    assert selected_ids(connection) == [1]


@pytest.mark.parametrize(
    "database,expected", [("SmartTOS", []), ("SMARTTOS", []), ("SmartTOS_BenThuy", [1]), ("Other", [1])]
)
def test_berth_13_is_excluded_only_in_cua_lo_database(scope_db, database, expected):
    connection, context = scope_db
    context["database"] = database
    connection.execute("INSERT INTO dbo.DoBerth VALUES (?, ?, ?, ?, ?, ?)", event(13))
    assert selected_ids(connection) == expected


def test_uses_tally_voyage_not_vessel_identity(scope_db):
    connection, _ = scope_db
    connection.executemany(
        "INSERT INTO dbo.TallyShift VALUES (?, ?, ?, NULL)",
        [(2, 200, 50), (3, None, 50), (4, 300, 50)],
    )
    connection.executemany(
        "INSERT INTO dbo.DoBerth VALUES (?, ?, ?, ?, ?, ?)",
        [event(13, voyage=100), event(2, voyage=200), event(13, voyage=999)],
    )
    assert selected_ids(connection) == [2, 3, 4]


def test_duplicate_history_cannot_multiply_returned_rows(scope_db):
    connection, _ = scope_db
    connection.executemany("INSERT INTO dbo.DoBerth VALUES (?, ?, ?, ?, ?, ?)", [event(2)] * 5)
    assert selected_ids(connection) == [1]


def test_filtering_before_pagination_fills_pages_without_leaking_cau5(scope_db):
    connection, _ = scope_db
    connection.executemany(
        "INSERT INTO dbo.TallyShift VALUES (?, ?, 50, NULL)", [(2, 200), (3, 100), (4, 200), (5, 200)]
    )
    connection.executemany(
        "INSERT INTO dbo.DoBerth VALUES (?, ?, ?, ?, ?, ?)", [event(13), event(2, voyage=200)]
    )
    assert selected_ids(connection, "LIMIT 2 OFFSET 0") == [2, 4]
    assert selected_ids(connection, "LIMIT 2 OFFSET 2") == [5]


@pytest.fixture
def api(monkeypatch):
    # These stubs are installed BEFORE main is imported. Production database.py
    # and auth.py (including their dotenv loading) are never imported here.
    database_stub = ModuleType("database")
    database_stub.db = SimpleNamespace(execute_query=Mock(return_value=[]))
    auth_stub = ModuleType("auth")
    auth_stub.authenticate_user = Mock(return_value=None)
    auth_stub.create_access_token = Mock(return_value="offline-test-token")
    auth_stub.verify_token = Mock(return_value=None)
    auth_stub.ACCESS_TOKEN_EXPIRE_HOURS = 1
    monkeypatch.setitem(sys.modules, "database", database_stub)
    monkeypatch.setitem(sys.modules, "auth", auth_stub)
    spec = importlib.util.spec_from_file_location("_scope_test_main", Path(__file__).parents[1] / "main.py")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    module.app.dependency_overrides[module.get_current_user] = lambda: SimpleNamespace(username="offline-test")
    with TestClient(module.app) as client:
        yield client, database_stub.db.execute_query


QUAY_PATHS = ["/api/contQuayVolumesCB", "/api/bulkQuayVolumesCB"]
GATE_PATHS = ["/api/contGateVolumesCB", "/api/bulkGateVolumesCB"]


@pytest.mark.parametrize("path", QUAY_PATHS + GATE_PATHS)
def test_scope_applies_to_quay_only_and_preserves_filters_and_pagination(api, path):
    client, execute = api
    params = {
        "startDate": "20260101", "endDate": "20260131", "handlingMethodId": "CONT TAU-BAI",
        "page": 3, "limit": 7,
    }
    expected_parameters = [date(2026, 1, 1), date(2026, 2, 1)]
    if path in QUAY_PATHS:
        params["shipId"] = "42"
        expected_parameters.append("42")
    expected_parameters.extend(["CONT TAU-BAI"] * 3 + [14, 7])
    response = client.get(path, params=params)
    assert response.status_code == 200
    assert response.json()["code"] == "1"
    assert response.json()["data"] == []
    execute.assert_called_once()
    sql, bound = execute.call_args.args
    assert bound == tuple(expected_parameters)
    assert sql.count("?") == len(bound)
    assert "ORDER BY t.shiftDate DESC, t.tallyShiftId OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql
    if path in QUAY_PATHS:
        assert sql.count(EXCLUDE_VIETSUN_SQL) == 1
        assert sql.index(EXCLUDE_VIETSUN_SQL) < sql.index(" OFFSET ")
    else:
        assert EXCLUDE_VIETSUN_SQL not in sql
        assert "DoBerth" not in sql


@pytest.mark.parametrize("path", QUAY_PATHS)
def test_query_error_is_not_retried_without_scope_filter(api, path):
    client, execute = api
    execute.side_effect = RuntimeError("offline simulated schema error")
    response = client.get(path)
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "0"
    execute.assert_called_once()
    assert EXCLUDE_VIETSUN_SQL in execute.call_args.args[0]


@pytest.mark.parametrize("path", QUAY_PATHS + GATE_PATHS)
@pytest.mark.parametrize("params", [{"page": 0}, {"limit": 0}, {"limit": 101}])
def test_invalid_pagination_never_calls_database(api, path, params):
    client, execute = api
    assert client.get(path, params=params).status_code == 422
    execute.assert_not_called()


@pytest.mark.parametrize(
    "cargo,quantity,teu,weight,size",
    [("20F", 3, 3, 75.0, 73), ("20E", 3, 3, 6.75, 73),
     ("40F", 3, 6, 90.0, 241), ("40E", 3, 6, 11.64, 241),
     ("45F", 3, 6, 90.0, 321), ("45E", 4, 9, 15.52, 321)],
)
def test_container_quay_response_and_supported_weights(api, cargo, quantity, teu, weight, size):
    client, execute = api
    execute.return_value = [{
        "tallyShiftId": 55, "shiftDate": datetime(2026, 1, 15), "vesselId": 42,
        "cargoDirectId": 2, "cargoCode": " " + cargo.lower() + " ", "quantityTotalSum": quantity,
        "weightNetSum": 999.0, "jobMethodCode": "CONT TAU-BAI", "consigneeFullName": "Test operator",
        "validatedContainerWeight": weight,
        "direction": "NHAP",
    }]
    response = client.get("/api/contQuayVolumesCB")
    assert response.status_code == 200
    row = response.json()["data"][0]
    assert set(row) == {
        "reportDate", "companyId", "shipId", "classId", "originId", "containerWeight", "containerTEU",
        "handlingMethodId", "finishDate", "shipOperatorId", "containerOperatorId", "containerSizeId", "direction",
    }
    assert row["containerTEU"] == teu
    assert row["containerWeight"] == pytest.approx(weight)
    assert row["containerSizeId"] == size
    assert row["finishDate"] == "2026-01-15"
    assert row["companyId"] == "CNT"
    assert row["shipId"] == "42"
    assert row["direction"] == "NHAP"


def test_bulk_quay_weight_is_not_recalculated(api):
    client, execute = api
    execute.return_value = [{
        "shiftDate": datetime(2026, 1, 15), "vesselId": 42, "agencyId": 3,
        "cargoDirectId": 2, "cargoGroupId": 4, "cargoId": 5, "jobMethodCode": "TAU-BAI",
        "weightNetSum": 123.456,
    }]
    response = client.get("/api/bulkQuayVolumesCB")
    assert response.status_code == 200
    assert response.json()["data"][0]["bulkWeight"] == 123.456


def test_container_gate_preserves_actual_weight(api):
    client, execute = api
    execute.return_value = [{
        "shiftDate": datetime(2026, 1, 15), "vesselId": 42, "cargoCode": "40F",
        "quantityTotalSum": 3, "weightNetSum": 54.321, "jobMethodCode": "BAI-XE",
    }]
    response = client.get("/api/contGateVolumesCB")
    assert response.status_code == 200
    row = response.json()["data"][0]
    assert row["containerWeight"] == 54.321
    assert row["containerTEU"] == 6
    assert "DoBerth" not in execute.call_args.args[0]

