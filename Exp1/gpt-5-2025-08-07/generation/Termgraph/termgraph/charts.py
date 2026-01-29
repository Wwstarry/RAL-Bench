import sys
from typing import List, Optional

from .data import Data
from .args import Args


BAR_CHAR = "▇"


_COLOR_NAMES = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "grey": 90,
    "gray": 90,
}


def _ansi_code(spec) -> Optional[str]:
    if spec is None:
        return None
    if isinstance(spec, int):
        return f"\033[{spec}m"
    if isinstance(spec, str):
        s = spec.strip().lower()
        if s.isdigit():
            return f"\033[{int(s)}m"
        if s in _COLOR_NAMES:
            return f"\033[{_COLOR_NAMES[s]}m"
        # allow raw codes like "\033[31m" (pass-through)
        if s.startswith("\033[") and s.endswith("m"):
            return spec
    return None


def _apply_color(text: str, spec) -> str:
    code = _ansi_code(spec)
    if not code:
        return text
    return f"{code}{text}\033[0m"


def _format_value(value: float, args: Args) -> str:
    if args.format:
        try:
            if "{" in args.format:
                s = args.format.format(value)
            else:
                s = format(value, args.format)
        except Exception:
            s = str(value)
    else:
        s = str(value)
    if args.suffix:
        s = f"{s}{args.suffix}"
    return s


def _compute_blocks(value: float, max_value: float, width: int) -> int:
    if width <= 0 or max_value <= 0:
        return 0
    # Round to nearest int to better match expected proportions
    blocks = int(round((value / max_value) * width))
    if blocks < 0:
        blocks = 0
    return blocks


class BaseChart:
    def __init__(self, data: Data, args: Args):
        self.data = data
        self.args = args

    def _label_width(self) -> int:
        if self.args.no_labels:
            return 0
        if self.data.labels:
            return max(len(lbl) for lbl in self.data.labels)
        return 0

    def _emit_title(self):
        if self.args.title:
            print(self.args.title, file=sys.stdout)


class BarChart(BaseChart):
    """
    Horizontal bar chart (grouped for multiple series).
    """

    def draw(self):
        self._emit_title()
        label_w = self._label_width()
        # Determine scales
        series_count = self.data.num_series()
        if self.args.different_scale and series_count > 1:
            per_series_max = self.data.max_per_series()
        else:
            global_max = self.data.max_value()
            per_series_max = [global_max] * max(1, series_count)

        for i in range(self.data.num_rows()):
            label = self.data.label(i)
            row = self.data.row(i)

            # Build bars for each value in row
            segments: List[str] = []
            for j, v in enumerate(row):
                maxv = per_series_max[j if j < len(per_series_max) else 0]
                blocks = _compute_blocks(v, maxv, self.args.width)
                bar = BAR_CHAR * blocks
                # Apply color for this series if provided
                color_spec = None
                if self.args.color and j < len(self.args.color):
                    color_spec = self.args.color[j]
                bar = _apply_color(bar, color_spec)

                if self.args.no_values:
                    seg = bar
                else:
                    seg = f"{bar} { _format_value(v, self.args) }"
                segments.append(seg)

            line_left = ""
            if not self.args.no_labels:
                # Align labels left
                line_left = f"{label:<{label_w}} "
            # If a row has no series, still output a blank line with label
            if not segments:
                segments = [""]

            print(f"{line_left}{' '.join(segments)}", file=sys.stdout)


class StackedChart(BaseChart):
    """
    Horizontal stacked bar chart. Multiple series per row are stacked to one bar.
    """

    def draw(self):
        self._emit_title()
        label_w = self._label_width()

        series_count = self.data.num_series()
        # Scaling for stacked chart:
        # - If different_scale: each series scales to width using its own max. Total may exceed width.
        # - Else: sum of series per row scaled to width using max row sum.
        if self.args.different_scale and series_count > 1:
            series_max = self.data.max_per_series()
        else:
            sum_max = max(self.data.sum_per_row()) if self.data.num_rows() > 0 else 0.0

        for i in range(self.data.num_rows()):
            label = self.data.label(i)
            row = self.data.row(i)

            pieces: List[str] = []

            if self.args.different_scale and series_count > 1:
                # Each segment uses its own scale.
                for j, v in enumerate(row):
                    blocks = _compute_blocks(v, series_max[j if j < len(series_max) else 0], self.args.width)
                    seg = BAR_CHAR * blocks
                    color_spec = None
                    if self.args.color and j < len(self.args.color):
                        color_spec = self.args.color[j]
                    seg = _apply_color(seg, color_spec)
                    pieces.append(seg)
            else:
                # Scale by total sum to fit within width.
                total = sum(row) if row else 0.0
                # When sum_max is 0, all blocks zero
                used = 0
                for j, v in enumerate(row):
                    blocks = _compute_blocks(v, sum_max, self.args.width)
                    used += blocks
                    seg = BAR_CHAR * blocks
                    color_spec = None
                    if self.args.color and j < len(self.args.color):
                        color_spec = self.args.color[j]
                    seg = _apply_color(seg, color_spec)
                    pieces.append(seg)

                # Constrain to width when rounding caused overflow
                if used > self.args.width:
                    # Trim from the end segments
                    overflow = used - self.args.width
                    idx = len(pieces) - 1
                    while overflow > 0 and idx >= 0:
                        s = pieces[idx]
                        # Count visible bar chars only (strip ANSI codes)
                        visible = s.replace("\033[0m", "")
                        for name, code in _COLOR_NAMES.items():
                            visible = visible.replace(f"\033[{code}m", "")
                        bars_count = visible.count(BAR_CHAR)
                        if bars_count > 0:
                            remove = min(overflow, bars_count)
                            # Rebuild segment without color codes
                            new_visible = BAR_CHAR * (bars_count - remove)
                            spec = None
                            if self.args.color and idx < len(self.args.color):
                                spec = self.args.color[idx]
                            pieces[idx] = _apply_color(new_visible, spec)
                            overflow -= remove
                        idx -= 1

            bar = "".join(pieces)
            # Build value string
            if self.args.no_values:
                value_str = ""
            else:
                total_value = sum(row) if row else 0.0
                value_str = f" {_format_value(total_value, self.args)}"

            line_left = ""
            if not self.args.no_labels:
                line_left = f"{label:<{label_w}} "

            print(f"{line_left}{bar}{value_str}", file=sys.stdout)