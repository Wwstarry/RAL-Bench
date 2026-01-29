from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


def _is_number_dtype(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s.dtype)


def _safe_exp(x: np.ndarray) -> np.ndarray:
    return np.exp(np.clip(x, -50.0, 50.0))


def _forward_fill_step_at(times_src: np.ndarray, values_src: np.ndarray, times_new: np.ndarray) -> np.ndarray:
    # times_src must be sorted ascending
    pos = np.searchsorted(times_src, times_new, side="right") - 1
    pos = np.clip(pos, 0, len(times_src) - 1)
    return values_src[pos]


@dataclass
class CoxPHFitter:
    penalizer: float = 0.0
    l1_ratio: float = 0.0
    strata: Any = None

    def __post_init__(self) -> None:
        self.params_: pd.Series | None = None
        self.variance_matrix_: pd.DataFrame | None = None
        self.standard_errors_: pd.Series | None = None
        self.summary: pd.DataFrame | None = None

        self.baseline_cumulative_hazard_: pd.DataFrame | None = None
        self.baseline_survival_: pd.DataFrame | None = None

        self.log_likelihood_: float | None = None
        self._duration_col: str | None = None
        self._event_col: str | None = None
        self._covariate_columns: list[str] | None = None

    def fit(
        self,
        df: pd.DataFrame,
        duration_col: str,
        event_col: str,
        show_progress: bool = False,
        **kwargs: Any,
    ) -> "CoxPHFitter":
        if duration_col not in df.columns or event_col not in df.columns:
            raise ValueError("duration_col and event_col must be present in df.")

        self._duration_col = duration_col
        self._event_col = event_col

        work = df.copy()
        # keep only rows with non-missing in duration/event and covariates later
        if not _is_number_dtype(work[duration_col]):
            work[duration_col] = pd.to_numeric(work[duration_col], errors="coerce")
        if not _is_number_dtype(work[event_col]):
            work[event_col] = pd.to_numeric(work[event_col], errors="coerce")

        # choose numeric covariates excluding duration/event
        covariate_cols = [c for c in work.columns if c not in (duration_col, event_col) and _is_number_dtype(work[c])]
        if len(covariate_cols) == 0:
            raise ValueError("No numeric covariates found to fit CoxPH model.")
        self._covariate_columns = covariate_cols

        used_cols = [duration_col, event_col] + covariate_cols
        work = work[used_cols].dropna(axis=0, how="any").copy()
        if work.shape[0] == 0:
            raise ValueError("No rows remaining after dropping missing values.")

        T = work[duration_col].to_numpy(dtype=float)
        E = (work[event_col].to_numpy(dtype=float) > 0).astype(int)
        X = work[covariate_cols].to_numpy(dtype=float)

        n, p = X.shape
        if n <= p:
            # still possible to fit, but warn-like behavior not needed; keep going
            pass

        order = np.argsort(T, kind="mergesort")
        T = T[order]
        E = E[order]
        X = X[order]

        unique_event_times = np.unique(T[E == 1])
        unique_event_times.sort()

        beta = np.zeros(p, dtype=float)
        tol = 1e-7
        max_iter = int(kwargs.get("max_iter", 50))

        def partial_log_lik(beta_vec: np.ndarray) -> float:
            eta = X @ beta_vec
            w = _safe_exp(eta)
            ll = 0.0
            # Breslow ties
            for t in unique_event_times:
                event_mask = (T == t) & (E == 1)
                d = int(np.sum(event_mask))
                if d == 0:
                    continue
                risk_mask = T >= t
                denom = float(np.sum(w[risk_mask]))
                if denom <= 0.0:
                    continue
                ll += float(np.sum(eta[event_mask])) - d * np.log(denom)
            if self.penalizer and self.penalizer > 0:
                ll -= 0.5 * float(self.penalizer) * float(beta_vec @ beta_vec)
            return float(ll)

        ll = partial_log_lik(beta)

        for _ in range(max_iter):
            eta = X @ beta
            w = _safe_exp(eta)

            grad = np.zeros(p, dtype=float)
            hess = np.zeros((p, p), dtype=float)

            for t in unique_event_times:
                event_mask = (T == t) & (E == 1)
                d = int(np.sum(event_mask))
                if d == 0:
                    continue
                risk_mask = T >= t

                w_risk = w[risk_mask]
                X_risk = X[risk_mask, :]
                S0 = float(np.sum(w_risk))
                if S0 <= 0.0:
                    continue
                S1 = (w_risk[:, None] * X_risk).sum(axis=0)  # (p,)
                # S2 = sum(w_i * x_i x_i^T)
                # compute via matrix multiplication
                S2 = (X_risk.T * w_risk) @ X_risk  # (p,p)

                x_events_sum = X[event_mask, :].sum(axis=0)
                grad += x_events_sum - d * (S1 / S0)

                mean = S1 / S0
                var = (S2 / S0) - np.outer(mean, mean)
                hess -= d * var

            if self.penalizer and self.penalizer > 0:
                grad -= self.penalizer * beta
                hess -= self.penalizer * np.eye(p)

            # Solve for Newton step: beta_new = beta - H^{-1} grad
            # Here hess is (approx) second derivative of loglik, negative definite; we use step = solve(-hess, grad)
            H = -hess
            # jitter for numerical stability
            jitter = 0.0
            try:
                step = np.linalg.solve(H, grad)
            except np.linalg.LinAlgError:
                jitter = 1e-9 if self.penalizer == 0 else 0.0
                try:
                    step = np.linalg.solve(H + jitter * np.eye(p), grad)
                except np.linalg.LinAlgError:
                    step = np.linalg.pinv(H + 1e-6 * np.eye(p)) @ grad

            # Backtracking line search to ensure improvement
            step_norm = float(np.max(np.abs(step))) if step.size else 0.0
            if step_norm < tol:
                break

            alpha = 1.0
            improved = False
            for _ls in range(15):
                beta_try = beta + alpha * step
                ll_try = partial_log_lik(beta_try)
                if ll_try >= ll - 1e-12:
                    beta = beta_try
                    ll = ll_try
                    improved = True
                    break
                alpha *= 0.5
            if not improved:
                # accept small step to avoid stalling
                beta = beta + 0.1 * step
                ll = partial_log_lik(beta)

            if float(np.max(np.abs(alpha * step))) < tol:
                break

        self.log_likelihood_ = float(ll)
        self.params_ = pd.Series(beta, index=covariate_cols, name="coef")

        # Variance matrix approx: inverse of observed information (-hess) at optimum
        # recompute hessian at beta
        eta = X @ beta
        w = _safe_exp(eta)
        hess = np.zeros((p, p), dtype=float)
        for t in unique_event_times:
            event_mask = (T == t) & (E == 1)
            d = int(np.sum(event_mask))
            if d == 0:
                continue
            risk_mask = T >= t
            w_risk = w[risk_mask]
            X_risk = X[risk_mask, :]
            S0 = float(np.sum(w_risk))
            if S0 <= 0.0:
                continue
            S1 = (w_risk[:, None] * X_risk).sum(axis=0)
            S2 = (X_risk.T * w_risk) @ X_risk
            mean = S1 / S0
            var = (S2 / S0) - np.outer(mean, mean)
            hess -= d * var
        if self.penalizer and self.penalizer > 0:
            hess -= self.penalizer * np.eye(p)

        info = -hess
        try:
            cov = np.linalg.inv(info)
        except np.linalg.LinAlgError:
            cov = np.linalg.pinv(info + 1e-9 * np.eye(p))

        self.variance_matrix_ = pd.DataFrame(cov, index=covariate_cols, columns=covariate_cols)
        se = np.sqrt(np.clip(np.diag(cov), 0.0, np.inf))
        self.standard_errors_ = pd.Series(se, index=covariate_cols, name="se(coef)")
        self.summary = pd.DataFrame({"coef": self.params_.values, "se(coef)": self.standard_errors_.values}, index=covariate_cols)

        # Baseline cumulative hazard via Breslow
        # H0(t) increments: d(t) / sum_{i in R(t)} exp(eta_i)
        event_times = unique_event_times
        if event_times.size == 0:
            # no events: degenerate baseline
            base_times = np.array([0.0])
            base_H = np.array([0.0])
        else:
            base_times = np.concatenate([[0.0], event_times.astype(float)])
            base_H = [0.0]
            cum = 0.0
            for t in event_times:
                d = int(np.sum((T == t) & (E == 1)))
                risk_mask = T >= t
                denom = float(np.sum(w[risk_mask]))
                inc = (d / denom) if denom > 0 else 0.0
                cum += inc
                base_H.append(float(cum))
            base_H = np.asarray(base_H, dtype=float)

        H_df = pd.DataFrame({"baseline cumulative hazard": base_H}, index=pd.Index(base_times, name="timeline"))
        S0 = np.exp(-H_df["baseline cumulative hazard"].to_numpy(dtype=float))
        S_df = pd.DataFrame({"baseline survival": np.clip(S0, 0.0, 1.0)}, index=H_df.index.copy())

        self.baseline_cumulative_hazard_ = H_df
        self.baseline_survival_ = S_df
        return self

    def predict_survival_function(self, row: pd.DataFrame, times: Any = None) -> pd.DataFrame:
        if self.params_ is None or self.baseline_cumulative_hazard_ is None:
            raise ValueError("Must call fit before predict_survival_function.")
        if not isinstance(row, pd.DataFrame):
            raise ValueError("row must be a pandas DataFrame.")
        if row.shape[0] != 1:
            raise ValueError("row must be a single-row DataFrame.")

        cov_cols = list(self.params_.index)
        missing = [c for c in cov_cols if c not in row.columns]
        if missing:
            raise ValueError(f"Missing covariate columns in row: {missing}")

        x = row[cov_cols].iloc[0].to_numpy(dtype=float)
        eta = float(x @ self.params_.to_numpy(dtype=float))
        hr = float(_safe_exp(np.array([eta], dtype=float))[0])  # exp(eta)

        base_H = self.baseline_cumulative_hazard_["baseline cumulative hazard"]
        base_times = base_H.index.to_numpy(dtype=float)
        base_vals = base_H.to_numpy(dtype=float)

        if times is None:
            out_times = base_times
            H_at = base_vals
        else:
            out_times = np.asarray(times, dtype=float).reshape(-1)
            out_times = np.sort(out_times)
            H_at = _forward_fill_step_at(base_times, base_vals, out_times)

        S = np.exp(-H_at * hr)
        S = np.clip(S, 0.0, 1.0)

        colname = str(row.index[0]) if row.index is not None and len(row.index) == 1 else "0"
        return pd.DataFrame({colname: S}, index=pd.Index(out_times, name="timeline"))