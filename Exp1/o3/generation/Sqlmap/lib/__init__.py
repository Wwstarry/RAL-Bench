"""
Top-level package initialiser.

The real sqlmap project provides a deeply nested package hierarchy that
tests refer to via absolute import paths such as:

    from lib.core.data import conf, kb

To remain interface-compatible we recreate that package structure (albeit
with a drastically reduced feature set).  This small shim merely marks
`lib` as a Python package.
"""
# Nothing to initialise here. The heavy lifting is done in sub-modules.