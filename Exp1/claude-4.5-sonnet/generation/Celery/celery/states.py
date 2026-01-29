"""
Task states
"""

# Task states
PENDING = 'PENDING'
STARTED = 'STARTED'
SUCCESS = 'SUCCESS'
FAILURE = 'FAILURE'
RETRY = 'RETRY'
REVOKED = 'REVOKED'

# State precedence
PRECEDENCE = [
    PENDING,
    STARTED,
    RETRY,
    FAILURE,
    SUCCESS,
    REVOKED,
]

# Ready states
READY_STATES = frozenset([SUCCESS, FAILURE, REVOKED])

# Unready states
UNREADY_STATES = frozenset([PENDING, STARTED, RETRY])

# Exception states
EXCEPTION_STATES = frozenset([FAILURE, RETRY, REVOKED])

# Propagate states
PROPAGATE_STATES = frozenset([FAILURE, REVOKED])