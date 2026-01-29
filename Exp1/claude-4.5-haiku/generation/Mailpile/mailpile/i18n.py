"""Internationalization utilities for Mailpile."""

import gettext
from typing import Optional, Callable


class I18n:
    """Internationalization helper."""
    
    _translator: Optional[gettext.GNUTranslations] = None
    _fallback_func: Optional[Callable[[str], str]] = None
    
    @classmethod
    def set_translator(cls, translator: Optional[gettext.GNUTranslations]) -> None:
        """
        Set the translator instance.
        
        Args:
            translator: gettext translator or None
        """
        cls._translator = translator
    
    @classmethod
    def set_fallback(cls, func: Optional[Callable[[str], str]]) -> None:
        """
        Set fallback translation function.
        
        Args:
            func: Fallback function or None
        """
        cls._fallback_func = func
    
    @classmethod
    def gettext(cls, message: str) -> str:
        """
        Translate a message.
        
        Args:
            message: Message to translate
            
        Returns:
            Translated message
        """
        if cls._translator:
            return cls._translator.gettext(message)
        if cls._fallback_func:
            return cls._fallback_func(message)
        return message
    
    @classmethod
    def ngettext(cls, singular: str, plural: str, n: int) -> str:
        """
        Translate a message with plural form.
        
        Args:
            singular: Singular form
            plural: Plural form
            n: Count
            
        Returns:
            Translated message
        """
        if cls._translator:
            return cls._translator.ngettext(singular, plural, n)
        return plural if n != 1 else singular


def gettext_passthrough(message: str) -> str:
    """
    Passthrough gettext function for marking strings.
    
    Args:
        message: Message to mark for translation
        
    Returns:
        The message unchanged
    """
    return message


def _(message: str) -> str:
    """
    Translate a message using I18n.
    
    Args:
        message: Message to translate
        
    Returns:
        Translated message
    """
    return I18n.gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """
    Translate a message with plural form.
    
    Args:
        singular: Singular form
        plural: Plural form
        n: Count
        
    Returns:
        Translated message
    """
    return I18n.ngettext(singular, plural, n)