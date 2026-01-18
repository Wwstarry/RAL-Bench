from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd  # type: ignore

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("LIFELINES_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "lifelines"
else:
    REPO_ROOT = ROOT / "generation" / "Lifelines"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lifelines import KaplanMeierFitter, CoxPHFitter  # type: ignore  # noqa: E402
from lifelines.datasets import load_waltons  # type: ignore  # noqa: E402


def _prepare_regression_frame() -> pd.DataFrame:
    """Prepare a regression-ready DataFrame from the Waltons dataset."""
    df = load_waltons()
    # Use one-hot encoding for the "group" column.
    df_reg = pd.get_dummies(df, columns=["group"], drop_first=True)
    # Rename to more generic names for the Cox model.
    df_reg = df_reg.rename(columns={"T": "duration", "E": "event"})
    return df_reg


def test_waltons_kmf_and_cox_integration() -> None:
    """End-to-end integration test combining KMF and CoxPH on Waltons dataset."""
    df = load_waltons()
    kmf = KaplanMeierFitter()

    for name, group_df in df.groupby("group"):
        kmf.fit(group_df["T"], group_df["E"], label=name)
        sf = kmf.survival_function_
        # Survival function should be non-increasing.
        values = sf[name].values
        for i in range(1, len(values)):
            assert values[i] <= values[i - 1] + 1e-8

    # Now fit a Cox model on a regression-ready frame.
    df_reg = _prepare_regression_frame()
    cph = CoxPHFitter()
    cph.fit(df_reg, duration_col="duration", event_col="event")
    summary = cph.summary
    assert not summary.empty

    # Predict a survival function for a single individual.
    sample = df_reg.iloc[[0]]
    surv_fn = cph.predict_survival_function(sample)
    # The survival function should be a Series-like object with values in (0, 1].
    vals = surv_fn.values.ravel()
    assert vals[0] <= 1.0 + 1e-8
    assert (vals >= 0.0).all()
    assert (vals <= 1.0 + 1e-8).all()
