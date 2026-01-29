from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
import pandas as pd


def _as_numpy_2d(x) -> np.ndarray:
    arr = np.asarray(x, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    return arr


def _check_finite(arr: np.ndarray, name: str) -> None:
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"Non-finite values found in {name}.")


@dataclass
class CoxPHFitter:
    """
    Minimal Cox Proportional Hazards fitter with core API:

      - fit(df, duration_col, event_col)
      - summary : pd.DataFrame with columns ["coef", "se(coef)"]
      - predict_survival_function(row)

    The implementation uses Newton-Raphson on the partial likelihood with
    Breslow's method for baseline hazard.
    """

    penalizer: float = 0.0
    l1_ratio: float = 0.0  # accepted for compatibility; not fully used

    params_: Optional[pd.Series] = None
    variance_matrix_: Optional[pd.DataFrame] = None
    summary: Optional[pd.DataFrame] = None

    baseline_cumulative_hazard_: Optional[pd.DataFrame] = None
    baseline_survival_: Optional[pd.DataFrame] = None

    _X_columns: Optional[Sequence[str]] = None

    def fit(
        self,
        df: pd.DataFrame,
        duration_col: str,
        event_col: str,
        show_progress: bool = False,
        step_size: float = 1.0,
        robust: bool = False,
        strata=None,
        weights_col=None,
        cluster_col=None,
        **kwargs,
    ) -> "CoxPHFitter":
        if strata is not None:
            raise NotImplementedError("strata is not supported in this minimal implementation.")
        if weights_col is not None:
            raise NotImplementedError("weights are not supported in this minimal implementation.")
        if cluster_col is not None:
            raise NotImplementedError("cluster is not supported in this minimal implementation.")
        if robust:
            # accepted but ignored for minimal compatibility
            pass

        if duration_col not in df.columns or event_col not in df.columns:
            raise KeyError("duration_col and event_col must exist in df.")

        df_ = df.copy()
        T = np.asarray(df_[duration_col], dtype=float)
        E = np.asarray(df_[event_col], dtype=int)
        if T.ndim != 1:
            T = T.reshape(-1)
        if E.ndim != 1:
            E = E.reshape(-1)

        covariate_cols = [c for c in df_.columns if c not in (duration_col, event_col)]
        if len(covariate_cols) == 0:
            raise ValueError("No covariates provided to CoxPHFitter.")

        Xdf = df_[covariate_cols]
        # Require numeric covariates; convert booleans to 0/1
        Xdf = Xdf.copy()
        for c in Xdf.columns:
            if pd.api.types.is_bool_dtype(Xdf[c]):
                Xdf[c] = Xdf[c].astype(int)
        # Try coercion
        Xdf = Xdf.apply(pd.to_numeric, errors="raise")

        X = _as_numpy_2d(Xdf.values)
        _check_finite(X, "covariates")
        _check_finite(T, "durations")

        n, p = X.shape
        self._X_columns = list(Xdf.columns)

        # Sort descending by time for risk set cumulative sums
        order = np.argsort(-T, kind="mergesort")
        T = T[order]
        E = E[order]
        X = X[order, :]

        beta = np.zeros(p, dtype=float)

        max_iter = int(kwargs.get("max_iter", 100))
        tol = float(kwargs.get("tol", 1e-7))

        def loglik_grad_hess(b: np.ndarray):
            xb = X @ b
            # stabilize
            xb = xb - np.max(xb)
            w = np.exp(xb)  # n,

            # cumulative sums over risk sets: since sorted desc, risk set for i is 0..i
            cw = np.cumsum(w)
            cXw = np.cumsum(X * w[:, None], axis=0)
            # For Hessian: cum sum of outer products weighted
            # We'll compute per i: sum_{j in R_i} w_j x_j x_j^T
            cXXw = np.zeros((n, p, p), dtype=float)
            acc = np.zeros((p, p), dtype=float)
            for i in range(n):
                xi = X[i, :]
                acc += w[i] * np.outer(xi, xi)
                cXXw[i] = acc

            # only for events contribute
            event_idx = np.where(E == 1)[0]
            if event_idx.size == 0:
                raise ValueError("No events observed; cannot fit Cox model.")

            ll = 0.0
            g = np.zeros(p, dtype=float)
            H = np.zeros((p, p), dtype=float)

            for i in event_idx:
                # Breslow: ties are handled later for baseline; for partial likelihood,
                # use standard approximation summing over events individually.
                ll += xb[i] - np.log(cw[i])

                mean_x = cXw[i] / cw[i]
                g += X[i, :] - mean_x

                # var = E[xx^T] - E[x]E[x]^T
                exx = cXXw[i] / cw[i]
                var = exx - np.outer(mean_x, mean_x)
                H -= var

            # L2 penalizer
            if self.penalizer and self.penalizer > 0:
                ll -= 0.5 * self.penalizer * float(np.dot(b, b))
                g -= self.penalizer * b
                H -= self.penalizer * np.eye(p)

            return ll, g, H

        prev_ll = -np.inf
        for _ in range(max_iter):
            ll, g, H = loglik_grad_hess(beta)
            # Convergence check on ll
            if np.isfinite(prev_ll) and abs(ll - prev_ll) < tol:
                break
            prev_ll = ll

            # Newton step: beta_new = beta - H^{-1} g  (since H is negative definite)
            try:
                step = np.linalg.solve(H, g)
            except np.linalg.LinAlgError:
                # add small ridge for stability
                ridge = 1e-8
                step = np.linalg.solve(H - ridge * np.eye(p), g)

            beta = beta - step_size * step

            if np.linalg.norm(step) < tol:
                break

        # Variance matrix: inverse of -H at optimum (observed information)
        _, _, Hopt = loglik_grad_hess(beta)
        info = -Hopt
        try:
            var = np.linalg.inv(info)
        except np.linalg.LinAlgError:
            var = np.linalg.pinv(info)

        se = np.sqrt(np.clip(np.diag(var), 0.0, np.inf))

        self.params_ = pd.Series(beta, index=self._X_columns, name="coef")
        self.variance_matrix_ = pd.DataFrame(var, index=self._X_columns, columns=self._X_columns)
        self.summary = pd.DataFrame(
            {"coef": self.params_.values, "se(coef)": se},
            index=self._X_columns,
        )

        # Compute baseline cumulative hazard via Breslow at unique event times.
        # Use original order (ascending time) for output.
        # We'll compute risk sums at each event time in the sorted-desc arrays and then reverse.
        xb = X @ beta
        xb = xb - np.max(xb)
        w = np.exp(xb)

        # unique times in ascending order
        unique_event_times = np.unique(T[E == 1])
        unique_event_times.sort()

        # For each time t, risk set is those with T >= t.
        # We can compute by using mask each time; n is small in tests, ok.
        H0 = []
        cum = 0.0
        for t in unique_event_times:
            d = float(np.sum((T == t) & (E == 1)))
            risk = float(np.sum(w[T >= t]))
            if risk <= 0:
                continue
            dh = d / risk
            cum += dh
            H0.append((t, cum))

        if len(H0) == 0:
            # Shouldn't happen if there are events, but be safe
            H0 = [(float(np.min(T)), 0.0)]

        times = np.array([t for t, _ in H0], dtype=float)
        cumhaz = np.array([h for _, h in H0], dtype=float)

        self.baseline_cumulative_hazard_ = pd.DataFrame(
            {"baseline cumulative hazard": cumhaz},
            index=pd.Index(times, name="timeline"),
        )
        self.baseline_survival_ = pd.DataFrame(
            {"baseline survival": np.exp(-cumhaz)},
            index=pd.Index(times, name="timeline"),
        )

        return self

    def predict_survival_function(self, row: pd.DataFrame) -> pd.DataFrame:
        if self.params_ is None or self.baseline_survival_ is None:
            raise ValueError("Call fit before predict_survival_function.")
        if not isinstance(row, pd.DataFrame):
            raise TypeError("row must be a pandas DataFrame.")
        if row.shape[0] != 1:
            raise ValueError("row must be a single-row DataFrame.")

        missing = [c for c in self._X_columns if c not in row.columns]
        if missing:
            raise KeyError(f"Missing covariate columns in row: {missing}")

        x = row[self._X_columns].copy()
        for c in x.columns:
            if pd.api.types.is_bool_dtype(x[c]):
                x[c] = x[c].astype(int)
        x = x.apply(pd.to_numeric, errors="raise")
        xv = x.values.astype(float).reshape(-1)

        lp = float(np.dot(self.params_.values, xv))
        hr = float(np.exp(lp))  # hazard ratio relative to baseline

        # S(t|x) = S0(t) ^ exp(xb) = exp(-H0(t) * exp(xb))
        s0 = self.baseline_survival_.iloc[:, 0].values.astype(float)
        times = self.baseline_survival_.index.values.astype(float)
        s = np.power(np.clip(s0, 0.0, 1.0), hr)

        s = np.clip(s, 0.0, 1.0)
        return pd.DataFrame({"survival_function": s}, index=pd.Index(times, name="timeline"))