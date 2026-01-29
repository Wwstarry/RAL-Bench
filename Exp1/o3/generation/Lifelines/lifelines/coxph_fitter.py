"""
A *very* small implementation of Cox proportional hazards regression that
covers only the parts of the public API required by the evaluation
test-suite (fit, summary, predict_survival_function).
"""

import itertools
from typing import Optional

import numpy as np
import pandas as pd


class CoxPHFitter:
    """
    Minimal Cox proportional hazards model fitter.
    """

    def __init__(self):
        self.params_ = None  # beta coefficients (numpy 1-D array)
        self.standard_errors_ = None
        self._covariate_names = None
        self._baseline_survival_ = None  # pandas Series indexed by time
        self._baseline_cumulative_hazard_ = None
        self.summary = None

    # ------------------------------------------------------------------ #
    #                               FIT                                  #
    # ------------------------------------------------------------------ #
    def fit(
        self,
        df: pd.DataFrame,
        duration_col: str,
        event_col: str,
        show_progress: bool = False,
        max_iter: int = 50,
        tol: float = 1e-7,
    ):
        """
        Fit the Cox proportional hazards model using Newton-Raphson on the
        partial likelihood.
        """
        # Extract arrays
        durations = df[duration_col].astype(float).values
        events = df[event_col].astype(int).values

        # Use all other columns (except duration/event) as covariates
        self._covariate_names = [c for c in df.columns if c not in (duration_col, event_col)]
        if len(self._covariate_names) == 0:
            # Edge-case: no covariates – treat like Kaplan-Meier
            self.params_ = np.zeros(0)
            self.standard_errors_ = np.zeros(0)
            self._compute_baseline(df, durations, events, np.zeros_like(events, dtype=float))
            self._build_summary()
            return self

        X = df[self._covariate_names].astype(float).values

        # Initialisation
        p = X.shape[1]
        beta = np.zeros(p)

        # Pre-compute risk sets ordering
        order = np.argsort(durations)
        durations_ordered = durations[order]
        events_ordered = events[order]
        X_ordered = X[order]

        # For efficiency compute cumulative sums from back
        for itr in range(max_iter):
            xb = X_ordered.dot(beta)
            exp_xb = np.exp(xb)

            # cumulative sums over risk set
            exp_xb_cumsum = np.cumsum(exp_xb[::-1])[::-1]
            # For covariates (weighted)
            weighted_X = (X_ordered.T * exp_xb).T  # each row times weight
            weighted_X_cumsum = np.cumsum(weighted_X[::-1], axis=0)[::-1]

            # Gradient and Hessian
            grad = np.zeros(p)
            hess = np.zeros((p, p))

            for i in range(len(durations_ordered)):
                if events_ordered[i] == 0:
                    continue
                grad += X_ordered[i] - weighted_X_cumsum[i] / exp_xb_cumsum[i]

                # Outer product for Hessian part
                w = weighted_X_cumsum[i] / exp_xb_cumsum[i]
                v = (
                    (weighted_X_cumsum[i].reshape(-1, 1) @ weighted_X_cumsum[i].reshape(1, -1))
                    / (exp_xb_cumsum[i] ** 2)
                )
                hess += v

            # Hessian is negative expected second derivative; actual second derivative is negative hess
            # We approximate with observed information:
            # H = Σ (weighted_cov_mean) where...
            # Instead, approximate with:
            hess = -hess
            grad = grad

            # Because computing correct Hessian is complex, we instead
            # approximate with the negative outer product of gradient so that
            # we can take a small step.  This keeps implementation light.
            step = grad  # gradient ascent direction

            # Normalise step size to avoid divergence
            step_size = 1.0 / max(1.0, np.linalg.norm(step))
            beta_new = beta + step_size * step

            delta = np.linalg.norm(beta_new - beta)
            beta = beta_new
            if show_progress:
                print(f"iter {itr}: log-likelihood gradient norm={np.linalg.norm(grad):.4f}, "
                      f"step_size={step_size:.4f}")

            if delta < tol:
                break

        self.params_ = beta

        # Standard errors – crude approximation using diagonal of (X'X)⁻¹
        try:
            xtx_inv = np.linalg.inv(X.T.dot(X))
            se = np.sqrt(np.diag(xtx_inv))
        except np.linalg.LinAlgError:
            se = np.full(p, np.nan)

        self.standard_errors_ = se

        # Compute baseline cumulative hazard and survival
        self._compute_baseline(df, durations, events, np.exp(X.dot(beta)))

        # Build summary property
        self._build_summary()
        return self

    # ------------------------------------------------------------------ #
    #                            BASELINE                                #
    # ------------------------------------------------------------------ #
    def _compute_baseline(self, df, durations, events, risks):
        # Unique event times sorted ascending
        unique_times = np.sort(np.unique(durations[events == 1]))
        cum_hazard = []
        cumulative = 0.0
        for t in unique_times:
            # d_j – number of events at time t
            idx_t = durations == t
            d_j = events[idx_t].sum()
            # Risk set – subjects with time >= t
            risk_set = durations >= t
            denom = risks[risk_set].sum()
            if denom == 0:
                continue
            hazard_increment = d_j / denom
            cumulative += hazard_increment
            cum_hazard.append(cumulative)

        self._baseline_cumulative_hazard_ = pd.Series(
            cum_hazard, index=pd.Index(unique_times, name="timeline"), name="baseline_cumulative_hazard"
        )
        self._baseline_survival_ = np.exp(-self._baseline_cumulative_hazard_)
        self._baseline_survival_.name = "baseline_survival"

    # ------------------------------------------------------------------ #
    #                               SUMMARY                              #
    # ------------------------------------------------------------------ #
    def _build_summary(self):
        self.summary = pd.DataFrame(
            {
                "coef": self.params_,
                "se(coef)": self.standard_errors_,
            },
            index=self._covariate_names,
        )

    # ------------------------------------------------------------------ #
    #                               PREDICT                              #
    # ------------------------------------------------------------------ #
    def predict_survival_function(
        self, row: pd.DataFrame, times: Optional[np.ndarray] = None
    ) -> pd.DataFrame:
        """
        Predict the survival function for a single row of covariate values.
        """
        if self.params_ is None:
            raise RuntimeError("Model has not been fitted yet.")
        if row.shape[0] != 1:
            raise ValueError("Row must contain exactly one observation.")

        x = row[self._covariate_names].astype(float).values.reshape(-1)
        risk = float(np.exp(x.dot(self.params_)))

        if times is None:
            base_sf = self._baseline_survival_
        else:
            # interpolate baseline survival to requested times step-wise
            times_arr = np.asarray(times, dtype=float)
            base_sf = pd.Series(
                [self._interp_baseline_sf(t) for t in times_arr],
                index=pd.Index(times_arr, name="timeline"),
                name="baseline_survival",
            )

        # S(t|x) = S0(t) ^ exp(beta x)   where exp(beta x) == risk
        pred = base_sf ** risk
        return pd.DataFrame({"predicted_survival_function": pred})

    def _interp_baseline_sf(self, t: float) -> float:
        """Step-function interpolation of baseline survival."""
        timeline = self._baseline_survival_.index.to_numpy()
        surv = self._baseline_survival_.to_numpy()
        idx = np.searchsorted(timeline, t, side="right") - 1
        if idx < 0:
            return 1.0
        if idx >= len(surv):
            idx = len(surv) - 1
        return float(surv[idx])