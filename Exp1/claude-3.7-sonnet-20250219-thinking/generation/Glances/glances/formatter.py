import csv
import io

def format_csv(stats, fields):
    """Format stats as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    row = []
    unknown_fields = []
    
    for field in fields:
        if field == 'now':
            row.append(stats['now'])
        elif '.' in field:
            main_field, sub_field = field.split('.')
            if main_field in stats and sub_field in stats[main_field]:
                row.append(stats[main_field][sub_field])
            else:
                unknown_fields.append(field)
        else:
            if field in stats:
                row.append(stats[field])
            else:
                unknown_fields.append(field)
    
    if unknown_fields:
        raise ValueError(f"Unknown fields: {', '.join(unknown_fields)}")
    
    writer.writerow(row)
    return output.getvalue().strip()