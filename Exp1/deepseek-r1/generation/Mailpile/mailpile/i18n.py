"""Internationalization helper."""
import gettext
import os
from typing import Optional, Callable

class I18N:
    """Simple gettext wrapper for Mailpile."""
    
    _translations: Dict[str, gettext.GNUTranslations] = {}
    _current_language: Optional[str] = None
    _default_domain: str = 'mailpile'
    
    @classmethod
    def set_language(cls, language: str, 
                    locale_dir: Optional[str] = None,
                    domain: str = 'mailpile') -> bool:
        """Set current language for translations."""
        cls._default_domain = domain
        
        if not locale_dir:
            # Try to find locale directory
            base_dir = os.path.dirname(os.path.dirname(__file__))
            locale_dir = os.path.join(base_dir, 'locale')
            
        if not os.path.exists(locale_dir):
            return False
            
        try:
            translation = gettext.translation(
                domain,
                localedir=locale_dir,
                languages=[language],
                fallback=True
            )
            cls._translations[language] = translation
            cls._current_language = language
            return True
        except (IOError, OSError):
            return False
            
    @classmethod
    def get_translator(cls, language: Optional[str] = None) -> Callable:
        """Get translation function for specified or current language."""
        if language is None:
            language = cls._current_language
            
        if language and language in cls._translations:
            return cls._translations[language].gettext
        return gettext.NullTranslations().gettext
        
    @classmethod
    def gettext(cls, message: str) -> str:
        """Translate message using current language."""
        translator = cls.get_translator()
        return translator(message)
        
    @classmethod
    def ngettext(cls, singular: str, plural: str, n: int) -> str:
        """Translate plural message."""
        if cls._current_language and cls._current_language in cls._translations:
            return cls._translations[cls._current_language].ngettext(singular, plural, n)
        return singular if n == 1 else plural

# Convenience functions
_ = I18N.gettext
_n = I18N.ngettext

def set_language(language: str, locale_dir: Optional[str] = None) -> bool:
    """Set current language for translations."""
    return I18N.set_language(language, locale_dir)

def gettext(message: str) -> str:
    """Translate message."""
    return I18N.gettext(message)

def ngettext(singular: str, plural: str, n: int) -> str:
    """Translate plural message."""
    return I18N.ngettext(singular, plural, n)