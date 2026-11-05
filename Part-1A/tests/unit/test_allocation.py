from itertools import product

from asset_allocation.allocation import allocate


def test_baseline_allocation() -> None:
    assert allocate(age=40, horizon_years=10, risk_tolerance=5) == (60, 40)


def test_risk_adjustments() -> None:
    assert allocate(age=40, horizon_years=10, risk_tolerance=1) == (44, 56)
    assert allocate(age=40, horizon_years=10, risk_tolerance=10) == (80, 20)


def test_clamps_upper_and_lower_equity_values() -> None:
    assert allocate(age=18, horizon_years=80, risk_tolerance=10) == (100, 0)
    assert allocate(age=100, horizon_years=1, risk_tolerance=1) == (0, 100)


def test_all_valid_inputs_preserve_percentage_invariants() -> None:
    for age, horizon_years, risk_tolerance in product(
        range(18, 101),
        range(1, 81),
        range(1, 11),
    ):
        result = allocate(age, horizon_years, risk_tolerance)
        assert type(result.equities_percent) is int
        assert type(result.fixed_income_percent) is int
        assert 0 <= result.equities_percent <= 100
        assert 0 <= result.fixed_income_percent <= 100
        assert result.equities_percent + result.fixed_income_percent == 100


def test_same_input_returns_same_allocation() -> None:
    first = allocate(age=40, horizon_years=10, risk_tolerance=5)
    second = allocate(age=40, horizon_years=10, risk_tolerance=5)

    assert first == second
