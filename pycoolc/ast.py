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


class UnaryOperation(Expr):
    def __init__(self):
        super(UnaryOperation, self).__init__()


class BinaryOperation(Expr):
    def __init__(self):
        super(BinaryOperation, self).__init__()


# ############################## PROGRAM, TYPE AND INHERITANCE ##############################


class Program(BaseNode):
    def __init__(self, classes):
        super(Program, self).__init__()
        self.classes = classes

    def to_tuple(self):
        return tuple([str(self.__class__), self.classes])


class Type(BaseNode):
    def __init__(self, name, base_type, features):
        super(Type, self).__init__()
        self.name = name
        self.base_type = base_type
        self.features = features

    def to_tuple(self):
        return tuple([self._clsname, self.name, self.base_type, self.features])


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


class Integer(Constant):
    def __init__(self, value):
        super(Integer, self).__init__()
        self.value = int(value)

    def to_tuple(self):
        return tuple([self._clsname, self.value])


class String(Constant):
    def __init__(self, value):
        super(String, self).__init__()
        self.value = str(value)

    def to_tuple(self):
        return tuple([self._clsname, self.value])


class Boolean(Constant):
    def __init__(self, value):
        super(Boolean, self).__init__()
        self.value = value is True

    def to_tuple(self):
        return tuple([self._clsname, self.value])


class Object(Constant):
    def __init__(self, identifier):
        super(Object, self).__init__()
        self.identifier = identifier

    def to_tuple(self):
        return tuple([self._clsname, self.identifier])


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
    def __init__(self, instance, expression):
        super(AssignmentExpr, self).__init__()
        self.instance = instance
        self.expression = expression

    def to_tuple(self):
        return tuple([self._clsname, self.instance, self.expression])


class BlockExpr(Expr):
    def __init__(self, expressions):
        super(BlockExpr, self).__init__()
        self.expressions = expressions

    def to_tuple(self):
        return tuple([self._clsname, self.expressions])


class DynamicDispatchExpr(Expr):
    def __init__(self, instance, method, arguments):
        super(DynamicDispatchExpr, self).__init__()
        self.instance = instance
        self.method = method
        self.arguments = arguments if arguments is not None else tuple()

    def to_tuple(self):
        return tuple([self._clsname, self.instance, self.method, self.arguments])


class StaticDispatchExpr(Expr):
    def __init__(self, instance, dispatch_type, method, arguments):
        super(StaticDispatchExpr, self).__init__()
        self.instance = instance
        self.dispatch_type = dispatch_type
        self.method = method
        self.arguments = arguments if arguments is not None else tuple()

    def to_tuple(self):
        return tuple([
            self._clsname, self.instance, self.dispatch_type, self.method, self.arguments
        ])


class LetExpr(Expr):
    def __init__(self, instance, let_type, assignment_expr, body):
        super(LetExpr, self).__init__()
        self.instance = instance
        self.let_type = let_type
        self.assignment_expr = assignment_expr
        self.body = body

    def to_tuple(self):
        return tuple([self._clsname, self.instance, self.let_type, self.assignment_expr, self.body])


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


# ############################## OPERATIONS ##################################


class IntegerComplement(UnaryOperation):
    def __init__(self, integer_expr):
        super(IntegerComplement, self).__init__()
        self.symbol = "~"
        self.integer_expr = integer_expr

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr])


class BooleanComplement(UnaryOperation):
    def __init__(self, boolean_expr):
        super(BooleanComplement, self).__init__()
        self.symbol = "!"
        self.boolean_expr = boolean_expr

    def to_tuple(self):
        return tuple([self._clsname, self.boolean_expr])


class Addition(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(Addition, self).__init__()
        self.symbol = "+"
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])


class Subtraction(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(Subtraction, self).__init__()
        self.symbol = "-"
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])


class Multiplication(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(Multiplication, self).__init__()
        self.symbol = "*"
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])


class Division(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(Division, self).__init__()
        self.symbol = "/"
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])


class Equal(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(Equal, self).__init__()
        self.symbol = "="
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])


class LessThan(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(LessThan, self).__init__()
        self.symbol = "<"
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])


class LessThanOrEqual(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(LessThanOrEqual, self).__init__()
        self.symbol = "<="
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])


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

