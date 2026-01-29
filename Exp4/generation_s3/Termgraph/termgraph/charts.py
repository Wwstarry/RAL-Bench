from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .data import Data
from .args import Args


def _safe_width(width: int) -> int:
    try:
        w = int(width)
    except Exception as e:
        raise TypeError("width must be an integer") from e
    return 1 if w <= 0 else w


def _fmt_value(fmt: str, value) -> str:
    # If string contains braces, treat as .format template (common in reference).
    if isinstance(fmt, str) and "{" in fmt:
        try:
            return fmt.format(value)
        except Exception:
            # fallback
            return str(value)
    try:
        return format(value, fmt)
    except Exception:
        return str(value)


def _clamp(n: int, lo: int, hi: int) -> int:
    return lo if n < lo else hi if n > hi else n


def _scale_len(value: float, max_value: float, width: int) -> int:
    if max_value <= 0 or width <= 0:
        return 0
    if value <= 0:
        return 0
    # Use rounding to be stable and intuitive.
    return _clamp(int(round((value / max_value) * width)), 0, width)


_SEG_CHARS = ["#", "=", "-", "+", "*", "@"]
_BAR_CHAR = "#"


@dataclass
class BarChart:
    data: Data
    args: Args

    def __init__(self, data: Data, args: Args):
        self.data = data
        self.args = args
        self.data.validate()
        self.args.width = _safe_width(self.args.width)

    def draw(self) -> None:
        if self.args.title is not None:
            print(str(self.args.title))

        width = _safe_width(self.args.width)

        labels = self.data.labels if not self.args.no_labels else []
        label_width = max((len(l) for l in labels), default=0)

        n_series = self.data.n_series
        if n_series == 0:
            return

        # Determine maxima for scaling.
        if self.args.different_scale and n_series > 1:
            series_max = [0.0] * n_series
            for row in self.data.values:
                for j, v in enumerate(row):
                    fv = float(v)
                    if fv > series_max[j]:
                        series_max[j] = fv
        else:
            gmax = 0.0
            for row in self.data.values:
                for v in row:
                    fv = float(v)
                    if fv > gmax:
                        gmax = fv
            series_max = [gmax] * n_series

        for i, row in enumerate(self.data.values):
            parts: List[str] = []

            if not self.args.no_labels:
                lab = self.data.labels[i] if i < len(self.data.labels) else str(i + 1)
                parts.append(lab.ljust(label_width))
                parts.append(" ")

            # Render bars
            if n_series == 1:
                v = row[0]
                blen = _scale_len(float(v), series_max[0], width)
                bar = _BAR_CHAR * blen
                parts.append(bar.ljust(width))
                if not self.args.no_values:
                    parts.append(" ")
                    parts.append(_fmt_value(self.args.format, v))
                    parts.append(str(self.args.suffix))
            else:
                # Multiple series: render each series bar with separators.
                bar_parts: List[str] = []
                for j, v in enumerate(row):
                    blen = _scale_len(float(v), series_max[j], width)
                    bar_parts.append((_SEG_CHARS[j % len(_SEG_CHARS)] * blen).ljust(width))
                parts.append(" ".join(bar_parts))

                if not self.args.no_values:
                    parts.append(" ")
                    formatted = [_fmt_value(self.args.format, v) + str(self.args.suffix) for v in row]
                    parts.append(", ".join(formatted))

            print("".join(parts))


@dataclass
class StackedChart:
    data: Data
    args: Args

    def __init__(self, data: Data, args: Args):
        self.data = data
        self.args = args
        self.data.validate()
        self.args.width = _safe_width(self.args.width)

    def draw(self) -> None:
        if self.args.title is not None:
            print(str(self.args.title))

        width = _safe_width(self.args.width)

        labels = self.data.labels if not self.args.no_labels else []
        label_width = max((len(l) for l in labels), default=0)

        if self.data.n_series == 0:
            return

        totals: List[float] = []
        for row in self.data.values:
            totals.append(sum(float(v) for v in row))

        max_total = max(totals) if totals else 0.0

        for i, row in enumerate(self.data.values):
            parts: List[str] = []

            if not self.args.no_labels:
                lab = self.data.labels[i] if i < len(self.data.labels) else str(i + 1)
                parts.append(lab.ljust(label_width))
                parts.append(" ")

            total = sum(float(v) for v in row)
            if max_total <= 0 or total <= 0:
                stack = ""
            else:
                # Compute provisional segment lengths then fit exactly into width.
                seg_lens: List[int] = []
                for v in row:
                    seg_lens.append(_scale_len(float(v), max_total, width))

                # Ensure the stack doesn't exceed width (rounding can overflow).
                overflow = sum(seg_lens) - width
                if overflow > 0 and seg_lens:
                    # Reduce from the largest segments first deterministically.
                    order = sorted(range(len(seg_lens)), key=lambda k: (-seg_lens[k], k))
                    idx = 0
                    while overflow > 0 and idx < len(order):
                        k = order[idx]
                        if seg_lens[k] > 0:
                            seg_lens[k] -= 1
                            overflow -= 1
                        else:
                            idx += 1
                        if idx >= len(order) and overflow > 0:
                            idx = 0

                # Build the stacked bar
                segs: List[str] = []
                for j, sl in enumerate(seg_lens):
                    segs.append(_SEG_CHARS[j % len(_SEG_CHARS)] * sl)
                stack = "".join(segs)

            parts.append(stack.ljust(width))

            if not self.args.no_values:
                parts.append(" ")
                # Print total only for stacked charts.
                parts.append(_fmt_value(self.args.format, total))
                parts.append(str(self.args.suffix))

            print("".join(parts))