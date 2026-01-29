from __future__ import annotations

import numpy as np
import pandas as pd


class KaplanMeierFitter:
    """
    Minimal Kaplan-Meier estimator compatible with core lifelines API.
    """

    def __init__(self, alpha: float = 0.05, label: str = "KM_estimate"):
        self.alpha = alpha
        self._label = label
        self.survival_function_: pd.DataFrame | None = None
        self.event_table_: pd.DataFrame | None = None
        self.timeline: np.ndarray | None = None

    def fit(self, durations, event_observed=None, timeline=None, label: str | None = None):
        durations = np.asarray(durations, dtype=float)
        if event_observed is None:
            event_observed = np.ones_like(durations, dtype=int)
        event_observed = np.asarray(event_observed).astype(int)

        if durations.ndim != 1 or event_observed.ndim != 1 or len(durations) != len(event_observed):
            raise ValueError("durations and event_observed must be 1D arrays of the same length.")

        if np.any(~np.isfinite(durations)):
            raise ValueError("durations must be finite.")
        if np.any(durations < 0):
            raise ValueError("durations must be non-negative.")

        label = self._label if label is None else label

        # Create event table at unique times (including censoring times for at_risk updates)
        order = np.argsort(durations, kind="mergesort")
        t = durations[order]
        e = event_observed[order]

        unique_times, first_idx = np.unique(t, return_index=True)
        # counts at each time
        # deaths: events==1
        # censored: events==0
        deaths = np.zeros_like(unique_times, dtype=float)
        censored = np.zeros_like(unique_times, dtype=float)
        # vectorized counting with groupby-like approach
        # For each unique time, count occurrences and sum events
        _, inv, counts = np.unique(t, return_inverse=True, return_counts=True)
        deaths = np.bincount(inv, weights=e, minlength=len(unique_times)).astype(float)
        censored = counts.astype(float) - deaths

        n = float(len(t))
        # at_risk at time just prior to each unique time
        # since sorted, at risk decreases by all individuals with time < current time
        # For discrete times, at_risk at unique_times[i] equals number with duration >= that time
        # We can compute cumulative removed before i:
        removed_before = np.concatenate([[0.0], np.cumsum(counts[:-1]).astype(float)])
        at_risk = n - removed_before

        # KM estimate at event times (and flat at censor-only times)
        # S(t_i) = S(t_{i-1}) * (1 - d_i / n_i)
        surv = np.ones(len(unique_times), dtype=float)
        prev = 1.0
        for i in range(len(unique_times)):
            ni = at_risk[i]
            di = deaths[i]
            if ni <= 0:
                prev = max(min(prev, 1.0), 0.0)
                surv[i] = prev
                continue
            frac = 1.0
            if di > 0:
                frac = 1.0 - (di / ni)
            prev = prev * frac
            prev = max(min(prev, 1.0), 0.0)
            surv[i] = prev

        # timeline handling: lifelines by default includes 0 at start.
        if timeline is None:
            timeline = unique_times
            if len(timeline) == 0 or timeline[0] != 0.0:
                timeline = np.insert(timeline, 0, 0.0)
        else:
            timeline = np.asarray(timeline, dtype=float)
            timeline = np.unique(timeline)
            timeline.sort()
            if len(timeline) == 0 or timeline[0] != 0.0:
                timeline = np.insert(timeline, 0, 0.0)

        # Build survival function over timeline as right-continuous step function:
        # S(t)=1 for t<first event/censor time; at times >=, use last computed at unique_times<=t
        # We computed surv at each unique_time; extend to timeline via searchsorted.
        sf_vals = np.ones_like(timeline, dtype=float)
        if len(unique_times) > 0:
            idx = np.searchsorted(unique_times, timeline, side="right") - 1
            mask = idx >= 0
            sf_vals[mask] = surv[idx[mask]]
        sf_vals = np.clip(sf_vals, 0.0, 1.0)

        self.timeline = timeline
        self.survival_function_ = pd.DataFrame(sf_vals, index=timeline, columns=[label])

        # event_table_ with standard lifelines column names
        # include row at 0 for convenience
        et_index = np.insert(unique_times, 0, 0.0)
        et = pd.DataFrame(index=et_index)
        et["removed"] = 0.0
        et["observed"] = 0.0
        et["censored"] = 0.0
        et["entrance"] = 0.0
        et["at_risk"] = 0.0

        if len(unique_times) > 0:
            et.loc[unique_times, "observed"] = deaths
            et.loc[unique_times, "censored"] = censored
            et.loc[unique_times, "removed"] = deaths + censored
            # at_risk at unique times:
            et.loc[unique_times, "at_risk"] = at_risk
        # At time 0, at_risk is full cohort, entrance is full cohort
        et.loc[0.0, "entrance"] = float(len(durations))
        et.loc[0.0, "at_risk"] = float(len(durations))

        self.event_table_ = et
        return self

    def predict(self, time):
        if self.survival_function_ is None:
            raise ValueError("Must call fit before predict.")
        t = float(time)
        # right-continuous step function: use last index <= t
        idx = self.survival_function_.index.values.astype(float)
        j = np.searchsorted(idx, t, side="right") - 1
        if j < 0:
            return 1.0
        val = float(self.survival_function_.iloc[j, 0])
        if val < 0.0:
            val = 0.0
        if val > 1.0:
            val = 1.0
        return val