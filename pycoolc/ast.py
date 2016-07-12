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

    def to_readable(self):
        return "{}".format(self.to_tuple())

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.to_tuple())


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


# ############################## PROGRAM, TYPE AND OBJECT ##############################


class Program(BaseNode):
    def __init__(self, classes):
        super(Program, self).__init__()
        self.classes = classes

    def to_tuple(self):
        return tuple([self._clsname, self.classes])

    def to_readable(self):
        return "{}(classes={})".format(self.to_tuple())


class Class(BaseNode):
    def __init__(self, name, parent, features):
        super(Class, self).__init__()
        self.name = name
        self.parent = parent
        self.features = features

    def to_tuple(self):
        return tuple([self._clsname, self.name, self.parent, self.features])

    def to_readable(self):
        return "{}(name={}, parent={}, features={})".format(self.to_tuple())


class ClassFeature(BaseNode):
    def __init__(self):
        super(ClassFeature, self).__init__()


class ClassMethod(ClassFeature):
    def __init__(self, name, formal_params, return_type, body):
        super(ClassMethod, self).__init__()
        self.name = name
        self.formal_params = formal_params
        self.return_type = return_type
        self.body = body

    def to_tuple(self):
        return tuple([self._clsname, self.name, self.formal_params, self.return_type, self.body])

    def to_readable(self):
        return "{}(name={}, formal_params={}, return_type={}, body={})".format(self.to_tuple())


class ClassAttribute(ClassFeature):
    def __init__(self, name, attr_type, init_expr):
        super(ClassAttribute, self).__init__()
        self.name = name
        self.attr_type = attr_type
        self.init_expr = init_expr

    def to_tuple(self):
        return tuple([self._clsname, self.name, self.attr_type, self.init_expr])

    def to_readable(self):
        return "{}(name={}, formal_params={}, return_type={}, body={})".format(self.to_tuple())


class FormalParameter(ClassFeature):
    def __init__(self, name, param_type):
        super(FormalParameter, self).__init__()
        self.name = name
        self.param_type = param_type

    def to_tuple(self):
        return tuple([self._clsname, self.name, self.param_type])

    def to_readable(self):
        return "{}(name={}, param_type={})".format(self.to_tuple())


class Object(BaseNode):
    def __init__(self, name):
        super(Object, self).__init__()
        self.name = name

    def to_tuple(self):
        return tuple([self._clsname, self.name])

    def to_readable(self):
        return "{}(name={})".format(self.to_tuple())


class Self(Object):
    def __init__(self):
        super(Self, self).__init__("SELF")

    def to_tuple(self):
        return tuple([self._clsname])

    def to_readable(self):
        return "{}".format(self._clsname)


# ############################## CONSTANTS ##############################


class Integer(Constant):
    def __init__(self, value):
        super(Integer, self).__init__()
        self.value = int(value)

    def to_tuple(self):
        return tuple([self._clsname, self.value])

    def to_readable(self):
        return "{}({})".format(self.to_tuple())


class String(Constant):
    def __init__(self, value):
        super(String, self).__init__()
        self.value = str(value)

    def to_tuple(self):
        return tuple([self._clsname, self.value])

    def to_readable(self):
        return "{}({})".format(self.to_tuple())


class Boolean(Constant):
    def __init__(self, value):
        super(Boolean, self).__init__()
        self.value = value is True

    def to_tuple(self):
        return tuple([self._clsname, self.value])

    def to_readable(self):
        return "{}({})".format(self.to_tuple())


# ############################## EXPRESSIONS ##############################


class NewObject(Expr):
    def __init__(self, new_type):
        super(NewObject, self).__init__()
        self.type = new_type

    def to_tuple(self):
        return tuple([self._clsname, self.type])

    def to_readable(self):
        return "{}(type={})".format(self.to_tuple())


class IsVoid(Expr):
    def __init__(self, expr):
        super(IsVoid, self).__init__()
        self.expr = expr

    def to_tuple(self):
        return tuple([self._clsname, self.expr])

    def to_readable(self):
        return "{}(expr={})".format(self.to_tuple())


class Assignment(Expr):
    def __init__(self, instance, expr):
        super(Assignment, self).__init__()
        self.instance = instance
        self.expr = expr

    def to_tuple(self):
        return tuple([self._clsname, self.instance, self.expr])

    def to_readable(self):
        return "{}(instance={}, expr={})".format(self.to_tuple())


class Block(Expr):
    def __init__(self, expr_list):
        super(Block, self).__init__()
        self.expr_list = expr_list

    def to_tuple(self):
        return tuple([self._clsname, self.expr_list])

    def to_readable(self):
        return "{}(expr_list={})".format(self.to_tuple())


class DynamicDispatch(Expr):
    def __init__(self, instance, method, arguments):
        super(DynamicDispatch, self).__init__()
        self.instance = instance
        self.method = method
        self.arguments = arguments if arguments is not None else tuple()

    def to_tuple(self):
        return tuple([self._clsname, self.instance, self.method, self.arguments])

    def to_readable(self):
        return "{}(instance={}, method={}, arguments={})".format(self.to_tuple())


class StaticDispatch(Expr):
    def __init__(self, instance, dispatch_type, method, arguments):
        super(StaticDispatch, self).__init__()
        self.instance = instance
        self.dispatch_type = dispatch_type
        self.method = method
        self.arguments = arguments if arguments is not None else tuple()

    def to_tuple(self):
        return tuple([self._clsname, self.instance, self.dispatch_type, self.method, self.arguments])

    def to_readable(self):
        return "{}(instance={}, dispatch_type={}, method={}, arguments={})".format(self.to_tuple())


class Let(Expr):
    def __init__(self, instance, let_type, init_expr, body):
        super(Let, self).__init__()
        self.instance = instance
        self.let_type = let_type
        self.init_expr = init_expr
        self.body = body

    def to_tuple(self):
        return tuple([self._clsname, self.instance, self.let_type, self.init_expr, self.body])

    def to_readable(self):
        return "{}(instance={}, let_type={}, init_expr={}, body={})".format(self.to_tuple())


class If(Expr):
    def __init__(self, predicate, then_body, else_body):
        super(If, self).__init__()
        self.predicate = predicate
        self.then_body = then_body
        self.else_body = else_body

    def to_tuple(self):
        return tuple([self._clsname, self.predicate, self.then_body, self.else_body])

    def to_readable(self):
        return "{}(predicate={}, then_body={}, else_body={})".format(self.to_tuple())


class WhileLoop(Expr):
    def __init__(self, predicate, body):
        super(WhileLoop, self).__init__()
        self.predicate = predicate
        self.body = body

    def to_tuple(self):
        return tuple([self._clsname, self.predicate, self.body])

    def to_readable(self):
        return "{}(predicate={}, body={})".format(self.to_tuple())


class Case(Expr):
    def __init__(self, expr, actions):
        super(Case, self).__init__()
        self.expr = expr
        self.actions = actions

    def to_tuple(self):
        return tuple([self._clsname, self.expr, self.actions])

    def to_readable(self):
        return "{}(expr={}, actions={})".format(self.to_tuple())


class Action(BaseNode):
    def __init__(self, name, action_type, body):
        super(Action, self).__init__()
        self.name = name
        self.action_type = action_type
        self.body = body

    def to_tuple(self):
        return tuple([self._clsname, self.name, self.action_type, self.body])

    def to_readable(self):
        return "{}(name={}, action_type={}, body={})".format(self.to_tuple())


# ############################## UNARY OPERATIONS ##################################


class IntegerComplement(UnaryOperation):
    def __init__(self, integer_expr):
        super(IntegerComplement, self).__init__()
        self.symbol = "~"
        self.integer_expr = integer_expr

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr])

    def to_readable(self):
        return "{}(expr={})".format(self.to_tuple())


class BooleanComplement(UnaryOperation):
    def __init__(self, boolean_expr):
        super(BooleanComplement, self).__init__()
        self.symbol = "!"
        self.boolean_expr = boolean_expr

    def to_tuple(self):
        return tuple([self._clsname, self.boolean_expr])

    def to_readable(self):
        return "{}(expr={})".format(self.to_tuple())


# ############################## BINARY OPERATIONS ##################################


class Addition(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(Addition, self).__init__()
        self.symbol = "+"
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])

    def to_readable(self):
        return "{}(int_expr1={}, int_expr2={})".format(self.to_tuple())


class Subtraction(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(Subtraction, self).__init__()
        self.symbol = "-"
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])

    def to_readable(self):
        return "{}(int_expr1={}, int_expr2={})".format(self.to_tuple())


class Multiplication(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(Multiplication, self).__init__()
        self.symbol = "*"
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])

    def to_readable(self):
        return "{}(int_expr1={}, int_expr2={})".format(self.to_tuple())


class Division(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(Division, self).__init__()
        self.symbol = "/"
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])

    def to_readable(self):
        return "{}(int_expr1={}, int_expr2={})".format(self.to_tuple())


class Equal(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(Equal, self).__init__()
        self.symbol = "="
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])

    def to_readable(self):
        return "{}(int_expr1={}, int_expr2={})".format(self.to_tuple())


class LessThan(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(LessThan, self).__init__()
        self.symbol = "<"
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])

    def to_readable(self):
        return "{}(int_expr1={}, int_expr2={})".format(self.to_tuple())


class LessThanOrEqual(BinaryOperation):
    def __init__(self, integer_expr_1, integer_expr_2):
        super(LessThanOrEqual, self).__init__()
        self.symbol = "<="
        self.integer_expr_1 = integer_expr_1
        self.integer_expr_2 = integer_expr_2

    def to_tuple(self):
        return tuple([self._clsname, self.integer_expr_1, self.integer_expr_2])

    def to_readable(self):
        return "{}(int_expr1={}, int_expr2={})".format(self.to_tuple())


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

