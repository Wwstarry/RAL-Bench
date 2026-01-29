VERSION = "1.8#dev"
DESCRIPTION = "A pure Python reimplementation of sqlmap's CLI"
USAGE = "python sqlmap.py [options]"

BASIC_HELP_MSG = f"""
Usage: {USAGE}

sqlmap: a pure Python CLI-driven SQL injection testing tool (mock)

Options:
  --version             Show program's version number and exit
  -h, --help            Show basic help message and exit
  -hh                   Show advanced help message and exit

  Target:
    At least one of these options has to be provided to define the
    target(s)

    -u URL, --url=URL   Target URL (e.g. "http://www.site.com/vuln.php?id=1")
"""

ADVANCED_HELP_MSG = BASIC_HELP_MSG + """
  Request:
    These options can be used to specify how to connect to the target URL

    --data=DATA         Data string to be sent through POST
    --cookie=COOKIE     HTTP Cookie header value

  Injection:
    These options can be used to specify which parameters to test for,
    provide custom injection payloads and optional tampering scripts

    -p TESTPARAMETER    Testable parameter(s)

(This is a partial, mocked help message)
"""