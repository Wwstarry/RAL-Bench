"""
A minimal pure-Python survival analysis library with a subset of the lifelines API.

Exposes:
- KaplanMeierFitter
- CoxPHFitter
- datasets submodule with load_waltons
"""

from .kmf import KaplanMeierFitter
from .cox import CoxPHFitter
from . import datasets

__all__ = ["KaplanMeierFitter", "CoxPHFitter", "datasets"]

__version__ = "0.1.0"