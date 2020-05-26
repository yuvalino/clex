# Filename: clex.py
# Description: Simple lexical analasys for programming syntax

import io
import sys
import six


# Exceptions


class UnexpectedToken(Exception):
    def __init__(self, token):
        self.token = token


class UnexpectedEOFError(Exception):
    pass


class UnexpectedEOLError(Exception):
    def __init__(self, eol):
        self.eol = eol


# Classes


class clex(object):
    """
    Simple lexical analasys for programming syntax.
    """

    def __init__(self, instream):
        """
        Initialize with input stream or string.
        """
        if isinstance(instream, six.string_types):
            instream = io.StringIO(six.text_type(instream))
        self._instream = instream
        self._tokenstack = []
        
        self.escape = '\\'
        self.quotes = '"\''
        self.whitespace = ' \t\r\n'
        
        self.oneline_commenters = ['//']
        self.multiline_commenters = [['/*', '*/']]
        
        # [ firstchars, morechars ]
        self.tokenchars = ['abcdfeghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_', '0123456789']
       
        # [ firstchars, oncechars ]
        self.numchars = ['0123456789', '.', '-+']
    
        self.eof = ''

        self.debug = 0
        self.logger = sys.stdout.write
        
        self._oops = []
    
    def get_token(self):
        """
        Get next token.
        Pops a token from tokens stack if available, else reads from input.
        """
        if len(self._tokenstack):
            return self._tokenstack.pop()
        return self.read_token()
    
    def read_token(self):
        """
        Reads a token from input.
        """
        # Skip whitespaces and comments
        while True:
            token = self._readone()
            
            if token == '':
                return self.eof

            # Skip whitespaces
            ntoken = self._findtokens(token, self.whitespace)
            if ntoken is not None:
                continue

            # Skip oneline comments
            ntoken = self._findtokens(token, self.oneline_commenters)
            if ntoken is not None:
                self._consumeuntil('\n', allow_eof=True, allow_eol=True)
                continue

            # Skip multiline comments
            ntoken = self._findtokens(token, [x[0] for x in self.multiline_commenters])
            if ntoken is not None:
                self._consumeuntil([x[1] for x in self.multiline_commenters if x[0] == ntoken][0], allow_eof=True, allow_eol=True)
                continue
            
            # Find strings
            ntoken = self._findtokens(token, self.quotes)
            if ntoken is not None:
                return self._consumestring(ntoken)

            # Find keywords
            if token in self.tokenchars[0]:
                while True:
                    ntoken = self._readone()
                    if not len(ntoken) or (ntoken not in self.tokenchars[0] and ntoken not in self.tokenchars[1]):
                        self._oops.append(ntoken)
                        return token
                    token = token + ntoken

            # Find numbers
            if token in self.numchars[0] or token in self.numchars[2]:
                while True:
                    ntoken = self._readone()
                    if not len(ntoken) or (ntoken not in self.numchars[0] and ntoken not in self.numchars[1]):
                        self._oops.append(ntoken)
                        return token
                    if ntoken in self.numchars[1] and ntoken in token:
                        raise UnexpectedToken(ntoken)
                    token = token + ntoken

            # Return single keywords
            return token
   
    def push_token(self, token):
        """
        Push token to tokens stack.
        """
        self._tokenstack.append(token)

    def _log(self, msg):
        """
        Logs a message if debug is on.
        """
        if self.debug:
            self.logger(msg)

    def _readone(self, exception=None):
        """
        Read one character from input.
        May possible acquire a character from `_oops` if available.
        Data member `oops` is used incase characters were read but needs to be pushed back to stream again.
        """
        if len(self._oops):
            one = self._oops.pop(0)
        else:
            one = self._instream.read(1)
            if not len(one) and exception:
                raise exception
        return one

    def _findtokens_pass(self, token, tokens):
        """
        Finds `token` in `tokens` list.
        If found, returns `None, True`.
        If not found, returns `<remaining>, False`.
        List `remaining` contains all entries from `tokens` that start with the given token.
        This way, multiple passes can be done until either token was found or no remaining tokens are left.
        """
        remaining = tokens[:]
        for i,w in enumerate(tokens[::-1]):
            if w == token:
                return None, True
            if not w.startswith(token):
                remaining.pop(len(tokens)-i-1)
        return remaining, False

    def _findtokens(self, token, tokens):
        """
        Finds a token in `tokens`, with initial token `token`.
        This function will further read from input until either token is finally found, not found or EOF is reached.
        Returns the found token or None if not found.
        If `None` is returned, `_oops` is adjusted accordingly to restore previous stream state.
        """
        if not len(tokens):
            return token, False
        if isinstance(tokens, str):
            tokens = [x for x in tokens]
        tokens, found = self._findtokens_pass(token, tokens)
        if found:
            return token
        if not len(tokens):
            return None
        while len(tokens):
            one = self._readone()
            if not len(one):
                self._oops.extend(x for x in token[1:])
                self._oops.append(one)
                return None
            token = token + one
            tokens, found = self._findtokens_pass(token, tokens)
            if found:
                return token
        self._oops.extend(x for x in token[1:])
        return None


    def _consumeuntil(self, value, allow_eof, allow_eol):
        """
        Consume characters from input until `value` has been consumed (including).
        Switches `allow_eof`, `allow_eol` mandate whether EOF and EOL mid-consumption is legal or not.
        If EOF is reached and `allow_eof` is True, returns all consumed data so far. Else raises `UnexpectedEOFError`.
        If EOL is reached and `allow_eol` is True or EOL is part of `value`, it is consumed like regular input. Else raises `UnexpectedEOLError`.
        """
        token = ''
        while not token.endswith(value):
            curr = self._readone()
            if not len(curr):
                if allow_eof:
                    return token
                raise UnexpectedEOFError()
            if not allow_eol and curr in '\r\n' and curr not in value:
                raise UnexpectedEOLError(curr)
            token = token + curr
        return token

    def _consumestring(self, quote):
        """
        Consumes a string starting with quote character `quote`.
        Returns the string (including quotes).
        """
        token = quote
        while True:
            curr = self._readone()
            if not len(curr):
                raise UnexpectedEOFError()
            if curr in '\r\n':
                raise UnexpectedEOLError(curr)
            if curr == quote and token[-1] not in self.escape:
                return token + curr
            token = token + curr


def split(instream):
    """
    Split `instream` to a full list of tokens.
    """
    cl = clex(instream)
    items = []
    while not len(items) or items[-1] != cl.eof:
        items.append(cl.get_token())
    items.pop()
    return items
