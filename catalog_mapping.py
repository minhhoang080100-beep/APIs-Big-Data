"""Stable catalog identities; no throughput calculations or source mutations.

Handling IDs remain source codes. Multiple source labels are retained in the
display name, not resolved by arbitrarily choosing a supposedly authoritative
row. Container identity comes from the ISO master, never its domestic aliases.
"""

import math
import re


def handling_methods_query(code=None):
    query = """
        SELECT jobMethodCode, jobMethodName, createTime, updateTime
        FROM dbo.vwJobMethodAll
        WHERE ISNULL(rowDeleted, 0) = 0 AND ISNULL(rowInvisible, 0) = 0
          AND jobMethodCode IS NOT NULL AND LTRIM(RTRIM(jobMethodCode)) <> ''
    """
    params = None
    if code is not None:
        query += " AND jobMethodCode = ?"
        params = (code,)
    # Do not GROUP BY under the server's case-insensitive collation: it could
    # collapse differently spelled source IDs before exact-code consolidation.
    query += " ORDER BY jobMethodCode, jobMethodName"
    return query, params


def _timestamp(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def canonical_handling_methods(rows):
    """One exact source code per item; preserve all non-empty source labels."""
    groups = {}
    for row in rows:
        code = row.get("jobMethodCode")
        if code is None or not str(code).strip():
            continue
        group = groups.setdefault(str(code), {"names": set(), "created": [], "updated": []})
        if row.get("jobMethodName") and str(row["jobMethodName"]).strip():
            group["names"].add(str(row["jobMethodName"]))
        for field, target in (("createTime", "created"), ("updateTime", "updated")):
            if row.get(field) is not None:
                group[target].append(_timestamp(row[field]))
    return [
        {
            "jobMethodCode": code,
            "jobMethodName": " / ".join(sorted(group["names"])),
            "createTime": min(group["created"], default=None),
            "updateTime": max(group["updated"], default=None),
        }
        for code, group in sorted(groups.items())
    ]


def container_sizes_query(size_id=None):
    # LEFT JOIN retains valid ISO masters without a domestic alias. Alias flags
    # belong in ON, so a missing/hidden alias cannot remove a valid master.
    query = """
        SELECT s.containerSizeTypeId, s.containerSizeTypeCode,
               s.containerLengthFt, s.containerHeightFt, s.createTime, s.updateTime,
               d.containerSizeTypeDomesticCode
        FROM dbo.ContainerSizeType AS s
        LEFT JOIN dbo.ContainerSizeTypeDomestic AS d
          ON d.containerSizeTypeId = s.containerSizeTypeId
         AND ISNULL(d.rowDeleted, 0) = 0 AND ISNULL(d.rowInvisible, 0) = 0
        WHERE ISNULL(s.rowDeleted, 0) = 0 AND ISNULL(s.rowInvisible, 0) = 0
    """
    params = ()
    if size_id is not None and size_id != "":
        query += " AND CAST(s.containerSizeTypeId AS VARCHAR) = ?"
        params = (size_id,)
    query += " ORDER BY s.containerSizeTypeId, d.containerSizeTypeDomesticId"
    return query, params


# Physical dimensions, not domestic-code prefixes. References:
# https://www.bic-code.org/size-type-code/
# https://www.hapag-lloyd.com/en/services-information/cargo-fleet/container/container-type-groups.html
# L=45 is explicitly used by Hapag-Lloyd for L5G1. Unmapped/interval codes
# remain unknown rather than inventing a precise dimension.
ISO_LENGTH_FT = {
    "1": "10", "2": "20", "3": "30", "4": "40", "5": "45",
    "B": "24", "C": "24.5", "G": "41", "H": "43", "L": "45",
    "M": "48", "N": "49", "P": "53",
}
ISO_HEIGHT_FT_IN = {
    "0": "80", "2": "86", "4": "90", "5": "96", "8": "43",
    "C": "86", "R": "86", "L": "86",
    "D": "90", "S": "90", "M": "90",
    "E": "96", "T": "96", "N": "96",
}


def _positive_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def container_dimensions(row):
    iso = str(row.get("containerSizeTypeCode") or "").strip().upper()
    valid_iso_shape = re.fullmatch(r"[A-Z0-9]{2}[A-Z][A-Z0-9]", iso) is not None
    length = _positive_number(row.get("containerLengthFt"))
    height = _positive_number(row.get("containerHeightFt"))
    size_code = format(length, "g") if length is not None else ""
    height_code = ""
    if height is not None:
        inches = height * 12
        # Do not round a non-inch value into a different physical size.
        if math.isclose(inches, round(inches), abs_tol=0.01):
            feet, remainder = divmod(round(inches), 12)
            height_code = f"{feet}{remainder}"
    if valid_iso_shape:
        # The ISO master's code defines its nominal dimensions. Use physical
        # fields only for codes without an exact mapped ISO dimension; stale
        # physical fields must not turn a 22G0 master into a 40-foot category.
        size_code = ISO_LENGTH_FT.get(iso[0], "") or size_code
        height_code = ISO_HEIGHT_FT_IN.get(iso[1], "") or height_code
    return size_code, height_code, iso[2:] if valid_iso_shape else ""


def canonical_container_sizes(rows):
    """Merge alias fan-out without inventing a preferred local size/type code.

    localSzTp is populated only when exactly one active alias exists. The
    additive localSzTpAliases field retains every alias for explicit consumers.
    """
    groups = {}
    master_fields = (
        "containerSizeTypeCode", "containerLengthFt", "containerHeightFt",
        "createTime", "updateTime",
    )
    for row in rows:
        size_id = int(row["containerSizeTypeId"])
        master = {field: row.get(field) for field in master_fields}
        if size_id not in groups:
            groups[size_id] = {"master": master, "aliases": set()}
        elif groups[size_id]["master"] != master:
            # SQL master ID is unique; don't silently pick conflicting values
            # if that invariant is ever violated by a future source change.
            raise ValueError("Conflicting container master attributes")
        alias = row.get("containerSizeTypeDomesticCode")
        if alias and str(alias).strip():
            groups[size_id]["aliases"].add(str(alias))
    result = []
    for size_id, group in sorted(groups.items()):
        row = dict(group["master"], containerSizeTypeId=size_id)
        aliases = sorted(group["aliases"])
        row["localSzTp"] = aliases[0] if len(aliases) == 1 else ""
        row["localSzTpAliases"] = aliases
        row["sizeCode"], row["heightCode"], row["containerTypeCode"] = container_dimensions(row)
        result.append(row)
    return result
