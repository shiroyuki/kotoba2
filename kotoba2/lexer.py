import re
from kotoba2.common import MapCollection

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

class DataToken(Token): pass

class ElementToken(Token):
    _re_element           = re.compile('</?(?P<name>[^\s>]+)(?P<attributes>[^>]*)/?>')
    _re_attribute_eq_q_op = re.compile('="')
    _re_attribute_q_ed    = re.compile('"')
    _re_attribute_spliter = re.compile('__T_EQ_Q_OP__')

    def __init__(self, data):
        self._data = data.strip()

        main_parts = ElementToken._re_element.search(self._data).groupdict()

        self._name       = main_parts['name']
        self._attributes = MapCollection()

        raw_attributes = main_parts['attributes'].strip()

        if not raw_attributes:
            return

        raw_attributes = ElementToken._re_attribute_eq_q_op.sub('__T_EQ_Q_OP__', raw_attributes)
        raw_attributes = ElementToken._re_attribute_q_ed.sub('__T_Q_ED__', raw_attributes)
        raw_attribute_parts = re.split('__T_Q_ED__\s*', raw_attributes)

        for raw_attribute_part in raw_attribute_parts:
            if not ElementToken._re_attribute_spliter.search(raw_attribute_part):
                continue
            
            name, value = ElementToken._re_attribute_spliter.split(raw_attribute_part)

            self._attributes.set(name, value)

    @property
    def name(self):
        return self._name

class CloseTagToken(ElementToken): pass
class OpenTagToken(ElementToken):  pass
class SoloTagToken(ElementToken):  pass

class TokenFactory(object):
    @staticmethod
    def make(data):
        sample_data = data.strip()
        TokenClass  = DataToken

        # Empty
        if not sample_data:
            return None

        # Close tag
        elif sample_data[0:2] == '</' and sample_data[-1] == '>':
            TokenClass = CloseTagToken

        # Solo tag
        elif sample_data[0] == '<' and sample_data[-2:] == '/>':
            TokenClass = SoloTagToken

        # Open tag
        elif sample_data[0] == '<' and sample_data[-1] == '>':
            TokenClass = OpenTagToken

        return TokenClass(data)

class Lexer(object):
    _line_ending_symbol = '_____LF_____'
    _re_line_ending_native = re.compile('(\r\n|\n)')
    _re_line_ending_symbol = re.compile(_line_ending_symbol)
    _re_comment = re.compile('<![^>]*>')
    _re_kind_tag = re.compile('^(</?[^!>]+>)')
    _re_kind_tag_script_open = re.compile('^(<(script|style)[^>]*>)')
    _re_kind_tag_script_close = re.compile('^(</(script|style)[^>]*>)')

    def tokenize(self, data):
        data = self._optimized_input(data)
        string_tokens = self._tokenize_to_string_tokens(data)

        return self._tokenize_to_objectized_tokens(string_tokens)

    def _optimized_input(self, data):
        data = self._re_line_ending_native.sub(self._line_ending_symbol, data)
        data = self._re_comment.sub('', data)
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
        lookahead_length     = 100
        iterating_position   = 0
        cutoff_head_position = None

        data_length = len(data)
        tokens      = []

        while iterating_position < data_length:
            cutoff_buffer      = None
            lookahead_buffer   = data[iterating_position:iterating_position + lookahead_length]
            previous_token     = tokens[-1] if tokens else None
            is_script_tag_open = previous_token and self._extract_tag_script_open(previous_token)

            tag_matches = self._extract_tag(lookahead_buffer)

            #print('>> {}'.format(lookahead_buffer))

            if tag_matches:
                content_buffer  = data[cutoff_head_position:iterating_position]
                tag_buffer      = tag_matches.groups()[0]
                tag_buffer_size = len(tag_buffer)
                next_is_close_script_tag = self._extract_tag_script_close(tag_buffer)

                #print('-- ! -- {}'.format(tag_matches.groups()))
                #print('-- ? -- {}, {}'.format(
                #    '-OPEN_SCRIPT' if not is_script_tag_open else '+OPEN_SCRIPT',
                #    '+CLOSE_SCRIPT' if next_is_close_script_tag else '-CLOSE_SCRIPT'
                #))

                if not is_script_tag_open or next_is_close_script_tag:
                    # Store the previous token
                    tokens.append(content_buffer)
                    tokens.append(tag_buffer)

                    cutoff_head_position = iterating_position + tag_buffer_size

                    # Forward the iterating position
                    iterating_position = cutoff_head_position

                    #print('-- C -- {}'.format(content_buffer.strip()))
                    #print('-- T -- {}'.format(tag_buffer.strip()))

                    continue

            elif cutoff_head_position == None:
                cutoff_head_position = iterating_position

            current_buffer = data[cutoff_head_position:iterating_position]

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
