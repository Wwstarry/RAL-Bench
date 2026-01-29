"""
A minimal, pure-Python subset of the lifelines API required by the tests.

This is NOT the full lifelines project. Only core interfaces are implemented:
- KaplanMeierFitter
- CoxPHFitter
- datasets.load_waltons
"""

from .fitters.kaplan_meier_fitter import KaplanMeierFitter
from .fitters.coxph_fitter import CoxPHFitter
from . import datasets

__all__ = ["KaplanMeierFitter", "CoxPHFitter", "datasets"]