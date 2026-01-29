import io
import pandas as pd


def load_waltons():
    """
    Load a small Waltons-like example dataset.

    Returns a pandas DataFrame with columns:
    - "T": durations
    - "E": event indicator (1=event, 0=censored)
    - "group": categorical group label
    """
    # Minimal embedded CSV for portability. This is not the original dataset,
    # but matches the expected schema and is suitable for tests.
    csv_data = """T,E,group
6,1,control
7,1,control
10,1,control
15,1,control
19,1,control
20,1,control
24,1,control
32,1,control
36,0,control
40,1,control
45,1,control
50,0,control
55,1,control
60,1,control
63,1,control
66,0,control
70,1,control
75,1,control
80,0,control
90,1,control
5,1,experimental
8,1,experimental
12,1,experimental
14,1,experimental
18,1,experimental
22,1,experimental
28,1,experimental
30,1,experimental
35,0,experimental
38,1,experimental
42,1,experimental
48,0,experimental
52,1,experimental
58,1,experimental
62,1,experimental
65,0,experimental
68,1,experimental
72,1,experimental
78,0,experimental
85,1,experimental
3,1,control
4,0,control
9,1,control
11,1,control
13,0,control
16,1,control
21,1,control
25,1,control
27,0,control
33,1,control
37,1,control
41,0,control
47,1,control
51,1,control
57,1,control
61,0,control
67,1,control
73,1,control
79,0,control
88,1,control
2,1,experimental
6,1,experimental
9,1,experimental
11,1,experimental
13,0,experimental
17,1,experimental
23,1,experimental
26,1,experimental
29,0,experimental
34,1,experimental
39,1,experimental
43,0,experimental
49,1,experimental
53,1,experimental
59,1,experimental
64,0,experimental
69,1,experimental
74,1,experimental
81,0,experimental
89,1,experimental
"""
    return pd.read_csv(io.StringIO(csv_data))