import pandas as pd
import numpy as np

class KaplanMeierFitter:
    """
    Class for fitting the Kaplan-Meier estimate for the survival function.
    """
    def __init__(self, alpha=0.05, label='KM_estimate'):
        self.alpha = alpha
        self.label = label
        self.survival_function_ = None
        self.timeline = None

    def fit(self, durations, event_observed, timeline=None, entry=None, label=None, alpha=None, ci_labels=None, weights=None):
        """
        Fit the model to the data.

        Parameters
        ----------
        durations : array-like
            An array or pd.Series of length n of times.
        event_observed : array-like
            An array or pd.Series of length n -- 1 if the event was observed, 0 if the event was censored.
        """
        if label:
            self.label = label

        df = pd.DataFrame({'T': durations, 'E': event_observed})
        
        unique_event_times = sorted(df.loc[df['E'] == 1, 'T'].unique())

        at_risk_count = len(df)
        survival_prob = 1.0
        
        results = [{'time': 0, 'survival': 1.0}]

        for t in unique_event_times:
            at_risk_count_t = (df['T'] >= t).sum()
            events_at_t = ((df['T'] == t) & (df['E'] == 1)).sum()
            
            if at_risk_count_t > 0:
                survival_prob *= (1 - events_at_t / at_risk_count_t)
            
            results.append({
                'time': t,
                'survival': survival_prob
            })

        sf = pd.DataFrame(results)
        sf = sf.set_index('time')
        self.survival_function_ = sf[['survival']].rename(columns={'survival': self.label})
        self.survival_function_.index.name = 'timeline'
        
        self.timeline = self.survival_function_.index.values

        return self

    def predict(self, time):
        """
        Predict the survival probability at a given time.

        Parameters
        ----------
        time : float or array-like
            A float or array of times to predict the survival probability at.

        Returns
        -------
        float or numpy.ndarray
            The survival probability. A float is returned if the input is a float.
        """
        if self.survival_function_ is None:
            raise RuntimeError("Must call `fit` first.")
        
        times = np.atleast_1d(time)
        
        sf_df = self.survival_function_.reset_index()
        predict_df = pd.DataFrame({'timeline': times})
        
        merged = pd.merge_asof(predict_df, sf_df, on='timeline')
        merged[self.label] = merged[self.label].fillna(1.0)
        
        predictions = merged[self.label].values
        
        if isinstance(time, (int, float)):
            return predictions[0]
        
        return predictions