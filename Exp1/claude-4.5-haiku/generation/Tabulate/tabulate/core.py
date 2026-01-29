"""
Core tabulate functionality.
"""

import re
from tabulate.formats import get_named_table_format, TableFormat


def _isnumber(obj):
    """Check if an object is a number."""
    try:
        float(obj)
        return True
    except (ValueError, TypeError):
        return False


def _type(obj):
    """Determine the type of an object for alignment purposes."""
    if obj is None:
        return "empty"
    if isinstance(obj, bool):
        return "text"
    if isinstance(obj, (int, float)):
        return "number"
    if _isnumber(obj):
        return "number"
    return "text"


def _align_column(strings, alignment, minwidth=0):
    """Align a column of strings."""
    if not strings:
        return []
    
    width = max(minwidth, max(len(s) for s in strings))
    
    if alignment == "center":
        return [s.center(width) for s in strings]
    elif alignment == "right":
        return [s.rjust(width) for s in strings]
    else:  # left
        return [s.ljust(width) for s in strings]


def _split_multiline(cell):
    """Split a cell into multiple lines."""
    cell_str = str(cell) if cell is not None else ""
    return cell_str.split("\n")


def _normalize_tabular_data(data, headers):
    """Normalize input data into a list of lists."""
    if isinstance(data, dict):
        # Single dict
        if headers == "keys":
            headers = list(data.keys())
        else:
            headers = headers or list(data.keys())
        rows = [[data.get(h, "") for h in headers]]
        return rows, headers
    
    if isinstance(data, list):
        if not data:
            return [], headers
        
        first = data[0]
        
        if isinstance(first, dict):
            # List of dicts
            if headers == "keys":
                headers = list(first.keys())
            else:
                headers = headers or list(first.keys())
            rows = [[row.get(h, "") for h in headers] for row in data]
            return rows, headers
        else:
            # List of lists or list of values
            if isinstance(first, (list, tuple)):
                return data, headers
            else:
                # Single row of values
                return [data], headers
    
    return data, headers


def tabulate(tabular_data, headers=(), tablefmt="simple", floatfmt="g",
             numalign="decimal", stralign="left", missingval="", 
             showindex=False, disable_numparse=False, colalign=None):
    """
    Format a table from tabular data.
    
    Args:
        tabular_data: List of lists, list of dicts, or dict
        headers: List of header names or "keys" for dict keys
        tablefmt: Table format name (e.g., "grid", "pipe", "plain")
        floatfmt: Format string for floats (default "g")
        numalign: Alignment for numbers ("decimal", "right", "center", "left")
        stralign: Alignment for strings ("left", "center", "right")
        missingval: String to use for missing values
        showindex: Show row indices
        disable_numparse: Don't parse numeric strings
        colalign: Per-column alignment override
    
    Returns:
        Formatted table as a string
    """
    
    # Get the table format
    if isinstance(tablefmt, str):
        fmt = get_named_table_format(tablefmt)
    else:
        fmt = tablefmt
    
    # Normalize data
    rows, headers = _normalize_tabular_data(tabular_data, headers)
    
    # Convert headers to strings
    if headers:
        headers = [str(h) for h in headers]
    
    # Add index column if needed
    if showindex:
        if headers:
            headers = [""] + headers
        rows = [[i] + list(row) for i, row in enumerate(rows)]
    
    # Convert all cells to strings and handle multiline
    max_lines = 1
    processed_rows = []
    for row in rows:
        processed_row = []
        for cell in row:
            lines = _split_multiline(cell)
            processed_row.append(lines)
            max_lines = max(max_lines, len(lines))
        processed_rows.append(processed_row)
    
    # Expand multiline cells
    expanded_rows = []
    for row in processed_rows:
        expanded_row = []
        for lines in row:
            # Pad lines to max_lines
            padded = lines + [""] * (max_lines - len(lines))
            expanded_row.append(padded)
        expanded_rows.append(expanded_row)
    
    # Transpose to get columns
    if not expanded_rows:
        columns = []
    else:
        num_cols = len(expanded_rows[0])
        columns = []
        for col_idx in range(num_cols):
            col = []
            for row in expanded_rows:
                col.extend(row[col_idx])
            columns.append(col)
    
    # Calculate column widths
    col_widths = []
    for col_idx, col in enumerate(columns):
        width = 0
        if headers and col_idx < len(headers):
            width = len(headers[col_idx])
        for cell_lines in col:
            for line in cell_lines:
                width = max(width, len(line))
        col_widths.append(width)
    
    # Determine alignment for each column
    alignments = []
    for col_idx, col in enumerate(columns):
        if colalign and col_idx < len(colalign):
            alignments.append(colalign[col_idx])
        else:
            # Auto-detect alignment
            has_number = False
            has_text = False
            for cell_lines in col:
                for line in cell_lines:
                    if line:
                        if _isnumber(line):
                            has_number = True
                        else:
                            has_text = True
            
            if has_number and not has_text:
                alignments.append(numalign if numalign != "decimal" else "right")
            else:
                alignments.append(stralign)
    
    # Align columns
    aligned_columns = []
    for col_idx, col in enumerate(columns):
        aligned_col = []
        for cell_lines in col:
            aligned_lines = []
            for line in cell_lines:
                aligned = _align_column([line], alignments[col_idx], col_widths[col_idx])[0]
                aligned_lines.append(aligned)
            aligned_col.append(aligned_lines)
        aligned_columns.append(aligned_col)
    
    # Build output
    lines = []
    
    # Line above
    if fmt.lineabove:
        line = _build_line(fmt.lineabove, col_widths, fmt.padding)
        lines.append(line)
    
    # Header row
    if headers:
        header_cells = []
        for col_idx, h in enumerate(headers):
            aligned = _align_column([h], alignments[col_idx], col_widths[col_idx])[0]
            header_cells.append(aligned)
        
        header_line = _build_row(fmt.headerrow, header_cells, fmt.padding)
        lines.append(header_line)
        
        # Line between header and data
        if fmt.linebetweenheader:
            line = _build_line(fmt.linebetweenheader, col_widths, fmt.padding)
            lines.append(line)
    
    # Data rows
    for row_idx, row in enumerate(expanded_rows):
        # Handle multiline rows
        for line_idx in range(max_lines):
            row_cells = []
            for col_idx, cell_lines in enumerate(row):
                if line_idx < len(cell_lines):
                    row_cells.append(cell_lines[line_idx])
                else:
                    row_cells.append("")
            
            row_line = _build_row(fmt.datarow, row_cells, fmt.padding)
            lines.append(row_line)
        
        # Line between rows
        if fmt.linebetweenrows and row_idx < len(expanded_rows) - 1:
            line = _build_line(fmt.linebetweenrows, col_widths, fmt.padding)
            lines.append(line)
    
    # Line after
    if fmt.lineafter:
        line = _build_line(fmt.lineafter, col_widths, fmt.padding)
        lines.append(line)
    
    # Line below
    if fmt.linebelow:
        line = _build_line(fmt.linebelow, col_widths, fmt.padding)
        lines.append(line)
    
    return "\n".join(lines)


def _build_line(template, col_widths, padding):
    """Build a separator line."""
    if not template:
        return ""
    
    # Handle special templates
    if template.startswith("\\begin{tabular}"):
        # LaTeX format
        cols = "".join("l" * len(col_widths))
        return template.replace("{cols}", cols)
    
    if template.startswith("<"):
        # HTML format
        return template
    
    if template.startswith("{|"):
        # MediaWiki format
        return template
    
    # Standard separator line
    parts = []
    for width in col_widths:
        parts.append("-" * (width + 2 * padding))
    
    # Replace placeholders
    result = template
    result = result.replace("{above}", "-".join(parts))
    result = result.replace("{below}", "-".join(parts))
    
    return result


def _build_row(template, cells, padding):
    """Build a data row."""
    if not template:
        return ""
    
    # Handle special templates
    if template.startswith("<tr"):
        # HTML format
        cell_html = "".join(f"<th>{c}</th>" if "<th>" in template else f"<td>{c}</td>" for c in cells)
        return template.replace("{name}", cell_html).replace("<th></th>", "").replace("<td></td>", "")
    
    if template.startswith("||") or template.startswith("|"):
        # Jira/MediaWiki format
        if template.startswith("||"):
            return "|| " + " || ".join(cells) + " ||"
        else:
            return "| " + " | ".join(cells) + " |"
    
    if template.startswith("\\begin{tabular}"):
        # LaTeX format
        return " & ".join(cells) + " \\\\"
    
    # Standard row format
    if "{name}" in template:
        # Replace {name} with each cell
        sep = template.split("{name}")[1] if len(template.split("{name}")) > 1 else ""
        
        # Build cells with padding
        padded_cells = []
        for cell in cells:
            padded = " " * padding + cell + " " * padding
            padded_cells.append(padded)
        
        # Join with separator
        result = template.split("{name}")[0]
        for i, cell in enumerate(padded_cells):
            result += cell
            if i < len(padded_cells) - 1:
                result += sep
            else:
                result += template.split("{name}")[-1]
        
        return result
    
    return template