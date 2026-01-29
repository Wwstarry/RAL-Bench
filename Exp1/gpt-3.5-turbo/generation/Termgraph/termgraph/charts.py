import sys

class BarChart:
    def __init__(self, data, args):
        self.data = data
        self.args = args

    def draw(self):
        # Only horizontal bar charts supported
        if self.args.vertical:
            print("Vertical charts not supported in this implementation.", file=sys.stderr)
            return

        labels = self.args.labels if self.args.labels is not None else self.data.labels
        if labels is None:
            labels = [''] * self.data.num_items()

        max_label_len = max((len(str(label)) for label in labels), default=0)
        max_label_len = min(max_label_len, 20)  # limit label width

        max_width = self.args.width
        format_str = self.args.format
        suffix = self.args.suffix
        no_labels = self.args.no_labels
        no_values = self.args.no_values

        # For bar length scaling
        max_val = 0
        for series in self.data.data:
            for val in series:
                if val > max_val:
                    max_val = val
        if max_val == 0:
            max_val = 1  # avoid division by zero

        # We only support one series in BarChart (like termgraph does)
        # If multiple series, just draw first series
        series = self.data.data[0] if self.data.data else []

        for i, val in enumerate(series):
            label = labels[i] if i < len(labels) else ''
            if no_labels:
                label_str = ''
            else:
                label_str = str(label)[:max_label_len].ljust(max_label_len) + ' | '

            # bar length proportional to val/max_val * max_width
            bar_len = int(round(val / max_val * max_width))
            bar = '█' * bar_len

            if no_values:
                val_str = ''
            else:
                try:
                    val_str = format_str.format(val) + suffix
                except Exception:
                    val_str = str(val) + suffix

            line = label_str + bar
            if val_str:
                # add space between bar and value if bar present
                if bar:
                    line += ' ' + val_str
                else:
                    line += val_str

            print(line)


class StackedChart:
    def __init__(self, data, args):
        self.data = data
        self.args = args

    def draw(self):
        # Only horizontal stacked bar charts supported
        if self.args.vertical:
            print("Vertical charts not supported in this implementation.", file=sys.stderr)
            return

        labels = self.args.labels if self.args.labels is not None else self.data.labels
        if labels is None:
            labels = [''] * self.data.num_items()

        max_label_len = max((len(str(label)) for label in labels), default=0)
        max_label_len = min(max_label_len, 20)  # limit label width

        max_width = self.args.width
        format_str = self.args.format
        suffix = self.args.suffix
        no_labels = self.args.no_labels
        no_values = self.args.no_values

        # sum values per item (stacked)
        sums = []
        n_items = self.data.num_items()
        n_series = self.data.num_series()
        for i in range(n_items):
            s = 0
            for series in self.data.data:
                if i < len(series):
                    s += series[i]
            sums.append(s)

        max_val = max(sums) if sums else 0
        if max_val == 0:
            max_val = 1  # avoid division by zero

        # For each item, draw stacked bar
        for i in range(n_items):
            label = labels[i] if i < len(labels) else ''
            if no_labels:
                label_str = ''
            else:
                label_str = str(label)[:max_label_len].ljust(max_label_len) + ' | '

            # total bar length for this item
            total_len = int(round(sums[i] / max_val * max_width))

            # calculate each series bar length proportional to its value
            lengths = []
            for series in self.data.data:
                val = series[i] if i < len(series) else 0
                length = int(round(val / max_val * max_width))
                lengths.append(length)

            # Adjust lengths to sum exactly total_len (fix rounding)
            length_sum = sum(lengths)
            diff = total_len - length_sum
            # Distribute diff to largest segments
            if diff != 0 and lengths:
                # indices sorted by length descending
                sorted_indices = sorted(range(len(lengths)), key=lambda x: lengths[x], reverse=True)
                for idx in sorted_indices:
                    if diff == 0:
                        break
                    lengths[idx] += 1 if diff > 0 else -1
                    diff += -1 if diff > 0 else 1

            # Build bar string
            bar = ''
            for length in lengths:
                bar += '█' * length

            if no_values:
                val_str = ''
            else:
                try:
                    val_str = format_str.format(sums[i]) + suffix
                except Exception:
                    val_str = str(sums[i]) + suffix

            line = label_str + bar
            if val_str:
                if bar:
                    line += ' ' + val_str
                else:
                    line += val_str

            print(line)