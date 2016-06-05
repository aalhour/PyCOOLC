# -----------------------------------------------------------------------------
# ast.py
#
# Author:       Ahmad Alhour (github.com/aalhour; aalhour.com).
# Date:         May 26rd, 2016.
# Description:  The Abstract Syntax Tree module. Provides classes for managing
#               the parse tree.
# -----------------------------------------------------------------------------


# ############################## BASE AST NODES CLASSES ##############################


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


class ClassFeature(BaseNode):
    def __init__(self):
        super(ClassFeature, self).__init__()


class Constant(BaseNode):
    def __init__(self):
        super(Constant, self).__init__()


class Expr(BaseNode):
    def __init__(self):
        super(Expr, self).__init__()


# ############################## PROGRAM, TYPE AND INHERITANCE ##############################


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
    def __init__(self, parent_type=None):
        super(Inheritance, self).__init__()
        self.type = parent_type

    def to_tuple(self):
        return tuple([self._clsname, self.type])


class ClassMethod(ClassFeature):
    def __init__(self, identifier, formal_params, return_type, method_body):
        super(ClassMethod, self).__init__()
        self.identifier = identifier
        self.formal_params = formal_params
        self.return_type = return_type
        self.method_body = method_body

    def to_tuple(self):
        return tuple([self._clsname, self.identifier, self.formal_params, self.return_type, self.method_body])


class ClassAttribute(ClassFeature):
    def __init__(self, identifier, attribute_type, assignment_expr):
        super(ClassAttribute, self).__init__()
        self.identifier = identifier
        self.type = attribute_type
        self.expr = assignment_expr

    def to_tuple(self):
        return tuple([self._clsname, self.identifier, self.type, self.expr])


class FormalParameter(ClassFeature):
    def __init__(self, identifier, param_type):
        super(FormalParameter, self).__init__()
        self.identifier = identifier
        self.type = param_type

    def to_tuple(self):
        return tuple([self._clsname, self.identifier, self.type])


# ############################## CONSTANTS ##############################


class IntegerContant(Constant):
    def __init__(self, value):
        super(IntegerContant, self).__init__()
        self.value = int(value)

    def to_tuple(self):
        return tuple([self._clsname, self.value])


class StringConstant(Constant):
    def __init__(self, value):
        super(StringConstant, self).__init__()
        self.value = str(value)

    def to_tuple(self):
        return tuple([self._clsname, self.value])


class BooleanConstant(Constant):
    def __init__(self, value):
        super(BooleanConstant, self).__init__()
        self.value = value is True

    def to_tuple(self):
        return tuple([self._clsname, self.value])


# ############################## FORMAL AND ACTION ##############################


class Formal(BaseNode):
    def __init__(self, identifier, formal_type, assignment_expr):
        super(Formal, self).__init__()
        self.identifier = identifier
        self.type = formal_type
        self.expr = assignment_expr

    def to_tuple(self):
        return tuple([self._clsname, self.identifier, self.type, self.expr])


class Action(BaseNode):
    def __init__(self, identifier, action_type, body):
        super(Action, self).__init__()
        self.identifier = identifier
        self.type = action_type
        self.body = body

    def to_tuple(self):
        return tuple([self._clsname, self.identifier, self.type, self.body])


# ############################## EXPRESSIONS ##############################


class IdentifierExpr(Expr):
    def __init__(self, identifier):
        super(IdentifierExpr, self).__init__()
        self.identifier = identifier

    def to_tuple(self):
        return tuple([self._clsname, self.identifier])


class NewTypeExpr(Expr):
    def __init__(self, new_type):
        super(NewTypeExpr, self).__init__()
        self.type = new_type

    def to_tuple(self):
        return tuple([self._clsname, self.type])


class IsVoidExpr(Expr):
    def __init__(self, expression):
        super(IsVoidExpr, self).__init__()
        self.expr = expression

    def to_tuple(self):
        return tuple([self._clsname, self.expr])


class AssignmentExpr(Expr):
    def __init__(self, identifier, expression):
        super(AssignmentExpr, self).__init__()
        self.identifier = identifier
        self.expression = expression

    def to_tuple(self):
        return tuple([self._clsname, self.identifier, self.expression])


class BlockExpr(Expr):
    def __init__(self, expressions):
        super(BlockExpr, self).__init__()
        self.expressions = expressions

    def to_tuple(self):
        return tuple([self._clsname, self.expressions])


class DynamicDispatchExpr(Expr):
    def __init__(self, identifier_expr, method_id, arguments):
        super(DynamicDispatchExpr, self).__init__()
        self.identifier_expr = identifier_expr
        self.method_id = method_id
        self.arguments = arguments if arguments is not None else tuple()

    def to_tuple(self):
        return tuple([self._clsname, self.identifier_expr, self.method_id, self.arguments])


class StaticDispatchExpr(Expr):
    def __init__(self, identifier_expr, dispatch_type, method_id, arguments):
        super(StaticDispatchExpr, self).__init__()
        self.identifier_expr = identifier_expr
        self.dispatch_type = dispatch_type
        self.method_id = method_id
        self.arguments = arguments if arguments is not None else tuple()

    def to_tuple(self):
        return tuple([
            self._clsname, self.identifier_expr, self.dispatch_type, self.method_id, self.arguments
        ])


class LetExpr(Expr):
    def __init__(self, formals, expression):
        super(LetExpr, self).__init__()
        self.formals = formals
        self.expr = expression

    def to_tuple(self):
        return tuple([self._clsname, self.formals, self.expr])


class ConditionalExpr(Expr):
    def __init__(self, predicate, then_expression, else_expression):
        super(ConditionalExpr, self).__init__()
        self.predicate = predicate
        self.then_expression = then_expression
        self.else_expression = else_expression

    def to_tuple(self):
        return tuple([self._clsname, self.predicate, self.then_expression, self.else_expression])


class LoopExpr(Expr):
    def __init__(self, predicate, body):
        super(LoopExpr, self).__init__()
        self.predicate = predicate
        self.body = body

    def to_tuple(self):
        return tuple([self._clsname, self.predicate, self.body])


class CaseExpr(Expr):
    def __init__(self, expression, actions):
        super(CaseExpr, self).__init__()
        self.expr = expression
        self.actions = actions

    def to_tuple(self):
        return tuple([self._clsname, self.expr, self.actions])


class UnaryOperation(Expr):
    def __init__(self, operation, expression):
        super(UnaryOperation, self).__init__()
        self.operation = operation
        self.expr = expression

    def to_tuple(self):
        return tuple([self._clsname, self.operation, self.expr])


class BinaryOperation(Expr):
    def __init__(self, left_expression, operation, right_expression):
        super(BinaryOperation, self).__init__()
        self.left_expr = left_expression
        self.right_expr = right_expression
        self.operation = operation

    def to_tuple(self):
        return tuple([self._clsname, self.left_expr, self.operation, self.right_expr])


# ############################## HELPER METHODS ##############################


def is_valid_unary_operation(operation):
    return operation in ["~", "not"]


def is_valid_binary_operation(operation):
    return operation in ["+", "-", "*", "/", "<", "<=", "="]


def get_operation(operation):
    if operation is None or not isinstance(operation, str):
        return None

    operation = operation.upper()
    if operation == "PLUS":
        return "+"
    elif operation == "MINUS":
        return "-"
    elif operation == "TIMES":
        return "*"
    elif operation == "DIVIDE":
        return "/"
    elif operation == "LTHAN":
        return "<"
    elif operation == "LTEQ":
        return "<="
    elif operation == "EQUALS":
        return "="
    elif operation == "NOT":
        return "not"
    elif operation == "INT_COMP":
        return "~"
    else:
        return None

