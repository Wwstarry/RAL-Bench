from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd


def _to_1d_array(x: Any, name: str) -> np.ndarray:
    if isinstance(x, (pd.Series, pd.Index)):
        arr = x.to_numpy()
    elif isinstance(x, pd.DataFrame):
        if x.shape[1] != 1:
            raise ValueError(f"{name} must be 1-dimensional.")
        arr = x.iloc[:, 0].to_numpy()
    else:
        arr = np.asarray(x)
    arr = np.asarray(arr).reshape(-1)
    return arr


@dataclass
class KaplanMeierFitter:
    label: str | None = None

    def __post_init__(self) -> None:
        if self.label is None:
            self.label = "KM_estimate"

        self.survival_function_: pd.DataFrame | None = None
        self.event_table_: pd.DataFrame | None = None
        self.timeline: pd.Index | None = None

    def fit(
        self,
        durations: Any,
        event_observed: Any | None = None,
        label: str | None = None,
    ) -> "KaplanMeierFitter":
        T = _to_1d_array(durations, "durations").astype(float)
        if event_observed is None:
            E = np.ones_like(T, dtype=int)
        else:
            E = _to_1d_array(event_observed, "event_observed")
            # allow bool, float, int
            E = (E.astype(float) > 0.0).astype(int)

        if T.shape[0] != E.shape[0]:
            raise ValueError("durations and event_observed must be the same length.")

        if label is not None:
            self.label = label

        mask = np.isfinite(T) & np.isfinite(E.astype(float))
        T = T[mask]
        E = E[mask].astype(int)

        if T.size == 0:
            raise ValueError("No valid observations.")

        # timeline includes all unique durations (events + censored) for robustness
        unique_times = np.unique(T)
        unique_times = unique_times[unique_times >= 0]
        unique_times.sort()
        if unique_times.size == 0 or unique_times[0] != 0.0:
            timeline = np.concatenate([[0.0], unique_times])
        else:
            timeline = unique_times

        # Precompute counts by time
        # at_risk at time t is number with T >= t
        # observed at time t is number with T == t and E==1
        # censored at time t is number with T == t and E==0
        observed = {}
        censored = {}
        for t in unique_times:
            at_t = (T == t)
            observed[t] = int(np.sum(at_t & (E == 1)))
            censored[t] = int(np.sum(at_t & (E == 0)))

        # KM estimate
        S = 1.0
        surv_vals = [1.0]
        ev_rows = []
        # at time 0, include an event table row too
        at_risk0 = int(np.sum(T >= 0.0))
        ev_rows.append((0.0, at_risk0, 0, 0))

        for t in unique_times:
            at_risk = int(np.sum(T >= t))
            d = observed.get(t, 0)
            c = censored.get(t, 0)

            # apply KM only for events
            if at_risk > 0 and d > 0:
                S *= (1.0 - d / at_risk)

            surv_vals.append(float(S))
            ev_rows.append((float(t), at_risk, int(d), int(c)))

        timeline_index = pd.Index(timeline, name="timeline")
        # surv_vals has len = 1 + len(unique_times); timeline has 1 + len(unique_times) unless unique_times started with 0
        # If unique_times includes 0, timeline == unique_times; but we still inserted initial 1.0 and then looped over unique_times
        # resulting in one extra entry. Fix by de-duplicating time 0.
        if unique_times.size > 0 and unique_times[0] == 0.0:
            # remove the initial 1.0 duplicate and align to timeline
            surv_vals = surv_vals[1:]
        # Now should align
        if len(surv_vals) != len(timeline_index):
            # fallback: align by building series on explicit times
            times = [0.0] + [float(t) for t in unique_times.tolist()]
            vals = [1.0]
            S2 = 1.0
            for t in unique_times:
                at_risk = int(np.sum(T >= t))
                d = observed.get(t, 0)
                if at_risk > 0 and d > 0:
                    S2 *= (1.0 - d / at_risk)
                vals.append(float(S2))
            s = pd.Series(vals, index=pd.Index(times, name="timeline"))
            s = s[~s.index.duplicated(keep="last")]
            s = s.reindex(timeline_index, method="ffill").fillna(1.0)
            surv = s.to_frame(name=self.label)
        else:
            surv = pd.DataFrame({self.label: np.clip(np.asarray(surv_vals, dtype=float), 0.0, 1.0)}, index=timeline_index)

        # Build event_table_ indexed by timeline (including 0 and all durations)
        # For 0 included twice in ev_rows if unique_times started with 0, dedupe keep last
        event_df = pd.DataFrame(ev_rows, columns=["event_at", "at_risk", "observed", "censored"]).set_index("event_at")
        event_df = event_df[~event_df.index.duplicated(keep="last")]
        event_df = event_df.reindex(timeline_index, method="ffill").fillna(0).astype({"at_risk": int, "observed": int, "censored": int})
        event_df.index.name = "timeline"

        self.survival_function_ = surv
        self.event_table_ = event_df
        self.timeline = timeline_index
        return self

    def predict(self, time: float) -> float:
        if self.survival_function_ is None:
            raise ValueError("Must call fit before predict.")
        try:
            t = float(time)
        except Exception as e:
            raise ValueError("time must be numeric.") from e

        if t <= 0:
            return 1.0

        sf = self.survival_function_.iloc[:, 0]
        idx = sf.index.to_numpy(dtype=float)

        # find rightmost index <= t
        pos = np.searchsorted(idx, t, side="right") - 1
        if pos < 0:
            return 1.0
        if pos >= len(sf):
            pos = len(sf) - 1
        val = float(sf.iloc[pos])
        if not np.isfinite(val):
            val = float(np.nan_to_num(val, nan=1.0))
        return float(np.clip(val, 0.0, 1.0))

    def survival_function_at_times(self, times: Iterable[float]) -> pd.Series:
        if self.survival_function_ is None:
            raise ValueError("Must call fit before survival_function_at_times.")
        out = []
        idx = []
        for t in times:
            idx.append(t)
            out.append(self.predict(t))
        return pd.Series(out, index=pd.Index(idx, name="timeline"), name=self.label)