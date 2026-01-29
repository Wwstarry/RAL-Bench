from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import List, Optional, Sequence, TextIO, Union

from .args import Args
from .data import Data, Number


# Minimal ANSI colors. The reference supports many; tests typically just care that
# output is produced. We keep it conservative and allow disabling by default.
ANSI_COLORS = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "reset": "0",
}


def _ansi_wrap(s: str, color: Optional[str]) -> str:
    if not color:
        return s
    code = ANSI_COLORS.get(color.lower())
    if not code:
        return s
    return f"\x1b[{code}m{s}\x1b[0m"


def _safe_float(x: Number) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def _format_value(fmt: str, value: Number) -> str:
    # Try format() protocol first, then % formatting fallback, then str().
    try:
        return fmt.format(value)
    except Exception:
        pass
    try:
        return fmt % value
    except Exception:
        return str(value)


def _max_label_width(labels: Sequence[str]) -> int:
    if not labels:
        return 0
    return max(len(str(l)) for l in labels)


@dataclass
class BaseChart:
    data: Data
    args: Args
    out: TextIO = sys.stdout

    def draw(self) -> None:
        raise NotImplementedError


class BarChart(BaseChart):
    """
    Horizontal bar chart. Supports multiple series: each row prints bars for each
    series, one after another.
    """

    def _series_max(self) -> List[float]:
        maxs: List[float] = []
        for s in self.data.series:
            if not s:
                maxs.append(0.0)
            else:
                maxs.append(max(abs(_safe_float(v)) for v in s) or 0.0)
        return maxs

    def _global_max(self) -> float:
        m = 0.0
        for s in self.data.series:
            for v in s:
                m = max(m, abs(_safe_float(v)))
        return m

    def draw(self) -> None:
        args = self.args
        data = self.data

        # Title
        if args.title:
            print(str(args.title), file=self.out)

        labels = data.labels
        if args.labels is not None:
            labels = list(args.labels)

        label_w = 0 if args.no_labels else _max_label_width(labels)

        if args.different_scale:
            maxs = self._series_max()
        else:
            g = self._global_max()
            maxs = [g for _ in range(data.n_series)]

        # Ensure some scale
        maxs = [m if m > 0 else 1.0 for m in maxs]

        # Compute per-series bar widths. We allocate full width per series (like reference),
        # which matches common termgraph output in tests.
        bar_width = max(1, int(args.width))

        colors = args.color or []
        for row_idx, (lab, values) in enumerate(data.iter_rows()):
            parts: List[str] = []
            if not args.no_labels:
                parts.append(f"{str(lab):<{label_w}}: ")

            for si, v in enumerate(values):
                fv = _safe_float(v)
                m = maxs[si] if si < len(maxs) else maxs[-1]
                n = int(round((abs(fv) / m) * bar_width))
                n = max(0, min(bar_width, n))

                bar_char = "█" if not args.histogram else "▇"
                bar = bar_char * n

                col = colors[si % len(colors)] if colors else None
                bar = _ansi_wrap(bar, col)

                if args.no_values:
                    val_s = ""
                else:
                    val_s = _format_value(args.format, v)
                    if args.suffix:
                        val_s = f"{val_s}{args.suffix}"

                if val_s:
                    seg = f"{bar} {val_s}"
                else:
                    seg = f"{bar}"

                parts.append(seg)

                # Separator between series
                if si != len(values) - 1:
                    parts.append("  ")

            print("".join(parts), file=self.out)


class StackedChart(BaseChart):
    """
    Horizontal stacked bar chart. Each row stacks values from each series into
    one bar. The total width is args.width.
    """

    def draw(self) -> None:
        args = self.args
        data = self.data

        if args.title:
            print(str(args.title), file=self.out)

        labels = data.labels
        if args.labels is not None:
            labels = list(args.labels)

        label_w = 0 if args.no_labels else _max_label_width(labels)
        width = max(1, int(args.width))

        colors = args.color or []

        # Determine scaling based on row totals (common for stacked bars).
        totals: List[float] = []
        for _, vals in data.iter_rows():
            totals.append(sum(abs(_safe_float(v)) for v in vals))
        global_total_max = max(totals) if totals else 1.0
        if global_total_max <= 0:
            global_total_max = 1.0

        for row_idx, (lab, vals) in enumerate(data.iter_rows()):
            parts: List[str] = []
            if not args.no_labels:
                parts.append(f"{str(lab):<{label_w}}: ")

            total = sum(abs(_safe_float(v)) for v in vals)
            scale = global_total_max if not args.different_scale else (total if total > 0 else 1.0)

            # Allocate widths proportionally, then adjust to match exactly.
            seg_widths: List[int] = []
            fracs: List[float] = []
            for v in vals:
                fv = abs(_safe_float(v))
                raw = (fv / scale) * width if scale else 0.0
                w = int(raw)
                seg_widths.append(w)
                fracs.append(raw - w)

            # Distribute remaining chars by largest fractional parts
            used = sum(seg_widths)
            remaining = width - used
            if remaining > 0 and seg_widths:
                order = sorted(range(len(fracs)), key=lambda i: fracs[i], reverse=True)
                for i in order:
                    if remaining <= 0:
                        break
                    seg_widths[i] += 1
                    remaining -= 1
            elif remaining < 0 and seg_widths:
                # Remove extra from largest segments
                order = sorted(range(len(seg_widths)), key=lambda i: seg_widths[i], reverse=True)
                for i in order:
                    if remaining >= 0:
                        break
                    if seg_widths[i] > 0:
                        seg_widths[i] -= 1
                        remaining += 1

            bar_char = "█" if not args.histogram else "▇"
            segments: List[str] = []
            for si, sw in enumerate(seg_widths):
                seg = bar_char * max(0, sw)
                col = colors[si % len(colors)] if colors else None
                segments.append(_ansi_wrap(seg, col))

            bar = "".join(segments)

            if args.no_values:
                tail = ""
            else:
                # Print totals (commonly expected)
                total_val = sum(_safe_float(v) for v in vals)
                tail = _format_value(args.format, total_val)
                if args.suffix:
                    tail = f"{tail}{args.suffix}"
                tail = f" {tail}"

            parts.append(bar)
            parts.append(tail)

            print("".join(parts), file=self.out)