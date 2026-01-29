import sys

# Unicode block for bar rendering
BAR_CHAR = "█"
STACK_CHARS = ["░", "▒", "▓", "█", "■", "▇", "▆", "▅", "▄", "▃", "▂", "▁"]

def _get_bar_char(idx):
    return STACK_CHARS[idx % len(STACK_CHARS)]

def _format_value(val, fmt, suffix):
    try:
        return fmt.format(val) + suffix
    except Exception:
        return str(val) + suffix

class BarChart:
    """
    Renders horizontal bar charts to stdout.
    """
    def __init__(self, data, args):
        self.data = data
        self.args = args

    def draw(self, file=sys.stdout):
        if self.args.title:
            print(self.args.title, file=file)
        max_label_len = max((len(str(label)) for label in self.data.labels), default=0)
        width = self.args.width
        fmt = self.args.format
        suffix = self.args.suffix
        no_labels = self.args.no_labels
        no_values = self.args.no_values
        color = self.args.color

        # Find max value for scaling
        if self.args.different_scale:
            max_vals = [max(series) if series else 0 for series in self.data.data]
        else:
            max_val = self.data.max_value()

        for idx, (label, series) in enumerate(zip(self.data.labels, self.data.data)):
            if self.args.different_scale:
                scale = max_vals[idx] if max_vals[idx] else 1
            else:
                scale = max_val if max_val else 1

            bars = []
            for sidx, value in enumerate(series):
                bar_len = int(round((value / scale) * width)) if scale else 0
                bar_char = color[sidx % len(color)] if color else BAR_CHAR
                bars.append(bar_char * bar_len)

            bar_str = " ".join(bars)
            label_str = "" if no_labels else str(label).ljust(max_label_len)
            value_str = "" if no_values else " " + " ".join(_format_value(v, fmt, suffix) for v in series)
            print(f"{label_str} | {bar_str}{value_str}", file=file)

class StackedChart:
    """
    Renders horizontal stacked bar charts to stdout.
    """
    def __init__(self, data, args):
        self.data = data
        self.args = args

    def draw(self, file=sys.stdout):
        if self.args.title:
            print(self.args.title, file=file)
        max_label_len = max((len(str(label)) for label in self.data.labels), default=0)
        width = self.args.width
        fmt = self.args.format
        suffix = self.args.suffix
        no_labels = self.args.no_labels
        no_values = self.args.no_values
        color = self.args.color

        # Find max value for scaling
        if self.args.different_scale:
            max_vals = [sum(series) for series in self.data.data]
        else:
            max_val = max(sum(series) for series in self.data.data) if self.data.data else 1

        for idx, (label, series) in enumerate(zip(self.data.labels, self.data.data)):
            if self.args.different_scale:
                scale = max_vals[idx] if max_vals[idx] else 1
            else:
                scale = max_val if max_val else 1

            total = sum(series)
            bar_str = ""
            for sidx, value in enumerate(series):
                bar_len = int(round((value / scale) * width)) if scale else 0
                bar_char = color[sidx % len(color)] if color else _get_bar_char(sidx)
                bar_str += bar_char * bar_len

            label_str = "" if no_labels else str(label).ljust(max_label_len)
            value_str = ""
            if not no_values:
                value_str = " " + _format_value(total, fmt, suffix)
            print(f"{label_str} | {bar_str}{value_str}", file=file)