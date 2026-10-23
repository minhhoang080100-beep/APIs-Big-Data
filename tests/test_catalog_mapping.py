"""Offline catalog identity/mapping regressions; no SQL Server or credentials."""

from datetime import datetime
from itertools import permutations
import sqlite3

import pytest

from catalog_mapping import (
    canonical_container_sizes, canonical_handling_methods, container_dimensions,
    container_sizes_query, handling_methods_query,
)
from test_vietsun_scope import api  # noqa: F401


def size(size_id=321, iso="45G0", alias=None, **extra):
    return {
        "containerSizeTypeId": size_id, "containerSizeTypeCode": iso,
        "containerLengthFt": 0, "containerHeightFt": 0,
        "containerSizeTypeDomesticCode": alias,
        "createTime": "2020-01-01T00:00:00", "updateTime": None, **extra,
    }


def method(code="NTAU", name="Name A", **extra):
    return {"jobMethodCode": code, "jobMethodName": name,
            "createTime": None, "updateTime": None, **extra}


@pytest.mark.parametrize("iso,expected", [
    ("22G0", ("20", "86", "G0")), ("42G0", ("40", "86", "G0")),
    ("45G0", ("40", "96", "G0")), ("L5G1", ("45", "96", "G1")),
    ("20T5", ("20", "80", "T5")), ("28P1", ("20", "43", "P1")),
    ("2CG0", ("20", "86", "G0")), ("2NG0", ("20", "96", "G0")),
    ("26G0", ("20", "", "G0")), ("7ZG0", ("", "", "G0")),
    ("", ("", "", "")), ("20", ("", "", "")),
    ("45HCX", ("", "", "")), (" 45g0 ", ("40", "96", "G0")),
])
def test_iso_dimensions_without_domestic_prefix_guessing(iso, expected):
    assert container_dimensions(size(iso=iso, alias="99WRONG")) == expected


@pytest.mark.parametrize("value", [None, 0, -1, "", "bad", float("nan"), float("inf")])
def test_missing_dimensions_fall_back_to_iso(value):
    assert container_dimensions(size(containerLengthFt=value, containerHeightFt=value)) == ("40", "96", "G0")


@pytest.mark.parametrize("height,expected", [(8.5, "86"), (9.5, "96"), (9, "90"), (4.25, "43")])
def test_physical_feet_height_uses_inches_not_decimal_times_ten(height, expected):
    assert container_dimensions(size(iso="", containerHeightFt=height)) == ("", expected, "")


def test_non_integral_inch_height_is_not_silently_rounded():
    assert container_dimensions(size(iso="", containerHeightFt=8.6))[1] == ""


def test_positive_source_length_is_preserved():
    assert container_dimensions(size(iso="", containerLengthFt=24.5))[0] == "24.5"


def test_known_iso_dimensions_take_priority_over_conflicting_physical_fields():
    assert container_dimensions(size(iso="22G0", containerLengthFt=40, containerHeightFt=9.5)) == ("20", "86", "G0")


def test_empty_container_filter_keeps_existing_unfiltered_behavior():
    assert container_sizes_query("") == container_sizes_query()


def test_container_canonicalization_is_order_independent_and_keeps_aliases():
    rows = [size(alias="40HC"), size(alias="45G"), size(alias="40HC")]
    expected = canonical_container_sizes(rows)
    for ordering in permutations(rows):
        assert canonical_container_sizes(ordering) == expected
    assert len(expected) == 1
    assert expected[0]["containerSizeTypeId"] == 321
    assert expected[0]["localSzTp"] == ""
    assert expected[0]["localSzTpAliases"] == ["40HC", "45G"]


@pytest.mark.parametrize("alias,scalar,aliases", [
    (None, "", []), ("", "", []), ("   ", "", []), ("20GP", "20GP", ["20GP"]),
])
def test_container_alias_missing_or_unique(alias, scalar, aliases):
    row = canonical_container_sizes([size(alias=alias)])[0]
    assert row["localSzTp"] == scalar
    assert row["localSzTpAliases"] == aliases


def test_conflicting_master_attributes_fail_instead_of_picking_first():
    with pytest.raises(ValueError, match="Conflicting container"):
        canonical_container_sizes([size(), size(iso="L5G1")])


def test_methods_keep_exact_ids_and_all_names_with_stable_dates():
    rows = [
        method(name="Name Z", createTime="2021-02-01T00:00:00", updateTime="2025-01-01T00:00:00"),
        method(name="Name A", createTime=datetime(2020, 1, 1), updateTime=datetime(2026, 1, 1)),
        method(name="Name A"), method("ntau", "Another exact ID"),
        method(None), method("   "), method("UNKNOWN", None), method("EMPTY", "   "),
    ]
    result = canonical_handling_methods(rows)
    assert result == canonical_handling_methods(list(reversed(rows)))
    assert [r["jobMethodCode"] for r in result] == ["EMPTY", "NTAU", "UNKNOWN", "ntau"]
    row = next(r for r in result if r["jobMethodCode"] == "NTAU")
    assert row["jobMethodName"] == "Name A / Name Z"
    assert row["createTime"] == "2020-01-01T00:00:00"
    assert row["updateTime"] == "2026-01-01T00:00:00"
    assert result[0]["jobMethodName"] == ""


@pytest.mark.parametrize("builder", [handling_methods_query, container_sizes_query])
def test_lookup_parameterized_not_interpolated(builder):
    query, params = builder("' OR 1=1 --")
    assert "' OR 1=1 --" not in query
    assert params == ("' OR 1=1 --",)
    assert query.count("?") == 1


def test_method_sql_does_not_collapse_exact_ids_under_ci_collation():
    query, params = handling_methods_query()
    assert "GROUP BY" not in query and "DISTINCT" not in query
    assert params is None


@pytest.fixture
def catalog_db():
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("ATTACH DATABASE ':memory:' AS dbo")
    connection.executescript("""
        CREATE TABLE dbo.ContainerSizeType (
            containerSizeTypeId INTEGER PRIMARY KEY, containerSizeTypeCode TEXT,
            containerLengthFt REAL, containerHeightFt REAL, createTime TEXT,
            updateTime TEXT, rowDeleted INTEGER, rowInvisible INTEGER
        );
        CREATE TABLE dbo.ContainerSizeTypeDomestic (
            containerSizeTypeDomesticId INTEGER PRIMARY KEY,
            containerSizeTypeId INTEGER, containerSizeTypeDomesticCode TEXT,
            rowDeleted INTEGER, rowInvisible INTEGER
        );
        INSERT INTO dbo.ContainerSizeType VALUES
            (73,'22G0',0,0,NULL,NULL,0,0), (241,'42G0',0,0,NULL,NULL,0,0),
            (321,'45G0',0,0,NULL,NULL,0,0), (900,'L5G1',0,0,NULL,NULL,0,0),
            (901,'22G1',0,0,NULL,NULL,0,1), (902,'22R1',0,0,NULL,NULL,1,0);
        INSERT INTO dbo.ContainerSizeTypeDomestic VALUES
            (1,73,'20GP',0,0), (2,321,'40HC',0,0), (3,321,'45G',0,0),
            (4,241,'DELETED',1,0), (5,241,'HIDDEN',0,1), (6,901,'hiddenMaster',0,0);
    """)
    try:
        yield connection
    finally:
        connection.close()


def query_sqlite(connection, sql, params=None):
    # SQLite checks join/filter semantics; this is NOT SQL Server verification.
    return [dict(row) for row in connection.execute(sql.replace("ISNULL(", "IFNULL("), params or ())]


def test_base_driven_sql_keeps_unaliased_masters_and_filters_aliases(catalog_db):
    rows = canonical_container_sizes(query_sqlite(catalog_db, *container_sizes_query()))
    assert [r["containerSizeTypeId"] for r in rows] == [73, 241, 321, 900]
    assert rows[1]["localSzTpAliases"] == []
    assert rows[2]["localSzTpAliases"] == ["40HC", "45G"]
    assert rows[3]["sizeCode"] == "45"


def test_container_http_filtered_and_list_are_identical(api, catalog_db):
    client, execute = api
    execute.side_effect = lambda sql, params: query_sqlite(catalog_db, sql, params)
    listed = client.get("/api/containerSize").json()["data"]
    for row in listed:
        response = client.get("/api/containerSize", params={"containerSizeId": row["containerSizeId"]})
        assert response.status_code == 200
        assert response.json()["data"] == [row]
    assert client.get("/api/containerSize", params={"containerSizeId": "missing"}).json()["data"] == []


def test_handling_http_list_and_detail_merge_same_names(api):
    client, execute = api
    execute.return_value = [method(name="B"), method(name="A"), method(name="A")]
    listed = client.get("/api/handlingMethodList")
    detail = client.get("/api/handlingMethodList/NTAU")
    assert listed.status_code == detail.status_code == 200
    assert listed.json()["data"] == [detail.json()["data"]]
    assert detail.json()["data"]["handlingMethodName"] == "A / B"


def test_handling_ambiguous_lookup_is_not_arbitrary(api):
    client, execute = api
    execute.return_value = [method("NTAU"), method("ntau")]
    assert client.get("/api/handlingMethodList/NTAU").status_code == 409


def test_handling_missing_still_404(api):
    client, execute = api
    execute.return_value = []
    assert client.get("/api/handlingMethodList/missing").status_code == 404


def test_container_master_conflict_returns_failure_not_success(api):
    client, execute = api
    execute.return_value = [size(), size(iso="L5G1")]
    assert client.get("/api/containerSize").status_code == 500
