import pandas as pd
from io import StringIO

def load_waltons():
    """
    Returns the Waltons dataset as a pandas DataFrame with columns:
    - "T": durations
    - "E": event indicator
    - "group": group label
    """
    # Data from lifelines.datasets.load_waltons
    csv = """T,E,group
6,1,control
6,1,control
6,1,control
7,1,control
10,1,control
13,1,control
16,1,control
22,1,control
23,1,control
6,1,miR-137
6,1,miR-137
7,1,miR-137
9,1,miR-137
13,1,miR-137
15,1,miR-137
17,1,miR-137
19,1,miR-137
25,1,miR-137
32,0,miR-137
"""
    df = pd.read_csv(StringIO(csv))
    return df