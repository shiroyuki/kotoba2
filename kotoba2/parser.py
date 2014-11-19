import logging
from kotoba2.common import MapCollection
from kotoba2.lexer import *

logging.basicConfig(level = logging.WARN)

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
    TOKEN_TYPES = (OpenTagToken, SoloTagToken, CloseTagToken, IrregularTagToken)

    def __init__(self):
        Node.__init__(self)
        self.name = None
        self.attributes = MapCollection()
        self.parent = None
        self.children = []

    def __repr__(self):
        label = self.name

        if self.parent:
            label = '{}.{}'.format(self.parent.name, self.name)

        return '<{} {}>'.format(self.__class__.__name__, label)

class NodeFactory(object):
    logger = logging.getLogger('kotoba2.parser.NodeFactory')
    logger.setLevel(logging.WARN)

    @staticmethod
    def make(token):
        token_type = type(token)

        if token_type not in ElementNode.TOKEN_TYPES:
            NodeFactory.logger.debug(u'-- DATA ----- {} ({})'.format(token_type.__name__, token))

            data = token.data.strip()
            node = DataNode()

            node.data = data

            return node

        NodeFactory.logger.debug(u'-- ELEMENT -- {} ({})'.format(token_type.__name__, token))

        data = token.data.strip()
        node = ElementNode()

        node.name       = token.name
        node.attributes = token.attributes

        return node

class Parser(object):
    logger = logging.getLogger('kotoba2.parser.Parser')
    logger.setLevel(logging.DEBUG)

    def parse(self, tokens):
        origin = None
        cursor = None
        cursor_index = 0
        token_count  = len(tokens)
        stack = []

        while cursor_index < token_count:
            cursor = tokens[cursor_index]
            cursor_index += 1

            token_type = type(cursor)

            parent = stack[-1] if stack else None
            node   = NodeFactory.make(cursor)

            if parent and token_type != CloseTagToken:
                node.parent = parent
                parent.children.append(node)

            if token_type == OpenTagToken:
                stack.append(node)
            elif token_type == CloseTagToken:
                if parent.name != cursor.name:
                    raise RuntimeError('Expected <{}>, got <{}> instead'.format(parent.name, cursor.name))
                stack.pop()

            Parser.logger.debug(u'-- LEVEL -- {}'.format(len(stack)))
            Parser.logger.debug(u'-- CLASS -- {}'.format(token_type.__name__))
            Parser.logger.debug(u'-- STACK -- {}'.format(stack))

            if not origin and token_type == OpenTagToken:
                Parser.logger.debug(u'-- ORIGIN -- {}'.format(node))
                origin = node

        return origin
