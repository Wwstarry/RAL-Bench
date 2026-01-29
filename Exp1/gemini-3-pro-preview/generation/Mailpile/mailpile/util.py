import re
import hashlib

def CleanText(text, clean_html=True, clean_whitespace=True):
    """
    Cleans text by removing HTML tags and normalizing whitespace.
    """
    if not text:
        return ""
        
    if clean_html:
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Decode HTML entities (simplified)
        text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

    if clean_whitespace:
        # Replace multiple spaces/newlines with single space
        text = re.sub(r'\s+', ' ', text).strip()
        
    return text

def int2b36(n):
    """
    Converts an integer to a base36 string.
    """
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
    if n < 0: raise ValueError("Negative numbers not supported")
    if n == 0: return '0'
    
    res = ''
    while n != 0:
        n, r = divmod(n, 36)
        res = alphabet[r] + res
    return res

def b362int(s):
    """
    Converts a base36 string to an integer.
    """
    return int(s, 36)

def md5_hex(data):
    """
    Returns the MD5 hex digest of the input data.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.md5(data).hexdigest()