import numpy as np
import pandas as pd
from typing import Optional, Union, List


class KaplanMeierFitter:
    """
    Kaplan-Meier estimator for univariate survival analysis.
    """
    
    def __init__(self):
        self.survival_function_ = None
        self.timeline_ = None
        self._fitted = False
    
    def fit(
        self,
        durations: Union[np.ndarray, pd.Series, List],
        event_observed: Optional[Union[np.ndarray, pd.Series, List]] = None,
        timeline: Optional[Union[np.ndarray, pd.Series, List]] = None,
        entry: Optional[Union[np.ndarray, pd.Series, List]] = None,
        label: Optional[str] = None,
        alpha: Optional[float] = None,
        ci_labels: Optional[List[str]] = None,
        weights: Optional[Union[np.ndarray, pd.Series, List]] = None,
        **kwargs
    ) -> "KaplanMeierFitter":
        """
        Fit the Kaplan-Meier estimator to survival data.
        
        Parameters
        ----------
        durations : array-like
            Length n, duration (relative to subject's birth) the subject was alive for.
        event_observed : array-like, optional
            Length n, True if the death was observed, False if the event was lost.
            Defaults to all True if event_observed==None.
        timeline : array-like, optional
            Specify the timeline for the survival function.
        entry : array-like, optional
            Relative time when a subject entered the study.
        label : str, optional
            A string to name the column of the estimate.
        alpha : float, optional
            The alpha value in the confidence intervals.
        ci_labels : list, optional
            Labels for the confidence interval columns.
        weights : array-like, optional
            Optional weights for each observation.
        
        Returns
        -------
        self : KaplanMeierFitter
        """
        # Convert inputs to numpy arrays
        durations = np.asarray(durations)
        
        if event_observed is None:
            event_observed = np.ones_like(durations, dtype=bool)
        else:
            event_observed = np.asarray(event_observed)
        
        if weights is None:
            weights = np.ones_like(durations)
        else:
            weights = np.asarray(weights)
        
        # Sort by duration
        sort_idx = np.argsort(durations)
        durations = durations[sort_idx]
        event_observed = event_observed[sort_idx]
        weights = weights[sort_idx]
        
        # Calculate Kaplan-Meier estimate
        unique_times = np.unique(durations)
        at_risk = np.zeros_like(unique_times, dtype=float)
        events = np.zeros_like(unique_times, dtype=float)
        
        # Count at risk and events at each unique time
        for i, t in enumerate(unique_times):
            at_risk[i] = np.sum(weights[durations >= t])
            events[i] = np.sum(weights[(durations == t) & event_observed])
        
        # Calculate survival probabilities
        survival_prob = np.ones_like(unique_times, dtype=float)
        for i in range(1, len(unique_times)):
            if at_risk[i] > 0:
                survival_prob[i] = survival_prob[i-1] * (1 - events[i] / at_risk[i])
        
        # Create survival function DataFrame
        self.survival_function_ = pd.DataFrame({
            'KM_estimate': survival_prob
        }, index=pd.Index(unique_times, name='timeline'))
        
        self.timeline_ = unique_times
        self._fitted = True
        
        return self
    
    def predict(self, time: Union[float, np.ndarray, pd.Series]) -> Union[float, np.ndarray]:
        """
        Predict survival probability at given time(s).
        
        Parameters
        ----------
        time : float or array-like
            Time(s) at which to predict survival probability.
        
        Returns
        -------
        float or array
            Survival probability at given time(s).
        """
        if not self._fitted:
            raise ValueError("Model must be fitted before prediction.")
        
        if self.survival_function_ is None or len(self.survival_function_) == 0:
            return np.array([1.0]) if np.isscalar(time) else np.ones_like(time)
        
        # Handle scalar input
        if np.isscalar(time):
            times = np.array([time])
            scalar_input = True
        else:
            times = np.asarray(time)
            scalar_input = False
        
        # Find survival probabilities
        results = []
        for t in times:
            # Find the last time point <= t
            mask = self.timeline_ <= t
            if np.any(mask):
                # Get the last available survival probability
                idx = np.where(mask)[0][-1]
                prob = self.survival_function_.iloc[idx, 0]
            else:
                # If t is before first event, survival is 1
                prob = 1.0
            results.append(max(0.0, min(1.0, prob)))  # Clamp to [0, 1]
        
        results = np.array(results)
        return results[0] if scalar_input else results
    
    def plot_survival_function(self, **kwargs):
        """
        Plot the survival function.
        
        Note: This is a stub for API compatibility.
        """
        raise NotImplementedError("Plotting not implemented in this version.")