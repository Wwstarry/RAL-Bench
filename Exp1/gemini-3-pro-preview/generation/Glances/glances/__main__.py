import argparse
import datetime
import sys
import psutil
from glances import __version__

def main():
    parser = argparse.ArgumentParser(
        prog="glances",
        description="Glances system monitoring tool (Mock)"
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"Glances v{__version__}"
    )
    parser.add_argument(
        "--stdout-csv",
        help="Output statistics in CSV format to stdout. Requires a comma-separated list of fields."
    )

    args = parser.parse_args()

    # If --stdout-csv is not provided, we exit with error as we don't support TUI
    if args.stdout_csv is None:
        sys.stderr.write("Error: --stdout-csv argument is required.\n")
        sys.exit(1)

    fields = [f.strip() for f in args.stdout_csv.split(',')]
    
    # Collect stats
    # We use a small interval (0.1s) to get accurate CPU percentages for this one-shot execution.
    try:
        cpu_times = psutil.cpu_times_percent(interval=0.1)
        # Calculate total CPU usage as 100% - idle%
        cpu_total = 100.0 - cpu_times.idle
        
        mem = psutil.virtual_memory()
        
        # Load Average handling
        if hasattr(psutil, "getloadavg"):
            load_avg = psutil.getloadavg()[0]
        else:
            try:
                import os
                load_avg = os.getloadavg()[0]
            except (AttributeError, OSError):
                load_avg = 0.0

        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        output = []
        for field in fields:
            if field == 'now':
                output.append(now_str)
            elif field == 'cpu.user':
                output.append(str(cpu_times.user))
            elif field == 'cpu.total':
                output.append(str(cpu_total))
            elif field == 'mem.used':
                output.append(str(mem.used))
            elif field == 'load':
                output.append(str(load_avg))
            else:
                sys.stderr.write(f"Error: Unknown field '{field}'\n")
                sys.exit(1)
        
        print(','.join(output))
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()