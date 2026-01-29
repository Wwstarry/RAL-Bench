from __future__ import annotations

import sys
from typing import List, Optional, Sequence, Tuple

from .args import Args
from .data import Data


_COLOR_MAP = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "purple": 35,
    "cyan": 36,
    "white": 37,
    "gray": 90,
    "grey": 90,
}


def _ansi(code: int) -> str:
    return f"\x1b[{code}m"


def _ansi_reset() -> str:
    return "\x1b[0m"


def _color_code(token: str) -> Optional[int]:
    if token is None:
        return None
    t = str(token).strip().lower()
    if not t:
        return None
    if t.isdigit():
        n = int(t)
        if 30 <= n <= 37 or 90 <= n <= 97:
            return n
        # Common "1-7" mapping (termgraph-ish)
        if 1 <= n <= 7:
            return 30 + n
        return None
    return _COLOR_MAP.get(t)


class BaseChart:
    BAR_CHAR = "#"

    def __init__(self, data: Data, args: Args):
        if not isinstance(data, Data):
            raise TypeError("data must be a termgraph.Data instance")
        if not isinstance(args, Args):
            raise TypeError("args must be a termgraph.Args instance")
        self.data = data
        self.args = args

    def _effective_labels(self) -> List[str]:
        if self.args.labels is not None:
            return list(self.args.labels)
        return list(self.data.labels)

    def _format_value(self, v) -> str:
        fmt = self.args.format
        try:
            if isinstance(fmt, str) and "{" in fmt:
                s = fmt.format(v)
            else:
                spec = fmt if isinstance(fmt, str) else ""
                s = ("{:" + spec + "}").format(v)
        except Exception:
            s = str(v)
        return s + (self.args.suffix or "")

    def _write_line(self, s: str) -> None:
        sys.stdout.write(s.rstrip() + "\n")

    def _colorize(self, s: str, series_idx: int) -> str:
        colors = self.args.color
        if not colors:
            return s
        token = colors[series_idx % len(colors)]
        code = _color_code(token)
        if code is None:
            return s
        return _ansi(code) + s + _ansi_reset()

    @staticmethod
    def _clamp_nonneg(x: float) -> float:
        return x if x > 0 else 0.0

    def _bar_len(self, value: float, max_value: float) -> int:
        w = int(self.args.width)
        if w <= 0:
            return 0
        if max_value <= 0:
            return 0
        r = w * (self._clamp_nonneg(value) / max_value)
        n = int(round(r))
        if n < 0:
            n = 0
        if n > w:
            n = w
        return n


class BarChart(BaseChart):
    def draw(self) -> None:
        # Vertical/histogram flags exist; for compatibility, render horizontally.
        labels = self._effective_labels()
        values = self.data.values

        if self.args.title:
            self._write_line(str(self.args.title))

        if not labels or not values:
            return

        n_rows = min(len(labels), len(values))
        n_series = self.data.n_series

        # Compute scale(s)
        if self.args.different_scale and n_series > 0:
            series_max = [0.0 for _ in range(n_series)]
            for i in range(n_rows):
                for j in range(n_series):
                    try:
                        fv = float(values[i][j])
                    except Exception:
                        fv = 0.0
                    if fv > series_max[j]:
                        series_max[j] = fv
        else:
            gmax = 0.0
            for i in range(n_rows):
                for j in range(n_series):
                    try:
                        fv = float(values[i][j])
                    except Exception:
                        fv = 0.0
                    if fv > gmax:
                        gmax = fv
            series_max = [gmax for _ in range(n_series)]

        for i in range(n_rows):
            lab = labels[i]
            row = values[i]

            if n_series <= 1:
                v = row[0] if row else 0
                try:
                    fv = float(v)
                except Exception:
                    fv = 0.0
                blen = self._bar_len(fv, series_max[0] if series_max else 0.0)
                bar = self.BAR_CHAR * blen
                bar = self._colorize(bar, 0)
                parts = []
                if not self.args.no_labels:
                    parts.append(f"{lab}: ")
                parts.append(bar)
                if not self.args.no_values:
                    parts.append(" " + self._format_value(v))
                self._write_line("".join(parts))
            else:
                # Multi-series: one line per series, label only on first line
                for j in range(n_series):
                    v = row[j]
                    try:
                        fv = float(v)
                    except Exception:
                        fv = 0.0
                    blen = self._bar_len(fv, series_max[j])
                    bar = self.BAR_CHAR * blen
                    bar = self._colorize(bar, j)
                    parts = []
                    if not self.args.no_labels:
                        if j == 0:
                            parts.append(f"{lab}: ")
                        else:
                            parts.append(" " * (len(lab) + 2))
                    parts.append(bar)
                    if not self.args.no_values:
                        parts.append(" " + self._format_value(v))
                    self._write_line("".join(parts))


class StackedChart(BaseChart):
    def _row_total(self, row: Sequence) -> float:
        s = 0.0
        for v in row:
            try:
                fv = float(v)
            except Exception:
                fv = 0.0
            if fv > 0:
                s += fv
        return s

    def _segment_lengths_exact(self, row: Sequence, row_len: int) -> List[int]:
        # Largest remainder method: ensure sum(lengths) == row_len.
        floats: List[float] = []
        for v in row:
            try:
                fv = float(v)
            except Exception:
                fv = 0.0
            floats.append(self._clamp_nonneg(fv))

        total = sum(floats)
        if row_len <= 0 or total <= 0:
            return [0 for _ in floats]

        raw = [row_len * (x / total) for x in floats]
        base = [int(r // 1) for r in raw]
        rem = row_len - sum(base)
        fracs = sorted([(raw[i] - base[i], i) for i in range(len(raw))], reverse=True)
        for k in range(rem):
            if not fracs:
                break
            _, idx = fracs[k % len(fracs)]
            base[idx] += 1
        return base

    def draw(self) -> None:
        labels = self._effective_labels()
        values = self.data.values

        if self.args.title:
            self._write_line(str(self.args.title))

        if not labels or not values:
            return

        n_rows = min(len(labels), len(values))
        n_series = self.data.n_series

        # Scale by max total per row.
        max_total = 0.0
        for i in range(n_rows):
            t = self._row_total(values[i])
            if t > max_total:
                max_total = t

        for i in range(n_rows):
            lab = labels[i]
            row = values[i]
            row_total = self._row_total(row)

            row_len = self._bar_len(row_total, max_total)
            seg_lens = self._segment_lengths_exact(row, row_len)

            segments: List[str] = []
            for j, seg in enumerate(seg_lens[:n_series]):
                s = self.BAR_CHAR * seg
                s = self._colorize(s, j)
                segments.append(s)

            bar = "".join(segments)
            parts: List[str] = []
            if not self.args.no_labels:
                parts.append(f"{lab}: ")
            parts.append(bar)

            if not self.args.no_values:
                # Print total for stacked charts (simple, stable)
                parts.append(" " + self._format_value(row_total))

            self._write_line("".join(parts))