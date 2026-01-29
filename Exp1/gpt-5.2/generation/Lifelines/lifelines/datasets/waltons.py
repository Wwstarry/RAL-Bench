from __future__ import annotations

import pandas as pd


def load_waltons() -> pd.DataFrame:
    """
    Return an example dataset similar in spirit to lifelines' waltons dataset.

    Columns:
      - T: duration
      - E: event observed indicator (1=event, 0=censored)
      - group: categorical group label
    """
    # A small, deterministic dataset sufficient for unit tests that require
    # presence and basic behavior. It is not intended to exactly match the
    # reference dataset values.
    data = {
        "T": [
            6, 7, 10, 15, 19, 25, 32, 34, 36, 38, 42, 45, 48, 52, 56,
            8, 12, 14, 18, 22, 27, 30, 33, 37, 41, 44, 49, 51, 55, 60
        ],
        "E": [
            1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1,
            1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0
        ],
        "group": (["control"] * 15) + (["miR-137"] * 15),
    }
    df = pd.DataFrame(data)
    df["group"] = df["group"].astype("category")
    return df