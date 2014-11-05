from kotoba2.lexer import *

class UnknownTokenError(Exception): pass

class Node(object):
    _global_last_uuid = 0

    def __init__(self):
        Node._global_last_uuid += 1

        self._uuid = Node._global_last_uuid

class DataNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.data = None

class ElementNode(Node):
    TOKEN_TYPES = (OpenTagToken, SoloTagToken, CloseTagToken)

    def __init__(self):
        Node.__init__(self)
        self.name = None
        self.parent = None
        self.children = []

class NodeFactory(object):
    @staticmethod
    def make(token):
        if type(token) in ElementNode.TOKEN_TYPES:
            node = ElementNode()
            data = token.data.strip()

class Parser(object):
    def parse(self, tokens):
        origin = None
        cursor = None
        cursor_index = 0
        token_count  = len(tokens)
        stack = []

        while cursor_index < token_count:
            cursor = tokens[cursor_index]
            cursor_index += 1

            if type(cursor) in ElementNode.TOKEN_TYPES:
                node = NodeFactory.make(cursor)
                print('---- {} ({}): element'.format(cursor.__class__.__name__, cursor))
                continue

            print('---- {} ({}): processed'.format(cursor.__class__.__name__, cursor))
