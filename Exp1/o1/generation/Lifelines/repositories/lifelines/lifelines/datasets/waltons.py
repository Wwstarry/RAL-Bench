import pandas as pd

def load_waltons():
    """
    Return a pandas DataFrame with columns "T", "E", and "group",
    mimicking a small version of the Waltons dataset.
    """
    # A small mock dataset
    data = {
        "T": [1, 2, 3, 4, 5, 6, 7, 8],
        "E": [1, 0, 1, 1, 0, 1, 1, 0],
        "group": ["control", "control", "miR-137", "miR-137",
                  "control", "control", "miR-137", "miR-137"]
    }
    df = pd.DataFrame(data)
    return df