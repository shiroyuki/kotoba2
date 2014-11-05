from kotoba2.lexer  import Lexer
from kotoba2.parser import Parser

def debug_lexer(data):
    show_output = False

    lexer  = Lexer()
    tokens = lexer.tokenize(data)

    line_length = 60

    for token in tokens:
        if show_output: print('{}\t| {}'.format(len(token), str(token).strip()[:line_length].strip()))
        pass

    reassembled_data = ''.join([str(token) for token in tokens])

    if show_output: print('ORIGINAL DATA LENGTH:    {}'.format(len(data)))
    if show_output: print('REASSEMBLED DATA LENGTH: {}'.format(len(reassembled_data)))

    return tokens

def debug_parser(tokens):
    parser = Parser()
    parser.parse(tokens)

##### SANDBOX #####

data = None

with open('test-shiroyuki.com.html', 'r') as f:
    data = f.read()

debug_parser(
    debug_lexer(data)
)
