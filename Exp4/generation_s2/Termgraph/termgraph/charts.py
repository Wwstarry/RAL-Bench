from __future__ import annotations

import sys
from typing import List, Optional, Sequence

from .args import Args
from .data import Data


_DEFAULT_SYMBOLS = ["#", "=", "-", "+", "*", "o", "x", "%", "@"]


def _fmt_value(fmt: str, v: float) -> str:
    # The reference uses old-style formatting sometimes; accept both.
    try:
        return fmt.format(v)
    except Exception:
        try:
            return fmt % v
        except Exception:
            # Fallback
            return str(v)


def _safe_label(label: str) -> str:
    return "" if label is None else str(label)


def _label_width(labels: Sequence[str]) -> int:
    if not labels:
        return 0
    return max(len(_safe_label(l)) for l in labels)


def _scale(value: float, max_value: float, width: int) -> int:
    if width <= 0:
        return 0
    if max_value <= 0:
        return 0
    # keep at least 0; round to nearest int, similar to reference feel
    n = int(round((float(value) / float(max_value)) * width))
    if n < 0:
        n = 0
    return n


class BaseChart:
    def __init__(self, data: Data, args: Args, symbols: Optional[Sequence[str]] = None, out=None):
        self.data = data
        self.args = args
        self.symbols = list(symbols) if symbols is not None else list(_DEFAULT_SYMBOLS)
        self.out = out if out is not None else sys.stdout

    def draw(self) -> None:
        raise NotImplementedError


class BarChart(BaseChart):
    """
    Horizontal bar chart. Supports multiple series (grouped) by printing one line per series per label.
    """
    def draw(self) -> None:
        if self.args.title:
            self.out.write(str(self.args.title).rstrip("\n") + "\n")

        labels = self.data.labels
        if self.args.labels is not None:
            labels = list(map(str, self.args.labels))
        if not labels:
            labels = ["" for _ in range(self.data.n_rows)]

        lw = 0 if self.args.no_labels else _label_width(labels)
        # Normalize scaling
        if self.args.different_scale:
            series_max = self.data.max_value_per_series()
        else:
            global_max = self.data.max_value()
            series_max = [global_max for _ in range(self.data.n_series)]

        for i in range(self.data.n_rows):
            label = _safe_label(labels[i]) if i < len(labels) else ""
            prefix = ""
            if not self.args.no_labels:
                prefix = f"{label:<{lw}}: "
            row_vals = self.data.values_for_row(i) if self.data.n_series else []
            if not row_vals:
                self.out.write(prefix.rstrip() + "\n")
                continue

            for s_idx, v in enumerate(row_vals):
                sym = self.symbols[s_idx % len(self.symbols)]
                maxv = series_max[s_idx] if s_idx < len(series_max) else (self.data.max_value() or 1.0)
                bar_len = _scale(v, maxv, self.args.width)
                bar = sym * bar_len

                line = prefix + bar
                if not self.args.no_values:
                    val_txt = _fmt_value(self.args.format, v) + (self.args.suffix or "")
                    # Separate with a space if there's a bar, else still show value
                    if bar:
                        line += " " + val_txt
                    else:
                        line += val_txt
                self.out.write(line.rstrip() + "\n")

                # Only print label prefix on first series line for that label in typical termgraph,
                # but many tests just check presence/shape. We'll match common behavior:
                prefix = " " * (lw + 2) if (not self.args.no_labels) else ""


class StackedChart(BaseChart):
    """
    Horizontal stacked bar chart. For each label, prints one line with segments for each series.
    """
    def draw(self) -> None:
        if self.args.title:
            self.out.write(str(self.args.title).rstrip("\n") + "\n")

        labels = self.data.labels
        if self.args.labels is not None:
            labels = list(map(str, self.args.labels))
        if not labels:
            labels = ["" for _ in range(self.data.n_rows)]

        lw = 0 if self.args.no_labels else _label_width(labels)

        sums = self.data.sums_per_row()
        max_sum = max(sums) if sums else 0.0
        if max_sum <= 0:
            max_sum = 1.0

        for i in range(self.data.n_rows):
            label = _safe_label(labels[i]) if i < len(labels) else ""
            prefix = ""
            if not self.args.no_labels:
                prefix = f"{label:<{lw}}: "

            row_vals = self.data.values_for_row(i) if self.data.n_series else []
            # Determine segment lengths, adjusting to fit width exactly-ish
            seg_lens: List[int] = []
            for v in row_vals:
                seg_lens.append(_scale(v, max_sum, self.args.width))

            # Clamp/adjust total to not exceed width too much
            total = sum(seg_lens)
            if total > self.args.width and total > 0:
                # Reduce from the largest segments until fits
                while total > self.args.width:
                    j = max(range(len(seg_lens)), key=lambda k: seg_lens[k])
                    if seg_lens[j] <= 0:
                        break
                    seg_lens[j] -= 1
                    total -= 1

            bar_parts = []
            for s_idx, seg in enumerate(seg_lens):
                sym = self.symbols[s_idx % len(self.symbols)]
                if seg > 0:
                    bar_parts.append(sym * seg)
            bar = "".join(bar_parts)

            line = prefix + bar
            if not self.args.no_values:
                # In stacked chart, often show sum
                total_value = sum(row_vals) if row_vals else 0.0
                val_txt = _fmt_value(self.args.format, total_value) + (self.args.suffix or "")
                if bar:
                    line += " " + val_txt
                else:
                    line += val_txt

            self.out.write(line.rstrip() + "\n")