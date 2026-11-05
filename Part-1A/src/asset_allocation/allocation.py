"""Pure asset allocation calculation."""

from typing import NamedTuple


class Allocation(NamedTuple):
    equities_percent: int
    fixed_income_percent: int


def allocate(age: int, horizon_years: int, risk_tolerance: int) -> Allocation:
    """Calculate the rule-based equity and fixed-income percentages."""
    raw_equities = (
        100
        - age
        + 4 * (risk_tolerance - 5)
        + 2 * (horizon_years - 10)
    )
    equities = min(100, max(0, raw_equities))
    return Allocation(
        equities_percent=equities,
        fixed_income_percent=100 - equities,
    )
