from dataclasses import dataclass

@dataclass(frozen=True)
class SeparatedFormat:
    sep: str
    header: bool = True  # whether separated format should include headers if provided
    allow_padding: bool = False  # no alignment/padding, just raw separated fields


# Preset names we support
AVAILABLE_FORMATS = frozenset(
    [
        "plain",
        "simple",
        "grid",
        "pipe",
        "tsv",
        "csv",
        "html",
    ]
)

def simple_separated_format(sep: str) -> SeparatedFormat:
    # Return a format object which signals the core renderer to emit
    # separated values without alignment/padding.
    return SeparatedFormat(sep=sep, header=True, allow_padding=False)