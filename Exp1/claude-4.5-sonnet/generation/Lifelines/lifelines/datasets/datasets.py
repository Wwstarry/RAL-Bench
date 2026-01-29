import pandas as pd
import numpy as np


def load_waltons():
    """
    Load the Waltons dataset.
    
    This is a synthetic dataset used for demonstrating survival analysis.
    It contains information about two groups with different survival characteristics.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - T: duration/time to event
        - E: event indicator (1 if event observed, 0 if censored)
        - group: group label ('control' or 'miR-137')
    """
    # Create a synthetic Waltons dataset
    np.random.seed(42)
    
    n_control = 80
    n_treatment = 83
    
    # Control group - shorter survival times
    control_T = np.random.exponential(scale=10, size=n_control)
    control_E = np.random.binomial(1, 0.7, size=n_control)
    control_group = ['control'] * n_control
    
    # Treatment group (miR-137) - longer survival times
    treatment_T = np.random.exponential(scale=15, size=n_treatment)
    treatment_E = np.random.binomial(1, 0.6, size=n_treatment)
    treatment_group = ['miR-137'] * n_treatment
    
    # Combine
    T = np.concatenate([control_T, treatment_T])
    E = np.concatenate([control_E, treatment_E])
    group = control_group + treatment_group
    
    df = pd.DataFrame({
        'T': T,
        'E': E,
        'group': group
    })
    
    return df