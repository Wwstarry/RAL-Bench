import numpy as np
import pandas as pd


class KaplanMeierFitter:
    """
    Very small, *pure-python* Kaplan-Meier estimator that implements the
    minimal public interface used by the test-suite.
    """

    def __init__(self):
        self.survival_function_ = None
        self.event_table_ = None
        self._label = None
        self.durations = None
        self.event_observed = None

    # --------------------------------------------------------------------- #
    #                               FITTING                                 #
    # --------------------------------------------------------------------- #
    def fit(self, durations, event_observed=None, label: str = "KM_estimate"):
        """
        Estimate the Kaplan-Meier survival curve.

        Parameters
        ----------
        durations : array-like
            Observed times (censored or event).
        event_observed : array-like (bool / {0,1}), optional
            1 if event was observed, 0 if right-censored.  If ``None`` every
            observation is treated as an event.
        label : str, default “KM_estimate”
            Name of the column in ``survival_function_`` produced after
            fitting.
        """
        self._label = str(label)
        self.durations = np.asarray(durations, dtype=float).ravel()

        if event_observed is None:
            self.event_observed = np.ones_like(self.durations, dtype=int)
        else:
            self.event_observed = np.asarray(event_observed, dtype=int).ravel()

        # Sorting by time ascending
        order = np.argsort(self.durations)
        durations = self.durations[order]
        events = self.event_observed[order]

        # Unique event/censor times
        unique_times, indices = np.unique(durations, return_inverse=True)
        n = len(durations)

        # Number at risk just *before* each unique time
        # n_i = subjects whose time >= that time
        # We can compute by reversing cumulative counts
        at_risk = np.zeros_like(unique_times, dtype=float)
        events_at_time = np.zeros_like(unique_times, dtype=float)

        # Count how many observations at each unique time
        counts = np.bincount(indices)
        events_counts = np.bincount(indices, weights=events)

        # Number at risk for time t_k is number of individuals whose duration >= t_k
        # We can compute by reversing cumulative sum
        at_risk = np.cumsum(counts[::-1])[::-1]

        events_at_time = events_counts

        # Kaplan-Meier product-limit estimate
        survival = []
        s = 1.0
        for n_i, d_i in zip(at_risk, events_at_time):
            if n_i == 0:
                survival.append(s)
                continue
            if d_i > 0:
                s *= (1.0 - d_i / n_i)
            survival.append(s)

        self.survival_function_ = pd.DataFrame(
            data=survival, index=pd.Index(unique_times, name="timeline"), columns=[self._label]
        )

        # Also helpful to expose the event table (counts, at risk, etc.) although
        # not strictly required.
        self.event_table_ = pd.DataFrame(
            {
                "at_risk": at_risk,
                "observed": events_at_time,
                "survival": survival,
            },
            index=pd.Index(unique_times, name="timeline"),
        )
        return self

    # --------------------------------------------------------------------- #
    #                               PREDICT                                 #
    # --------------------------------------------------------------------- #
    def predict(self, times):
        """
        Step-function prediction of the survival probability at the requested
        time point(s).  For values before the first event time the survival
        probability is 1.  For values after the last observed time the value at
        the last step is returned.
        """
        if self.survival_function_ is None:
            raise RuntimeError("Estimator not fitted yet.")

        sf = self.survival_function_[self._label]
        timeline = sf.index.to_numpy()
        surv_values = sf.to_numpy()

        def _interp(t):
            # Index of last timeline point ≤ t
            idx = np.searchsorted(timeline, t, side="right") - 1
            if idx < 0:
                return 1.0
            if idx >= len(surv_values):
                idx = len(surv_values) - 1
            return float(surv_values[idx])

        if np.isscalar(times):
            return _interp(times)
        else:
            times_arr = np.asarray(times, dtype=float)
            return pd.Series([_interp(t) for t in times_arr], index=times)