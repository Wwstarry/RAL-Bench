from __future__ import annotations

import os
import pandas as pd


def load_waltons() -> pd.DataFrame:
    """
    Load the Waltons example dataset.

    Returns a DataFrame with at least:
    - T: duration
    - E: event observed (1) or censored (0)
    - group: categorical label
    """
    here = os.path.dirname(__file__)
    path = os.path.join(here, "waltons.csv")
    df = pd.read_csv(path)
    # basic normalization
    if "T" not in df.columns or "E" not in df.columns or "group" not in df.columns:
        raise ValueError("waltons dataset is missing required columns.")
    return df


__all__ = ["load_waltons"]