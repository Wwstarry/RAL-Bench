import pandas as pd

def load_waltons():
    # Waltons dataset from lifelines example
    # Columns: T (duration), E (event observed), group (treatment group)
    data = {
        "T": [6, 6, 6, 7, 10, 10, 11, 11, 11, 11,
              12, 12, 12, 13, 13, 13, 13, 14, 14, 14,
              15, 15, 15, 16, 16, 17, 17, 17, 18, 18,
              19, 19, 20, 21, 22, 23, 24, 25, 26, 27,
              28, 29, 30, 31, 32, 33, 34, 35, 36, 37],
        "E": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
              1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
              1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
              1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
              1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "group": ["control", "control", "control", "control", "control", "control", "control", "control", "control", "control",
                  "control", "control", "control", "control", "control", "control", "control", "control", "control", "control",
                  "control", "control", "control", "control", "control", "control", "control", "control", "control", "control",
                  "treatment", "treatment", "treatment", "treatment", "treatment", "treatment", "treatment", "treatment", "treatment", "treatment",
                  "treatment", "treatment", "treatment", "treatment", "treatment", "treatment", "treatment", "treatment", "treatment", "treatment"]
    }
    df = pd.DataFrame(data)
    return df