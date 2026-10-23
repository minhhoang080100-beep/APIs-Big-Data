"""Offline catalog regressions; configured database/auth are never imported.

SQLite checks the cargo-group queries against a master table with no cargo
children. HTTP checks reuse the isolated production regression fixture.
"""

import sqlite3

import pytest

from test_vietsun_scope import api


@pytest.fixture
def cargo_group_db(api):
    client, execute = api
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("ATTACH DATABASE ':memory:' AS dbo")
    connection.executescript(
        """
        CREATE TABLE dbo.CargoGroup (
            cargoGroupId INTEGER PRIMARY KEY,
            cargoGroupCode TEXT,
            cargoGroupName TEXT,
            createTime TEXT,
            updateTime TEXT,
            rowDeleted INTEGER,
            rowInvisible INTEGER
        );
        INSERT INTO dbo.CargoGroup VALUES
            (1040, 'GROUP_A', 'Group without cargo A',
             '2020-01-02T03:04:05', '2025-06-07T08:09:10', 0, 0),
            (1041, 'GROUP_B', 'Group without cargo B',
             '2021-02-03T04:05:06', '2026-01-02T03:04:05', NULL, NULL),
            (1042, 'DELETED', 'Deleted group', NULL, NULL, 1, 0),
            (1043, 'INVISIBLE', 'Invisible group', NULL, NULL, 0, 1);
        """
    )

    def read(query, params=None):
        # This is the endpoint query, with only SQL Server's null function
        # translated. No vwCargo table exists: reading it must fail the test.
        cursor = connection.execute(query.replace("ISNULL(", "IFNULL("), params or ())
        return [dict(row) for row in cursor.fetchall()]

    execute.side_effect = read
    try:
        yield client, execute
    finally:
        connection.close()


@pytest.mark.parametrize("group_id,group_code", [(1040, "GROUP_A"), (1041, "GROUP_B")])
def test_cargo_type_master_without_children_has_matching_detail(cargo_group_db, group_id, group_code):
    client, execute = cargo_group_db
    listing = client.get("/api/cargoType")
    assert listing.status_code == 200
    item = next(row for row in listing.json()["data"] if row["cargoTypeId"] == str(group_id))
    assert item["createdDate"] is not None
    assert item["modifiedDate"] is not None

    for lookup in (str(group_id), group_code):
        detail = client.get(f"/api/cargoType/{lookup}")
        assert detail.status_code == 200
        assert detail.json()["data"] == item
        query, params = execute.call_args.args
        assert "FROM dbo.CargoGroup" in query
        assert "vwCargo" not in query
        assert "MIN(" not in query and "MAX(" not in query
        assert params == ((group_id,) if lookup.isdigit() else (group_code,))


def test_cargo_type_list_includes_only_active_master_rows(cargo_group_db):
    client, _ = cargo_group_db
    response = client.get("/api/cargoType")
    assert response.status_code == 200
    assert [row["cargoTypeId"] for row in response.json()["data"]] == ["1040", "1041"]


@pytest.mark.parametrize("lookup", ["1042", "DELETED", "1043", "INVISIBLE", "999999", "MISSING"])
def test_cargo_type_deleted_invisible_or_missing_returns_404(cargo_group_db, lookup):
    client, _ = cargo_group_db
    response = client.get(f"/api/cargoType/{lookup}")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "0"


def test_cargo_type_code_lookup_is_parameterized(cargo_group_db):
    client, execute = cargo_group_db
    lookup = "GROUP_A' OR 1=1 --"
    response = client.get(f"/api/cargoType/{lookup}")
    assert response.status_code == 404
    query, params = execute.call_args.args
    assert lookup not in query
    assert params == (lookup,)


@pytest.mark.parametrize("value", [0, 1040])
def test_cargo_category_applies_explicit_type_filter_including_zero(api, value):
    client, execute = api
    response = client.get("/api/cargoCategory", params={"cargoTypeId": value})
    assert response.status_code == 200
    query, params = execute.call_args.args
    assert "AND cargoGroupId = ?" in query
    assert params == (value,)


def test_cargo_category_without_type_filter_is_unchanged(api):
    client, execute = api
    response = client.get("/api/cargoCategory")
    assert response.status_code == 200
    query, params = execute.call_args.args
    assert "AND cargoGroupId = ?" not in query
    assert params is None


def test_origin_missing_returns_http_404_not_200_or_wrapped_500(api):
    client, execute = api
    response = client.get("/api/origins/999999")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "0"
    query, params = execute.call_args.args
    assert "FROM dbo.CargoOrigin" in query
    assert "ISNULL(rowDeleted, 0) = 0" in query
    assert "ISNULL(rowInvisible, 0) = 0" in query
    assert params == ["999999"]


def test_origins_list_and_detail_preserve_success_contract(api):
    client, execute = api
    execute.return_value = [{
        "cargoOriginId": 3,
        "cargoOriginCode": "DOMESTIC",
        "cargoOriginName": "Hàng nội",
        "createTime": "2020-01-02T03:04:05",
        "updateTime": "2026-01-02T03:04:05",
    }]
    listing = client.get("/api/origins")
    detail = client.get("/api/origins/3")
    assert listing.status_code == detail.status_code == 200
    assert listing.json()["code"] == detail.json()["code"] == "1"
    assert detail.json()["data"] == listing.json()["data"][0]
    assert detail.json()["data"]["originId"] == 3
    assert detail.json()["data"]["originName"] == "Nội địa"
    assert detail.json()["data"]["createdAt"] == "2020-01-02T03:04:05Z"


def test_origins_pagination_has_unique_tie_breaker_and_bound_filter(api):
    client, execute = api
    response = client.get("/api/origins", params={"page": 3, "limit": 7, "origin": "nội"})
    assert response.status_code == 200
    query, params = execute.call_args.args
    assert "ORDER BY cargoOriginCode, cargoOriginId" in query
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in query
    assert "cargoOriginName LIKE ?" in query
    assert params == ["%nội%", 14, 7]


@pytest.mark.parametrize("params", [{"page": 0}, {"limit": 0}, {"limit": 101}])
def test_origins_invalid_pagination_is_rejected_before_database(api, params):
    client, execute = api
    assert client.get("/api/origins", params=params).status_code == 422
    execute.assert_not_called()


@pytest.mark.parametrize("path", ["/api/cargoType", "/api/cargoType/1040", "/api/origins", "/api/origins/3"])
def test_catalog_database_failure_does_not_look_like_empty_success(api, path):
    client, execute = api
    execute.side_effect = RuntimeError("offline database unavailable")
    assert client.get(path).status_code == 500


@pytest.mark.parametrize("path", ["/api/cargoCategory", "/api/cargoType", "/api/cargoType/1040", "/api/origins", "/api/origins/3"])
def test_catalog_routes_still_require_authentication(api, path):
    client, execute = api
    client.app.dependency_overrides.clear()
    # FastAPI versions differ on a missing bearer header (401 versus 403).
    # Invalid bearer credentials must still hit the application's 401 path.
    assert client.get(path).status_code in (401, 403)
    assert client.get(path, headers={"Authorization": "Bearer invalid-offline-token"}).status_code == 401
    execute.assert_not_called()
