from __future__ import annotations

import pandas as pd


def load_waltons() -> pd.DataFrame:
    """
    Return a small Waltons-like example dataset with columns:
      - T: duration
      - E: event indicator
      - group: categorical label

    Note: This is a lightweight embedded dataset sufficient for tests and examples.
    """
    data = {
        "T": [6, 7, 10, 15, 19, 25, 32, 34, 38, 46, 3, 5, 8, 12, 17, 23, 28, 30, 41, 50],
        "E": [1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1],
        "group": [
            "control",
            "control",
            "control",
            "control",
            "control",
            "control",
            "control",
            "control",
            "control",
            "control",
            "miR-137",
            "miR-137",
            "miR-137",
            "miR-137",
            "miR-137",
            "miR-137",
            "miR-137",
            "miR-137",
            "miR-137",
            "miR-137",
        ],
    }
    return pd.DataFrame(data)