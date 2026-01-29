"""
Thread utilities.
"""

try:
    from threading import local
except ImportError:
    from dummy_threading import local


class LocalStack:
    """Thread-local stack."""
    
    def __init__(self):
        self._local = local()
        
    def push(self, obj):
        """Push item onto stack."""
        rv = getattr(self._local, "stack", None)
        if rv is None:
            self._local.stack = rv = []
        rv.append(obj)
        return rv
        
    def pop(self):
        """Pop item from stack."""
        stack = getattr(self._local, "stack", None)
        if stack is None:
            return None
        elif len(stack) == 1:
            del self._local.stack
            return stack[-1]
        else:
            return stack.pop()
            
    def top(self):
        """Get top item without removing."""
        stack = getattr(self._local, "stack", None)
        if stack:
            return stack[-1]
        return None