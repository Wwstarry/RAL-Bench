"""
A minimal pure-python re-implementation of some core API elements of the
`lifelines` package that are required by the evaluation test-suite.
Only a subset of the real library’s functionality is provided.
"""

from .kaplan_meier_fitter import KaplanMeierFitter
from .coxph_fitter import CoxPHFitter
from . import datasets

__all__ = ["KaplanMeierFitter", "CoxPHFitter", "datasets"]