import pandas as pd
import numpy as np
from scipy import linalg

class CoxPHFitter:
    """
    Class for fitting the Cox Proportional Hazards model.
    """
    def __init__(self, alpha=0.05, penalizer=0.0, l1_ratio=0.0):
        if penalizer != 0.0 or l1_ratio != 0.0:
            raise NotImplementedError("Penalizers are not implemented.")
        self.alpha = alpha
        self.hazards_ = None
        self.summary = None
        self.baseline_survival_ = None
        self._log_likelihood = None

    def _newton_rhapson(self, X, T, E, initial_beta, max_iter=50, tol=1e-9):
        n_features = X.shape[1]
        beta = np.array(initial_beta, dtype=float)

        for i in range(max_iter):
            risk_scores = np.exp(X @ beta)
            unique_event_times = np.unique(T[E == 1])
            
            gradient = np.zeros(n_features)
            hessian = np.zeros((n_features, n_features))
            log_likelihood = 0.0

            for t in sorted(unique_event_times):
                at_risk_mask = T >= t
                event_mask = (T == t) & (E == 1)
                d_i = np.sum(event_mask)
                
                if d_i == 0: continue

                risk_set_X = X[at_risk_mask]
                risk_set_scores = risk_scores[at_risk_mask]
                
                S0 = np.sum(risk_set_scores)
                if S0 == 0: continue

                S1 = np.sum(risk_set_X * risk_set_scores[:, np.newaxis], axis=0)
                S2 = np.sum(np.einsum('ij,ik->ijk', risk_set_X, risk_set_X) * risk_set_scores[:, np.newaxis, np.newaxis], axis=0)

                event_X_sum = np.sum(X[event_mask], axis=0)
                
                log_likelihood += np.sum(X[event_mask] @ beta) - d_i * np.log(S0)
                gradient += event_X_sum - d_i * (S1 / S0)
                hessian -= d_i * ((S2 / S0) - np.outer(S1, S1) / (S0 ** 2))

            try:
                inv_hessian = linalg.inv(-hessian)
                delta = inv_hessian @ gradient
            except (linalg.LinAlgError, ValueError):
                inv_hessian = linalg.pinv(-hessian)
                delta = inv_hessian @ gradient

            beta -= delta

            if np.linalg.norm(delta) < tol:
                self._log_likelihood = log_likelihood
                return beta, -hessian

        print(f"Warning: Convergence failed after {max_iter} iterations.")
        self._log_likelihood = log_likelihood
        return beta, -hessian

    def fit(self, df, duration_col, event_col, formula=None, show_progress=False, initial_point=None):
        """
        Fit the Cox Proportional Hazards model to a dataset.

        Parameters
        ----------
        df : pandas.DataFrame
            A DataFrame with covariates, duration, and event columns.
        duration_col : str
            The name of the column in df that contains the durations.
        event_col : str
            The name of the column in df that contains the event status.
        """
        self.duration_col = duration_col
        self.event_col = event_col
        
        T = df[duration_col].values
        E = df[event_col].values
        
        X_df = df.drop(columns=[duration_col, event_col])
        self.covariates_ = X_df.columns
        X = X_df.values
        
        n_features = X.shape[1]
        initial_beta = np.zeros(n_features) if initial_point is None else initial_point

        final_beta, final_hessian = self._newton_rhapson(X, T, E, initial_beta)
        
        self.hazards_ = pd.DataFrame(final_beta[np.newaxis, :], columns=self.covariates_, index=['coef']).T

        try:
            inv_hessian = linalg.inv(final_hessian)
            se = np.sqrt(np.diag(inv_hessian))
        except linalg.LinAlgError:
            se = np.full(n_features, np.nan)

        self.summary = self.hazards_.copy()
        self.summary['se(coef)'] = se
        
        self._X_fit = X
        self._T_fit = T
        self._E_fit = E
        self._final_beta = final_beta

        self._compute_baseline_survival()
        return self

    def _compute_baseline_survival(self):
        risk_scores = np.exp(self._X_fit @ self._final_beta)
        unique_event_times = sorted(np.unique(self._T_fit[self._E_fit == 1]))
        
        baseline_hazard = []
        for t in unique_event_times:
            events_at_t = ((self._T_fit == t) & (self._E_fit == 1)).sum()
            at_risk_mask = self._T_fit >= t
            risk_sum_at_t = np.sum(risk_scores[at_risk_mask])
            
            if risk_sum_at_t > 0:
                baseline_hazard.append({'time': t, 'hazard': events_at_t / risk_sum_at_t})

        if not baseline_hazard:
            self.baseline_survival_ = pd.DataFrame({'baseline survival': [1.0]}, index=[0])
            self.baseline_survival_.index.name = 'timeline'
            return

        bh_df = pd.DataFrame(baseline_hazard)
        bh_df['cumulative_hazard'] = bh_df['hazard'].cumsum()
        
        survival_df = pd.DataFrame({
            'time': bh_df['time'],
            'baseline survival': np.exp(-bh_df['cumulative_hazard'])
        })
        
        baseline_survival = pd.concat([
            pd.DataFrame({'time': [0], 'baseline survival': [1.0]}),
            survival_df
        ], ignore_index=True)
        
        self.baseline_survival_ = baseline_survival.set_index('time')
        self.baseline_survival_.index.name = 'timeline'

    def predict_survival_function(self, row):
        """
        Predict the survival function for a new subject.

        Parameters
        ----------
        row : pandas.DataFrame
            A single-row DataFrame with the same columns as the training data.

        Returns
        -------
        pandas.DataFrame
            The survival function, with time as index and probability as values.
        """
        if self.baseline_survival_ is None:
            raise RuntimeError("Must call `fit` first.")
        
        X_new = row[self.covariates_].values
        partial_hazard = np.exp(X_new @ self._final_beta)
        
        survival_function = self.baseline_survival_ ** partial_hazard[0]
        survival_function.columns = [0]
        
        return survival_function