"""
Pure Python survival analysis library compatible with lifelines API.
"""

from .fitters.kaplan_meier_fitter import KaplanMeierFitter
from .fitters.coxph_fitter import CoxPHFitter
from .datasets import load_waltons

__version__ = "0.1.0"
__all__ = [
    "KaplanMeierFitter",
    "CoxPHFitter",
    "load_waltons",
]