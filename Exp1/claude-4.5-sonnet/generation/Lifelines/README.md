# Lifelines

A pure Python survival analysis library providing API-compatible implementations of core survival analysis methods.

## Features

- **Kaplan-Meier Fitter**: Non-parametric survival function estimation
- **Cox Proportional Hazards**: Semi-parametric regression for survival data
- **Example Datasets**: Built-in datasets for learning and testing

## Installation

```bash
pip install -e .
```

## Quick Start

```python
import lifelines
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.datasets import load_waltons

# Load example data
df = load_waltons()

# Kaplan-Meier estimation
kmf = KaplanMeierFitter()
kmf.fit(df['T'], df['E'])
print(kmf.survival_function_)

# Cox Proportional Hazards
cph = CoxPHFitter()
cph.fit(df, duration_col='T', event_col='E')
print(cph.summary)
```

## API Compatibility

This library is designed to be API-compatible with the core functionality of the lifelines package, supporting the same method signatures and return types for common use cases.