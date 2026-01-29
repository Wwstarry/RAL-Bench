"""
Kaplan-Meier non-parametric survival estimator.
"""

import numpy as np
import pandas as pd
from typing import Optional, Union


class KaplanMeierFitter:
    """Kaplan-Meier estimator for univariate survival analysis."""
    
    def __init__(self):
        """Initialize the Kaplan-Meier fitter."""
        self.survival_function_ = None
        self._fitted = False
        
    def fit(
        self,
        durations: Union[np.ndarray, pd.Series, list],
        event_observed: Optional[Union[np.ndarray, pd.Series, list]] = None
    ) -> 'KaplanMeierFitter':
        """
        Fit the Kaplan-Meier estimator to survival data.
        
        Parameters
        ----------
        durations : array-like
            Length n, duration (relative to origin) of each subject
        event_observed : array-like, optional
            Length n, 1 if event observed, 0 if censored. Defaults to all observed.
            
        Returns
        -------
        self : KaplanMeierFitter
            Returns self with fitted survival function.
        """
        # Convert inputs to numpy arrays
        durations = np.asarray(durations, dtype=np.float64)
        
        if event_observed is None:
            event_observed = np.ones_like(durations, dtype=np.int32)
        else:
            event_observed = np.asarray(event_observed, dtype=np.int32)
        
        # Sort by duration
        sort_idx = np.argsort(durations)
        durations = durations[sort_idx]
        event_observed = event_observed[sort_idx]
        
        # Calculate unique times and counts
        unique_times, counts = np.unique(durations, return_counts=True)
        
        # Initialize survival function
        survival_prob = 1.0
        survival_times = [0.0]
        survival_probs = [1.0]
        
        # Calculate Kaplan-Meier estimator
        at_risk = len(durations)
        event_idx = 0
        
        for time, count in zip(unique_times, counts):
            # Count events and censored at this time
            events_at_time = 0
            for i in range(count):
                if event_observed[event_idx + i]:
                    events_at_time += 1
            
            # Update survival probability if events occurred
            if events_at_time > 0:
                survival_prob *= (at_risk - events_at_time) / at_risk
            
            # Record time and survival probability
            survival_times.append(time)
            survival_probs.append(survival_prob)
            
            # Update at-risk count and event index
            at_risk -= count
            event_idx += count
        
        # Create survival function DataFrame
        self.survival_function_ = pd.DataFrame({
            'KM_estimate': survival_probs
        }, index=pd.Index(survival_times, name='timeline'))
        
        self._fitted = True
        return self
    
    def predict(self, time: float) -> float:
        """
        Predict survival probability at given time.
        
        Parameters
        ----------
        time : float
            Time at which to predict survival probability.
            
        Returns
        -------
        float
            Survival probability at given time, in range [0, 1].
        """
        if not self._fitted:
            raise ValueError("Model must be fitted before prediction.")
        
        if time < 0:
            return 1.0
        
        # Find the last time point <= given time
        times = self.survival_function_.index.values
        probs = self.survival_function_['KM_estimate'].values
        
        # If time is before first event, survival is 1.0
        if time < times[0]:
            return 1.0
        
        # Find the index of the last time <= given time
        idx = np.searchsorted(times, time, side='right') - 1
        
        # Clamp index to valid range
        idx = max(0, min(idx, len(probs) - 1))
        
        return float(probs[idx])