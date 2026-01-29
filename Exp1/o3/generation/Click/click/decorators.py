"""
Decorator helpers that mark functions as click commands and attach parameter
declarations.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from .core import Command, Group, Option, Argument
from .core import CommandBuilder

Callback = Callable[..., Any]


def _attach_param(func: Callable, param) -> None:
    params = getattr(func, "__click_params__", [])
    params.insert(0, param)
    setattr(func, "__click_params__", params)


# ------------------------------------------------------------------------------
# parameter decorators
# ------------------------------------------------------------------------------

def option(*param_decls: str, **attrs: Any):
    """
    Usage::

        @click.option("-n", "--name", required=True, help="User name")
        def cmd(name):
            ...
    """
    def decorator(f: Callback) -> Callback:
        _attach_param(f, Option(param_decls, **attrs))
        return f

    return decorator


def argument(name: str, **attrs: Any):
    """
    Usage::

        @click.argument("filename")
        def cmd(filename):
            ...
    """

    def decorator(f: Callback) -> Callback:
        _attach_param(f, Argument(name, **attrs))
        return f

    return decorator


# ------------------------------------------------------------------------------
# command / group decorators
# ------------------------------------------------------------------------------

def command(name: str | None = None, **attrs: Any):
    """
    Decorator that converts a function into a :class:`~click.core.Command`
    instance.
    """

    def decorator(f: Callback) -> Command:
        cmd = CommandBuilder.from_callback(f, (), dict(name=name, **attrs))
        return cmd

    return decorator


def group(name: str | None = None, **attrs: Any):
    """
    Decorator that converts a function into a :class:`~click.core.Group`
    instance.
    """

    def decorator(f: Callback) -> Group:
        grp = CommandBuilder.from_group_callback(f, (), dict(name=name, **attrs))
        return grp

    return decorator