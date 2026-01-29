from __future__ import annotations

import numpy as np
import pandas as pd


class KaplanMeierFitter:
    """
    Minimal Kaplan-Meier estimator compatible with the subset of lifelines API
    used by the test suite.
    """

    def __init__(self, *args, **kwargs):
        # accept/ignore any kwargs for compatibility
        self._args = args
        self._kwargs = dict(kwargs)
        self.survival_function_ = None
        self._label = None

    def fit(self, durations, event_observed=None, timeline=None, label=None):
        durations = np.asarray(durations, dtype=float).reshape(-1)
        if durations.size == 0:
            raise ValueError("durations must be non-empty.")
        if not np.all(np.isfinite(durations)):
            raise ValueError("durations must be finite.")
        if np.any(durations < 0):
            raise ValueError("durations must be non-negative.")

        n = durations.shape[0]

        if event_observed is None:
            events = np.ones(n, dtype=bool)
        else:
            eo = np.asarray(event_observed).reshape(-1)
            if eo.shape[0] != n:
                raise ValueError("event_observed must be the same length as durations.")
            # interpret nonzero as True
            events = eo.astype(int) != 0

        self._label = str(label) if label is not None else "KM_estimate"

        # Times we will produce in survival_function_
        if timeline is None:
            # lifelines uses a timeline, but tests usually just need a step function.
            unique_times = np.unique(durations)
            times = np.sort(unique_times.astype(float))
        else:
            times = np.asarray(timeline, dtype=float).reshape(-1)
            if times.size == 0:
                raise ValueError("timeline must be non-empty if provided.")
            if not np.all(np.isfinite(times)):
                raise ValueError("timeline must be finite.")
            times = np.sort(times)

        # ensure time 0 exists for predict behavior
        if times[0] > 0.0:
            times = np.concatenate(([0.0], times))
        elif times[0] < 0.0:
            raise ValueError("timeline must be non-negative.")

        # Kaplan-Meier computed at event times; we forward fill across timeline.
        # Prepare counts at each unique time in observed durations.
        order = np.argsort(durations)
        d_sorted = durations[order]
        e_sorted = events[order]

        unique_durations, idx_start = np.unique(d_sorted, return_index=True)
        # for each unique duration, counts of events and censorings
        # we'll compute n_at_risk just before time t as number with duration >= t
        # Using sorted durations: at time t, at-risk includes those from idx_start onward.
        n_at_risk = (n - idx_start).astype(float)

        # compute d_i at each time
        d_i = np.zeros_like(unique_durations, dtype=float)
        for k, t in enumerate(unique_durations):
            start = idx_start[k]
            end = idx_start[k + 1] if k + 1 < len(idx_start) else n
            d_i[k] = float(np.sum(e_sorted[start:end]))

        # only event times contribute multiplicative decrement
        # We'll compute S(t) for all unique durations (including censored times),
        # but if d_i == 0, multiplier is 1.
        with np.errstate(divide="ignore", invalid="ignore"):
            frac = np.where(n_at_risk > 0, d_i / n_at_risk, 0.0)
        one_minus = 1.0 - frac
        one_minus = np.clip(one_minus, 0.0, 1.0)

        # cumulative product in time order
        S_unique = np.cumprod(one_minus)

        # Right-continuous step: S(t) changes at time t when events occur at t.
        # Define value at time t (exact) as after updating at that time.
        # For times before first observed duration, survival is 1.0.
        # Build a step function mapping t -> S at max unique_duration <= t.
        # We'll later evaluate at supplied timeline via searchsorted.
        # If time 0 is present, set it to 1.0 (prior to any events at t=0 we still want 1,
        # but tests typically accept near-1; we enforce 1.0 at t=0).
        # However, if there are events at t=0, lifelines would drop at 0; not crucial here.
        # We'll keep t=0 as 1 and allow drop at 0+.
        # Create evaluation for each timeline time:
        def eval_surv(t_arr):
            t_arr = np.asarray(t_arr, dtype=float)
            out = np.ones_like(t_arr, dtype=float)
            # index of last unique_duration <= t
            pos = np.searchsorted(unique_durations, t_arr, side="right") - 1
            mask = pos >= 0
            out[mask] = S_unique[pos[mask]]
            # clamp
            return np.clip(out, 0.0, 1.0)

        surv_vals = eval_surv(times)
        if times[0] == 0.0:
            surv_vals[0] = 1.0

        self.survival_function_ = None  # for partial compatibility
        self.survival_function_ = pd.DataFrame({self._label: surv_vals}, index=pd.Index(times, name="timeline"))
        return self

    def predict(self, time):
        if self.survival_function_ is None:
            raise ValueError("Must call fit before predict.")

        idx = self.survival_function_.index.values.astype(float)
        vals = self.survival_function_.iloc[:, 0].values.astype(float)

        def predict_one(t):
            t = float(t)
            if not np.isfinite(t) or t < 0:
                # lifelines would maybe error; keep simple but strict for negatives.
                if t < 0:
                    raise ValueError("time must be non-negative.")
                raise ValueError("time must be finite.")
            # right-continuous step: take last index <= t
            pos = np.searchsorted(idx, t, side="right") - 1
            if pos < 0:
                return 1.0
            if pos >= len(vals):
                pos = len(vals) - 1
            return float(np.clip(vals[pos], 0.0, 1.0))

        if np.isscalar(time):
            return predict_one(time)

        arr = np.asarray(time, dtype=float).reshape(-1)
        out = np.array([predict_one(t) for t in arr], dtype=float)
        return pd.Series(out, index=pd.Index(time), name=self._label)