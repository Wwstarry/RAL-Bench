import numpy as np
import pandas as pd


class KaplanMeierFitter:
    """
    A simple Kaplan-Meier estimator compatible with the core lifelines API used in tests.

    Methods:
    - fit(durations, event_observed)
    - predict(time)
    Attributes:
    - survival_function_: pandas DataFrame indexed by event times with column "KM_estimate"
    """

    def __init__(self):
        self.survival_function_ = None
        self.event_table_ = None
        self._event_times = None

    def fit(self, durations, event_observed=None):
        """
        Fit the Kaplan-Meier survival function.

        Parameters
        - durations: array-like of non-negative durations
        - event_observed: array-like of booleans or 0/1; if None, all events are observed
        """
        durations = np.asarray(durations).astype(float)
        if event_observed is None:
            event_observed = np.ones_like(durations, dtype=int)
        else:
            event_observed = np.asarray(event_observed)
            # convert to 0/1 ints
            event_observed = (event_observed.astype(int) != 0).astype(int)

        # Remove NaNs
        mask = np.isfinite(durations) & np.isfinite(event_observed)
        durations = durations[mask]
        event_observed = event_observed[mask]

        # Sort by time
        order = np.argsort(durations, kind="mergesort")
        durations = durations[order]
        event_observed = event_observed[order]

        unique_times = np.unique(durations)
        survival_values = []
        survival_times = []
        S = 1.0

        # Compute KM estimate only at event times
        for t in unique_times:
            d = int(np.sum((durations == t) & (event_observed == 1)))
            if d == 0:
                # No events at this time -> survival doesn't change
                continue
            n_at_risk = int(np.sum(durations >= t))
            if n_at_risk <= 0:
                continue
            q = 1.0 - d / n_at_risk
            S *= q
            survival_times.append(t)
            survival_values.append(S)

        if len(survival_times) == 0:
            # No observed events -> survival is always 1
            self.survival_function_ = pd.DataFrame(
                {"KM_estimate": []}, index=pd.Index([], name="timeline")
            )
            self._event_times = np.array([])
            return self

        index = pd.Index(survival_times, name="timeline")
        self.survival_function_ = pd.DataFrame({"KM_estimate": survival_values}, index=index)
        self._event_times = np.array(survival_times, dtype=float)
        return self

    def predict(self, time):
        """
        Predict survival probability at a given time (scalar or array-like).

        Returns float if scalar input, else numpy array.
        """
        if self.survival_function_ is None or len(self.survival_function_) == 0:
            # No events fitted, survival is 1
            if np.isscalar(time):
                return 1.0
            else:
                arr = np.asarray(time, dtype=float)
                return np.ones_like(arr, dtype=float)

        event_times = self._event_times
        surv_values = self.survival_function_["KM_estimate"].values

        def predict_one(t):
            # If before first event time, survival is 1
            if t < event_times[0]:
                return 1.0
            # If after last event time, take last survival value
            if t >= event_times[-1]:
                return float(surv_values[-1])
            # Find the last event time <= t
            idx = np.searchsorted(event_times, t, side="right") - 1
            return float(surv_values[idx])

        if np.isscalar(time):
            val = predict_one(float(time))
            # Keep in [0,1]
            return max(0.0, min(1.0, val))
        else:
            arr = np.asarray(time, dtype=float)
            out = np.array([predict_one(t) for t in arr], dtype=float)
            out = np.clip(out, 0.0, 1.0)
            return out