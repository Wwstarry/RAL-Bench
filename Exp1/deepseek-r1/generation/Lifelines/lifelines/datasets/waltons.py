"""
Waltons dataset for survival analysis examples.
"""

import pandas as pd
import numpy as np


def load_waltons() -> pd.DataFrame:
    """
    Load the Waltons dataset.
    
    Returns
    -------
    pandas.DataFrame
        DataFrame with columns:
        - T: duration/event time
        - E: event indicator (1 if event, 0 if censored)
        - group: categorical group label
    """
    # Generate synthetic data similar to Waltons dataset
    np.random.seed(42)
    
    n_samples = 100
    
    # Generate two groups with different survival patterns
    group_a_size = 50
    group_b_size = 50
    
    # Group A: shorter survival times
    group_a_times = np.random.exponential(scale=10, size=group_a_size)
    group_a_events = np.random.binomial(1, 0.9, size=group_a_size)
    
    # Group B: longer survival times
    group_b_times = np.random.exponential(scale=20, size=group_b_size)
    group_b_events = np.random.binomial(1, 0.8, size=group_b_size)
    
    # Combine groups
    times = np.concatenate([group_a_times, group_b_times])
    events = np.concatenate([group_a_events, group_b_events])
    groups = np.array(['control'] * group_a_size + ['miR-137'] * group_b_size)
    
    # Create DataFrame
    df = pd.DataFrame({
        'T': times,
        'E': events,
        'group': groups
    })
    
    return df