import numpy as np
import pandas as pd
from scipy.optimize import minimize

class CoxPHFitter:
    def __init__(self):
        self.summary = None
        self._coefs = None
        self._baseline_hazard = None
        
    def fit(self, df, duration_col, event_col):
        durations = df[duration_col].values
        events = df[event_col].values.astype(bool)
        covariates = df.drop([duration_col, event_col], axis=1).values
        
        # Initialize coefficients
        initial_coefs = np.zeros(covariates.shape[1])
        
        # Optimize partial likelihood
        result = minimize(
            fun=self._partial_log_likelihood,
            x0=initial_coefs,
            args=(covariates, durations, events),
            method='BFGS'
        )
        
        self._coefs = result.x
        self._compute_baseline_hazard(durations, events, covariates)
        
        # Create summary DataFrame
        self.summary = pd.DataFrame({
            'coef': self._coefs,
            'se(coef)': np.sqrt(np.diag(result.hess_inv))
        }, index=df.drop([duration_col, event_col], axis=1).columns)
        
        return self
        
    def _partial_log_likelihood(self, coefs, covariates, durations, events):
        risk_scores = np.exp(covariates @ coefs)
        log_lik = 0
        
        for t in np.unique(durations[events]):
            at_risk = durations >= t
            events_at_t = (durations == t) & events
            
            sum_risk = np.sum(risk_scores[at_risk])
            if sum_risk == 0:
                continue
                
            log_lik += np.sum(covariates[events_at_t] @ coefs) - np.sum(events_at_t) * np.log(sum_risk)
            
        return -log_lik
        
    def _compute_baseline_hazard(self, durations, events, covariates):
        unique_times = np.sort(np.unique(durations[events]))
        baseline_hazard = []
        risk_scores = np.exp(covariates @ self._coefs)
        
        for t in unique_times:
            at_risk = durations >= t
            events_at_t = (durations == t) & events
            
            sum_risk = np.sum(risk_scores[at_risk])
            if sum_risk == 0:
                hazard = 0
            else:
                hazard = np.sum(events_at_t) / sum_risk
                
            baseline_hazard.append((t, hazard))
            
        self._baseline_hazard = pd.DataFrame(baseline_hazard, columns=['timeline', 'baseline_hazard'])
        
    def predict_survival_function(self, row):
        if self._coefs is None or self._baseline_hazard is None:
            raise ValueError("Model not fitted yet")
            
        covariates = row.drop([col for col in row.index if col in ['T', 'E']]).values
        risk_score = np.exp(np.dot(covariates, self._coefs))
        
        cumulative_hazard = self._baseline_hazard['baseline_hazard'].cumsum() * risk_score
        survival = np.exp(-cumulative_hazard)
        
        return pd.DataFrame({
            'timeline': self._baseline_hazard['timeline'],
            'survival_function': survival.values
        }).set_index('timeline')