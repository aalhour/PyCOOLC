# -----------------------------------------------------------------------------
# ast.py
#
# Author:       Ahmad Alhour (aalhour.com).
# Date:         May 26rd, 2016.
# Description:  The Abstract Syntax Tree module. Provides classes for managing
#               the parse tree.
# -----------------------------------------------------------------------------

from __future__ import annotations
from typing import Any


# ############################## BASE AST NODES CLASSES ##############################


class AST:
    """Base class for all AST nodes."""

    @property
    def clsname(self) -> str:
        return self.__class__.__name__

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (("class_name", self.clsname),)

    def to_readable(self) -> str:
        return f"{self.clsname}"

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return self.to_readable()


# ############################## PROGRAM, TYPE AND OBJECT ##############################


class Program(AST):
    """Root AST node representing a complete COOL program."""

    def __init__(self, classes: tuple[Class, ...]) -> None:
        self.classes = classes

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("classes", self.classes),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(classes={self.classes})"


class Class(AST):
    """AST node for a class definition."""

    def __init__(self, name: str, parent: str | None, features: tuple[ClassFeature, ...]) -> None:
        self.name = name
        self.parent = parent
        self.features = features

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("name", self.name),
            ("parent", self.parent),
            ("features", self.features),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(name='{self.name}', parent={self.parent}, features={self.features})"


class ClassFeature(AST):
    """Base class for class features (attributes and methods)."""
    pass


class ClassMethod(ClassFeature):
    """AST node for a method definition."""

    def __init__(
        self,
        name: str,
        formal_params: tuple[FormalParameter, ...],
        return_type: str,
        body: AST | None,
    ) -> None:
        self.name = name
        self.formal_params = formal_params
        self.return_type = return_type
        self.body = body

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("name", self.name),
            ("formal_params", self.formal_params),
            ("return_type", self.return_type),
            ("body", self.body),
        )

    def to_readable(self) -> str:
        return (
            f"{self.clsname}(name='{self.name}', formal_params={self.formal_params}, "
            f"return_type={self.return_type}, body={self.body})"
        )


class ClassAttribute(ClassFeature):
    """AST node for a class attribute definition."""

    def __init__(self, name: str, attr_type: str, init_expr: AST | None) -> None:
        self.name = name
        self.attr_type = attr_type
        self.init_expr = init_expr

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("name", self.name),
            ("attr_type", self.attr_type),
            ("init_expr", self.init_expr),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(name='{self.name}', attr_type={self.attr_type}, init_expr={self.init_expr})"


class FormalParameter(ClassFeature):
    """AST node for a formal parameter in a method signature."""

    def __init__(self, name: str, param_type: str) -> None:
        self.name = name
        self.param_type = param_type

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("name", self.name),
            ("param_type", self.param_type),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(name='{self.name}', param_type={self.param_type})"


class Object(AST):
    """AST node for an object identifier (variable reference)."""

    def __init__(self, name: str) -> None:
        self.name = name

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("name", self.name),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(name='{self.name}')"


class Self(Object):
    """AST node for the 'self' keyword."""

    def __init__(self) -> None:
        super().__init__("SELF")

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (("class_name", self.clsname),)

    def to_readable(self) -> str:
        return self.clsname


# ############################## CONSTANTS ##############################


class Constant(AST):
    """Base class for literal constants."""
    pass


class Integer(Constant):
    """AST node for an integer literal."""

    def __init__(self, content: int) -> None:
        self.content = content

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("content", self.content),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(content={self.content})"


class String(Constant):
    """AST node for a string literal."""

    def __init__(self, content: str) -> None:
        self.content = content

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("content", self.content),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(content={self.content!r})"


class Boolean(Constant):
    """AST node for a boolean literal."""

    def __init__(self, content: bool) -> None:
        self.content = content

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("content", self.content),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(content={self.content})"


# ############################## EXPRESSIONS ##############################


class Expr(AST):
    """Base class for expression nodes."""
    pass


class NewObject(Expr):
    """AST node for 'new Type' expression."""

    def __init__(self, new_type: str) -> None:
        self.type = new_type

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("type", self.type),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(type={self.type})"


class IsVoid(Expr):
    """AST node for 'isvoid expr' expression."""

    def __init__(self, expr: AST) -> None:
        self.expr = expr

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("expr", self.expr),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(expr={self.expr})"


class Assignment(Expr):
    """AST node for assignment expression 'id <- expr'."""

    def __init__(self, instance: Object, expr: AST) -> None:
        self.instance = instance
        self.expr = expr

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("instance", self.instance),
            ("expr", self.expr),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(instance={self.instance}, expr={self.expr})"


class Block(Expr):
    """AST node for block expression '{ expr1; expr2; ... }'."""

    def __init__(self, expr_list: tuple[AST, ...]) -> None:
        self.expr_list = expr_list

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("expr_list", self.expr_list),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(expr_list={self.expr_list})"


class DynamicDispatch(Expr):
    """AST node for dynamic method dispatch 'expr.method(args)'."""

    def __init__(self, instance: AST, method: str, arguments: tuple[AST, ...] | None) -> None:
        self.instance = instance
        self.method = method
        self.arguments = arguments if arguments is not None else ()

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("instance", self.instance),
            ("method", self.method),
            ("arguments", self.arguments),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(instance={self.instance}, method={self.method}, arguments={self.arguments})"


class StaticDispatch(Expr):
    """AST node for static method dispatch 'expr@Type.method(args)'."""

    def __init__(
        self,
        instance: AST,
        dispatch_type: str,
        method: str,
        arguments: tuple[AST, ...] | None,
    ) -> None:
        self.instance = instance
        self.dispatch_type = dispatch_type
        self.method = method
        self.arguments = arguments if arguments is not None else ()

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("instance", self.instance),
            ("dispatch_type", self.dispatch_type),
            ("method", self.method),
            ("arguments", self.arguments),
        )

    def to_readable(self) -> str:
        return (
            f"{self.clsname}(instance={self.instance}, dispatch_type={self.dispatch_type}, "
            f"method={self.method}, arguments={self.arguments})"
        )


class Let(Expr):
    """AST node for let expression 'let id : Type [<- expr] in body'."""

    def __init__(self, instance: str, return_type: str, init_expr: AST | None, body: AST) -> None:
        self.instance = instance
        self.return_type = return_type
        self.init_expr = init_expr
        self.body = body

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("instance", self.instance),
            ("return_type", self.return_type),
            ("init_expr", self.init_expr),
            ("body", self.body),
        )

    def to_readable(self) -> str:
        return (
            f"{self.clsname}(instance={self.instance}, return_type={self.return_type}, "
            f"init_expr={self.init_expr}, body={self.body})"
        )


class If(Expr):
    """AST node for if expression 'if pred then expr1 else expr2 fi'."""

    def __init__(self, predicate: AST, then_body: AST, else_body: AST) -> None:
        self.predicate = predicate
        self.then_body = then_body
        self.else_body = else_body

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("predicate", self.predicate),
            ("then_body", self.then_body),
            ("else_body", self.else_body),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(predicate={self.predicate}, then_body={self.then_body}, else_body={self.else_body})"


class WhileLoop(Expr):
    """AST node for while loop 'while pred loop expr pool'."""

    def __init__(self, predicate: AST, body: AST) -> None:
        self.predicate = predicate
        self.body = body

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("predicate", self.predicate),
            ("body", self.body),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(predicate={self.predicate}, body={self.body})"


class Case(Expr):
    """AST node for case expression 'case expr of branches esac'."""

    def __init__(self, expr: AST, actions: tuple[tuple[str, str, AST], ...]) -> None:
        self.expr = expr
        self.actions = actions

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("expr", self.expr),
            ("actions", self.actions),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(expr={self.expr}, actions={self.actions})"


class Action(AST):
    """AST node for a case branch 'id : Type => expr'."""

    def __init__(self, name: str, action_type: str, body: AST) -> None:
        self.name = name
        self.action_type = action_type
        self.body = body

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("name", self.name),
            ("action_type", self.action_type),
            ("body", self.body),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(name='{self.name}', action_type={self.action_type}, body={self.body})"


# ############################## UNARY OPERATIONS ##################################


class UnaryOperation(Expr):
    """Base class for unary operations."""
    pass


class IntegerComplement(UnaryOperation):
    """AST node for integer complement '~expr'."""

    def __init__(self, integer_expr: AST) -> None:
        self.symbol = "~"
        self.integer_expr = integer_expr

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("integer_expr", self.integer_expr),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(expr={self.integer_expr})"


class BooleanComplement(UnaryOperation):
    """AST node for boolean complement 'not expr'."""

    def __init__(self, boolean_expr: AST) -> None:
        self.symbol = "!"
        self.boolean_expr = boolean_expr

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("boolean_expr", self.boolean_expr),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(expr={self.boolean_expr})"


# ############################## BINARY OPERATIONS ##################################


class BinaryOperation(Expr):
    """Base class for binary operations."""
    pass


class Addition(BinaryOperation):
    """AST node for addition 'expr + expr'."""

    def __init__(self, first: AST, second: AST) -> None:
        self.symbol = "+"
        self.first = first
        self.second = second

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(first={self.first}, second={self.second})"


class Subtraction(BinaryOperation):
    """AST node for subtraction 'expr - expr'."""

    def __init__(self, first: AST, second: AST) -> None:
        self.symbol = "-"
        self.first = first
        self.second = second

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(first={self.first}, second={self.second})"


class Multiplication(BinaryOperation):
    """AST node for multiplication 'expr * expr'."""

    def __init__(self, first: AST, second: AST) -> None:
        self.symbol = "*"
        self.first = first
        self.second = second

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(first={self.first}, second={self.second})"


class Division(BinaryOperation):
    """AST node for division 'expr / expr'."""

    def __init__(self, first: AST, second: AST) -> None:
        self.symbol = "/"
        self.first = first
        self.second = second

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(first={self.first}, second={self.second})"


class Equal(BinaryOperation):
    """AST node for equality comparison 'expr = expr'."""

    def __init__(self, first: AST, second: AST) -> None:
        self.symbol = "="
        self.first = first
        self.second = second

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(first={self.first}, second={self.second})"


class LessThan(BinaryOperation):
    """AST node for less-than comparison 'expr < expr'."""

    def __init__(self, first: AST, second: AST) -> None:
        self.symbol = "<"
        self.first = first
        self.second = second

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(first={self.first}, second={self.second})"


class LessThanOrEqual(BinaryOperation):
    """AST node for less-than-or-equal comparison 'expr <= expr'."""

    def __init__(self, first: AST, second: AST) -> None:
        self.symbol = "<="
        self.first = first
        self.second = second

    def to_tuple(self) -> tuple[tuple[str, Any], ...]:
        return (
            ("class_name", self.clsname),
            ("first", self.first),
            ("second", self.second),
        )

    def to_readable(self) -> str:
        return f"{self.clsname}(first={self.first}, second={self.second})"


# ############################## HELPER FUNCTIONS ##############################


def is_valid_unary_operation(operation: str) -> bool:
    """Check if operation is a valid unary operator."""
    return operation in ("~", "not")


def is_valid_binary_operation(operation: str) -> bool:
    """Check if operation is a valid binary operator."""
    return operation in ("+", "-", "*", "/", "<", "<=", "=")


def get_operation(operation: str | None) -> str | None:
    """Convert operation name to symbol."""
    if operation is None or not isinstance(operation, str):
        return None

    ops = {
        "PLUS": "+",
        "MINUS": "-",
        "TIMES": "*",
        "DIVIDE": "/",
        "LTHAN": "<",
        "LTEQ": "<=",
        "EQUALS": "=",
        "NOT": "not",
        "INT_COMP": "~",
    }
    return ops.get(operation.upper())
