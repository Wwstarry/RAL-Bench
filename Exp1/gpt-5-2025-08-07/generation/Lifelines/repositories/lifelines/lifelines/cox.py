import numpy as np
import pandas as pd


class CoxPHFitter:
    """
    A minimal Cox Proportional Hazards model fitter.

    Methods:
    - fit(df, duration_col, event_col)
    - predict_survival_function(row)

    Attributes:
    - summary: pandas DataFrame with columns "coef" and "se(coef)"
    """

    def __init__(self, penalizer: float = 1e-5, max_iter: int = 50, tol: float = 1e-7):
        self.penalizer = float(penalizer)
        self.max_iter = int(max_iter)
        self.tol = float(tol)

        self.summary = None
        self.params_ = None  # pandas Series of coefficients
        self._beta = None  # numpy array of coefficients
        self._columns = None  # column names of X used in fitting
        self._baseline_times = None  # event times used for baseline survival
        self._baseline_cumulative_hazard = None  # pandas Series
        self.baseline_survival_ = None  # pandas DataFrame with baseline survival

        self._duration_col = None
        self._event_col = None

    def _prepare_design(self, df, duration_col, event_col):
        # Drop rows with missing duration/event
        df = df.copy()
        if duration_col not in df.columns or event_col not in df.columns:
            raise ValueError("duration_col and event_col must be columns in the DataFrame.")

        df = df.dropna(subset=[duration_col, event_col])
        # Numeric covariates: take float/int; handle categorical via get_dummies(drop_first=True)
        covariate_cols = [c for c in df.columns if c not in (duration_col, event_col)]
        X_raw = df[covariate_cols]

        # Create dummies for non-numeric columns
        non_numeric = [c for c in X_raw.columns if not np.issubdtype(X_raw[c].dtype, np.number)]
        if len(non_numeric) > 0:
            X = pd.get_dummies(X_raw, columns=non_numeric, drop_first=True)
        else:
            X = X_raw.copy()

        # Ensure numeric dtype
        for c in X.columns:
            X[c] = pd.to_numeric(X[c], errors="coerce")

        # Drop rows with NA in covariates
        valid_rows = X.notna().all(axis=1)
        X = X.loc[valid_rows]
        durations = df.loc[valid_rows, duration_col].astype(float).values
        events = df.loc[valid_rows, event_col].astype(int).values
        events = (events != 0).astype(int)

        # Sort by durations ascending (stable)
        order = np.argsort(durations, kind="mergesort")
        durations = durations[order]
        events = events[order]
        X = X.iloc[order]

        return X, durations, events

    def fit(self, df, duration_col, event_col):
        """
        Fit the Cox model via Newton-Raphson on the Breslow partial likelihood.

        Parameters:
        - df: pandas DataFrame
        - duration_col: column name for durations
        - event_col: column name for event indicator (1 for event, 0 for censored)
        """
        X, T, E = self._prepare_design(df, duration_col, event_col)
        self._columns = list(X.columns)
        self._duration_col = duration_col
        self._event_col = event_col

        n, p = X.shape
        if p == 0:
            raise ValueError("No covariates to fit. Provide numeric or categorical covariates.")

        # Initialize coefficients
        beta = np.zeros(p, dtype=float)

        X_mat = X.values
        unique_times = np.unique(T)

        # Newton-Raphson iterations
        for iter_idx in range(self.max_iter):
            g = np.zeros(p, dtype=float)
            H = np.zeros((p, p), dtype=float)

            # Compute gradient and Hessian using Breslow approximation
            # For each unique time, risk set includes all individuals with T >= t
            for t in unique_times:
                d = int(np.sum((T == t) & (E == 1)))
                if d == 0:
                    continue
                risk_mask = T >= t
                XR = X_mat[risk_mask, :]
                r = np.exp(XR @ beta)  # shape (R,)
                S0 = np.sum(r)
                if S0 <= 0:
                    continue
                S1 = XR.T @ r  # shape (p,)
                S2 = XR.T @ (XR * r[:, None])  # shape (p,p)

                events_mask = (T == t) & (E == 1)
                XE = X_mat[events_mask, :]
                sum_x_events = XE.sum(axis=0)  # shape (p,)

                g += sum_x_events - d * (S1 / S0)
                H += -d * (S2 / S0 - np.outer(S1, S1) / (S0 ** 2))

            # Ridge penalization for stability: l(beta) - 0.5*penalizer*||beta||^2
            # Gradient penalty: -penalizer*beta
            # Hessian penalty: -penalizer*I
            g_pen = g - self.penalizer * beta
            H_pen = H - self.penalizer * np.eye(p)

            # Solve H_pen * delta = -g_pen
            # Add small damping if singular
            damping = 0.0
            max_damping = 1e3
            delta = None
            while True:
                try:
                    delta = np.linalg.solve(H_pen - damping * np.eye(p), -g_pen)
                    break
                except np.linalg.LinAlgError:
                    damping = (damping * 10.0 + 1e-6) if damping > 0 else 1e-6
                    if damping > max_damping:
                        # Fallback to pseudo-inverse
                        delta = -np.linalg.pinv(H_pen) @ g_pen
                        break

            beta_new = beta + delta

            if np.linalg.norm(delta) < self.tol:
                beta = beta_new
                break

            beta = beta_new

        self._beta = beta.copy()
        self.params_ = pd.Series(beta, index=self._columns)

        # Compute variance-covariance from observed information at solution
        g = np.zeros(p, dtype=float)
        H = np.zeros((p, p), dtype=float)
        for t in unique_times:
            d = int(np.sum((T == t) & (E == 1)))
            if d == 0:
                continue
            risk_mask = T >= t
            XR = X_mat[risk_mask, :]
            r = np.exp(XR @ beta)
            S0 = np.sum(r)
            if S0 <= 0:
                continue
            S1 = XR.T @ r
            S2 = XR.T @ (XR * r[:, None])
            H += -d * (S2 / S0 - np.outer(S1, S1) / (S0 ** 2))

        # Use unpenalized information for SEs; add tiny jitter to diagonal for invertibility
        info = -H + 1e-9 * np.eye(p)
        try:
            var = np.linalg.inv(info)
        except np.linalg.LinAlgError:
            var = np.linalg.pinv(info)
        se = np.sqrt(np.clip(np.diag(var), 0.0, np.inf))

        self.summary = pd.DataFrame(
            {"coef": self.params_.values, "se(coef)": se},
            index=self._columns,
        )

        # Compute baseline cumulative hazard (Breslow) and baseline survival
        baseline_times = []
        baseline_H = []
        H0 = 0.0
        for t in unique_times:
            d = int(np.sum((T == t) & (E == 1)))
            if d == 0:
                continue
            risk_mask = T >= t
            XR = X_mat[risk_mask, :]
            S0 = np.sum(np.exp(XR @ beta))
            if S0 <= 0:
                continue
            H0 += d / S0
            baseline_times.append(t)
            baseline_H.append(H0)

        self._baseline_times = np.array(baseline_times, dtype=float)
        self._baseline_cumulative_hazard = pd.Series(
            baseline_H, index=pd.Index(baseline_times, name="timeline")
        )
        baseline_surv_vals = np.exp(-np.array(baseline_H, dtype=float))
        self.baseline_survival_ = pd.DataFrame(
            {"baseline_survival": baseline_surv_vals},
            index=pd.Index(baseline_times, name="timeline"),
        )
        return self

    def _transform_row(self, row_df: pd.DataFrame) -> np.ndarray:
        """
        Transform a single-row DataFrame into the design vector aligned to training columns.
        Categorical columns are one-hot encoded with drop_first semantics; missing columns filled with 0.
        """
        if not isinstance(row_df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame with a single row.")
        if row_df.shape[0] != 1:
            # Allow more than one row but we'll use the first
            row_df = row_df.iloc[[0]]

        # Exclude duration/event columns if present
        row_df = row_df.drop(columns=[c for c in [self._duration_col, self._event_col] if c in row_df.columns], errors="ignore")

        # Encode categoricals similar to training
        non_numeric = [c for c in row_df.columns if not np.issubdtype(row_df[c].dtype, np.number)]
        if len(non_numeric) > 0:
            row_X = pd.get_dummies(row_df, columns=non_numeric, drop_first=True)
        else:
            row_X = row_df.copy()

        # Align to training columns
        # Drop any columns not seen during training, then reindex to training columns filling missing with 0.
        row_X = row_X[[c for c in row_X.columns if c in self._columns]]
        row_X = row_X.reindex(columns=self._columns, fill_value=0.0)

        # Ensure numeric dtype
        for c in row_X.columns:
            row_X[c] = pd.to_numeric(row_X[c], errors="coerce").fillna(0.0)

        return row_X.values[0, :]

    def predict_survival_function(self, row: pd.DataFrame) -> pd.DataFrame:
        """
        Predict survival function for a single individual described by a one-row DataFrame.

        Returns:
        - pandas DataFrame indexed by baseline event times with a single column of survival probabilities in [0,1].
        """
        if self._beta is None or self.baseline_survival_ is None or len(self.baseline_survival_) == 0:
            # Model not fitted or no events -> survival is 1 over empty index or default times
            idx = pd.Index([], name="timeline")
            return pd.DataFrame({"survival": []}, index=idx)

        x = self._transform_row(row)
        linpred = float(np.dot(x, self._beta))
        scale = np.exp(linpred)

        # S(t | x) = S0(t) ^ exp(x'beta) = exp(-H0(t) * exp(x'beta))
        # Use baseline cumulative hazard to be numerically stable
        H0 = self._baseline_cumulative_hazard.values
        times = self._baseline_cumulative_hazard.index
        surv = np.exp(-H0 * scale)
        surv = np.clip(surv, 0.0, 1.0)
        return pd.DataFrame({"survival": surv}, index=times)