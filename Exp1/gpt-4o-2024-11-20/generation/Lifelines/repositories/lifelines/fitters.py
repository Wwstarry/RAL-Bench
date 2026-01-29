import numpy as np
import pandas as pd
from scipy.optimize import minimize

class KaplanMeierFitter:
    def __init__(self):
        self.survival_function_ = None
        self.timeline = None

    def fit(self, durations, event_observed):
        durations = np.asarray(durations)
        event_observed = np.asarray(event_observed)

        df = pd.DataFrame({"durations": durations, "event_observed": event_observed})
        df = df.sort_values("durations")

        n_at_risk = len(df)
        survival_prob = 1.0
        survival_function = []

        for i, row in df.iterrows():
            if row["event_observed"] == 1:
                survival_prob *= (n_at_risk - 1) / n_at_risk
            survival_function.append((row["durations"], survival_prob))
            n_at_risk -= 1

        self.survival_function_ = pd.DataFrame(survival_function, columns=["timeline", "survival_probability"]).set_index("timeline")
        self.timeline = self.survival_function_.index
        return self

    def predict(self, time):
        if self.survival_function_ is None:
            raise ValueError("Model must be fitted before calling predict.")
        return self.survival_function_.loc[:time].iloc[-1]["survival_probability"] if time in self.timeline else 0.0


class CoxPHFitter:
    def __init__(self):
        self.summary = None
        self.params_ = None

    def fit(self, df, duration_col, event_col):
        durations = df[duration_col].values
        events = df[event_col].values
        covariates = df.drop(columns=[duration_col, event_col]).values

        def negative_log_likelihood(params):
            baseline_hazard = np.exp(np.dot(covariates, params))
            log_likelihood = np.sum(events * np.dot(covariates, params) - baseline_hazard * durations)
            return -log_likelihood

        initial_params = np.zeros(covariates.shape[1])
        result = minimize(negative_log_likelihood, initial_params, method="BFGS")
        self.params_ = result.x

        se = np.sqrt(np.diag(result.hess_inv))
        self.summary = pd.DataFrame({"coef": self.params_, "se(coef)": se})
        return self

    def predict_survival_function(self, row):
        if self.params_ is None:
            raise ValueError("Model must be fitted before calling predict_survival_function.")
        baseline_hazard = np.exp(np.dot(row.values, self.params_))
        survival_curve = np.exp(-baseline_hazard * self.summary.index.values)
        return pd.Series(survival_curve, index=self.summary.index)