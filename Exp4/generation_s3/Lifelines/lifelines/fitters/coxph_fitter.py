from __future__ import annotations

import numpy as np
import pandas as pd


class CoxPHFitter:
    """
    Minimal Cox Proportional Hazards model fitter.

    Implements Newton-Raphson optimization of the partial likelihood with
    Breslow ties approximation and a Breslow baseline cumulative hazard estimator.

    This is a small subset sufficient for the unit tests.
    """

    def __init__(self, *args, **kwargs):
        # accept/ignore unknown kwargs for compatibility
        self._args = args
        self._kwargs = dict(kwargs)

        self.params_ = None
        self.variance_matrix_ = None
        self.summary = None

        self._duration_col = None
        self._event_col = None

        self._x_columns_ = None  # encoded columns used in training
        self._baseline_cumulative_hazard_ = None  # pd.Series indexed by time
        self._baseline_survival_ = None  # pd.Series indexed by time

    @staticmethod
    def _validate_df(df, duration_col, event_col):
        if not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a pandas DataFrame.")
        if duration_col not in df.columns:
            raise ValueError(f"duration_col '{duration_col}' not found in df.")
        if event_col not in df.columns:
            raise ValueError(f"event_col '{event_col}' not found in df.")
        if df.shape[0] == 0:
            raise ValueError("df must be non-empty.")

    @staticmethod
    def _ensure_numeric_durations_events(T, E):
        T = np.asarray(T, dtype=float).reshape(-1)
        if T.size == 0:
            raise ValueError("durations must be non-empty.")
        if not np.all(np.isfinite(T)):
            raise ValueError("durations must be finite.")
        if np.any(T < 0):
            raise ValueError("durations must be non-negative.")

        E = np.asarray(E).reshape(-1)
        if E.shape[0] != T.shape[0]:
            raise ValueError("event indicator must be the same length as durations.")
        E = (E.astype(int) != 0).astype(int)
        return T, E

    def _prepare_X(self, df_covariates: pd.DataFrame, fitting: bool):
        # One-hot encode non-numeric columns (including categories/objects)
        X = pd.get_dummies(df_covariates, drop_first=True)

        # Ensure all are numeric
        for c in X.columns:
            if not pd.api.types.is_numeric_dtype(X[c]):
                X[c] = pd.to_numeric(X[c], errors="coerce")

        if X.isna().any().any():
            raise ValueError("Covariates contain NaNs after encoding/coercion.")

        if fitting:
            self._x_columns_ = list(X.columns)
            return X.astype(float)

        # prediction: align to training columns
        if self._x_columns_ is None:
            raise ValueError("Model is not fit yet.")
        X = X.reindex(columns=self._x_columns_, fill_value=0.0)
        return X.astype(float)

    def fit(
        self,
        df: pd.DataFrame,
        duration_col: str,
        event_col: str,
        show_progress: bool = False,
        strata=None,
        weights_col=None,
        robust: bool = False,
        step_size=None,
        timeline=None,
        **kwargs,
    ):
        # accept but ignore many args for compatibility
        _ = (show_progress, strata, weights_col, robust, step_size, timeline, kwargs)

        self._validate_df(df, duration_col, event_col)
        self._duration_col = duration_col
        self._event_col = event_col

        T, E = self._ensure_numeric_durations_events(df[duration_col].values, df[event_col].values)

        covar_cols = [c for c in df.columns if c not in (duration_col, event_col)]
        if len(covar_cols) == 0:
            raise ValueError("No covariates provided for CoxPHFitter.")

        X = self._prepare_X(df[covar_cols], fitting=True)
        Xv = X.values.astype(float)

        n, p = Xv.shape
        if n == 0 or p == 0:
            raise ValueError("Design matrix is empty.")

        # Sort by increasing time for stable risk set calculations.
        order = np.argsort(T, kind="mergesort")
        T = T[order]
        E = E[order]
        Xv = Xv[order, :]

        # Unique event times
        event_mask = E == 1
        if not np.any(event_mask):
            raise ValueError("At least one event is required to fit Cox model.")

        unique_event_times = np.unique(T[event_mask])

        # Newton-Raphson
        beta = np.zeros(p, dtype=float)
        max_iter = 50
        tol = 1e-6
        ridge = 1e-7

        # Precompute indices for each unique event time: events at t, and risk set for t (T >= t)
        # We'll use boolean masks; OK for small/medium test sizes.
        for _iter in range(max_iter):
            eta = Xv @ beta
            # clip to avoid overflow in exp
            eta_clip = np.clip(eta, -50, 50)
            w = np.exp(eta_clip)

            grad = np.zeros(p, dtype=float)
            hess = np.zeros((p, p), dtype=float)

            for t in unique_event_times:
                at_t = (T == t)
                d = float(np.sum(E[at_t]))
                if d <= 0:
                    continue

                risk = (T >= t)
                w_risk = w[risk]
                X_risk = Xv[risk, :]

                S0 = float(np.sum(w_risk))
                if S0 <= 0:
                    continue
                S1 = np.sum(X_risk * w_risk[:, None], axis=0)  # shape (p,)
                S2 = (X_risk.T * w_risk) @ X_risk  # shape (p,p)

                # sum x for events at t
                X_events_sum = np.sum(Xv[at_t & (E == 1), :], axis=0)

                # Breslow ties:
                grad += X_events_sum - d * (S1 / S0)
                hess -= d * (S2 / S0 - np.outer(S1, S1) / (S0 * S0))

            # Solve for step: (-H) delta = grad  where H here is second derivative of loglik (negative semidef)
            # We computed hess as Hessian of loglik (should be negative definite-ish). Use -hess for information.
            info = -hess
            info = info + ridge * np.eye(p)

            try:
                delta = np.linalg.solve(info, grad)
            except np.linalg.LinAlgError:
                delta = np.linalg.lstsq(info, grad, rcond=None)[0]

            beta_new = beta + delta
            if np.max(np.abs(delta)) < tol:
                beta = beta_new
                break
            beta = beta_new

        self.params_ = pd.Series(beta, index=self._x_columns_, name="coef")

        # Variance = inverse information at optimum
        eta = Xv @ beta
        eta_clip = np.clip(eta, -50, 50)
        w = np.exp(eta_clip)

        # Recompute information matrix
        hess = np.zeros((p, p), dtype=float)
        for t in unique_event_times:
            at_t = (T == t)
            d = float(np.sum(E[at_t]))
            if d <= 0:
                continue
            risk = (T >= t)
            w_risk = w[risk]
            X_risk = Xv[risk, :]
            S0 = float(np.sum(w_risk))
            if S0 <= 0:
                continue
            S1 = np.sum(X_risk * w_risk[:, None], axis=0)
            S2 = (X_risk.T * w_risk) @ X_risk
            hess -= d * (S2 / S0 - np.outer(S1, S1) / (S0 * S0))

        info = -hess + ridge * np.eye(p)
        try:
            var = np.linalg.inv(info)
        except np.linalg.LinAlgError:
            var = np.linalg.pinv(info)

        self.variance_matrix_ = pd.DataFrame(var, index=self._x_columns_, columns=self._x_columns_)
        se = np.sqrt(np.clip(np.diag(var), 0.0, np.inf))
        self.summary = pd.DataFrame({"coef": beta, "se(coef)": se}, index=self._x_columns_)

        # Baseline cumulative hazard via Breslow at event times
        # Use original (sorted) arrays.
        eta = Xv @ beta
        eta_clip = np.clip(eta, -50, 50)
        w = np.exp(eta_clip)

        base_times = np.sort(unique_event_times.astype(float))
        cumhaz = []
        ch = 0.0
        for t in base_times:
            at_t = (T == t)
            d = float(np.sum(E[at_t]))
            risk = (T >= t)
            denom = float(np.sum(w[risk]))
            if denom <= 0:
                dh = 0.0
            else:
                dh = d / denom
            ch += dh
            cumhaz.append(ch)

        # Include 0.0
        if len(base_times) == 0:
            base_index = pd.Index([0.0], name="timeline")
            base_ch = pd.Series([0.0], index=base_index)
        else:
            if base_times[0] > 0.0:
                base_times2 = np.concatenate(([0.0], base_times))
                cumhaz2 = np.concatenate(([0.0], np.array(cumhaz, dtype=float)))
            else:
                base_times2 = base_times
                cumhaz2 = np.array(cumhaz, dtype=float)
                if base_times2[0] == 0.0:
                    cumhaz2[0] = max(0.0, cumhaz2[0])
            base_index = pd.Index(base_times2, name="timeline")
            base_ch = pd.Series(cumhaz2, index=base_index)

        self._baseline_cumulative_hazard_ = base_ch
        self._baseline_survival_ = np.exp(-base_ch).clip(0.0, 1.0)
        return self

    def predict_survival_function(self, row: pd.DataFrame, times=None) -> pd.DataFrame:
        if self.params_ is None or self._baseline_survival_ is None:
            raise ValueError("Must call fit before predict_survival_function.")

        if not isinstance(row, pd.DataFrame):
            raise ValueError("row must be a pandas DataFrame.")
        if row.shape[0] != 1:
            raise ValueError("row must be a single-row DataFrame.")

        # Extract covariates (ignore any duration/event columns if present)
        cov = row.copy()
        for col in (self._duration_col, self._event_col):
            if col in cov.columns:
                cov = cov.drop(columns=[col])

        X_row = self._prepare_X(cov, fitting=False)
        x = X_row.values.reshape(-1)
        beta = self.params_.values.reshape(-1)

        eta = float(np.dot(x, beta))
        eta = float(np.clip(eta, -50, 50))
        hr = float(np.exp(eta))

        if times is None:
            base = self._baseline_survival_
            idx = base.index.values.astype(float)
            s0 = base.values.astype(float)
        else:
            t = np.asarray(times, dtype=float).reshape(-1)
            if t.size == 0:
                raise ValueError("times must be non-empty if provided.")
            if not np.all(np.isfinite(t)):
                raise ValueError("times must be finite.")
            if np.any(t < 0):
                raise ValueError("times must be non-negative.")
            t = np.sort(t)
            # ensure starts at 0 for sane curves
            if t[0] > 0.0:
                t = np.concatenate(([0.0], t))

            # Evaluate baseline survival as step function (right-continuous) over requested times
            base_idx = self._baseline_survival_.index.values.astype(float)
            base_vals = self._baseline_survival_.values.astype(float)
            pos = np.searchsorted(base_idx, t, side="right") - 1
            s0 = np.ones_like(t, dtype=float)
            mask = pos >= 0
            s0[mask] = base_vals[pos[mask]]
            idx = t

        # S(t|x) = S0(t) ^ exp(eta)
        s = np.power(np.clip(s0, 0.0, 1.0), hr)
        # ensure within [0,1] and monotone non-increasing (numerical cleanup)
        s = np.clip(s, 0.0, 1.0)
        # enforce non-increasing
        for i in range(1, len(s)):
            if s[i] > s[i - 1]:
                s[i] = s[i - 1]

        colname = "survival_function"
        return pd.DataFrame({colname: s}, index=pd.Index(idx, name="timeline"))