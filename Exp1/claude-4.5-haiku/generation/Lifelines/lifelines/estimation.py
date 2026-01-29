import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import xlogy


class KaplanMeierFitter:
    """
    Kaplan-Meier estimator for univariate survival analysis.
    """
    
    def __init__(self):
        self.survival_function_ = None
        self.durations = None
        self.event_observed = None
        self._timeline = None
    
    def fit(self, durations, event_observed, timeline=None):
        """
        Fit the Kaplan-Meier estimator.
        
        Parameters
        ----------
        durations : array-like
            Duration times (T).
        event_observed : array-like
            Event indicators (E), 1 if event occurred, 0 if censored.
        timeline : array-like, optional
            Timeline to evaluate survival function on.
        
        Returns
        -------
        self
        """
        durations = np.asarray(durations, dtype=float)
        event_observed = np.asarray(event_observed, dtype=float)
        
        self.durations = durations
        self.event_observed = event_observed
        
        if timeline is None:
            timeline = np.sort(np.unique(durations[event_observed == 1]))
        
        self._timeline = timeline
        
        # Compute Kaplan-Meier survival function
        survival_prob = np.ones(len(timeline))
        
        for i, t in enumerate(timeline):
            # Number at risk at time t
            at_risk = np.sum(durations >= t)
            # Number of events at time t
            events = np.sum((durations == t) & (event_observed == 1))
            
            if at_risk > 0:
                survival_prob[i] = np.prod(1.0 - events / at_risk)
        
        # Cumulative product to get survival function
        survival_prob = np.cumprod(1.0 - np.diff(np.concatenate([[1.0], survival_prob])))
        survival_prob = survival_prob[1:]
        
        # Recompute more carefully
        survival_prob = np.ones(len(timeline))
        for i, t in enumerate(timeline):
            at_risk = np.sum(durations >= t)
            events = np.sum((durations == t) & (event_observed == 1))
            if at_risk > 0:
                if i == 0:
                    survival_prob[i] = 1.0 - events / at_risk
                else:
                    survival_prob[i] = survival_prob[i-1] * (1.0 - events / at_risk)
        
        self.survival_function_ = pd.DataFrame(
            survival_prob,
            index=timeline,
            columns=['KM_estimate']
        )
        self.survival_function_.index.name = 'T'
        
        return self
    
    def predict(self, time):
        """
        Predict survival probability at a given time.
        
        Parameters
        ----------
        time : float
            Time point at which to predict.
        
        Returns
        -------
        float
            Estimated survival probability at the given time.
        """
        if self.survival_function_ is None:
            raise ValueError("Must fit the model before predicting.")
        
        timeline = self.survival_function_.index.values
        survival_prob = self.survival_function_.iloc[:, 0].values
        
        if time < timeline[0]:
            return 1.0
        
        if time >= timeline[-1]:
            return float(survival_prob[-1])
        
        # Find the largest time point <= given time
        idx = np.searchsorted(timeline, time, side='right') - 1
        return float(survival_prob[idx])


class CoxPHFitter:
    """
    Cox proportional hazards regression model.
    """
    
    def __init__(self):
        self.summary = None
        self.params_ = None
        self._durations = None
        self._event_observed = None
        self._covariates = None
        self._covariate_names = None
        self._baseline_survival = None
        self._baseline_cumulative_hazard = None
    
    def fit(self, df, duration_col, event_col):
        """
        Fit the Cox proportional hazards model.
        
        Parameters
        ----------
        df : pandas.DataFrame
            Data frame containing duration, event, and covariate columns.
        duration_col : str
            Name of the duration column.
        event_col : str
            Name of the event indicator column.
        
        Returns
        -------
        self
        """
        df = df.copy()
        
        durations = df[duration_col].values.astype(float)
        event_observed = df[event_col].values.astype(float)
        
        # Extract covariates (all columns except duration and event)
        covariate_cols = [col for col in df.columns 
                         if col not in [duration_col, event_col]]
        covariates = df[covariate_cols].values.astype(float)
        
        self._durations = durations
        self._event_observed = event_observed
        self._covariates = covariates
        self._covariate_names = covariate_cols
        
        # Standardize covariates
        self._covariate_mean = np.mean(covariates, axis=0)
        self._covariate_std = np.std(covariates, axis=0)
        self._covariate_std[self._covariate_std == 0] = 1.0
        covariates_std = (covariates - self._covariate_mean) / self._covariate_std
        
        # Fit Cox model using partial likelihood
        n_covariates = covariates_std.shape[1]
        
        def partial_likelihood(params):
            risk_scores = np.exp(covariates_std @ params)
            
            ll = 0.0
            unique_times = np.sort(np.unique(durations[event_observed == 1]))
            
            for t in unique_times:
                at_risk_mask = durations >= t
                event_mask = (durations == t) & (event_observed == 1)
                
                at_risk_scores = risk_scores[at_risk_mask]
                event_scores = risk_scores[event_mask]
                
                if np.sum(event_mask) > 0:
                    sum_at_risk = np.sum(at_risk_scores)
                    if sum_at_risk > 0:
                        ll += np.sum(np.log(event_scores / sum_at_risk))
            
            return -ll
        
        # Initial guess
        initial_params = np.zeros(n_covariates)
        
        # Optimize
        result = minimize(partial_likelihood, initial_params, method='BFGS')
        params = result.x
        
        self.params_ = params
        
        # Compute standard errors using Hessian
        eps = 1e-5
        hessian = np.zeros((n_covariates, n_covariates))
        for i in range(n_covariates):
            for j in range(n_covariates):
                params_pp = params.copy()
                params_pp[i] += eps
                params_pp[j] += eps
                
                params_pm = params.copy()
                params_pm[i] += eps
                params_pm[j] -= eps
                
                params_mp = params.copy()
                params_mp[i] -= eps
                params_mp[j] += eps
                
                params_mm = params.copy()
                params_mm[i] -= eps
                params_mm[j] -= eps
                
                hessian[i, j] = (
                    partial_likelihood(params_pp) 
                    - partial_likelihood(params_pm)
                    - partial_likelihood(params_mp)
                    + partial_likelihood(params_mm)
                ) / (4 * eps * eps)
        
        try:
            cov_matrix = np.linalg.inv(hessian)
            se = np.sqrt(np.diag(cov_matrix))
        except np.linalg.LinAlgError:
            se = np.ones(n_covariates) * np.nan
        
        # Create summary DataFrame
        summary_data = {
            'coef': params,
            'se(coef)': se,
        }
        
        self.summary = pd.DataFrame(
            summary_data,
            index=self._covariate_names
        )
        
        # Compute baseline survival
        self._compute_baseline_survival()
        
        return self
    
    def _compute_baseline_survival(self):
        """Compute baseline survival function."""
        risk_scores = np.exp((self._covariates - self._covariate_mean) / self._covariate_std @ self.params_)
        
        unique_times = np.sort(np.unique(self._durations[self._event_observed == 1]))
        baseline_survival = np.ones(len(unique_times))
        
        for i, t in enumerate(unique_times):
            at_risk_mask = self._durations >= t
            event_mask = (self._durations == t) & (self._event_observed == 1)
            
            at_risk_scores = risk_scores[at_risk_mask]
            n_events = np.sum(event_mask)
            
            if np.sum(at_risk_mask) > 0 and n_events > 0:
                sum_at_risk = np.sum(at_risk_scores)
                if i == 0:
                    baseline_survival[i] = np.exp(-n_events / sum_at_risk)
                else:
                    baseline_survival[i] = baseline_survival[i-1] * np.exp(-n_events / sum_at_risk)
        
        self._baseline_survival = pd.DataFrame(
            baseline_survival,
            index=unique_times,
            columns=['baseline_survival']
        )
        self._baseline_survival.index.name = 'T'
    
    def predict_survival_function(self, row):
        """
        Predict survival function for a given covariate row.
        
        Parameters
        ----------
        row : pandas.DataFrame
            Single-row DataFrame with covariate values.
        
        Returns
        -------
        pandas.DataFrame
            Survival function indexed by time.
        """
        if self.params_ is None:
            raise ValueError("Must fit the model before predicting.")
        
        row = row.copy()
        
        # Extract covariates in the same order as training
        covariates = row[self._covariate_names].values.astype(float)
        
        # Standardize using training statistics
        covariates_std = (covariates - self._covariate_mean) / self._covariate_std
        
        # Compute risk score
        risk_score = np.exp(covariates_std @ self.params_)[0]
        
        # Compute survival function
        baseline_times = self._baseline_survival.index.values
        baseline_surv = self._baseline_survival.iloc[:, 0].values
        
        survival_prob = baseline_surv ** risk_score
        
        result = pd.DataFrame(
            survival_prob,
            index=baseline_times,
            columns=['survival_function']
        )
        result.index.name = 'T'
        
        return result