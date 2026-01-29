import numpy as np
import pandas as pd


class KaplanMeierFitter:
    def __init__(self):
        self.survival_function_ = None
        self.event_table_ = None

    def fit(self, durations, event_observed=None):
        durations = np.asarray(durations)
        if event_observed is None:
            event_observed = np.ones_like(durations, dtype=bool)
        else:
            event_observed = np.asarray(event_observed).astype(bool)

        # Sort durations and events by ascending time
        order = np.argsort(durations)
        durations = durations[order]
        event_observed = event_observed[order]

        # Unique event times
        unique_times = np.unique(durations[event_observed])

        n = len(durations)
        at_risk = n
        survival_prob = 1.0
        survival_probs = []
        times = []

        # For each unique event time, compute number of events and number at risk
        for t in unique_times:
            d = np.sum((durations == t) & event_observed)
            # Number at risk is number with duration >= t
            at_risk = np.sum(durations >= t)
            if at_risk == 0:
                # no one at risk, survival stays the same
                survival_probs.append(survival_prob)
                times.append(t)
                continue
            survival_prob *= (1 - d / at_risk)
            survival_probs.append(survival_prob)
            times.append(t)

        self.survival_function_ = pd.DataFrame(
            data={"KM_estimate": survival_probs}, index=pd.Index(times, name="timeline")
        )
        return self

    def predict(self, time):
        # Return survival probability at given time
        # If time < first event time, survival = 1
        # If time > last event time, survival = last survival prob
        if self.survival_function_ is None:
            raise ValueError("Must fit before calling predict")

        sf = self.survival_function_
        if time < sf.index[0]:
            return 1.0
        if time > sf.index[-1]:
            return sf.iloc[-1, 0]

        # Find the greatest time <= time
        idx = sf.index.get_indexer([time], method="ffill")[0]
        return sf.iloc[idx, 0]


class CoxPHFitter:
    def __init__(self):
        self.params_ = None  # coefficients
        self.standard_errors_ = None
        self.baseline_survival_ = None
        self.duration_col = None
        self.event_col = None
        self._fitted = False
        self._unique_times = None
        self._X = None
        self._df = None

    def fit(self, df, duration_col, event_col):
        self.duration_col = duration_col
        self.event_col = event_col

        # Extract data
        durations = df[duration_col].values
        events = df[event_col].values.astype(bool)
        X = df.drop(columns=[duration_col, event_col])
        X = X.astype(float)
        self._X = X
        self._df = df

        n, p = X.shape

        # Sort by duration ascending
        order = np.argsort(durations)
        durations = durations[order]
        events = events[order]
        X = X.iloc[order]

        # Unique event times
        unique_times = np.unique(durations[events])
        self._unique_times = unique_times

        # Initialize coefficients
        beta = np.zeros(p)

        # Newton-Raphson method for partial likelihood maximization
        max_iter = 100
        tol = 1e-6

        for iteration in range(max_iter):
            # Compute risk scores and exp(beta'x)
            lin_pred = np.dot(X, beta)
            exp_lin_pred = np.exp(lin_pred)

            # Initialize gradient and Hessian
            gradient = np.zeros(p)
            hessian = np.zeros((p, p))

            # For each unique event time, compute risk set sums
            for t in unique_times:
                # Risk set: individuals with duration >= t
                risk_set = durations >= t
                X_risk = X[risk_set]
                exp_risk = exp_lin_pred[risk_set]

                # Sum of exp(beta'x) in risk set
                sum_exp = np.sum(exp_risk)
                # Weighted sums of covariates
                weighted_sum = np.sum(X_risk.multiply(exp_risk, axis=0), axis=0).values

                # Number of events at time t
                d = np.sum((durations == t) & events)

                # Sum of covariates for events at time t
                X_events = X[(durations == t) & events]
                sum_events = np.sum(X_events.values, axis=0)

                # Update gradient and Hessian
                gradient += sum_events - d * weighted_sum / sum_exp

                # Compute weighted outer product for Hessian
                weighted_outer = np.zeros((p, p))
                for i in range(len(X_risk)):
                    xi = X_risk.iloc[i].values.reshape(-1, 1)
                    weighted_outer += exp_risk[i] * (xi @ xi.T)
                hessian += d * (weighted_outer / sum_exp - np.outer(weighted_sum, weighted_sum) / (sum_exp ** 2))

            # Newton-Raphson update
            try:
                delta = np.linalg.solve(hessian, gradient)
            except np.linalg.LinAlgError:
                # Hessian singular, stop
                break

            beta_new = beta + delta

            if np.max(np.abs(delta)) < tol:
                beta = beta_new
                break

            beta = beta_new

        self.params_ = pd.Series(beta, index=X.columns, name="coef")

        # Compute standard errors from inverse Hessian
        try:
            cov_matrix = np.linalg.inv(-hessian)
            se = np.sqrt(np.diag(cov_matrix))
        except np.linalg.LinAlgError:
            se = np.full(p, np.nan)

        self.standard_errors_ = pd.Series(se, index=X.columns, name="se(coef)")

        # Compute baseline survival function using Breslow estimator
        baseline_hazard = []
        baseline_survival = []
        cum_hazard = 0.0

        for t in unique_times:
            risk_set = durations >= t
            exp_risk = np.exp(np.dot(X[risk_set], beta))
            d = np.sum((durations == t) & events)
            hazard = d / np.sum(exp_risk)
            cum_hazard += hazard
            baseline_hazard.append(hazard)
            baseline_survival.append(np.exp(-cum_hazard))

        self.baseline_survival_ = pd.Series(baseline_survival, index=unique_times, name="baseline_survival")

        # Prepare summary DataFrame
        self.summary = pd.DataFrame({
            "coef": self.params_,
            "se(coef)": self.standard_errors_,
        })

        self._fitted = True
        return self

    def predict_survival_function(self, row):
        if not self._fitted:
            raise ValueError("Model must be fitted before prediction")

        if not isinstance(row, pd.DataFrame):
            raise ValueError("Input must be a single-row DataFrame")

        if row.shape[0] != 1:
            raise ValueError("Input DataFrame must have exactly one row")

        # Extract covariates in same order as fitted
        X_row = row[self.params_.index].astype(float).values.flatten()
        beta = self.params_.values

        # Compute linear predictor
        lin_pred = np.dot(X_row, beta)

        # Compute survival function at each baseline time
        surv = self.baseline_survival_ ** np.exp(lin_pred)

        # Return as DataFrame indexed by timeline
        return pd.DataFrame(surv.values, index=self.baseline_survival_.index, columns=["survival_function"])