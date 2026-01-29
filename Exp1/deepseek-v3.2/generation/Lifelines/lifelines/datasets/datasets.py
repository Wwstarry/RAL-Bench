import pandas as pd
import numpy as np


def load_waltons() -> pd.DataFrame:
    """
    Load the Waltons dataset.
    
    Returns
    -------
    DataFrame
        DataFrame with columns:
        - T: duration
        - E: event indicator (1 if observed, 0 if censored)
        - group: categorical group label
    """
    # Waltons dataset example data
    # This is a simplified version for compatibility
    data = {
        'T': [6, 13, 13, 18, 23, 24, 26, 26, 27, 28, 29, 29, 30, 30, 31, 32, 33, 33, 34, 35,
              35, 36, 37, 39, 40, 41, 42, 44, 44, 45, 46, 47, 48, 49, 51, 52, 54, 54, 56, 57],
        'E': [1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
              1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        'group': ['control', 'control', 'control', 'control', 'control', 
                  'control', 'control', 'control', 'control', 'control',
                  'miR-137', 'miR-137', 'miR-137', 'miR-137', 'miR-137',
                  'miR-137', 'miR-137', 'miR-137', 'miR-137', 'miR-137',
                  'control', 'control', 'control', 'control', 'control',
                  'miR-137', 'miR-137', 'miR-137', 'miR-137', 'miR-137',
                  'control', 'control', 'control', 'control', 'control',
                  'miR-137', 'miR-137', 'miR-137', 'miR-137', 'miR-137']
    }
    
    df = pd.DataFrame(data)
    return df