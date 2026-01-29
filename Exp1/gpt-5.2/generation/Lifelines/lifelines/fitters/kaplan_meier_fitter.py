from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

import numpy as np
import pandas as pd


Number = Union[int, float, np.number]


@dataclass
class KaplanMeierFitter:
    """
    Minimal Kaplan-Meier fitter with core API-compatible attributes:

      - fit(durations, event_observed=None)
      - survival_function_ : pd.DataFrame
      - predict(time)

    This implementation focuses on correctness for typical unit tests rather
    than feature completeness.
    """

    label: str = "KM_estimate"

    survival_function_: Optional[pd.DataFrame] = None
    timeline_: Optional[np.ndarray] = None

    def fit(
        self,
        durations,
        event_observed=None,
        label: Optional[str] = None,
    ) -> "KaplanMeierFitter":
        if label is not None:
            self.label = label

        T = np.asarray(durations, dtype=float)
        if event_observed is None:
            E = np.ones_like(T, dtype=int)
        else:
            E = np.asarray(event_observed, dtype=int)

        if T.ndim != 1:
            T = T.reshape(-1)
        if E.ndim != 1:
            E = E.reshape(-1)
        if T.shape[0] != E.shape[0]:
            raise ValueError("durations and event_observed must be the same length.")

        # Sort by time
        order = np.argsort(T, kind="mergesort")
        T = T[order]
        E = E[order]

        # Unique event/censor times
        unique_times = np.unique(T)
        n = T.shape[0]

        # Precompute counts at each time
        # at_risk(t) = number with T >= t
        # events(t) = number with T == t and E==1
        # Note: Include times with no events (only censoring) to allow step curve.
        survival = []
        S = 1.0

        # Efficient at-risk counts using reverse cumulative counts
        # For each unique time, find first index where T == time.
        # Number at risk is n - first_idx
        for t in unique_times:
            mask_t = (T == t)
            d_i = int(np.sum(E[mask_t] == 1))
            # at risk: those with time >= t
            first_idx = int(np.searchsorted(T, t, side="left"))
            n_i = int(n - first_idx)
            if n_i <= 0:
                continue
            if d_i > 0:
                S *= (1.0 - d_i / n_i)
            survival.append((t, S))

        if len(survival) == 0:
            # no observed times?
            self.timeline_ = np.array([0.0])
            self.survival_function_ = pd.DataFrame(
                {self.label: [1.0]}, index=pd.Index([0.0], name="timeline")
            )
            return self

        timeline = np.array([t for t, _ in survival], dtype=float)
        values = np.array([s for _, s in survival], dtype=float)

        self.timeline_ = timeline
        self.survival_function_ = pd.DataFrame(
            {self.label: values}, index=pd.Index(timeline, name="timeline")
        )
        return self

    def predict(self, time: Number) -> float:
        if self.survival_function_ is None or self.timeline_ is None:
            raise ValueError("Call fit before predict.")

        t = float(time)
        if t < self.timeline_[0]:
            return 1.0

        # Step function: S(t) = last estimate at time <= t
        idx = np.searchsorted(self.timeline_, t, side="right") - 1
        idx = int(np.clip(idx, 0, len(self.timeline_) - 1))
        s = float(self.survival_function_.iloc[idx, 0])
        # Ensure numerical stability in [0,1]
        if s < 0.0:
            s = 0.0
        if s > 1.0:
            s = 1.0
        return s