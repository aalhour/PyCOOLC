# -----------------------------------------------------------------------------
# ast.py
#
# Author:       Ahmad Alhour (github.com/aalhour; aalhour.com).
# Date:         May 26rd, 2016.
# Description:  The Abstract Syntax Tree module. Provides classes for managing
#               the parse tree.
# -----------------------------------------------------------------------------


class BaseNode:
    def __init__(self):
        pass

    def to_tuple(self):
        pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.to_tuple())


class ProgramNode(BaseNode):
    NODE_NAME = "PROGRAM"

    def __init__(self, classes):
        super(ProgramNode, self).__init__()
        self.classes = classes

    def to_tuple(self):
        return tuple([self.NODE_NAME, self.classes])


class ClassNode(BaseNode):
    NODE_NAME = "CLASS"

    def __init__(self, name, inherits, features):
        super(ClassNode, self).__init__()
        self.name = name
        self.inherits = inherits
        self.features = features

    def to_tuple(self):
        return tuple([self.NODE_NAME, self.name, self.inherits, self.features])


class InheritanceNode(BaseNode):
    NODE_NAME = "INHERITS"

    def __init__(self, inheritance_type=None):
        super(InheritanceNode, self).__init__()
        self.inheritance_type = inheritance_type

    def to_tuple(self):
        return tuple([self.NODE_NAME, self.inheritance_type])

    def is_empty(self):
        return self.inheritance_type is None


class FeaturesNode(BaseNode):
    NODE_NAME = "FEATURES"

    def __init__(self, features):
        super(FeaturesNode, self).__init__()
        if features is None:
            self.features = tuple()
        else:
            self.features = features

    def to_tuple(self):
        return tuple([self.NODE_NAME, self.features])

    def is_empty(self):
        return len(self.features) == 0


class AttributeNode(BaseNode):
    NODE_NAME = "FORMAL"

    def __init__(self, identifier, attr_type, formals, expression):
        super(AttributeNode, self).__init__()
        self.identifier = identifier
        self.type = attr_type
        self.expression = expression
        self.formals = formals

    def to_tuple(self):
        return tuple([self.NODE_NAME, self.identifier, self.type, self.expression, self.formals])


class FormalNode(BaseNode):
    NODE_NAME = "FORMAL"

    def __init__(self, identifier, formal_type, assignment):
        super(FormalNode, self).__init__()
        self.identifier = identifier
        self.type = formal_type
        self.assignment = assignment

    def to_tuple(self):
        return tuple([self.NODE_NAME, self.identifier, self.type, self.assignment])


class Expr(BaseNode):
    NODE_NAME = "EXPRESSION"

    def __init__(self, expression):
        super(Expr, self).__init__()
        self.expression = expression

