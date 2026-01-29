from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Iterable, Tuple
import re

from fail2ban.server import filter as f2bfilter


@dataclass
class RegexMatch:
    line_no: int
    line: str
    regex: str
    host: Optional[str]


@dataclass
class RegexReport:
    matched: List[RegexMatch]
    missed: int
    ignored: int

    @property
    def total_lines(self) -> int:
        return self.missed + self.ignored + len(self.matched)


def _compile_list(patterns: Iterable[str]) -> List[re.Pattern]:
    return [re.compile(p) for p in patterns]


def run_regex(
    log_text: str,
    failregex: List[str],
    ignoreregex: Optional[List[str]] = None,
) -> RegexReport:
    """
    Offline equivalent of `fail2ban-regex`:
    - Apply ignoreregex first (ignored count)
    - If any failregex matches line -> record match with extracted host
    """
    fr = _compile_list(failregex)
    ir = _compile_list(ignoreregex or [])

    matched: List[RegexMatch] = []
    missed = 0
    ignored = 0

    for idx, line in enumerate(log_text.splitlines(), start=1):
        if any(p.search(line) for p in ir):
            ignored += 1
            continue

        hits: List[Tuple[re.Pattern, re.Match]] = []
        for p in fr:
            m = p.search(line)
            if m:
                hits.append((p, m))

        if not hits:
            missed += 1
            continue

        # record all matching regexes (like fail2ban-regex can show multiple)
        for p, m in hits:
            host = f2bfilter.extract_host_from_match(m)
            matched.append(RegexMatch(line_no=idx, line=line, regex=p.pattern, host=host))

    return RegexReport(matched=matched, missed=missed, ignored=ignored)