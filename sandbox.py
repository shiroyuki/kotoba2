from kotoba2.lexer  import Lexer
from kotoba2.parser import Parser, DataNode

def debug_lexer(data):
    show_output = False

    lexer  = Lexer()
    tokens = lexer.tokenize(data)

    line_length = 60

    for token in tokens:
        if show_output: print('{}\t| {}'.format(len(token), str(token).strip()[:line_length].strip()))
        pass

    reassembled_data = ''.join([u'{}'.format(token) for token in tokens])

    if show_output: print('ORIGINAL DATA LENGTH:    {}'.format(len(data)))
    if show_output: print('REASSEMBLED DATA LENGTH: {}'.format(len(reassembled_data)))

    return tokens

def debug_parser(tokens):
    parser = Parser()
    root   = parser.parse(tokens)

    print_tree(root, 0)

def print_tree(node, level):
    indent = '    ' * level

    if type(node) == DataNode:
        #print(u'{}{}'.format(indent, node.data))
        print(u'{}(... {}B)'.format(indent, len(node.data)))

        return

    attrs = []

    for k in node.attributes:
        v = node.attributes[k]
        attrs.append('{}="{}"'.format(k, v))

    if attrs:
        print(u'{}<{} {}>'.format(indent, node.name, ' '.join(attrs)))
    else:
        print(u'{}<{}>'.format(indent, node.name))

    for child in node.children:
        print_tree(child, level + 1)

##### SANDBOX #####

test_file = 'test.html'
#test_file = 'test-shiroyuki.com.html'
#test_file = 'test.xml'
data = None

with open(test_file, 'r') as f:
    data = f.read()

debug_parser(
    debug_lexer(data)
)
