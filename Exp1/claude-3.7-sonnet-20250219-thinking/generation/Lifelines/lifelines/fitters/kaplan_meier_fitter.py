import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

class KaplanMeierFitter:
    """
    Class for fitting the Kaplan-Meier estimate for the survival function.
    
    Parameters:
        None
    """
    
    def __init__(self):
        self.survival_function_ = None
        self.median_ = None
        self.durations = None
        self.event_observed = None
        self.timeline = None
        self.entry = None
        self.event_table = None
        self.predicted_median_ = None
        self._label = 'KM_estimate'
        
    def fit(self, durations, event_observed=None, timeline=None, entry=None, label=None, alpha=None, ci_labels=None, weights=None):
        """
        Fit the Kaplan-Meier estimator to the data.
        
        Parameters:
            durations: array or pd.Series
                duration subject was observed for
            event_observed: array or pd.Series, optional
                boolean or binary array indicating whether the death was observed (True) or if the subject was right-censored (False)
            timeline: array, optional
                return the best estimate at the values in this array
            entry: array or pd.Series, optional
                relative time when a subject entered the study
            label: string, optional
                a string to name the fitted model
            alpha: float, optional
                the alpha value in the confidence intervals
            ci_labels: tuple, optional
                add custom labels to the confidence intervals
            weights: array, optional
                optional weights for each observation
                
        Returns:
            self
        """
        if event_observed is None:
            event_observed = np.ones_like(durations, dtype=bool)
            
        self.durations = np.asarray(durations, dtype=float)
        self.event_observed = np.asarray(event_observed, dtype=float).astype(bool)
        
        if label is not None:
            self._label = label
            
        # Sort data by durations
        ix = np.argsort(self.durations)
        self.durations = self.durations[ix]
        self.event_observed = self.event_observed[ix]
        
        # Compute the survival function
        unique_durations = np.unique(self.durations)
        observed_deaths = np.zeros(unique_durations.shape[0])
        censored = np.zeros(unique_durations.shape[0])
        at_risk = np.zeros(unique_durations.shape[0])
        
        for i, t in enumerate(unique_durations):
            mask = self.durations == t
            at_risk[i] = sum(self.durations >= t)
            observed_deaths[i] = sum(mask & self.event_observed)
            censored[i] = sum(mask & ~self.event_observed)
        
        survival_function = np.cumprod(1 - observed_deaths / at_risk)
        
        self.timeline = unique_durations
        self.survival_function_ = pd.DataFrame(
            {
                self._label: survival_function
            },
            index=unique_durations
        )
        
        # Find the median if it exists
        if min(survival_function) < 0.5:
            self.median_ = unique_durations[survival_function <= 0.5][0]
        
        self._survival_function_interpolator = interp1d(
            self.timeline,
            self.survival_function_.values.flatten(),
            bounds_error=False,
            fill_value=(1.0, 0.0)
        )
        
        return self
    
    def predict(self, times):
        """
        Return the estimated survival probability at the given time point(s).
        
        Parameters:
            times: scalar, or array
                time(s) to predict survival at
        
        Returns:
            scalar, or array
                predicted survival probability
        """
        if not hasattr(self, '_survival_function_interpolator'):
            raise ValueError("You must call `fit` first before calling `predict`.")
            
        if np.isscalar(times):
            return float(self._survival_function_interpolator(times))
        else:
            return np.asarray([float(self._survival_function_interpolator(t)) for t in times])
            
    def plot(self, **kwargs):
        """Placeholder for plot method to maintain API compatibility"""
        pass