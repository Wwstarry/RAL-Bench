import re
from pygments.token import Token, Error, Text

def lex(code, lexer):
    """
    Lex code with the given lexer and return an iterable of tokens.
    """
    return lexer.get_tokens(code)

class Lexer(object):
    def __init__(self, **options):
        self.options = options
        self.stripnl = options.get('stripnl', True)
        self.stripall = options.get('stripall', False)
        self.ensurenl = options.get('ensurenl', True)
        self.tabsize = options.get('tabsize', 0)
        self.encoding = options.get('encoding', 'utf-8')

    def get_tokens(self, text):
        """
        Return an iterable of (tokentype, value) pairs.
        """
        if not isinstance(text, str):
            # Simple decoding if bytes are passed
            text = text.decode(self.encoding)
            
        # Preprocessing
        if self.stripall:
            text = text.strip()
        elif self.stripnl:
            text = text.strip('\n')
            
        if self.ensurenl and not text.endswith('\n'):
            text += '\n'

        for type, value in self.get_tokens_unprocessed(text):
            yield type, value

    def get_tokens_unprocessed(self, text):
        """
        Return an iterable of (index, tokentype, value).
        Must be implemented by subclasses.
        """
        raise NotImplementedError

class RegexLexer(Lexer):
    """
    Base class for regex-based lexers.
    """
    tokens = {} # To be overridden

    def get_tokens_unprocessed(self, text):
        """
        Split ``text`` into (tokentype, text) pairs.
        """
        # Process tokens definition (compiling regexes)
        if not hasattr(self, '_tokens'):
            self._tokens = {}
            for state, items in self.tokens.items():
                self._tokens[state] = []
                for item in items:
                    # item is (regex, token, new_state) or (regex, token)
                    regex = item[0]
                    token = item[1]
                    new_state = item[2] if len(item) > 2 else None
                    
                    # Handle 'include'
                    if regex == 'include':
                        # Simplified include handling: we assume it's resolved 
                        # or we just skip for this basic implementation if not needed
                        # For full compat, we'd recurse. 
                        # Here we assume the subclasses provided are flat or we implement basic include.
                        if token in self.tokens:
                            self._tokens[state].extend(self._process_state(self.tokens[token]))
                        continue

                    if isinstance(token, (list, tuple)):
                        # Combined tokens (bygroups)
                        pass 
                    
                    self._tokens[state].append((re.compile(regex, re.VERBOSE | re.DOTALL | re.MULTILINE), token, new_state))

        # Lexing loop
        pos = 0
        statestack = ['root']
        statetokens = self._tokens['root']
        
        while True:
            match = None
            for regex, token, new_state in statetokens:
                match = regex.match(text, pos)
                if match:
                    # If we have a match
                    value = match.group()
                    if token is not None:
                        yield token, value
                    
                    pos = match.end()
                    
                    if new_state is not None:
                        if new_state == '#pop':
                            statestack.pop()
                        elif new_state == '#push':
                            statestack.append(statestack[-1])
                        else:
                            statestack.append(new_state)
                        statetokens = self._tokens[statestack[-1]]
                    break
            
            if not match:
                # No match found
                if pos < len(text):
                    yield Error, text[pos]
                    pos += 1
                else:
                    break

    def _process_state(self, items):
        # Helper to compile a list of items (used for include)
        processed = []
        for item in items:
            regex = item[0]
            token = item[1]
            new_state = item[2] if len(item) > 2 else None
            if regex == 'include':
                if token in self.tokens:
                    processed.extend(self._process_state(self.tokens[token]))
            else:
                processed.append((re.compile(regex, re.VERBOSE | re.DOTALL | re.MULTILINE), token, new_state))
        return processed

def include(state):
    return 'include', state