import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.linalg import inv


class CoxPHFitter:
    """Cox Proportional Hazards regression model."""
    
    def __init__(self, alpha=0.05, penalizer=0.0):
        self.alpha = alpha
        self.penalizer = penalizer
        self.params_ = None
        self.variance_matrix_ = None
        self.summary = None
        self._baseline_hazard = None
        self._baseline_cumulative_hazard = None
        self._baseline_survival = None
        self.duration_col = None
        self.event_col = None
        
    def fit(self, df, duration_col, event_col, show_progress=False, 
            timeline=None, weights_col=None, robust=False, strata=None,
            initial_point=None, formula=None):
        """
        Fit the Cox Proportional Hazards model.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the data
        duration_col : str
            Column name for durations
        event_col : str
            Column name for event indicator
        show_progress : bool, optional
            Whether to show progress
        timeline : array-like, optional
            Timeline for baseline hazard
        weights_col : str, optional
            Column name for weights
        robust : bool, optional
            Use robust variance estimation
        strata : list, optional
            Stratification columns
        initial_point : array-like, optional
            Initial parameter values
        formula : str, optional
            R-style formula
            
        Returns
        -------
        self
        """
        self.duration_col = duration_col
        self.event_col = event_col
        
        # Extract durations and events
        T = df[duration_col].values
        E = df[event_col].values.astype(bool)
        
        # Get covariate columns (exclude duration and event columns)
        covariate_cols = [col for col in df.columns 
                         if col not in [duration_col, event_col]]
        
        if weights_col and weights_col in covariate_cols:
            covariate_cols.remove(weights_col)
        
        X = df[covariate_cols].values
        self.covariate_cols = covariate_cols
        
        # Sort by duration
        sort_idx = np.argsort(T)
        T = T[sort_idx]
        E = E[sort_idx]
        X = X[sort_idx]
        
        n_samples, n_features = X.shape
        
        # Initialize parameters
        if initial_point is not None:
            beta = np.array(initial_point)
        else:
            beta = np.zeros(n_features)
        
        # Define negative log partial likelihood
        def neg_log_likelihood(beta):
            # Compute risk scores
            risk_scores = np.exp(X @ beta)
            
            # Compute log partial likelihood
            log_lik = 0.0
            for i in range(n_samples):
                if E[i]:
                    # Risk set: all subjects with T >= T[i]
                    at_risk = T >= T[i]
                    risk_sum = np.sum(risk_scores[at_risk])
                    if risk_sum > 0:
                        log_lik += X[i] @ beta - np.log(risk_sum)
            
            # Add L2 penalty
            penalty = 0.5 * self.penalizer * np.sum(beta ** 2)
            
            return -(log_lik - penalty)
        
        # Define gradient
        def gradient(beta):
            risk_scores = np.exp(X @ beta)
            grad = np.zeros(n_features)
            
            for i in range(n_samples):
                if E[i]:
                    at_risk = T >= T[i]
                    risk_sum = np.sum(risk_scores[at_risk])
                    if risk_sum > 0:
                        weighted_mean = np.sum(
                            X[at_risk] * risk_scores[at_risk, np.newaxis], 
                            axis=0
                        ) / risk_sum
                        grad += X[i] - weighted_mean
            
            # Add penalty gradient
            grad -= self.penalizer * beta
            
            return -grad
        
        # Optimize
        result = minimize(
            neg_log_likelihood,
            beta,
            method='BFGS',
            jac=gradient,
            options={'disp': False}
        )
        
        self.params_ = pd.Series(result.x, index=covariate_cols)
        
        # Compute variance matrix (inverse of observed information matrix)
        # Using numerical approximation
        eps = 1e-5
        hessian = np.zeros((n_features, n_features))
        
        for i in range(n_features):
            for j in range(n_features):
                beta_pp = result.x.copy()
                beta_pm = result.x.copy()
                beta_mp = result.x.copy()
                beta_mm = result.x.copy()
                
                beta_pp[i] += eps
                beta_pp[j] += eps
                
                beta_pm[i] += eps
                beta_pm[j] -= eps
                
                beta_mp[i] -= eps
                beta_mp[j] += eps
                
                beta_mm[i] -= eps
                beta_mm[j] -= eps
                
                hessian[i, j] = (
                    neg_log_likelihood(beta_pp) 
                    - neg_log_likelihood(beta_pm)
                    - neg_log_likelihood(beta_mp)
                    + neg_log_likelihood(beta_mm)
                ) / (4 * eps * eps)
        
        try:
            self.variance_matrix_ = inv(hessian)
        except:
            # If inversion fails, use diagonal approximation
            self.variance_matrix_ = np.diag(1.0 / (np.diag(hessian) + 1e-10))
        
        # Compute standard errors
        se = np.sqrt(np.diag(self.variance_matrix_))
        
        # Create summary DataFrame
        self.summary = pd.DataFrame({
            'coef': self.params_.values,
            'se(coef)': se,
            'z': self.params_.values / se,
            'p': 2 * (1 - self._normal_cdf(np.abs(self.params_.values / se)))
        }, index=covariate_cols)
        
        # Compute baseline hazard using Breslow estimator
        self._compute_baseline_hazard(T, E, X, result.x)
        
        return self
    
    def _normal_cdf(self, x):
        """Cumulative distribution function for standard normal."""
        return 0.5 * (1 + np.vectorize(self._erf)(x / np.sqrt(2)))
    
    def _erf(self, x):
        """Error function approximation."""
        # Abramowitz and Stegun approximation
        a1 =  0.254829592
        a2 = -0.284496736
        a3 =  1.421413741
        a4 = -1.453152027
        a5 =  1.061405429
        p  =  0.3275911
        
        sign = 1 if x >= 0 else -1
        x = abs(x)
        
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-x * x)
        
        return sign * y
    
    def _compute_baseline_hazard(self, T, E, X, beta):
        """Compute baseline hazard using Breslow estimator."""
        risk_scores = np.exp(X @ beta)
        
        # Get unique event times
        event_times = np.unique(T[E])
        
        baseline_hazard = []
        for t in event_times:
            # Number of events at time t
            d_t = np.sum(E & (T == t))
            
            # Risk set at time t
            at_risk = T >= t
            risk_sum = np.sum(risk_scores[at_risk])
            
            if risk_sum > 0:
                h_t = d_t / risk_sum
            else:
                h_t = 0.0
            
            baseline_hazard.append(h_t)
        
        self._baseline_hazard = pd.DataFrame({
            'baseline hazard': baseline_hazard
        }, index=event_times)
        
        # Compute cumulative baseline hazard
        cumulative_hazard = np.cumsum(baseline_hazard)
        self._baseline_cumulative_hazard = pd.DataFrame({
            'baseline cumulative hazard': cumulative_hazard
        }, index=event_times)
        
        # Compute baseline survival
        baseline_survival = np.exp(-cumulative_hazard)
        self._baseline_survival = pd.DataFrame({
            'baseline survival': baseline_survival
        }, index=event_times)
    
    def predict_survival_function(self, X, times=None):
        """
        Predict survival function for given covariates.
        
        Parameters
        ----------
        X : pd.DataFrame
            DataFrame with one or more rows of covariates
        times : array-like, optional
            Times at which to predict survival
            
        Returns
        -------
        pd.DataFrame
            Survival function predictions
        """
        if self.params_ is None:
            raise ValueError("Must call fit() before predict_survival_function()")
        
        # Extract covariate values
        X_values = X[self.covariate_cols].values
        
        # Compute risk scores
        risk_scores = np.exp(X_values @ self.params_.values)
        
        # Get baseline survival times and values
        baseline_times = self._baseline_survival.index.values
        baseline_surv = self._baseline_survival.iloc[:, 0].values
        
        # For each row in X, compute survival function
        if len(X) == 1:
            # Single row case
            risk_score = risk_scores[0]
            survival = baseline_surv ** risk_score
            
            result = pd.DataFrame(
                survival,
                index=baseline_times,
                columns=[0]
            )
            result.index.name = 'timeline'
            return result
        else:
            # Multiple rows
            results = {}
            for i in range(len(X)):
                risk_score = risk_scores[i]
                survival = baseline_surv ** risk_score
                results[i] = survival
            
            result = pd.DataFrame(results, index=baseline_times)
            result.index.name = 'timeline'
            return result
    
    def predict_partial_hazard(self, X):
        """
        Predict partial hazard for given covariates.
        
        Parameters
        ----------
        X : pd.DataFrame
            DataFrame with covariates
            
        Returns
        -------
        pd.Series
            Partial hazard predictions
        """
        if self.params_ is None:
            raise ValueError("Must call fit() before predict_partial_hazard()")
        
        X_values = X[self.covariate_cols].values
        partial_hazard = np.exp(X_values @ self.params_.values)
        
        return pd.Series(partial_hazard, index=X.index)