import pandas as pd
import io

WALTONS_DATA = """T,E,group
6,1,miR-137
13,1,miR-137
13,1,miR-137
13,1,miR-137
19,1,miR-137
19,1,miR-137
19,1,miR-137
26,1,miR-137
26,1,miR-137
26,1,miR-137
26,1,miR-137
26,1,miR-137
33,1,miR-137
33,1,miR-137
40,1,miR-137
40,1,miR-137
40,1,miR-137
40,1,miR-137
6,1,control
9,1,control
9,1,control
13,1,control
13,1,control
19,1,control
19,1,control
19,1,control
19,1,control
26,1,control
26,1,control
26,1,control
26,1,control
33,1,control
33,1,control
33,1,control
33,1,control
40,1,control
40,1,control
40,1,control
40,1,control
"""

def load_waltons():
    """
    Loads the Waltons dataset from a built-in CSV.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with columns 'T', 'E', and 'group'.
    """
    return pd.read_csv(io.StringIO(WALTONS_DATA))