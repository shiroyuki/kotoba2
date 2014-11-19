import logging
import re

try:
    from html.parser import HTMLParser
except ImportError as python2_detected:
    from HTMLParser import HTMLParser

from kotoba2.common import MapCollection
from kotoba2.definition import HTML as HTMLDefinition

logging.basicConfig(level = logging.WARN)

FEATURE_JUMPING_TOKENIZER = True

class AttributeSyntaxError(Exception): pass

class Token(object):
    def __init__(self, data):
        self._data = data

    @property
    def data(self):
        return self._data

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return self.data

    def __repr__(self):
        return '<{} ({}...)>'.format(self.__class__.__name__, self.data[:10].encode('ascii', errors = 'backslashreplace'))

class DataToken(Token): pass
class CommentToken(Token): pass
class HTMLDeclarationToken(Token): pass
class UnknownDeclarationToken(Token): pass

class ElementToken(Token):
    logger = logging.getLogger('kotoba2.lexer.ElementToken')
    logger.setLevel(logging.ERROR)

    def __init__(self, data = None, name = None, attributes = {}):
        self._data = ''
        self._name = name
        self._attributes = MapCollection(attributes or {})

    @property
    def name(self):
        return self._name

    @property
    def attributes(self):
        return self._attributes

    def __repr__(self):
        return '<{} ({}...)>'.format(self.__class__.__name__, self.name, self.attributes)

class CloseTagToken(ElementToken): pass
class OpenTagToken(ElementToken):  pass
class SoloTagToken(ElementToken):  pass
class IrregularTagToken(ElementToken):  pass

class TokenFactory(object):
    logger = logging.getLogger('kotoba2.lexer.TokenFactory')
    logger.setLevel(logging.DEBUG)

    @staticmethod
    def create(data):
        token_class, parameters = data

        TokenFactory.logger.debug('Creating {}'.format(token_class.__name__))
        TokenFactory.logger.debug('using parameters {}'.format(parameters))

        token = token_class(**parameters)

        TokenFactory.logger.debug('result {}'.format(type(token)))

        return token

class InternalLexer(HTMLParser):
    logger = logging.getLogger('kotoba2.lexer.InternalLexer')
    logger.setLevel(logging.WARN)

    def __init__(self):
        HTMLParser.__init__(self)
        self.tokens = []

    def handle_starttag(self, tag, attrs):
        InternalLexer.logger.debug('OPEN TAG [{}]'.format(tag))
        self.tokens.append((
            OpenTagToken,
            {
                'name':       tag,
                'attributes': attrs
            }
        ))

    def handle_startendtag(self, tag, attrs):
        InternalLexer.logger.debug('SOLO TAG [{}]'.format(tag))
        self.tokens.append((
            SoloTagToken,
            {
                'name':       tag,
                'attributes': attrs
            }
        ))

    def handle_endtag(self, tag):
        InternalLexer.logger.debug('CLOSE TAG [{}]'.format(tag))
        self.tokens.append((
            CloseTagToken,
            {
                'name': tag
            }
        ))

    def handle_data(self, data):
        sample_data = data.strip()

        if not sample_data:
            InternalLexer.logger.debug(u'EMPTY DATA')
            return

        InternalLexer.logger.debug(u'DATA [{}]'.format(data))
        self.tokens.append((
            DataToken,
            {
                'data': data
            }
        ))

    def handle_comment(self, data):
        InternalLexer.logger.debug(u'COMMENT [{}]'.format(data))
        self.tokens.append((
            CommentToken,
            {
                'data': data
            }
        ))

    def handle_decl(self, decl):
        InternalLexer.logger.debug('DOCTYPE [{}]'.format(decl))
        self.tokens.append((
            HTMLDeclarationToken,
            {
                'data': decl
            }
        ))

    def unknown_decl(self, data):
        InternalLexer.logger.debug('UNKNOWN [{}]'.format(data))
        self.tokens.append((
            UnknownDeclarationToken,
            {
                'data': data
            }
        ))

class Lexer(object):
    """ HTML Lexer
    """

    logger = logging.getLogger('kotoba2.lexer.Lexer')
    logger.setLevel(logging.DEBUG)

    def __init__(self, internal_lexer_class = None):
        self.internal_lexer_class = internal_lexer_class or InternalLexer

    def tokenize(self, data):
        internal_lexer = self.internal_lexer_class()
        internal_lexer.feed(data.decode('utf-8', errors='backslashreplace'))

        return self._tokenize_to_objectized_tokens(internal_lexer.tokens)

    def _tokenize_to_objectized_tokens(self, raw_tokens):
        objectized_tokens = []

        for raw_token in raw_tokens:
            objectized_token = TokenFactory.create(raw_token)

            objectized_tokens.append(objectized_token)

        return objectized_tokens

