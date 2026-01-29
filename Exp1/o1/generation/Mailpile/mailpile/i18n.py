def gettext_passthrough(s):
    """
    A simple i18n helper which just returns the string unchanged for now.
    
    :param s: String to translate
    :return: Unchanged string
    """
    return s

# Shortcut function typically named _
_ = gettext_passthrough