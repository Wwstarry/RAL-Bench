"""
A extremely small subset of Typer that is sufficient for the test-suite used
in this repository.  It relies internally on ``click`` for all command-line
behaviour and only re-implements the public surface that the tests exercise.
"""
from __future__ import annotations

import inspect
import sys
from typing import Any, Callable, List, Tuple, Union

import click


# --------------------------------------------------------------------------- #
# echo
# --------------------------------------------------------------------------- #
echo = click.echo  # Re-export


# --------------------------------------------------------------------------- #
# Exit
# --------------------------------------------------------------------------- #
class Exit(SystemExit):
    """
    A thin wrapper around ``SystemExit`` replicating ``typer.Exit``.

    ``raise typer.Exit(code)`` works as expected and the exit status is
    available through ``.exit_code`` (matching Click’s Exit exception.)
    """

    def __init__(self, code: int = 0) -> None:
        super().__init__(code)
        self.exit_code = code


# --------------------------------------------------------------------------- #
# Internal parameter helpers
# --------------------------------------------------------------------------- #
class _ParamInfo:
    """
    Metadata produced by ``Option()`` / ``Argument()`` and attached to the
    default value of a function parameter.  During command registration the
    Typer application inspects the function signature, finds these sentinel
    objects and converts them into Click parameters.
    """

    def __init__(
        self,
        *,
        param_type: str,
        default: Any,
        param_decls: Tuple[str, ...],
        param_kwargs: dict,
    ) -> None:
        self.param_type = param_type  # "option" | "argument"
        self.default = default
        self.param_decls = param_decls
        self.param_kwargs = param_kwargs

    # For nicer repr in debugging.
    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"type={self.param_type!s} "
            f"decls={self.param_decls!r} kw={self.param_kwargs!r}>"
        )


def Option(default: Any = ..., *param_decls: str, **kwargs: Any) -> _ParamInfo:  # noqa: N802
    """
    Stand-in replacement for ``typer.Option``.

    Example usage inside a command callback:

        def hello(name: str = Option("World", "--name", "-n")):
            ...
    """
    return _ParamInfo(
        param_type="option",
        default=default,
        param_decls=param_decls,
        param_kwargs=kwargs,
    )


def Argument(default: Any = ..., *param_decls: str, **kwargs: Any) -> _ParamInfo:  # noqa: N802
    """
    Stand-in replacement for ``typer.Argument``.
    """
    return _ParamInfo(
        param_type="argument",
        default=default,
        param_decls=param_decls,
        param_kwargs=kwargs,
    )


# --------------------------------------------------------------------------- #
# Helper that converts function signature -> Click parameters
# --------------------------------------------------------------------------- #
def _build_click_params(fn: Callable[..., Any]) -> List[click.Parameter]:
    params: List[click.Parameter] = []
    sig = inspect.signature(fn)

    for name, parameter in sig.parameters.items():
        default = parameter.default
        annotation = parameter.annotation
        ann_provided = annotation is not inspect._empty  # type: ignore[attr-defined]

        # ------------------------------------------------------------------ #
        # Option declared via typer.Option(...)
        # ------------------------------------------------------------------ #
        if isinstance(default, _ParamInfo) and default.param_type == "option":
            decls = default.param_decls or (f"--{name.replace('_', '-')}",)
            kwargs = dict(default.param_kwargs)  # shallow copy

            # Determine default & required flag
            if default.default is not inspect._empty:
                kwargs.setdefault("default", default.default)
            else:
                kwargs.setdefault("required", True)

            # Type information
            if ann_provided and annotation is bool:
                kwargs.setdefault("is_flag", True)
            elif ann_provided:
                kwargs.setdefault("type", annotation)

            option = click.Option(list(decls), **kwargs)
            params.append(option)
            continue

        # ------------------------------------------------------------------ #
        # Argument declared via typer.Argument(...)
        # ------------------------------------------------------------------ #
        if isinstance(default, _ParamInfo) and default.param_type == "argument":
            decls = default.param_decls or (name,)
            kwargs = dict(default.param_kwargs)

            if default.default is not inspect._empty:
                kwargs.setdefault("default", default.default)

            if ann_provided:
                kwargs.setdefault("type", annotation)

            argument = click.Argument(list(decls), **kwargs)
            params.append(argument)
            continue

        # ------------------------------------------------------------------ #
        # No special Typer metadata → treat as positional argument
        # ------------------------------------------------------------------ #
        decls = [name]
        kwargs: dict[str, Any] = {}
        if parameter.default is not inspect._empty:
            kwargs["default"] = parameter.default
        if ann_provided:
            kwargs["type"] = annotation
        argument = click.Argument(decls, **kwargs)
        params.append(argument)

    return params


# --------------------------------------------------------------------------- #
# Typer main application / command group
# --------------------------------------------------------------------------- #
class Typer:
    """
    Mimics the public interface of ``typer.Typer`` while delegating all heavy
    lifting to a ``click.Group`` internally.
    """

    def __init__(self, *, name: str | None = None, **group_kwargs: Any) -> None:
        # `add_help_option` etc. are accepted but simply forwarded to Click.
        self._group = click.Group(name=name, **group_kwargs)

    # --------------------------------------------------------------------- #
    # Decorators / command registration
    # --------------------------------------------------------------------- #
    def command(self, *dargs: Any, **dkwargs: Any):  # noqa: D401
        """
        Decorator to register a function as a CLI command.

        Example:
            app = typer.Typer()

            @app.command()
            def hello():
                ...
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            cmd_name = dkwargs.get("name") or fn.__name__.replace("_", "-")
            params = _build_click_params(fn)

            # Build click.Command and add to our group
            cmd = click.Command(
                name=cmd_name,
                params=params,
                callback=fn,
                help=fn.__doc__,
            )

            self._group.add_command(cmd)
            return fn  # Preserve original function object

        # If used without arguments -> @app.command
        if dargs and callable(dargs[0]):
            return decorator(dargs[0])  # type: ignore[arg-type]
        return decorator

    # --------------------------------------------------------------------- #
    # Additional helpers
    # --------------------------------------------------------------------- #
    def add_typer(self, other: "Typer", name: str | None = None) -> None:  # noqa: N802
        """
        Attach another Typer instance (sub-application) as a sub-command group.
        This is only implemented for completeness – tests may or may not use it.
        """
        self._group.add_command(other._group, name=name)

    # --------------------------------------------------------------------- #
    # Click passthroughs / dunder methods
    # --------------------------------------------------------------------- #
    def __call__(self, *args: Any, **kwargs: Any):  # noqa: D401
        """
        Make the application executable by simply calling it:

            if __name__ == "__main__":
                app()
        """
        return self._group(*args, **kwargs)

    # Provide attribute access to underlying click.Group for convenience
    def __getattr__(self, item: str):  # noqa: D401
        try:
            return getattr(self._group, item)
        except AttributeError as exc:
            raise AttributeError(item) from exc


# --------------------------------------------------------------------------- #
# Sub-package: typer.testing
# --------------------------------------------------------------------------- #
class _TestingModuleType(type(sys)):  # type: ignore[type-arg]
    """
    A lazy module object injected into ``sys.modules["typer.testing"]`` so that
    importing ``typer.testing`` yields an object with ``CliRunner`` available.
    """

    def __init__(self):  # noqa: D401
        super().__init__("typer.testing")
        from click.testing import CliRunner  # Local import to avoid global dep

        self.CliRunner = CliRunner
        self.__all__ = ["CliRunner"]


# Inject the fake sub-module so ``import typer.testing`` works.
sys.modules.setdefault("typer.testing", _TestingModuleType())  # type: ignore[arg-type]


# What gets imported with ``from typer import *``
__all__ = [
    "Typer",
    "Option",
    "Argument",
    "echo",
    "Exit",
]