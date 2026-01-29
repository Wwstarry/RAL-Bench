import numpy as np
import pandas as pd

class KaplanMeierFitter:
    """
    A minimal Kaplan-Meier fitter that computes the univariate survival function
    from duration and event data.
    """
    def __init__(self):
        self.survival_function_ = None
        self._label = "KM_estimate"
        self.durations = None
        self.event_observed = None

    def fit(self, durations, event_observed=None, label="KM_estimate"):
        # Convert to numpy arrays
        durations = np.array(durations, dtype=float)
        if event_observed is None:
            event_observed = np.ones_like(durations, dtype=int)
        else:
            event_observed = np.array(event_observed, dtype=int)

        # Sort by time
        order = np.argsort(durations)
        durations = durations[order]
        event_observed = event_observed[order]

        # Compute the number at risk and number of events at each unique time
        unique_times, indices = np.unique(durations, return_index=True)
        n = len(durations)
        at_risk = n - indices  # number at risk at each unique time

        # events at each unique time
        event_counts = []
        start_idx = 0
        for idx in indices:
            event_counts.append(event_observed[start_idx:idx+1].sum())
            start_idx = idx+1
        event_counts = np.array(event_counts, dtype=float)

        # Kaplan-Meier estimation
        km_values = []
        km_current = 1.0
        for i, t in enumerate(unique_times):
            if at_risk[i] > 0:
                # update step
                km_current *= (1.0 - event_counts[i] / at_risk[i])
            km_values.append(km_current)

        # Build survival_function_ as a DataFrame
        self.survival_function_ = pd.DataFrame(km_values, 
                                               index=unique_times, 
                                               columns=[label])
        self._label = label
        self.durations = durations
        self.event_observed = event_observed
        return self

    def predict(self, time):
        """
        Returns the estimated survival probability at the given time.
        """
        # If no fit has been performed, return None or raise an error
        if self.survival_function_ is None:
            raise ValueError("KaplanMeierFitter has not been fit yet.")

        sf_index = self.survival_function_.index
        sf_values = self.survival_function_[self._label].values

        # If time < first time in index, survival is 1.0
        if time < sf_index[0]:
            return 1.0

        # If time > last time in index, survival is the last known value
        if time >= sf_index[-1]:
            return sf_values[-1]

        # Otherwise, find where time fits
        idx = np.searchsorted(sf_index, time, side="right") - 1
        return sf_values[idx]


class CoxPHFitter:
    """
    A minimal Cox Proportional Hazards fitter.
    """
    def __init__(self):
        self.summary = None
        self.params_ = None
        self.baseline_hazard_ = None
        self.baseline_cumulative_hazard_ = None
        self.baseline_survival_ = None
        self._duration_col = None
        self._event_col = None
        self._covariates = []

    def fit(self, df, duration_col=None, event_col=None, show_progress=False):
        """
        Fit a Cox proportional hazards model using a simple Newton-Raphson
        method on the partial log-likelihood.
        """
        # Copy data to avoid modification
        df = df.copy()

        self._duration_col = duration_col
        self._event_col = event_col

        # Extract durations and events
        T = np.asarray(df[duration_col], dtype=float)
        E = np.asarray(df[event_col], dtype=bool)

        # Covariates are numeric columns other than duration_col and event_col
        self._covariates = [col for col in df.columns 
                            if col not in [duration_col, event_col]]
        X = df[self._covariates].values.astype(float)

        # Sort data by time ascending
        order = np.argsort(T)
        T = T[order]
        E = E[order]
        X = X[order, :]

        # Initialize coefficients (betas)
        n_covs = X.shape[1]
        beta = np.zeros(n_covs, dtype=float)

        # Newton-Raphson loop
        # We'll do a small number of iterations for simplicity
        for _ in range(20):
            # Calculate the risk score for each row
            risk = np.exp(np.dot(X, beta))

            # For partial likelihood, we need sums over risk sets
            # We'll go event by event and accumulate
            loglik = 0.0
            g = np.zeros(n_covs)
            h = np.zeros((n_covs, n_covs))

            # We'll track the cumulative sum of the risk from the end
            # but here we'll do it in a straightforward approach
            for i in range(len(T)):
                if E[i]:  # if event
                    # risk set = everyone with T_j >= T_i
                    idx_risk = (T >= T[i])
                    r_sum = risk[idx_risk].sum()
                    loglik += np.dot(beta, X[i]) - np.log(r_sum)

                    # gradient
                    g += X[i] - (X[idx_risk] * risk[idx_risk, None]).sum(axis=0) / r_sum

                    # hessian
                    x_mean = (X[idx_risk] * risk[idx_risk, None]).sum(axis=0) / r_sum
                    # second term
                    s2 = (X[idx_risk] * risk[idx_risk, None]).T @ (X[idx_risk] * risk[idx_risk, None]) / (r_sum**2)
                    h -= np.outer(x_mean, x_mean) - s2

            # update coefficients
            # invert h
            try:
                step = np.linalg.inv(-h) @ g
            except np.linalg.LinAlgError:
                # fallback or break
                break

            beta_update = beta + step
            if np.max(np.abs(step)) < 1e-6:
                beta = beta_update
                break
            beta = beta_update

        self.params_ = beta

        # Compute standard errors from the inverted Hessian
        try:
            cov = np.linalg.inv(-h)
        except np.linalg.LinAlgError:
            cov = np.full((n_covs, n_covs), np.nan)

        se = np.sqrt(np.diag(cov))

        # Build summary
        self.summary = pd.DataFrame({
            'coef': beta,
            'se(coef)': se
        }, index=self._covariates)

        # Compute baseline hazard function step-wise
        # baseline_hazard at time t_i = number of events at t_i / sum_{j in R(t_i)} exp(x_j^T beta)
        unique_times, event_counts = np.unique(T[E], return_counts=True)
        self.baseline_hazard_ = pd.DataFrame(index=unique_times, columns=["baseline hazard"])
        for t_idx, t_val in enumerate(unique_times):
            # risk set = T >= t_val
            idx_risk = (T >= t_val)
            r_sum = np.exp(np.dot(X[idx_risk], beta)).sum()
            self.baseline_hazard_.loc[t_val, "baseline hazard"] = event_counts[t_idx] / r_sum

        # fill cumulative hazard
        self.baseline_cumulative_hazard_ = self.baseline_hazard_.cumsum()
        self.baseline_survival_ = pd.DataFrame(
            data=np.exp(-self.baseline_cumulative_hazard_.values),
            index=self.baseline_cumulative_hazard_.index,
            columns=["baseline survival"]
        )

        return self

    def predict_survival_function(self, row):
        """
        Given a single-row DataFrame (or dict-like) with covariate values,
        return the predicted survival function as a pandas DataFrame
        with survival probabilities in [0,1].
        """
        if self.params_ is None:
            raise ValueError("Model has not been fit yet.")

        x = row[self._covariates].values[0]  # single row
        # hazard ratio
        hr = np.exp(np.dot(x, self.params_))

        # times for baseline
        times = self.baseline_survival_.index
        baseline_surv = self.baseline_survival_["baseline survival"].values

        # S(t|x) = [S0(t)]^exp(x^T beta) in classical formulations
        # or exp(-H0(t) * exp(x^T beta)) - they are equivalent
        # We'll use the baseline_surv^(hr^0?), wait carefully:
        # baseline_surv(t) = exp(- H0(t))
        # S(t|x) = exp(- H0(t) * exp(x^T beta))
        # => S(t|x) = ( exp(-H0(t)) )^exp(x^T beta) = (baseline_surv)^(hr)
        surv_vals = baseline_surv ** hr

        return pd.DataFrame(surv_vals, index=times, columns=["predicted_survival"])