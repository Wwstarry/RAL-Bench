# -*- coding: utf-8 -*-

VERSION = "1.0.0"
DESCRIPTION = "Advanced SQL injection testing tool"
AUTHOR = "sqlmap developers"

# Default settings
DEFAULT_USER_AGENT = "sqlmap/1.0"
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3

# Supported databases
SUPPORTED_DBMS = [
    "MySQL",
    "PostgreSQL",
    "Microsoft SQL Server",
    "Oracle",
    "SQLite",
    "IBM DB2",
    "SAP MaxDB",
    "Sybase",
    "Informix",
    "MongoDB",
    "CouchDB",
    "Firebird",
    "Vertica",
    "Presto",
    "Drizzle",
    "Apache Derby",
    "H2",
    "HSQLDB",
    "Mckoi",
    "Virtuoso",
    "OpenEdge",
    "Frontbase",
    "Interleaf",
    "Altibase",
    "MimerSQL",
    "Primebase",
    "Raima",
    "Unify",
    "Exasol",
]

# Injection techniques
INJECTION_TECHNIQUES = {
    "B": "Boolean-based blind",
    "E": "Error-based",
    "U": "UNION query-based",
    "S": "Stacked queries",
    "T": "Time-based blind",
    "C": "Inline queries",
}

# Risk levels
RISK_LEVELS = {
    1: "Low",
    2: "Medium",
    3: "High",
}

# Detection levels
DETECTION_LEVELS = {
    1: "Minimal",
    2: "Normal",
    3: "Advanced",
    4: "Extensive",
    5: "Exhaustive",
}