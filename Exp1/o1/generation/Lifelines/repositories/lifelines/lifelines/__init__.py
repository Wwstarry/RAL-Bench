"""
lifelines package
"""

from .fitters import KaplanMeierFitter, CoxPHFitter

# Keep datasets as a sub-package importable like lifelines.datasets
import lifelines.datasets