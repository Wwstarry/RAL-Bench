import click


class CliRunner(click.testing.CliRunner):
    """
    Typer-compatible test runner.

    This is a thin subclass of Click's CliRunner so tests can import:
    `from typer.testing import CliRunner`.
    """

    pass