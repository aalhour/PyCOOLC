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

    @property
    def _clsname(self):
        return str(self.__class__.__name__)

    def to_tuple(self):
        return tuple(self._clsname)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.to_tuple())


class Program(BaseNode):
    def __init__(self, classes):
        super(Program, self).__init__()
        self.classes = classes

    def to_tuple(self):
        return tuple([str(self.__class__), self.classes])


class Type(BaseNode):
    def __init__(self, name, inherits, features):
        super(Type, self).__init__()
        self.name = name
        self.inherits = inherits
        self.features = features

    def to_tuple(self):
        return tuple([self._clsname, self.name, self.inherits, self.features])


class Inheritance(BaseNode):
    def __init__(self, inheritance_type=None):
        super(Inheritance, self).__init__()
        self.type = inheritance_type

    def to_tuple(self):
        return tuple([self._clsname, self.type])


class Feature(BaseNode):
    pass


class Attribute(Feature):
    def __init__(self, identifier, attr_type, formals, expression):
        super(Attribute, self).__init__()
        self.identifier = identifier
        self.type = attr_type
        self.expression = expression
        self.formals = formals

    def to_tuple(self):
        return tuple([self._clsname, self.identifier, self.type, self.expression, self.formals])


class Formal(Feature):
    def __init__(self, identifier, formal_type, assignment_expr):
        super(Formal, self).__init__()
        self.identifier = identifier
        self.type = formal_type
        self.assignment = assignment_expr

    def to_tuple(self):
        return tuple([self._clsname, self.identifier, self.type, self.assignment])


class Expr(BaseNode):
    def __init__(self):
        pass

    def get_expr_type(self):
        pass


class IntegerExpr(Expr):
    pass


class StringExpr(Expr):
    pass


class VariableExpr(Expr):
    pass


class UnaryExpr(Expr):
    pass


class BinaryExpr(Expr):
    pass


class NewTypeExpr(Expr):
    def __init__(self, new_type):
        super(NewTypeExpr, self).__init__()
        self.type = new_type

    def to_tuple(self):
        return tuple([self._clsname, self.type])


class AssignmentExpr(Expr):
    def __init__(self, identifier, expression):
        super(AssignmentExpr, self).__init__()
        self.identifier = identifier
        self.expression = expression

    def to_tuple(self):
        return tuple([self._clsname, self.identifier, self.expression])


class BlockExpr(Expr):
    def __init__(self, expressions_block):
        super(BlockExpr, self).__init__()
        self.expressions_block = expressions_block

    def to_tuple(self):
        return tuple([self._clsname, self.expressions_block])


class MethodCallExp(Expr):
    def __init__(self, expression, statically_dispatched_type, method_identifier, call_params):
        super(MethodCallExp, self).__init__()
        self.expression = expression
        self.statically_dispatched_type = statically_dispatched_type
        self.method_identifier = method_identifier
        self.call_params = call_params

    def to_tuple(self):
        return tuple([
            self._clsname, self.expression, self.statically_dispatched_type, self.method_identifier, self.call_params])

