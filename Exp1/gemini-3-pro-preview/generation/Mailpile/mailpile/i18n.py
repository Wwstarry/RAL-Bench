import gettext as py_gettext

# A minimal mock of Mailpile's i18n module which wraps gettext
# In a real scenario, this would load translations based on config.

def gettext(message):
    return message

def ngettext(singular, plural, n):
    if n == 1:
        return singular
    return plural

# Common alias
_ = gettext

class I18nManager:
    def __init__(self):
        self.lang = 'en_US'

    def activate(self, lang):
        self.lang = lang
        # In real code, this would load .mo files
        pass

    def gettext(self, message):
        return message