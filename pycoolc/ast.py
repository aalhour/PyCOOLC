# -----------------------------------------------------------------------------
# ast.py
#
# Author:       Ahmad Alhour (aalhour.com).
# Date:         May 26rd, 2016.
# Description:  The Abstract Syntax Tree module. Provides classes for managing
#               the parse tree.
# -----------------------------------------------------------------------------


# ############################## BASE AST NODES CLASSES ##############################


class AST:
    def __init__(self):
        pass

    @property
    def clsname(self):
        return str(self.__class__.__name__)

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname)
        ])

    def to_readable(self):
        return "{}".format(self.clsname)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.to_readable())


# ############################## PROGRAM, TYPE AND OBJECT ##############################


class Program(AST):
    def __init__(self, classes):
        super(Program, self).__init__()
        self.classes = classes

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname), 
            ("classes", self.classes)
        ])

    def to_readable(self):
        return "{}(classes={})".format(self.clsname, self.classes)


class Class(AST):
    def __init__(self, name, parent, features):
        super(Class, self).__init__()
        self.name = name
        self.parent = parent
        self.features = features

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("name", self.name),
            ("parent", self.parent), 
            ("features", self.features)
        ])

    def to_readable(self):
        return "{}(name='{}', parent={}, features={})".format(self.clsname, self.name, self.parent, self.features)


class ClassFeature(AST):
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
        return tuple([
            ("class_name", self.clsname),
            ("name", self.name),
            ("formal_params", self.formal_params),
            ("return_type", self.return_type),
            ("body", self.body)
        ])

    def to_readable(self):
        return "{}(name='{}', formal_params={}, return_type={}, body={})".format(
            self.clsname, self.name, self.formal_params, self.return_type, self.body)


class ClassAttribute(ClassFeature):
    def __init__(self, name, attr_type, init_expr):
        super(ClassAttribute, self).__init__()
        self.name = name
        self.attr_type = attr_type
        self.init_expr = init_expr

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("name", self.name),
            ("attr_type", self.attr_type),
            ("init_expr", self.init_expr)  
        ])

    def to_readable(self):
        return "{}(name='{}', attr_type={}, init_expr={})".format(
            self.clsname, self.name, self.attr_type, self.init_expr)


class FormalParameter(ClassFeature):
    def __init__(self, name, param_type):
        super(FormalParameter, self).__init__()
        self.name = name
        self.param_type = param_type

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("name", self.name),
            ("param_type", self.param_type)
        ])

    def to_readable(self):
        return "{}(name='{}', param_type={})".format(self.clsname, self.name, self.param_type)


class Object(AST):
    def __init__(self, name):
        super(Object, self).__init__()
        self.name = name

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("name", self.name)
        ])

    def to_readable(self):
        return "{}(name='{}')".format(self.clsname, self.name)


class Self(Object):
    def __init__(self):
        super(Self, self).__init__("SELF")

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname)
        ])

    def to_readable(self):
        return "{}".format(self.clsname)


# ############################## CONSTANTS ##############################


class Constant(AST):
    def __init__(self):
        super(Constant, self).__init__()


class Integer(Constant):
    def __init__(self, content):
        super(Integer, self).__init__()
        self.content = content

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("content", self.content)
        ])

    def to_readable(self):
        return "{}(content={})".format(self.clsname, self.content)


class String(Constant):
    def __init__(self, content):
        super(String, self).__init__()
        self.content = content

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("content", self.content)
        ])

    def to_readable(self):
        return "{}(content={})".format(self.clsname, repr(self.content))


class Boolean(Constant):
    def __init__(self, content):
        super(Boolean, self).__init__()
        self.content = content

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("content", self.content)
        ])

    def to_readable(self):
        return "{}(content={})".format(self.clsname, self.content)


# ############################## EXPRESSIONS ##############################


class Expr(AST):
    def __init__(self):
        super(Expr, self).__init__()


class NewObject(Expr):
    def __init__(self, new_type):
        super(NewObject, self).__init__()
        self.type = new_type

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("type", self.type)
        ])

    def to_readable(self):
        return "{}(type={})".format(self.clsname, self.type)


class IsVoid(Expr):
    def __init__(self, expr):
        super(IsVoid, self).__init__()
        self.expr = expr

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("expr", self.expr)
        ])

    def to_readable(self):
        return "{}(expr={})".format(self.clsname, self.expr)


class Assignment(Expr):
    def __init__(self, instance, expr):
        super(Assignment, self).__init__()
        self.instance = instance
        self.expr = expr

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("instance", self.instance),
            ("expr", self.expr)
        ])

    def to_readable(self):
        return "{}(instance={}, expr={})".format(self.clsname, self.instance, self.expr)


class Block(Expr):
    def __init__(self, expr_list):
        super(Block, self).__init__()
        self.expr_list = expr_list

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("expr_list", self.expr_list)
        ])

    def to_readable(self):
        return "{}(expr_list={})".format(self.clsname, self.expr_list)


class DynamicDispatch(Expr):
    def __init__(self, instance, method, arguments):
        super(DynamicDispatch, self).__init__()
        self.instance = instance
        self.method = method
        self.arguments = arguments if arguments is not None else tuple()

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("instance", self.instance),
            ("method", self.method),
            ("arguments", self.arguments)
        ])

    def to_readable(self):
        return "{}(instance={}, method={}, arguments={})".format(
            self.clsname, self.instance, self.method, self.arguments)


class StaticDispatch(Expr):
    def __init__(self, instance, dispatch_type, method, arguments):
        super(StaticDispatch, self).__init__()
        self.instance = instance
        self.dispatch_type = dispatch_type
        self.method = method
        self.arguments = arguments if arguments is not None else tuple()

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("instance", self.instance),
            ("dispatch_type", self.dispatch_type),
            ("method", self.method),
            ("arguments", self.arguments)
        ])

    def to_readable(self):
        return "{}(instance={}, dispatch_type={}, method={}, arguments={})".format(
            self.clsname, self.instance, self.dispatch_type, self.method, self.arguments)


class Let(Expr):
    def __init__(self, instance, return_type, init_expr, body):
        super(Let, self).__init__()
        self.instance = instance
        self.return_type = return_type
        self.init_expr = init_expr
        self.body = body

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("instance", self.instance),
            ("return_type", self.return_type),
            ("init_expr", self.init_expr),
            ("body", self.body)
        ])

    def to_readable(self):
        return "{}(instance={}, return_type={}, init_expr={}, body={})".format(
            self.clsname, self.instance, self.return_type, self.init_expr, self.body)


class If(Expr):
    def __init__(self, predicate, then_body, else_body):
        super(If, self).__init__()
        self.predicate = predicate
        self.then_body = then_body
        self.else_body = else_body

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("predicate", self.predicate),
            ("then_body", self.then_body),
            ("else_body", self.else_body)
        ])

    def to_readable(self):
        return "{}(predicate={}, then_body={}, else_body={})".format(
            self.clsname, self.predicate, self.then_body, self.else_body)


class WhileLoop(Expr):
    def __init__(self, predicate, body):
        super(WhileLoop, self).__init__()
        self.predicate = predicate
        self.body = body

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("predicate", self.predicate),
            ("body", self.body)
        ])

    def to_readable(self):
        return "{}(predicate={}, body={})".format(self.clsname, self.predicate, self.body)


class Case(Expr):
    def __init__(self, expr, actions):
        super(Case, self).__init__()
        self.expr = expr
        self.actions = actions

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("expr", self.expr),
            ("actions", self.actions)
        ])

    def to_readable(self):
        return "{}(expr={}, actions={})".format(self.clsname, self.expr, self.actions)


class Action(AST):
    def __init__(self, name, action_type, body):
        super(Action, self).__init__()
        self.name = name
        self.action_type = action_type
        self.body = body

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("name", self.name),
            ("action_type", self.action_type),
            ("body", self.body)
        ])

    def to_readable(self):
        return "{}(name='{}', action_type={}, body={})".format(self.clsname, self.name, self.action_type, self.body)


# ############################## UNARY OPERATIONS ##################################


class UnaryOperation(Expr):
    def __init__(self):
        super(UnaryOperation, self).__init__()


class IntegerComplement(UnaryOperation):
    def __init__(self, integer_expr):
        super(IntegerComplement, self).__init__()
        self.symbol = "~"
        self.integer_expr = integer_expr

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("integer_expr", self.integer_expr)
        ])

    def to_readable(self):
        return "{}(expr={})".format(self.clsname, self.integer_expr)


class BooleanComplement(UnaryOperation):
    def __init__(self, boolean_expr):
        super(BooleanComplement, self).__init__()
        self.symbol = "!"
        self.boolean_expr = boolean_expr

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("boolean_expr", self.boolean_expr)
        ])

    def to_readable(self):
        return "{}(expr={})".format(self.clsname, self.boolean_expr)


# ############################## BINARY OPERATIONS ##################################


class BinaryOperation(Expr):
    def __init__(self):
        super(BinaryOperation, self).__init__()

class Addition(BinaryOperation):
    def __init__(self, first, second):
        super(Addition, self).__init__()
        self.symbol = "+"
        self.first = first
        self.second = second

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second)
        ])

    def to_readable(self):
        return "{}(first={}, second={})".format(self.clsname, self.first, self.second)


class Subtraction(BinaryOperation):
    def __init__(self, first, second):
        super(Subtraction, self).__init__()
        self.symbol = "-"
        self.first = first
        self.second = second

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second)
        ])

    def to_readable(self):
        return "{}(first={}, second={})".format(self.clsname, self.first, self.second)


class Multiplication(BinaryOperation):
    def __init__(self, first, second):
        super(Multiplication, self).__init__()
        self.symbol = "*"
        self.first = first
        self.second = second

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second)
        ])

    def to_readable(self):
        return "{}(first={}, second={})".format(self.clsname, self.first, self.second)


class Division(BinaryOperation):
    def __init__(self, first, second):
        super(Division, self).__init__()
        self.symbol = "/"
        self.first = first
        self.second = second

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second)
        ])

    def to_readable(self):
        return "{}(first={}, second={})".format(self.clsname, self.first, self.second)


class Equal(BinaryOperation):
    def __init__(self, first, second):
        super(Equal, self).__init__()
        self.symbol = "="
        self.first = first
        self.second = second

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second)
        ])

    def to_readable(self):
        return "{}(first={}, second={})".format(self.clsname, self.first, self.second)


class LessThan(BinaryOperation):
    def __init__(self, first, second):
        super(LessThan, self).__init__()
        self.symbol = "<"
        self.first = first
        self.second = second

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second)
        ])

    def to_readable(self):
        return "{}(first={}, second={})".format(self.clsname, self.first, self.second)


class LessThanOrEqual(BinaryOperation):
    def __init__(self, first, second):
        super(LessThanOrEqual, self).__init__()
        self.symbol = "<="
        self.first = first
        self.second = second

    def to_tuple(self):
        return tuple([
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second)
        ])

    def to_readable(self):
        return "{}(first={}, second={})".format(self.clsname, self.first, self.second)


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

