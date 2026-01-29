from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize


class CoxPHFitter:
    """
    Minimal Cox proportional hazards fitter compatible with core lifelines API.

    Implements partial likelihood estimation with Efron tie handling (approx).
    Provides coef_ and summary (coef, se(coef)).
    Also provides predict_survival_function for a single-row DataFrame.
    """

    def __init__(self, penalizer: float = 0.0):
        self.penalizer = float(penalizer)
        self.params_: pd.Series | None = None
        self.variance_matrix_: pd.DataFrame | None = None
        self.summary: pd.DataFrame | None = None
        self.baseline_cumulative_hazard_: pd.DataFrame | None = None
        self.baseline_survival_: pd.DataFrame | None = None
        self._duration_col: str | None = None
        self._event_col: str | None = None
        self._covariate_cols: list[str] | None = None

    def fit(self, df: pd.DataFrame, duration_col: str, event_col: str):
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame.")
        if duration_col not in df.columns or event_col not in df.columns:
            raise ValueError("duration_col and event_col must be columns in df.")
        self._duration_col = duration_col
        self._event_col = event_col

        work = df.copy()
        # select covariates: numeric columns excluding duration/event
        covariate_cols = [c for c in work.columns if c not in (duration_col, event_col)]
        if len(covariate_cols) == 0:
            raise ValueError("No covariates found to fit CoxPH model.")
        X = work[covariate_cols]
        # coerce to numeric
        X = X.apply(pd.to_numeric, errors="raise")
        T = pd.to_numeric(work[duration_col], errors="raise").astype(float).values
        E = pd.to_numeric(work[event_col], errors="raise").astype(int).values

        if np.any(T < 0) or np.any(~np.isfinite(T)):
            raise ValueError("durations must be non-negative and finite.")
        if np.any((E != 0) & (E != 1)):
            # allow other ints but treat nonzero as 1? lifelines expects 0/1.
            E = (E != 0).astype(int)

        # Standardize covariates to improve numerical stability; keep means/stds for later.
        Xv = X.values.astype(float)
        means = Xv.mean(axis=0)
        stds = Xv.std(axis=0, ddof=0)
        stds[stds == 0] = 1.0
        Z = (Xv - means) / stds

        # Sort by time ascending (required for risk sets)
        order = np.argsort(T, kind="mergesort")
        T = T[order]
        E = E[order]
        Z = Z[order, :]

        n, p = Z.shape

        # unique event times
        event_times = np.unique(T[E == 1])

        def neg_loglik_and_grad(beta):
            beta = beta.reshape(-1)
            eta = Z @ beta
            exp_eta = np.exp(np.clip(eta, -50, 50))

            ll = 0.0
            grad = np.zeros(p, dtype=float)

            # For each event time, compute risk set sums and event sums.
            # Efron approximation for ties:
            for t in event_times:
                ix_event = (T == t) & (E == 1)
                d = int(ix_event.sum())
                if d == 0:
                    continue
                ix_risk = T >= t

                sum_risk = exp_eta[ix_risk].sum()
                sum_risk_x = (exp_eta[ix_risk, None] * Z[ix_risk]).sum(axis=0)

                sum_event = exp_eta[ix_event].sum()
                sum_event_x = (exp_eta[ix_event, None] * Z[ix_event]).sum(axis=0)

                # contribution of tied deaths:
                # ll += sum_i in D eta_i - sum_{l=0}^{d-1} log( sum_risk - l/d * sum_event )
                ll += eta[ix_event].sum()
                for l in range(d):
                    frac = l / d
                    denom = sum_risk - frac * sum_event
                    denom = max(denom, 1e-50)
                    ll -= np.log(denom)
                    grad += (sum_risk_x - frac * sum_event_x) / denom
                grad -= Z[ix_event].sum(axis=0)

            # penalizer (L2)
            if self.penalizer > 0:
                ll -= 0.5 * self.penalizer * float(beta @ beta)
                grad -= self.penalizer * beta

            return -ll, -grad

        def objective(beta):
            val, _ = neg_loglik_and_grad(beta)
            return float(val)

        def gradient(beta):
            _, g = neg_loglik_and_grad(beta)
            return g

        beta0 = np.zeros(p, dtype=float)
        res = minimize(objective, beta0, jac=gradient, method="BFGS")
        beta_hat = res.x

        # Approximate variance from inverse Hessian (BFGS provides it)
        if hasattr(res, "hess_inv"):
            try:
                hess_inv = np.array(res.hess_inv)
                if hess_inv.shape != (p, p):
                    hess_inv = np.eye(p)
            except Exception:
                hess_inv = np.eye(p)
        else:
            hess_inv = np.eye(p)

        # Transform coefficients back to original scale: eta = (x-mean)/std @ beta
        # => coef_original = beta / std ; baseline absorbed by intercept not present.
        coef = beta_hat / stds
        var = hess_inv / (stds[:, None] * stds[None, :])

        self._covariate_cols = covariate_cols
        self.params_ = pd.Series(coef, index=covariate_cols, name="coef")
        self.variance_matrix_ = pd.DataFrame(var, index=covariate_cols, columns=covariate_cols)

        se = np.sqrt(np.clip(np.diag(var), 0.0, np.inf))
        self.summary = pd.DataFrame(
            {
                "coef": self.params_.values,
                "se(coef)": se,
            },
            index=covariate_cols,
        )

        # Baseline cumulative hazard via Breslow estimator using original-scale X
        X_orig = X.values.astype(float)[order, :]
        linpred = X_orig @ coef
        exp_lp = np.exp(np.clip(linpred, -50, 50))

        base_times = np.unique(T)
        H0 = np.zeros_like(base_times, dtype=float)
        cum = 0.0
        for i, t in enumerate(base_times):
            d = float(((T == t) & (E == 1)).sum())
            if d <= 0:
                H0[i] = cum
                continue
            risk = exp_lp[T >= t].sum()
            risk = max(float(risk), 1e-50)
            cum += d / risk
            H0[i] = cum

        self.baseline_cumulative_hazard_ = pd.DataFrame({"baseline cumulative hazard": H0}, index=base_times)
        S0 = np.exp(-H0)
        S0 = np.clip(S0, 0.0, 1.0)
        self.baseline_survival_ = pd.DataFrame({"baseline survival": S0}, index=base_times)
        return self

    def predict_survival_function(self, df: pd.DataFrame, times=None) -> pd.DataFrame:
        if self.params_ is None or self.baseline_survival_ is None:
            raise ValueError("Must call fit before predict_survival_function.")
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame.")
        if len(df) != 1:
            raise ValueError("df must be a single-row DataFrame.")
        covariate_cols = list(self.params_.index)
        x = df[covariate_cols].apply(pd.to_numeric, errors="raise").iloc[0].values.astype(float)
        coef = self.params_.values.astype(float)
        hr = float(np.exp(np.clip(x @ coef, -50, 50)))

        base = self.baseline_survival_.iloc[:, 0]
        base_times = self.baseline_survival_.index.values.astype(float)

        if times is None:
            times_arr = base_times
        else:
            times_arr = np.asarray(times, dtype=float)
            times_arr = np.unique(times_arr)
            times_arr.sort()

        # interpolate baseline cumulative hazard then compute S(t|x)=exp(-H0(t)*hr)
        H0 = -np.log(np.clip(base.values, 1e-50, 1.0))
        H0_interp = np.interp(times_arr, base_times, H0, left=0.0, right=float(H0[-1]) if len(H0) else 0.0)
        S = np.exp(-H0_interp * hr)
        S = np.clip(S, 0.0, 1.0)
        return pd.DataFrame(S, index=times_arr, columns=["survival_function"])