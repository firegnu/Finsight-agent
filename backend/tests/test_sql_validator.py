import pytest

from backend.tools.sql_query import validate_sql_readonly, SQLValidationError


def test_accepts_simple_select():
    validate_sql_readonly("SELECT * FROM credit_card_metrics")


def test_accepts_select_with_where():
    validate_sql_readonly("SELECT year_month FROM credit_card_metrics WHERE region='华东'")


def test_accepts_aggregate():
    validate_sql_readonly("SELECT region, AVG(overdue_rate) FROM credit_card_metrics GROUP BY region")


def test_accepts_trailing_semicolon():
    validate_sql_readonly("SELECT 1 FROM credit_card_metrics;")


def test_rejects_insert():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("INSERT INTO credit_card_metrics VALUES (1)")


def test_rejects_update():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("UPDATE credit_card_metrics SET overdue_rate=0")


def test_rejects_delete():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("DELETE FROM credit_card_metrics")


def test_rejects_drop():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("DROP TABLE credit_card_metrics")


def test_rejects_multiple_statements():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("SELECT 1; DELETE FROM credit_card_metrics")


def test_rejects_attach():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("ATTACH DATABASE 'foo.db' AS bar")


def test_rejects_pragma():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("PRAGMA table_info(credit_card_metrics)")
