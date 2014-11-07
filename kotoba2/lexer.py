import logging
import re
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
        return '<{} ({}...)>'.format(self.__class__.__name__, data[:10])

class DataToken(Token): pass

class ElementToken(Token):
    logger = logging.getLogger('kotoba2.lexer.ElementToken')

    _re_element = re.compile('</?(?P<name>[^\s>]+)(?P<attributes>[^>]*)/?>')

    def __init__(self, data):
        self.logger.setLevel(logging.WARN)
        
        self._data = data.strip()

        main_parts = ElementToken._re_element.search(self._data).groupdict()

        self._name = main_parts['name']
        self._attributes = MapCollection()

        raw_attributes = main_parts['attributes'].strip()

        if not raw_attributes:
            return

        attributes = self.analyze_raw_attributes(raw_attributes)

        self._attributes.update(attributes)

    @property
    def name(self):
        return self._name

    @property
    def attributes(self):
        return self._attributes

    def analyze_raw_attributes(self, raw_attributes):
        iterating_size = len(raw_attributes)
        cursor = 0
        previous_cursor = None
        attributes = {}

        self.logger.debug('Analyze the attribute [{}]'.format(raw_attributes))
        
        while cursor < iterating_size:
            name  = None
            value = None

            try:
                if previous_cursor == cursor:
                    raise RuntimeError('Infinite loop detected while analyzing [{}]'.format(raw_attributes))

                previous_cursor = cursor

                self.logger.debug('cursor = {}'.format(cursor))

                eq_pos = raw_attributes.index('=', cursor)

                self.logger.debug('eq_pos = {}'.format(eq_pos))

                name   = raw_attributes[cursor:eq_pos]
                cursor = eq_pos + 2

                self.logger.debug('name = ' + name)
       
                ed_q_pos = raw_attributes.find('"', cursor)

                if ed_q_pos < cursor:
                    ed_q_pos = raw_attributes.index('\'', cursor)

                self.logger.debug('ed_q_pos = {}'.format(ed_q_pos))

                value  = raw_attributes[cursor:ed_q_pos]
                cursor = ed_q_pos + 2

                self.logger.debug('value = ' + value)

                if name in attributes:
                    raise RuntimeError('Infinite loop detected while analyzing [{}]'.format(raw_attributes))
            except ValueError as error:
                if not name:
                    break

            attributes[name] = value if value else True

        return attributes

class CloseTagToken(ElementToken): pass
class OpenTagToken(ElementToken):  pass
class SoloTagToken(ElementToken):  pass
class IrregularTagToken(ElementToken):  pass

class TokenFactory(object):
    logger = logging.getLogger('kotoba2.lexer.TokenFactory')

    _re_element_name = re.compile('^</?(?P<name>[^\s>]+)')
    _re_special_element = re.compile('[-:_?]')

    @staticmethod
    def make(data):
        sample_data = data.strip()
        sample_name = None
        definition  = None
        TokenClass  = DataToken
        name_matches = TokenFactory._re_element_name.search(sample_data)

        if sample_data and name_matches:
            sample_name = name_matches.groupdict()['name']
            definition  = HTMLDefinition[sample_name] if sample_name in HTMLDefinition else None

        # Empty
        if not sample_data:
            return None

        # Sepcial HTML Element
        elif sample_name and TokenFactory._re_special_element.search(sample_name):
            TokenClass = IrregularTagToken

        # Close tag
        elif sample_data[0:2] == '</' and sample_data[-1] == '>':
            TokenClass = CloseTagToken

        # Solo tag
        elif (definition and definition.single) or (sample_data[0] == '<' and sample_data[-2:] == '/>'):
            TokenClass = SoloTagToken

        # Open tag
        elif sample_data[0] == '<' and sample_data[-1] == '>':
            TokenClass = OpenTagToken

        return TokenClass(data)

class Lexer(object):
    """ HTML Lexer
    """

    logger = logging.getLogger('kotoba2.lexer.Lexer')

    _line_ending_symbol       = '__T_LF__'
    _comment_op_symbol        = chr(240)
    _comment_ed_symbol        = chr(241)
    _re_line_ending_native    = re.compile('(\r\n|\n)')
    _re_line_ending_symbol    = re.compile(_line_ending_symbol)
    _re_comment_op            = re.compile('<!--')
    _re_comment_ed            = re.compile('-->')
    _re_comment_op_symbol     = re.compile(_comment_op_symbol)
    _re_comment_ed_symbol     = re.compile(_comment_ed_symbol)
    _re_comment               = re.compile('{}[^{}]*{}'.format(_comment_op_symbol, _comment_ed_symbol, _comment_ed_symbol))
    _re_definition            = re.compile('<![^>]*>')
    _re_kind_tag              = re.compile('^(</?[^!>][^>]*>)')
    _re_kind_tag_script_open  = re.compile('^(<(script|style)[^>]*>)')
    _re_kind_tag_script_close = re.compile('^(</(script|style)[^>]*>)')

    def tokenize(self, data):
        data = self._optimized_input(data)
        string_tokens = self._tokenize_to_string_tokens(data)

        return self._tokenize_to_objectized_tokens(string_tokens)

    def _optimized_input(self, data):
        data = self._re_line_ending_native.sub(self._line_ending_symbol, data)
        data = self._re_comment_op.sub(self._comment_op_symbol, data)
        data = self._re_comment_ed.sub(self._comment_ed_symbol, data)
        data = self._re_comment.sub('', data)
        data = self._re_definition.sub('', data)
        data = self._re_comment_op_symbol.sub('<!--', data)
        data = self._re_comment_ed_symbol.sub('-->', data)
        data = self._re_line_ending_symbol.sub('\n', data)

        return data

    def _tokenize_to_objectized_tokens(self, string_tokens):
        objectized_tokens = []

        for string_token in string_tokens:
            objectized_token = TokenFactory.make(string_token)

            if not objectized_token:
                continue

            objectized_tokens.append(objectized_token)

        return objectized_tokens

    def _tokenize_to_string_tokens(self, data):
        global FEATURE_JUMPING_TOKENIZER

        default_lookahead_length = 1024
        lookahead_length     = default_lookahead_length
        iterating_position   = 0
        cutoff_head_position = None

        data_length = len(data)
        tokens      = []

        while iterating_position < data_length:
            if FEATURE_JUMPING_TOKENIZER:
                # Variable look-ahead buffer size
                try:
                    iterating_position = data.index('<', iterating_position, iterating_position + lookahead_length)
                    lookahead_length   = data.index('>', iterating_position) - iterating_position + 1
                except ValueError as error:
                    lookahead_length = default_lookahead_length

            cutoff_buffer      = None
            lookahead_buffer   = data[iterating_position:iterating_position + lookahead_length]
            previous_token     = tokens[-1] if tokens else None
            is_script_tag_open = previous_token and self._extract_tag_script_open(previous_token)

            tag_matches = self._extract_tag(lookahead_buffer)
            
            #self.logger.debug('LOOKAHEAD BUFFER: {} (maybe truncated)'.format(lookahead_buffer[:70]))

            if tag_matches:
                content_buffer  = data[cutoff_head_position:iterating_position]
                tag_buffer      = tag_matches.groups()[0]
                tag_buffer_size = len(tag_buffer)
                next_is_close_script_tag = self._extract_tag_script_close(tag_buffer)

                self.logger.debug('MATCHED: {}'.format(tag_matches.groups()))
                self.logger.debug('EXTRA CONDITIONS: {}, {}'.format(
                    '-OPEN_SCRIPT' if not is_script_tag_open else '+OPEN_SCRIPT',
                    '+CLOSE_SCRIPT' if next_is_close_script_tag else '-CLOSE_SCRIPT'
                ))
            
                if not is_script_tag_open or next_is_close_script_tag:
                    # Store the previous token
                    tokens.append(content_buffer)
                    tokens.append(tag_buffer)

                    cutoff_head_position = iterating_position + tag_buffer_size

                    # Forward the iterating position
                    iterating_position = cutoff_head_position

                    self.logger.debug('FLUSHED CONTENT: {} (maybe truncated)'.format(content_buffer.strip()[:70]))
                    self.logger.debug('FLUSHED ELEMENT: {}'.format(tag_buffer.strip()))

                    continue

            elif cutoff_head_position == None:
                cutoff_head_position = iterating_position

            iterating_position += 1

        if cutoff_head_position != iterating_position:
            cutoff_buffer = data[cutoff_head_position:]
            tokens.append(cutoff_buffer)

        return tokens

    def _extract_tag(self, current_buffer):
        return self._re_kind_tag.search(current_buffer)

    def _extract_tag_script_open(self, current_buffer):
        return self._re_kind_tag_script_open.search(current_buffer)

    def _extract_tag_script_close(self, current_buffer):
        return self._re_kind_tag_script_close.search(current_buffer)
