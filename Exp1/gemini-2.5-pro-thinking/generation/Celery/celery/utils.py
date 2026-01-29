import uuid

def gen_unique_id():
    """Generate a unique id, suitable for a task ID."""
    return uuid.uuid4().hex