import pandas as pd

def load_waltons():
    data = {
        "T": [6, 13, 13, 18, 28, 31, 38, 38, 40, 44],
        "E": [1, 1, 1, 1, 1, 1, 1, 0, 1, 0],
        "group": ["control", "control", "control", "control", "control", "control", "control", "control", "control", "control"]
    }
    return pd.DataFrame(data)