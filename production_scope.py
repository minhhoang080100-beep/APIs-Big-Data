"""Exclude confirmed VietSun voyages from Cua Lo quay throughput only.

The first actual berth owns the whole voyage, including operations after a
berth move. This is a removal-only rule: missing or ambiguous berth evidence
is retained, not silently treated as confirmed Nghe Tinh production. Yard/gate
pseudo-voyages need their own verified mapping and must not use this filter.

Keep the predicate inside SQL, before pagination. EXISTS preserves tally
cardinality even when berth history has duplicates. The base TallyShift table
provides the voyage identity; vwTallyShiftAll need not expose vesselVoyageId.
No source data is modified and no reporting-date restriction is put on history.
"""


def _actual_time(alias: str) -> str:
    # Aliases are fixed below, never supplied by an API caller.
    return f"""CASE WHEN {alias}.ATB >= '1900-01-01T00:00:00' THEN {alias}.ATB
                   WHEN {alias}.ATA >= '1900-01-01T00:00:00' THEN {alias}.ATA END"""


_first_time = _actual_time("first_berth")
_other_time = _actual_time("other_berth")

# Cua Lo's native berthId 13 must never be applied to another source database.
# The correlated anti-semi-join examines only each selected tally's voyage.
# Do not replace it with a raw DoBerth join or a vessel-name/customer filter.
EXCLUDE_VIETSUN_SQL = f"""
            AND NOT EXISTS (
                SELECT 1
                FROM dbo.TallyShift scope_tally
                JOIN dbo.DoBerth first_berth
                  ON first_berth.vesselVoyageId = scope_tally.vesselVoyageId
                JOIN dbo.Berth first_code ON first_code.berthId = first_berth.berthId
                WHERE scope_tally.tallyShiftId = t.tallyShiftId
                  AND LOWER(DB_NAME()) = 'smarttos'
                  AND COALESCE(first_berth.rowDeleted, 0) = 0
                  AND first_berth.berthId = 13
                  AND NULLIF(LTRIM(RTRIM(first_code.berthCode)), '') IS NOT NULL
                  AND ({_first_time}) IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1
                      FROM dbo.DoBerth other_berth
                      LEFT JOIN dbo.Berth other_code
                        ON other_code.berthId = other_berth.berthId
                      WHERE other_berth.vesselVoyageId = scope_tally.vesselVoyageId
                        AND COALESCE(other_berth.rowDeleted, 0) = 0
                        AND (other_berth.isArrival = 1
                             OR other_berth.ATB >= '1900-01-01T00:00:00'
                             OR other_berth.ATA >= '1900-01-01T00:00:00')
                        AND (
                            ({_other_time}) IS NULL
                            OR ({_other_time}) < ({_first_time})
                            OR (({_other_time}) = ({_first_time}) AND (
                                other_berth.berthId IS NULL
                                OR other_berth.berthId <> 13
                                OR NULLIF(LTRIM(RTRIM(other_code.berthCode)), '') IS NULL
                            ))
                        )
                  )
            )
"""

