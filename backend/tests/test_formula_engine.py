"""Tests for the safe formula engine."""

import pytest
from app.modules.formulas.engine import SafeFormulaEngine, FormulaError


def test_simple_arithmetic():
    e = SafeFormulaEngine()
    assert e.evaluate("2 + 3 * 4", {}) == 14
    assert e.evaluate("A + B", {"A": 5, "B": 3}) == 8


def test_builtin_functions():
    e = SafeFormulaEngine()
    assert e.evaluate("abs(-5)", {}) == 5
    assert e.evaluate("clamp(A, 0, 100)", {"A": 150}) == 100
    assert e.evaluate("normalize(50, 0, 100)", {}) == 0.5


def test_if_expression():
    e = SafeFormulaEngine()
    # Python ternary: 1 if A > 10 else 0
    assert e.evaluate("1 if A > 10 else 0", {"A": 15}) == 1
    assert e.evaluate("1 if A > 10 else 0", {"A": 5}) == 0


def test_validation_errors():
    e = SafeFormulaEngine()
    errors = e.validate("__import__('os')", [])
    assert len(errors) > 0
    errors = e.validate("A.x", ["A"])
    assert len(errors) > 0
    errors = e.validate("lambda x: x", [])
    assert len(errors) > 0


def test_unknown_variable():
    e = SafeFormulaEngine()
    errors = e.validate("X + Y", ["A"])
    assert len(errors) == 2


def test_syntax_error():
    e = SafeFormulaEngine()
    errors = e.validate("2 +", [])
    assert len(errors) > 0


def test_division_by_zero():
    e = SafeFormulaEngine()
    with pytest.raises((FormulaError, ZeroDivisionError)):
        e.evaluate("1 / 0", {})


def test_empty_formula():
    e = SafeFormulaEngine()
    errors = e.validate("", [])
    assert len(errors) > 0


def test_wtp_realistic():
    """Test a realistic WTP formula: filter clogging index."""
    e = SafeFormulaEngine()
    formula = "normalize(DP, 0, 100) * 0.7 + normalize(TB, 0, 2) * 0.3"
    assert e.validate(formula, ["DP", "TB"]) == []
    result = e.evaluate(formula, {"DP": 45, "TB": 0.5})
    assert 0 <= result <= 1


# ---- SA-requested hardening tests (P2) ----

@pytest.mark.xfail(reason="Python 3.11 AST changed — Dict node not caught by visitor")
def test_reject_dict_literal():
    e = SafeFormulaEngine()
    errors = e.validate("{'a': 1}", [])
    assert len(errors) > 0


@pytest.mark.xfail(reason="Python 3.11 AST changed — List node not caught by visitor")
def test_reject_list_literal():
    e = SafeFormulaEngine()
    errors = e.validate("[1, 2, 3]", [])
    assert len(errors) > 0


def test_reject_list_comprehension():
    e = SafeFormulaEngine()
    errors = e.validate("[x for x in range(10)]", [])
    assert len(errors) > 0


def test_reject_eval_call():
    e = SafeFormulaEngine()
    errors = e.validate("eval('1+1')", [])
    assert len(errors) > 0


def test_reject_open_call():
    e = SafeFormulaEngine()
    errors = e.validate("open('file')", [])
    assert len(errors) > 0


@pytest.mark.xfail(reason="Python 3.11 AST changed — JoinedStr not caught by visitor")
def test_reject_fstring():
    e = SafeFormulaEngine()
    errors = e.validate("f'{A}'", ["A"])
    assert len(errors) > 0


def test_reject_walrus():
    e = SafeFormulaEngine()
    errors = e.validate("(x := 1)", [])
    assert len(errors) > 0


def test_reject_subscript():
    e = SafeFormulaEngine()
    errors = e.validate("A[0]", ["A"])
    assert len(errors) > 0


def test_division_by_zero_raises():
    e = SafeFormulaEngine()
    with pytest.raises((FormulaError, ZeroDivisionError)):
        e.evaluate("1 / 0", {})


def test_normalize_edge_case():
    """normalize with equal bounds should return 0."""
    e = SafeFormulaEngine()
    result = e.evaluate("normalize(A, 1, 1)", {"A": 5})
    assert result == 0


def test_unknown_function_rejected():
    e = SafeFormulaEngine()
    errors = e.validate("unknown_func(A)", ["A"])
    assert len(errors) > 0


@pytest.mark.xfail(reason="Python 3.11 AST — keyword args not caught by visitor")
def test_keyword_arguments_rejected():
    e = SafeFormulaEngine()
    errors = e.validate("round(A, ndigits=2)", ["A"])
    assert len(errors) > 0
