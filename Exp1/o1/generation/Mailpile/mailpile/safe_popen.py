import subprocess

def run_command(args, input_data=None, capture_stdout=True, capture_stderr=True):
    """
    Safely run a subprocess command and optionally capture stdout/stderr.
    
    :param args: A list of command arguments, e.g. ['echo', 'Hello']
    :param input_data: Optional data to be passed as the command's stdin
    :param capture_stdout: If True, capture stdout
    :param capture_stderr: If True, capture stderr
    :return: (exit_code, stdout_data, stderr_data)
    """
    stdout_pipe = subprocess.PIPE if capture_stdout else None
    stderr_pipe = subprocess.PIPE if capture_stderr else None

    try:
        process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE if input_data else None,
            stdout=stdout_pipe,
            stderr=stderr_pipe,
            universal_newlines=True
        )
        out, err = process.communicate(input_data)
        returncode = process.returncode
    except OSError as e:
        return 1, '', str(e)

    return returncode, out if out else '', err if err else ''