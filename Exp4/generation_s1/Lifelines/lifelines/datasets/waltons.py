from __future__ import annotations

import pandas as pd


def load_waltons() -> pd.DataFrame:
    """
    A small built-in Waltons-like dataset.

    Returns a DataFrame with columns:
      - T: duration
      - E: event indicator (1=event observed, 0=censored)
      - group: categorical group label
    """
    data = [
        {"T": 6, "E": 1, "group": "control"},
        {"T": 7, "E": 1, "group": "control"},
        {"T": 10, "E": 0, "group": "control"},
        {"T": 12, "E": 1, "group": "control"},
        {"T": 15, "E": 0, "group": "control"},
        {"T": 18, "E": 1, "group": "control"},
        {"T": 3, "E": 1, "group": "miR"},
        {"T": 4, "E": 1, "group": "miR"},
        {"T": 5, "E": 1, "group": "miR"},
        {"T": 8, "E": 0, "group": "miR"},
        {"T": 9, "E": 1, "group": "miR"},
        {"T": 11, "E": 0, "group": "miR"},
    ]
    df = pd.DataFrame(data)
    df["T"] = pd.to_numeric(df["T"], errors="raise")
    df["E"] = pd.to_numeric(df["E"], errors="raise").astype(int)
    df["group"] = df["group"].astype("object")
    return df