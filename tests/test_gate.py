from __future__ import annotations

import pytest

from energy_lakehouse.dq.gate import (
    DQGateError,
    failures,
    validate_stage,
)
from energy_lakehouse.models import DQResult, DQStatus


def _result(status: DQStatus, table: str = "silver.demand_daily") -> DQResult:
    return DQResult(
        check="value_range",
        table=table,
        status=status,
        observed=1.0,
        threshold=0.0,
        details="1 rows outside [0.0, inf]",
        column="value",
    )


def test_validate_stage_accepts_silver() -> None:
    assert validate_stage("silver") == "silver"


def test_validate_stage_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="stage must be one of"):
        validate_stage("bronze")


def test_failures_filters_only_failing_results() -> None:
    results = [_result(DQStatus.PASS), _result(DQStatus.FAIL), _result(DQStatus.PASS)]
    failed = failures(results)
    assert len(failed) == 1
    assert failed[0].status is DQStatus.FAIL


def test_dq_gate_error_summarizes_every_failure() -> None:
    failed = [_result(DQStatus.FAIL, "silver.demand_daily")]
    err = DQGateError(failed)
    assert err.failures == failed
    assert "silver.demand_daily" in str(err)
    assert "value_range" in str(err)
    assert "1 check(s)" in str(err)
