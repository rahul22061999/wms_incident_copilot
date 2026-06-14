"""
SQL safety guard tests.

These run in CI with no external dependencies — no LLM calls, no DB, no network.
AsyncWMSSQLService._validate_sql is pure Python and security-critical: it is the
only thing preventing LLM-generated SQL from mutating the WMS database.
"""

from unittest.mock import MagicMock

import pytest

from utils.sql_tools import AsyncWMSSQLService


@pytest.fixture
def service():
    return AsyncWMSSQLService(engine=MagicMock())


# ── valid queries ────────────────────────────────────────────────────────────

def test_accepts_select(service):
    sql = service._validate_sql("SELECT sku, SUM(unit_qty) FROM wms1.inventory GROUP BY sku")
    assert sql.startswith("SELECT")


def test_accepts_with_cte(service):
    sql = service._validate_sql("WITH cte AS (SELECT id FROM wms1.pckwrk) SELECT * FROM cte")
    assert sql.startswith("WITH")


def test_strips_trailing_semicolon(service):
    sql = service._validate_sql("SELECT 1;")
    assert ";" not in sql


# ── write operations blocked ─────────────────────────────────────────────────

@pytest.mark.parametrize("bad_sql", [
    "DELETE FROM wms1.inventory WHERE sku = 'SKU001'",
    "INSERT INTO wms1.inventory (sku) VALUES ('SKU999')",
    "UPDATE wms1.inventory SET unit_qty = 0",
    "DROP TABLE wms1.inventory",
    "ALTER TABLE wms1.inventory ADD COLUMN foo TEXT",
    "TRUNCATE wms1.inventory",
])
def test_rejects_write_operations(service, bad_sql):
    with pytest.raises(ValueError):
        service._validate_sql(bad_sql)


# ── injection patterns blocked ───────────────────────────────────────────────

def test_rejects_multiple_statements(service):
    with pytest.raises(ValueError, match="Multiple statements"):
        service._validate_sql("SELECT 1; SELECT 2")


def test_rejects_select_with_embedded_delete(service):
    # blocked-keyword check fires before semicolon check
    with pytest.raises(ValueError, match="Blocked"):
        service._validate_sql("SELECT * FROM t WHERE 1=1; DELETE FROM t")


def test_rejects_empty_sql(service):
    with pytest.raises(ValueError, match="Empty SQL"):
        service._validate_sql("   ")
