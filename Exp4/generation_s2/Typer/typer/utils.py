import click


def echo(message=None, file=None, nl=True, err=False, color=None):
    """
    Print a message to stdout/stderr.

    Delegates to click.echo to match Typer/Click behavior.
    """
    return click.echo(message=message, file=file, nl=nl, err=err, color=color)