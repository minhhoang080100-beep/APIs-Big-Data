"""Offline customer-date and ambiguous-IMO catalog regressions."""

import sqlite3
from datetime import date

import pytest

from test_vietsun_scope import api


@pytest.mark.parametrize(
    "params,bounds",
    [
        ({}, None),
        ({"startDate": "20260101"}, (date(2026, 1, 1),)),
        ({"startDate": "2026-01-01"}, (date(2026, 1, 1),)),
        ({"endDate": "20260131"}, (date(2026, 2, 1),)),
        ({"endDate": "2026-01-31"}, (date(2026, 2, 1),)),
        ({"startDate": "20260131", "endDate": "2026-01-31"},
         (date(2026, 1, 31), date(2026, 2, 1))),
        ({"startDate": "20240229", "endDate": "2024-02-29"},
         (date(2024, 2, 29), date(2024, 3, 1))),
        ({"startDate": "20261231", "endDate": "2026-12-31"},
         (date(2026, 12, 31), date(2027, 1, 1))),
    ],
)
def test_customer_date_bounds_preserve_update_time_semantics(api, params, bounds):
    client, execute = api
    response = client.get("/api/customers", params=params)
    assert response.status_code == 200
    query, bound = execute.call_args.args
    assert bound == bounds
    assert "CAST(updateTime AS DATE)" not in query
    assert ("updateTime >= ?" in query) == ("startDate" in params)
    assert ("updateTime < ?" in query) == ("endDate" in params)
    assert "createTime >= ?" not in query
    assert "createTime < ?" not in query
    assert "ORDER BY partnerCode" in query


@pytest.mark.parametrize(
    "params",
    [
        {"startDate": ""},
        {"endDate": ""},
        {"startDate": "20260229"},
        {"endDate": "2026-02-30"},
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
    ],
)
def test_invalid_customer_dates_return_422_before_database(api, params):
    client, execute = api
    response = client.get("/api/customers", params=params)
    assert response.status_code == 422
    execute.assert_not_called()


def test_customer_filter_includes_entire_end_day_not_creation_day(api):
    client, execute = api
    response = client.get("/api/customers", params={"startDate": "20260101", "endDate": "20260131"})
    assert response.status_code == 200
    query, params = execute.call_args.args
    # Exercise the actual WHERE predicate in a disposable in-memory database.
    # Creation dates deliberately oppose update dates to catch field switching.
    with sqlite3.connect(":memory:") as connection:
        connection.execute(
            "CREATE TABLE records (partnerCode TEXT, updateTime TEXT, "
            "createTime TEXT, rowDeleted INTEGER, rowInvisible INTEGER)"
        )
        connection.executemany(
            "INSERT INTO records VALUES (?, ?, ?, ?, ?)",
            [
                ("BEFORE", "2025-12-31T23:59:59", "2026-01-15", 0, 0),
                ("START", "2026-01-01T00:00:00", "2020-01-01", 0, 0),
                ("END", "2026-01-31T23:59:59.999999", "2020-01-01", 0, None),
                ("AFTER", "2026-02-01T00:00:00", "2026-01-15", 0, 0),
                ("DELETED", "2026-01-15T12:00:00", "2020-01-01", 1, 0),
                ("INVISIBLE", "2026-01-15T12:00:00", "2020-01-01", 0, 1),
            ],
        )
        predicate = query.split("WHERE", 1)[1].replace("ISNULL(", "IFNULL(")
        rows = connection.execute(
            "SELECT partnerCode FROM records WHERE " + predicate,
            tuple(value.isoformat() for value in params),
        ).fetchall()
    assert rows == [("END",), ("START",)]


def test_customer_tax_filter_remains_parameterized_after_dates(api):
    client, execute = api
    tax_code = "OFFLINE' OR 1=1 --"
    response = client.get("/api/customers", params={
        "startDate": "20260101", "endDate": "20260131", "customerTaxCode": tax_code,
    })
    assert response.status_code == 200
    query, params = execute.call_args.args
    assert tax_code not in query
    assert "partnerTaxCode = ?" in query
    assert params == (date(2026, 1, 1), date(2026, 2, 1), tax_code)


def test_customer_date_documentation_describes_update_time(api):
    client, _ = api
    operation = client.get("/openapi.json").json()["paths"]["/api/customers"]["get"]
    descriptions = {item["name"]: item["description"] for item in operation["parameters"]}
    assert "ngày cập nhật" in descriptions["startDate"]
    assert "ngày cập nhật" in descriptions["endDate"]
    assert "updateTime" in operation["description"]


@pytest.mark.parametrize("path", ["/api/customers", "/api/shipDetails/1234567"])
def test_catalog_filter_database_failure_is_500(api, path):
    client, execute = api
    execute.side_effect = RuntimeError("offline unavailable")
    assert client.get(path).status_code == 500


def ship_row(vessel_id):
    return {
        "vesselId": vessel_id,
        "numberIMO": "1234567",
        "vesselName": f"Offline ship {vessel_id}",
        "createTime": "2020-01-02T03:04:05",
        "updateTime": "2026-01-02T03:04:05",
    }


def test_ship_single_imo_match_keeps_existing_schema_and_id(api):
    client, execute = api
    execute.return_value = [ship_row(17)]
    listing = client.get("/api/shipDetails")
    detail = client.get("/api/shipDetails/1234567")
    assert listing.status_code == detail.status_code == 200
    assert detail.json()["data"] == listing.json()["data"][0]
    assert detail.json()["data"]["shipId"] == "17"
    assert detail.json()["data"]["shipIMO"] == "1234567"
    query, params = execute.call_args.args
    assert "AND v.numberIMO = ?" in query
    assert params == ("1234567",)


@pytest.mark.parametrize("vessel_ids", [(17, 18), (18, 17), (17, 18, 19), (17, 17)])
def test_ship_duplicate_imo_returns_explicit_conflict_without_arbitrary_first(api, vessel_ids):
    client, execute = api
    execute.return_value = [ship_row(vessel_id) for vessel_id in vessel_ids]
    response = client.get("/api/shipDetails/1234567")
    assert response.status_code == 409
    payload = response.json()
    assert payload["detail"]["code"] == "0"
    assert "IMO" in payload["detail"]["message"]
    assert "shipId" not in payload["detail"]


def test_ship_missing_imo_still_returns_404(api):
    client, _ = api
    assert client.get("/api/shipDetails/9999999").status_code == 404


def test_ship_conflict_is_documented_without_changing_route(api):
    client, _ = api
    operation = client.get("/openapi.json").json()["paths"]["/api/shipDetails/{ship_imo}"]["get"]
    assert "409" in operation["responses"]
    assert "numberIMO" in operation["description"]


@pytest.mark.parametrize("path", ["/api/customers", "/api/shipDetails/1234567"])
def test_customer_and_ship_filters_still_require_authentication(api, path):
    client, execute = api
    client.app.dependency_overrides.clear()
    assert client.get(path).status_code in (401, 403)
    assert client.get(path, headers={"Authorization": "Bearer invalid-offline-token"}).status_code == 401
    execute.assert_not_called()
