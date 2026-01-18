from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd  # type: ignore
import pytest

# ---------------------------------------------------------------------------
# Repo root resolution (RACB-compatible + local fallback)
# ---------------------------------------------------------------------------

PACKAGE_NAME = "lifelines"

_racb_root = os.environ.get("RACB_REPO_ROOT", "").strip()
if _racb_root:
    REPO_ROOT = Path(_racb_root).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.environ.get("LIFELINES_TARGET", "reference").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "lifelines"
    else:
        REPO_ROOT = ROOT / "generation" / "Lifelines"

if not REPO_ROOT.exists():
    pytest.skip(
        "Target repository does not exist: {}".format(REPO_ROOT),
        allow_module_level=True,
    )

src_pkg_init = REPO_ROOT / "src" / PACKAGE_NAME / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE_NAME / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find '{}' package under repo root. Expected {} or {}.".format(
            PACKAGE_NAME, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )

try:
    from lifelines import KaplanMeierFitter, CoxPHFitter  # type: ignore  # noqa: E402
    from lifelines.datasets import load_waltons  # type: ignore  # noqa: E402
except Exception as exc:
    pytest.skip(
        "Failed to import lifelines from {}: {}".format(REPO_ROOT, exc),
        allow_module_level=True,
    )


def _toy_kmf_data():
    durations = [5, 6, 6, 2, 4, 3]
    events = [1, 0, 1, 1, 1, 0]
    return durations, events


def _toy_cox_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "duration": [5, 6, 6, 2, 4, 3, 8, 7],
            "event": [1, 0, 1, 1, 1, 0, 1, 1],
            "age": [30, 40, 50, 20, 60, 35, 45, 55],
            "treatment": [0, 0, 1, 1, 1, 0, 1, 0],
        }
    )


# ---------------------------------------------------------------------------
# Original tests (kept intent)
# ---------------------------------------------------------------------------

def test_kmf_on_small_manual_dataset() -> None:
    """Basic sanity check for KaplanMeierFitter on a tiny dataset."""
    durations, events = _toy_kmf_data()

    kmf = KaplanMeierFitter()
    kmf.fit(durations=durations, event_observed=events, label="test")
    sf = kmf.survival_function_

    values = sf["test"].values
    assert 0.0 < values[0] <= 1.0
    for i in range(1, len(values)):
        assert values[i] <= values[i - 1] + 1e-8
    assert 0.0 <= values[-1] <= 1.0


def test_kmf_on_waltons_groups() -> None:
    """Fit KMF on the Waltons dataset for two groups."""
    df = load_waltons()
    assert {"T", "E", "group"}.issubset(df.columns)

    control = df[df["group"] == "control"]
    treated = df[df["group"] != "control"]

    kmf_control = KaplanMeierFitter()
    kmf_treated = KaplanMeierFitter()

    kmf_control.fit(control["T"], control["E"], label="control")
    kmf_treated.fit(treated["T"], treated["E"], label="treated")

    t = 10.0
    s_control = float(kmf_control.predict(t))
    s_treated = float(kmf_treated.predict(t))

    assert 0.0 <= s_control <= 1.0
    assert 0.0 <= s_treated <= 1.0
    assert abs(s_control - s_treated) > 1e-3


def test_coxph_basic_fit() -> None:
    """Fit a simple Cox proportional hazards model on a toy dataset."""
    df = _toy_cox_df()

    cph = CoxPHFitter()
    cph.fit(df, duration_col="duration", event_col="event")
    summary = cph.summary

    assert "coef" in summary.columns
    assert "se(coef)" in summary.columns
    assert "p" in summary.columns or "p" in "".join(summary.columns).lower()

    if "exp(coef)" in summary.columns:
        assert (summary["exp(coef)"] > 0).all()


# ---------------------------------------------------------------------------
# Added functional (happy-path) coverage (>= 10 test_* total)
# ---------------------------------------------------------------------------

def test_kmf_predict_at_time_zero_is_one() -> None:
    """KMF predict at t=0 should be 1.0 for standard KM survival."""
    durations, events = _toy_kmf_data()
    kmf = KaplanMeierFitter().fit(durations=durations, event_observed=events, label="km")
    s0 = float(kmf.predict(0.0))
    assert 0.99 <= s0 <= 1.0


def test_kmf_predict_is_non_increasing_over_time() -> None:
    """KMF predicted survival should not increase as time increases."""
    durations, events = _toy_kmf_data()
    kmf = KaplanMeierFitter().fit(durations=durations, event_observed=events, label="km")

    s1 = float(kmf.predict(1.0))
    s3 = float(kmf.predict(3.0))
    s10 = float(kmf.predict(10.0))

    eps = 1e-8

    # Bounds (avoid chaining eps into the hard upper bound 1.0)
    assert 0.0 <= s1 <= 1.0
    assert 0.0 <= s3 <= 1.0
    assert 0.0 <= s10 <= 1.0

    # Monotonic non-increasing (allow tiny numerical wiggle)
    assert s3 <= s1 + eps
    assert s10 <= s3 + eps


def test_kmf_cumulative_density_is_non_decreasing() -> None:
    """Cumulative density should be non-decreasing and within [0, 1]."""
    durations, events = _toy_kmf_data()
    kmf = KaplanMeierFitter().fit(durations=durations, event_observed=events, label="km")
    cd = kmf.cumulative_density_

    values = cd.iloc[:, 0].values
    assert 0.0 <= float(values[0]) <= 1.0
    for i in range(1, len(values)):
        assert values[i] >= values[i - 1] - 1e-8
    assert 0.0 <= float(values[-1]) <= 1.0


def test_kmf_event_table_has_standard_columns() -> None:
    """KM event table should include standard bookkeeping columns."""
    durations, events = _toy_kmf_data()
    kmf = KaplanMeierFitter().fit(durations=durations, event_observed=events, label="km")
    et = kmf.event_table
    for col in ["removed", "observed", "censored", "at_risk"]:
        assert col in et.columns


def test_kmf_confidence_interval_matches_survival_index() -> None:
    """Confidence intervals should align with survival function index."""
    durations, events = _toy_kmf_data()
    kmf = KaplanMeierFitter().fit(durations=durations, event_observed=events, label="km")
    ci = kmf.confidence_interval_
    sf = kmf.survival_function_

    assert hasattr(ci, "index")
    assert ci.index.equals(sf.index)
    assert ci.shape[0] == sf.shape[0]
    assert ci.shape[1] >= 2


def test_kmf_median_survival_time_is_within_duration_range() -> None:
    """Median survival time should be within the observed duration range."""
    durations, events = _toy_kmf_data()
    kmf = KaplanMeierFitter().fit(durations=durations, event_observed=events, label="km")

    m = float(kmf.median_survival_time_)
    assert min(durations) <= m <= max(durations)


def test_coxph_params_index_matches_covariates() -> None:
    """Cox model params_ should be indexed by covariate names."""
    df = _toy_cox_df()
    cph = CoxPHFitter().fit(df, duration_col="duration", event_col="event")

    params = cph.params_
    assert list(params.index) == ["age", "treatment"]
    assert params.shape[0] == 2


def test_coxph_baseline_cumulative_hazard_is_non_decreasing() -> None:
    """Baseline cumulative hazard should be non-decreasing over time."""
    df = _toy_cox_df()
    cph = CoxPHFitter().fit(df, duration_col="duration", event_col="event")

    bch = cph.baseline_cumulative_hazard_
    assert isinstance(bch, pd.DataFrame)
    vals = bch.iloc[:, 0].values
    for i in range(1, len(vals)):
        assert vals[i] >= vals[i - 1] - 1e-10


def test_coxph_predict_partial_hazard_is_positive_and_varies() -> None:
    """Partial hazards should be positive and reflect covariate differences."""
    df = _toy_cox_df()
    cph = CoxPHFitter().fit(df, duration_col="duration", event_col="event")

    x_low = pd.DataFrame({"age": [25], "treatment": [0]})
    x_high = pd.DataFrame({"age": [55], "treatment": [1]})

    h_low = float(cph.predict_partial_hazard(x_low).iloc[0])
    h_high = float(cph.predict_partial_hazard(x_high).iloc[0])

    assert h_low > 0.0
    assert h_high > 0.0
    assert abs(h_low - h_high) > 1e-12


def test_coxph_predict_survival_function_shape_and_bounds() -> None:
    """Predict survival functions for two individuals; verify shape and bounds."""
    df = _toy_cox_df()
    cph = CoxPHFitter().fit(df, duration_col="duration", event_col="event")

    x = pd.DataFrame({"age": [30, 60], "treatment": [0, 1]})
    sf = cph.predict_survival_function(x)

    assert isinstance(sf, pd.DataFrame)
    assert sf.shape[1] == 2
    assert sf.shape[0] > 1

    col0 = sf.iloc[:, 0].values
    assert 0.0 <= float(col0[-1]) <= float(col0[0]) <= 1.0


def test_coxph_concordance_index_in_unit_interval() -> None:
    """Concordance index should lie in [0, 1] after fitting."""
    df = _toy_cox_df()
    cph = CoxPHFitter().fit(df, duration_col="duration", event_col="event")

    c = float(cph.concordance_index_)
    assert 0.0 <= c <= 1.0


def test_coxph_fit_on_waltons_with_binary_group_feature() -> None:
    """Fit CoxPH on Waltons dataset using a binary treated indicator derived from group."""
    df = load_waltons()
    assert {"T", "E", "group"}.issubset(df.columns)

    df2 = df.copy()
    df2["treated"] = (df2["group"] != "control").astype(int)

    model_df = df2[["T", "E", "treated"]].rename(columns={"T": "duration", "E": "event"})

    cph = CoxPHFitter()
    cph.fit(model_df, duration_col="duration", event_col="event")

    coef = float(cph.params_.loc["treated"])
    assert coef == coef  # not NaN
