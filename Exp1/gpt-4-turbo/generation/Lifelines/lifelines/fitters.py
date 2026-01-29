import numpy as np
import pandas as pd

class KaplanMeierFitter:
    """
    Pure Python implementation of the Kaplan-Meier estimator.
    """

    def __init__(self):
        self.survival_function_ = None
        self.event_table_ = None
        self.timeline = None
        self._fitted = False

    def fit(self, durations, event_observed=None, timeline=None, label="KM_estimate"):
        durations = np.asarray(durations)
        if event_observed is None:
            event_observed = np.ones_like(durations, dtype=int)
        else:
            event_observed = np.asarray(event_observed, dtype=int)
        # Remove NaNs
        mask = ~np.isnan(durations)
        durations = durations[mask]
        event_observed = event_observed[mask]

        # Get unique event/censor times
        unique_times = np.sort(np.unique(durations))
        if timeline is not None:
            timeline = np.asarray(timeline)
        else:
            timeline = unique_times

        n = len(durations)
        at_risk = n
        survival_prob = 1.0
        survival_probs = []
        times = []
        idx = 0

        # Precompute event table
        event_table = []
        for t in timeline:
            observed = np.sum((durations == t) & (event_observed == 1))
            censored = np.sum((durations == t) & (event_observed == 0))
            removed = observed + censored
            if at_risk > 0:
                if removed > 0:
                    if observed > 0:
                        survival_prob *= (1.0 - observed / at_risk)
                times.append(t)
                survival_probs.append(survival_prob)
                event_table.append({
                    "removed": removed,
                    "observed": observed,
                    "censored": censored,
                    "at_risk": at_risk,
                })
                at_risk -= removed

        self.survival_function_ = pd.DataFrame(
            data={label: survival_probs},
            index=pd.Index(times, name="timeline"),
        )
        self.event_table_ = pd.DataFrame(event_table, index=pd.Index(times, name="timeline"))
        self.timeline = np.array(times)
        self._label = label
        self._fitted = True
        return self

    def predict(self, times):
        if not self._fitted:
            raise RuntimeError("fit must be called before predict.")
        # Accept scalar or array-like
        times = np.atleast_1d(times)
        surv = self.survival_function_[self._label]
        index = self.survival_function_.index.values
        # For each time, find the last survival prob at or before that time
        res = []
        for t in times:
            idx = np.searchsorted(index, t, side="right") - 1
            if idx < 0:
                res.append(1.0)
            else:
                res.append(surv.iloc[idx])
        if res.__class__ == list and len(res) == 1:
            return float(res[0])
        return np.array(res)

class CoxPHFitter:
    """
    Pure Python implementation of Cox Proportional Hazards model (no ties, Breslow).
    """

    def __init__(self):
        self.summary = None
        self.params_ = None
        self.standard_errors_ = None
        self._fitted = False
        self._X_cols = None
        self._baseline_hazard_ = None
        self._baseline_survival_ = None
        self._duration_col = None
        self._event_col = None

    def fit(self, df, duration_col, event_col, show_progress=False):
        # Only numeric covariates supported
        X = df.drop([duration_col, event_col], axis=1)
        X = X.astype(float)
        T = df[duration_col].values
        E = df[event_col].values.astype(int)
        n, p = X.shape
        self._X_cols = list(X.columns)
        # Sort by time ascending
        order = np.argsort(T)
        T = T[order]
        E = E[order]
        X = X.values[order, :]

        # Newton-Raphson for partial likelihood
        beta = np.zeros(p)
        max_iter = 50
        tol = 1e-7
        for it in range(max_iter):
            risk_scores = np.exp(np.dot(X, beta))
            # For each subject, compute risk set sum
            # Breslow: for each event time, sum over those at risk
            # Compute log-likelihood, gradient, Hessian
            loglik = 0.0
            grad = np.zeros(p)
            hess = np.zeros((p, p))
            for i in range(n):
                if E[i] == 1:
                    xi = X[i]
                    ti = T[i]
                    at_risk = (T >= ti)
                    rs_sum = np.sum(risk_scores[at_risk])
                    loglik += np.dot(beta, xi) - np.log(rs_sum)
                    grad += xi - np.dot(risk_scores[at_risk], X[at_risk]) / rs_sum
                    xbar = np.dot(risk_scores[at_risk], X[at_risk]) / rs_sum
                    x2bar = np.dot(risk_scores[at_risk], X[at_risk]**2) / rs_sum
                    hess -= np.outer(xbar, xbar)
                    hess += np.dot(risk_scores[at_risk], X[at_risk][:, :, None] * X[at_risk][:, None, :]) / rs_sum
            # Invert Hessian
            try:
                delta = np.linalg.solve(-hess, grad)
            except np.linalg.LinAlgError:
                delta = np.linalg.pinv(-hess).dot(grad)
            if np.all(np.abs(delta) < tol):
                break
            beta += delta
        self.params_ = pd.Series(beta, index=self._X_cols)
        # Standard errors: sqrt(diag(inv(-Hessian)))
        try:
            se = np.sqrt(np.diag(np.linalg.inv(-hess)))
        except np.linalg.LinAlgError:
            se = np.full(p, np.nan)
        self.standard_errors_ = pd.Series(se, index=self._X_cols)
        self.summary = pd.DataFrame({
            "coef": self.params_,
            "se(coef)": self.standard_errors_,
        })
        self._fitted = True
        self._duration_col = duration_col
        self._event_col = event_col
        # Estimate baseline hazard and survival
        self._compute_baseline_hazard(T, E, X, beta)
        return self

    def _compute_baseline_hazard(self, T, E, X, beta):
        # Breslow estimator
        n = len(T)
        risk_scores = np.exp(np.dot(X, beta))
        unique_times = np.sort(np.unique(T[E == 1]))
        baseline_hazard = []
        for t in unique_times:
            ix = (T == t) & (E == 1)
            d = np.sum(ix)
            at_risk = (T >= t)
            rs_sum = np.sum(risk_scores[at_risk])
            if rs_sum > 0:
                baseline_hazard.append(d / rs_sum)
            else:
                baseline_hazard.append(0.0)
        baseline_hazard = np.array(baseline_hazard)
        baseline_cum_hazard = np.cumsum(baseline_hazard)
        baseline_survival = np.exp(-baseline_cum_hazard)
        self._baseline_hazard_ = pd.DataFrame({
            "baseline hazard": baseline_hazard
        }, index=unique_times)
        self._baseline_survival_ = pd.DataFrame({
            "baseline survival": baseline_survival
        }, index=unique_times)
        self._baseline_times_ = unique_times

    def predict_survival_function(self, row):
        """
        row: single-row DataFrame of covariates (no duration/event columns)
        Returns: DataFrame with index as time, column as survival probability
        """
        if not self._fitted:
            raise RuntimeError("fit must be called before predict_survival_function.")
        if isinstance(row, pd.Series):
            row = row.to_frame().T
        # Only use covariate columns
        x = row[self._X_cols].values[0]
        exp_xb = np.exp(np.dot(x, self.params_.values))
        surv = self._baseline_survival_["baseline survival"].values ** exp_xb
        df = pd.DataFrame(
            {0: surv},
            index=self._baseline_survival_.index
        )
        return df