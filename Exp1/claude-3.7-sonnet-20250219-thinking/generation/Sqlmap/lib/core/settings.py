#!/usr/bin/env python

"""
Copyright (c) 2023 SQLmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import os
import platform
import sys

# sqlmap version
VERSION = "1.7.2.0#dev"
TYPE = "dev" if VERSION.count(".") > 2 and "#" in VERSION else "stable"
TYPE_COLORS = {"dev": 33, "stable": 90}
VERSION_STRING = VERSION.split("#")[0] if "#" in VERSION else VERSION

# sqlmap website
DESCRIPTION = "Automatic SQL injection and database takeover tool"
SITE = "http://sqlmap.org"
GIT_REPOSITORY = "https://github.com/sqlmapproject/sqlmap.git"

# Platform and Python version
IS_WIN = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MAC = platform.system() == "Darwin"

UNICODE_ENCODING = sys.getfilesystemencoding() or "utf8"

# Defaults
DEFAULTS = {
    "agent": "",
    "dbms": "",
    "testParameter": "",
    "timeout": 30,
    "threads": 1,
    "verbose": 1,
    "tech": "BEUSTQ",
}

# SQLmap server response codes
SQLMAP_FAILURE_EXIT_CODE = 1
SQLMAP_CONNECTION_RETRY_EXIT_CODE = 2
SQLMAP_ERROR_EXIT_CODE = 3
SQLMAP_WARNING_EXIT_CODE = 4
SQLMAP_SUCCESS_EXIT_CODE = 0