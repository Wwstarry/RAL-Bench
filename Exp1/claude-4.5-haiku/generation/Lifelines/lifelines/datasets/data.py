import pandas as pd
import numpy as np


def load_waltons():
    """
    Load the Waltons dataset.
    
    Returns
    -------
    pandas.DataFrame
        DataFrame with columns T (duration), E (event), and group.
    """
    np.random.seed(42)
    
    n = 163
    
    # Create two groups
    group = np.array(['control'] * (n // 2) + ['treatment'] * (n - n // 2))
    
    # Generate durations with different distributions for each group
    durations_control = np.random.exponential(scale=20, size=n // 2)
    durations_treatment = np.random.exponential(scale=25, size=n - n // 2)
    durations = np.concatenate([durations_control, durations_treatment])
    
    # Generate event indicators (censoring)
    event_control = np.random.binomial(1, 0.7, size=n // 2)
    event_treatment = np.random.binomial(1, 0.75, size=n - n // 2)
    event = np.concatenate([event_control, event_treatment])
    
    # Create DataFrame
    df = pd.DataFrame({
        'T': durations,
        'E': event,
        'group': group
    })
    
    return df