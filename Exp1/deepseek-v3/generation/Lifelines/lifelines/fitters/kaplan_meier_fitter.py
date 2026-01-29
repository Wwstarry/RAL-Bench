import numpy as np
import pandas as pd

class KaplanMeierFitter:
    def __init__(self):
        self.survival_function_ = None
        
    def fit(self, durations, event_observed=None):
        if event_observed is None:
            event_observed = np.ones_like(durations)
            
        durations = np.asarray(durations)
        event_observed = np.asarray(event_observed).astype(bool)
        
        # Sort by duration
        order = np.argsort(durations)
        durations = durations[order]
        event_observed = event_observed[order]
        
        # Calculate survival probabilities
        at_risk = np.arange(len(durations), 0, -1)
        hazards = np.where(event_observed, 1.0 / at_risk, 0)
        survival = np.cumprod(1 - hazards)
        
        # Create survival function DataFrame
        self.survival_function_ = pd.DataFrame({
            'timeline': durations,
            'KM_estimate': survival
        }).set_index('timeline')
        
        return self
        
    def predict(self, time):
        if self.survival_function_ is None:
            raise ValueError("Model not fitted yet")
            
        # Find last time point where timeline <= time
        mask = self.survival_function_.index <= time
        if not mask.any():
            return 1.0
            
        return float(self.survival_function_.loc[mask].iloc[-1]['KM_estimate'])