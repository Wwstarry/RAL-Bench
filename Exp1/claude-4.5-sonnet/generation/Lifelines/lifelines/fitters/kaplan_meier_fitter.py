import numpy as np
import pandas as pd


class KaplanMeierFitter:
    """Kaplan-Meier survival function estimator."""
    
    def __init__(self):
        self.survival_function_ = None
        self.event_table = None
        self.durations = None
        self.event_observed = None
        
    def fit(self, durations, event_observed=None, timeline=None, entry=None, 
            label=None, alpha=None, ci_labels=None, weights=None):
        """
        Fit the Kaplan-Meier estimate from a dataset.
        
        Parameters
        ----------
        durations : array-like
            The observed durations (time to event or censoring)
        event_observed : array-like, optional
            Boolean array indicating if the event was observed (True) or censored (False).
            If None, assumes all events were observed.
        timeline : array-like, optional
            Return the survival function at specific times
        entry : array-like, optional
            Entry times for left truncation
        label : str, optional
            Label for the survival function
        alpha : float, optional
            Confidence interval level
        ci_labels : tuple, optional
            Labels for confidence intervals
        weights : array-like, optional
            Sample weights
            
        Returns
        -------
        self
        """
        durations = np.asarray(durations)
        
        if event_observed is None:
            event_observed = np.ones_like(durations, dtype=bool)
        else:
            event_observed = np.asarray(event_observed, dtype=bool)
            
        if weights is None:
            weights = np.ones_like(durations)
        else:
            weights = np.asarray(weights)
        
        self.durations = durations
        self.event_observed = event_observed
        
        # Get unique event times
        unique_times = np.unique(durations)
        unique_times = np.sort(unique_times)
        
        # Build event table
        n_at_risk = []
        n_events = []
        
        for t in unique_times:
            # Number at risk at time t (all subjects with duration >= t)
            at_risk = np.sum(weights[durations >= t])
            n_at_risk.append(at_risk)
            
            # Number of events at time t
            events = np.sum(weights[(durations == t) & event_observed])
            n_events.append(events)
        
        n_at_risk = np.array(n_at_risk)
        n_events = np.array(n_events)
        
        # Calculate survival probabilities using Kaplan-Meier formula
        # S(t) = prod_{t_i <= t} (1 - d_i / n_i)
        # where d_i is number of events at t_i and n_i is number at risk
        
        survival_probs = []
        cumulative_survival = 1.0
        
        for i in range(len(unique_times)):
            if n_at_risk[i] > 0:
                cumulative_survival *= (1 - n_events[i] / n_at_risk[i])
            survival_probs.append(cumulative_survival)
        
        # Create survival function DataFrame
        if label is None:
            label = 'KM_estimate'
            
        self.survival_function_ = pd.DataFrame(
            {label: survival_probs},
            index=unique_times
        )
        self.survival_function_.index.name = 'timeline'
        
        # Store event table for reference
        self.event_table = pd.DataFrame({
            'at_risk': n_at_risk,
            'observed': n_events
        }, index=unique_times)
        
        return self
    
    def predict(self, times):
        """
        Predict survival probability at given time(s).
        
        Parameters
        ----------
        times : float or array-like
            Time(s) at which to predict survival probability
            
        Returns
        -------
        float or pd.Series
            Survival probability at the given time(s)
        """
        if self.survival_function_ is None:
            raise ValueError("Must call fit() before predict()")
        
        is_scalar = np.isscalar(times)
        if is_scalar:
            times = [times]
        
        times = np.asarray(times)
        predictions = []
        
        sf_times = self.survival_function_.index.values
        sf_values = self.survival_function_.iloc[:, 0].values
        
        for t in times:
            # Find the survival probability at time t
            # Use step function: S(t) = S(t_i) for t_i <= t < t_{i+1}
            if t < sf_times[0]:
                # Before first event time, survival is 1.0
                predictions.append(1.0)
            elif t >= sf_times[-1]:
                # At or after last event time, use last value
                predictions.append(sf_values[-1])
            else:
                # Find the largest time <= t
                idx = np.searchsorted(sf_times, t, side='right') - 1
                predictions.append(sf_values[idx])
        
        if is_scalar:
            return predictions[0]
        else:
            return pd.Series(predictions, index=times)