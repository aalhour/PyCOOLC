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
    def __init__(self, name, inherits, features_seq):
        super(Type, self).__init__()
        self.name = name
        self.inherits = inherits
        self.features_seq = features_seq

    def to_tuple(self):
        return tuple([self._clsname, self.name, self.inherits, self.features_seq])


class Inheritance(BaseNode):
    def __init__(self, inheritance_type=None):
        super(Inheritance, self).__init__()
        self.type = inheritance_type

    def to_tuple(self):
        return tuple([self._clsname, self.type])


class Feature(BaseNode):
    pass


class Attribute(Feature):
    def __init__(self, identifier, attr_type, formals_seq, expression):
        super(Attribute, self).__init__()
        self.identifier = identifier
        self.type = attr_type
        self.expression = expression
        self.formals_seq = formals_seq

    def to_tuple(self):
        return tuple([self._clsname, self.identifier, self.type, self.expression, self.formals_seq])


class Formal(Feature):
    def __init__(self, identifier, formal_type, assignment_expr):
        super(Formal, self).__init__()
        self.identifier = identifier
        self.type = formal_type
        self.assignment_expr = assignment_expr

    def to_tuple(self):
        return tuple([self._clsname, self.identifier, self.type, self.assignment_expr])


class Expr(BaseNode):
    def __init__(self):
        super(Expr, self).__init__()


class IdentifierExpr(Expr):
    def __init__(self, identifier):
        super(IdentifierExpr, self).__init__()
        self.identifier = identifier

    def to_tuple(self):
        return tuple([self._clsname, self.identifier])


class IntegerExpr(Expr):
    def __init__(self, value):
        super(IntegerExpr, self).__init__()
        self.value = int(value)

    def to_tuple(self):
        return tuple([self._clsname, self.value])


class StringExpr(Expr):
    def __init__(self, value):
        super(StringExpr, self).__init__()
        self.value = str(value)

    def to_tuple(self):
        return tuple([self._clsname, self.value])


class BooleanExpr(Expr):
    def __init__(self, value):
        super(BooleanExpr, self).__init__()
        self.value = value is True

    def to_tuple(self):
        return tuple([self._clsname, self.value])


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


class DispatchExpr(Expr):
    def __init__(self, identifier_expr, statically_dispatched_type, attribute_id, arguments_seq):
        super(DispatchExpr, self).__init__()
        self.identifier_expr = identifier_expr
        self.statically_dispatched_type = statically_dispatched_type
        self.attribute_id = attribute_id
        self.arguments_seq = arguments_seq if arguments_seq is not None else tuple()

    def to_tuple(self):
        return tuple([
            self._clsname, self.identifier_expr, self.statically_dispatched_type, self.attribute_id, self.arguments_seq
        ])


class LetExpr(Expr):
    def __init__(self, formals_seq, in_expr):
        super(LetExpr, self).__init__()
        self.formals_seq = formals_seq
        self.in_expr = in_expr

    def to_tuple(self):
        return tuple([self._clsname, self.formals_seq, self.in_expr])


class ConditionalExpr(Expr):
    def __init__(self, condition, true_eval, false_eval):
        super(ConditionalExpr, self).__init__()
        self.condition = condition
        self.true_eval = true_eval
        self.false_eval = false_eval

    def to_tuple(self):
        return tuple([self._clsname, self.condition, self.true_eval, self.false_eval])

