"""HITL approvals persistence — one decision per report_id."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from .database import execute, query_one

Decision = Literal["approved", "rejected"]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def submit_decision(
    report_id: str,
    decision: Decision,
    trace_id: str | None = None,
    decided_by: str | None = None,
    note: str | None = None,
) -> dict:
    """Insert-or-replace (upsert) the approval decision for a report.
    Returns the stored record."""
    if decision not in ("approved", "rejected"):
        raise ValueError(f"invalid decision: {decision}")

    decided_at = _utc_iso()
    # SQLite upsert (requires >= 3.24). report_id has UNIQUE constraint.
    execute(
        "INSERT INTO approvals (report_id, trace_id, decision, decided_by, note, decided_at) "
        "VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(report_id) DO UPDATE SET "
        "  trace_id = excluded.trace_id, "
        "  decision = excluded.decision, "
        "  decided_by = excluded.decided_by, "
        "  note = excluded.note, "
        "  decided_at = excluded.decided_at",
        (report_id, trace_id, decision, decided_by, note, decided_at),
    )
    return {
        "report_id": report_id,
        "trace_id": trace_id,
        "decision": decision,
        "decided_by": decided_by,
        "note": note,
        "decided_at": decided_at,
    }


def get_decision(report_id: str) -> dict | None:
    return query_one(
        "SELECT report_id, trace_id, decision, decided_by, note, decided_at "
        "FROM approvals WHERE report_id = ?",
        (report_id,),
    )


def revoke_decision(report_id: str) -> bool:
    """Remove an approval record. Returns True if a row was deleted."""
    before = get_decision(report_id)
    if not before:
        return False
    execute("DELETE FROM approvals WHERE report_id = ?", (report_id,))
    return True
