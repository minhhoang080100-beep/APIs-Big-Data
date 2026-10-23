"""Read-only verification of catalog SQL against the configured real database.

Run explicitly: python -B scripts/check_catalogs_sql.py --connect
Uses local configuration; never prints credentials, source names or aliases.
Prints aggregate JSON to stdout, makes no source-data or filesystem writes.
Requires live SQL connectivity; offline unit tests are not a substitute.
"""

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connect", action="store_true", help="Opt in to a real read-only SQL connection")
    args = parser.parse_args()
    if not args.connect:
        parser.error("Pass --connect to explicitly run the real-database check")

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    logging.disable(logging.CRITICAL)
    import pyodbc
    from database import db
    from catalog_mapping import (
        canonical_container_sizes, canonical_handling_methods,
        container_sizes_query, handling_methods_query,
    )

    started = time.monotonic()
    report = {"activity": "read_only_sql", "started_at_utc": datetime.now(timezone.utc).isoformat()}
    connection = None
    try:
        connection = pyodbc.connect(db.get_connection_string(), timeout=12)
        connection.timeout = 20
        cursor = connection.cursor()

        def read(query, params=None):
            cursor.execute(query, params) if params else cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        method_source = read(*handling_methods_query())
        methods = canonical_handling_methods(method_source)
        sizes = canonical_container_sizes(read(*container_sizes_query()))
        old_size_ids = {row["containerSizeTypeId"] for row in read("""
            SELECT DISTINCT containerSizeTypeId FROM dbo.vwContainerSizeTypeDomestic
            WHERE ISNULL(rowDeleted,0)=0 AND ISNULL(rowInvisible,0)=0
        """)}
        new_size_ids = {row["containerSizeTypeId"] for row in sizes}
        method_codes = {str(row["jobMethodCode"]) for row in method_source if str(row["jobMethodCode"]).strip()}
        checks = {
            "nonempty_methods": bool(methods), "nonempty_sizes": bool(sizes),
            "unique_method_ids": len(methods) == len({row["jobMethodCode"] for row in methods}),
            "all_source_method_codes_preserved": method_codes == {row["jobMethodCode"] for row in methods},
            "unique_container_ids": len(sizes) == len(new_size_ids),
            "all_previous_container_ids_preserved": old_size_ids <= new_size_ids,
        }
        for size_id, expected in {73: ("20", "86", "G0"), 241: ("40", "86", "G0"), 321: ("40", "96", "G0")}.items():
            matching = [row for row in sizes if row["containerSizeTypeId"] == size_id]
            checks[f"container_{size_id}_dimensions"] = len(matching) == 1 and tuple(
                matching[0][field] for field in ("sizeCode", "heightCode", "containerTypeCode")
            ) == expected
        report.update({
            "query_execution_verified": True, "checks": checks, "passed": all(checks.values()),
            "method_source_rows": len(method_source), "method_rows": len(methods),
            "container_rows": len(sizes), "previous_container_unique_ids": len(old_size_ids),
            "missing_previous_container_id_count": len(old_size_ids - new_size_ids),
            "added_container_id_count": len(new_size_ids - old_size_ids),
            "container_multiple_alias_count": sum(len(row["localSzTpAliases"]) > 1 for row in sizes),
            "limitations": ["Sequential SELECTs are not a transactional snapshot.",
                            "Does not verify HTTP deployment or all production foreign keys."],
        })
    except Exception as exc:
        report.update({"query_execution_verified": False, "passed": False,
                       "error_type": type(exc).__name__})
        if isinstance(exc, pyodbc.Error) and exc.args:
            report["sqlstate"] = str(exc.args[0])[:5]
    finally:
        if connection is not None:
            connection.close()
        report["elapsed_seconds"] = round(time.monotonic() - started, 2)
    print(json.dumps(report, ensure_ascii=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
