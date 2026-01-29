import numpy as np
import pandas as pd

import lifelines


def test_imports_and_datasets():
    assert hasattr(lifelines, "KaplanMeierFitter")
    assert hasattr(lifelines, "CoxPHFitter")
    assert hasattr(lifelines, "datasets")
    df = lifelines.datasets.load_waltons()
    assert isinstance(df, pd.DataFrame)
    assert set(["T", "E", "group"]).issubset(df.columns)
    assert df.shape[0] > 0
    assert pd.api.types.is_numeric_dtype(df["T"])
    assert pd.api.types.is_integer_dtype(df["E"])
    assert df["group"].dtype == object


def test_kaplan_meier_fit_predict_handcheck():
    kmf = lifelines.KaplanMeierFitter()
    durations = [1, 2, 2, 3]
    events = [1, 1, 0, 1]
    kmf.fit(durations, events)

    sf = kmf.survival_function_
    assert isinstance(sf, pd.DataFrame)
    assert sf.index.is_monotonic_increasing
    vals = sf.iloc[:, 0].to_numpy()
    assert np.all((vals >= 0) & (vals <= 1))

    # Hand-checked:
    # at t=1: S= (1-1/4)=0.75
    # at t=2: risk just before 2 is 3, d=1 => 0.75*(1-1/3)=0.5
    # at t=3: risk just before 3 is 1, d=1 => 0.0
    assert abs(kmf.predict(0) - 1.0) < 1e-12
    assert abs(kmf.predict(1) - 0.75) < 1e-12
    assert abs(kmf.predict(1.5) - 0.75) < 1e-12
    assert abs(kmf.predict(2) - 0.5) < 1e-12
    assert abs(kmf.predict(10) - 0.0) < 1e-12


def test_coxph_fit_and_predict_survival_function():
    # Construct a small dataset where higher x tends to have earlier events.
    df = pd.DataFrame(
        {
            "T": [1, 2, 3, 4, 5, 6],
            "E": [1, 1, 1, 1, 0, 0],
            "x": [2.0, 2.0, 1.0, 1.0, 0.0, 0.0],
            "non_numeric": ["a", "b", "c", "d", "e", "f"],
        }
    )
    cph = lifelines.CoxPHFitter(penalizer=0.1)
    cph.fit(df, duration_col="T", event_col="E")
    assert isinstance(cph.summary, pd.DataFrame)
    assert "coef" in cph.summary.columns
    assert "se(coef)" in cph.summary.columns
    assert "x" in cph.summary.index

    # Positive coef means higher x -> higher hazard -> shorter survival, expected here.
    assert np.isfinite(cph.summary.loc["x", "coef"])

    row = pd.DataFrame({"x": [2.0]})
    sf = cph.predict_survival_function(row)
    assert isinstance(sf, pd.DataFrame)
    svals = sf.iloc[:, 0].to_numpy(dtype=float)
    assert np.all((svals >= -1e-12) & (svals <= 1 + 1e-12))
    # starts at 1 at time 0
    assert abs(float(sf.iloc[0, 0]) - 1.0) < 1e-8
    # should be non-increasing
    assert np.all(np.diff(svals) <= 1e-10)


def test_coxph_ignores_non_numeric_and_drops_missing():
    df = pd.DataFrame(
        {
            "T": [1, 2, 3, 4],
            "E": [1, 1, 0, 1],
            "x": [0.0, 1.0, np.nan, 2.0],
            "group": ["a", "a", "b", "b"],  # should be ignored
        }
    )
    cph = lifelines.CoxPHFitter(penalizer=0.1)
    cph.fit(df, duration_col="T", event_col="E")
    assert "x" in cph.params_.index
    assert "group" not in cph.params_.index