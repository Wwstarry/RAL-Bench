import gettext

def gettext_passthrough(message):
    """
    A passthrough for gettext, useful for testing and stubbing.
    """
    return gettext.gettext(message)