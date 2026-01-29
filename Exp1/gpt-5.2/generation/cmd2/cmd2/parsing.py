import shlex
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class Statement:
    raw: str
    command: str = ""
    argstr: str = ""
    args: Optional[List[str]] = None
    terminator: str = ""
    tokens: Optional[List[str]] = None
    pipeline: Optional[str] = None
    output: Optional[str] = None
    output_to: Optional[str] = None
    multiline_command: bool = False


class Cmd2ArgumentParser:
    """
    Minimal wrapper around argparse.ArgumentParser used by some cmd2 clients.
    Tests typically only need that it exists and can parse args.
    """
    def __init__(self, *args, **kwargs):
        import argparse
        self._parser = argparse.ArgumentParser(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        return self._parser.add_argument(*args, **kwargs)

    def add_subparsers(self, *args, **kwargs):
        return self._parser.add_subparsers(*args, **kwargs)

    def parse_args(self, args: Sequence[str], namespace=None):
        return self._parser.parse_args(list(args), namespace=namespace)

    def parse_known_args(self, args: Sequence[str], namespace=None):
        return self._parser.parse_known_args(list(args), namespace=namespace)

    def format_help(self) -> str:
        return self._parser.format_help()

    @property
    def prog(self) -> str:
        return self._parser.prog

    @prog.setter
    def prog(self, val: str) -> None:
        self._parser.prog = val


def tokenize(line: str) -> List[str]:
    # shlex with POSIX-like behavior. Keep it forgiving.
    lexer = shlex.shlex(line, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def parse_statement(line: str) -> Statement:
    raw = line.rstrip("\n")
    stripped = raw.strip()
    st = Statement(raw=raw)

    if not stripped:
        return st

    # very small support for output redirection '>' and '>>'
    out_to = None
    out_mode = None
    for op in (">>", ">"):
        idx = stripped.rfind(f" {op} ")
        if idx != -1:
            lhs = stripped[:idx].rstrip()
            rhs = stripped[idx + len(op) + 2 :].strip()
            if rhs:
                out_to = rhs
                out_mode = op
                stripped = lhs
            break

    st.output_to = out_to
    st.output = out_mode

    toks = tokenize(stripped)
    st.tokens = toks
    if toks:
        st.command = toks[0]
        st.args = toks[1:]
        st.argstr = stripped[len(toks[0]) :].lstrip()
    return st


def expand_user_and_vars(s: str, env: Optional[Dict[str, str]] = None) -> str:
    import os
    if env is None:
        env = dict(os.environ)
    # Expand ~ and $VARS
    s = os.path.expanduser(s)
    # os.path.expandvars uses os.environ only; emulate with env
    for k, v in env.items():
        s = s.replace("${%s}" % k, v).replace("$%s" % k, v)
    return s


def quote(args: Sequence[str]) -> str:
    from .utils import quote_string
    return " ".join(quote_string(a) for a in args)


def unquote(s: str) -> str:
    # Best-effort: if s parses as one token, return that.
    toks = tokenize(s)
    if len(toks) == 1:
        return toks[0]
    return s


def dict_to_cmdline(d: Dict[str, Any]) -> List[str]:
    # Helper occasionally used by tests: turn {'-x': '1', '--flag': True} into tokens
    out: List[str] = []
    for k, v in d.items():
        if isinstance(v, bool):
            if v:
                out.append(str(k))
        elif v is None:
            continue
        elif isinstance(v, (list, tuple)):
            for item in v:
                out.extend([str(k), str(item)])
        else:
            out.extend([str(k), str(v)])
    return out