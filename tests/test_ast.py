"""
Tests for AST node classes.

These tests verify the to_tuple(), to_readable(), __str__, and __repr__
methods on AST nodes.
"""

from pycoolc import ast as AST


class TestASTBase:
    """Tests for the base AST class."""

    def test_clsname(self):
        node = AST.Integer(content=42)
        assert node.clsname == "Integer"

    def test_base_to_tuple(self):
        node = AST.Self()
        result = node.to_tuple()
        assert isinstance(result, tuple)
        assert ("class_name", "Self") in result

    def test_str_repr(self):
        node = AST.Integer(content=42)
        assert str(node) == repr(node)


class TestProgram:
    """Tests for Program node."""

    def test_to_tuple(self):
        program = AST.Program(classes=())
        result = program.to_tuple()
        assert ("class_name", "Program") in result
        assert ("classes", ()) in result

    def test_to_readable(self):
        program = AST.Program(classes=())
        readable = program.to_readable()
        assert "Program" in readable
        assert "classes=" in readable


class TestClass:
    """Tests for Class node."""

    def test_to_tuple(self):
        cls = AST.Class(name="Foo", parent="Object", features=())
        result = cls.to_tuple()
        assert ("name", "Foo") in result
        assert ("parent", "Object") in result

    def test_to_readable(self):
        cls = AST.Class(name="Foo", parent="Object", features=())
        readable = cls.to_readable()
        assert "Foo" in readable
        assert "Object" in readable


class TestClassMethod:
    """Tests for ClassMethod node."""

    def test_to_tuple(self):
        method = AST.ClassMethod(name="foo", formal_params=(), return_type="Int", body=None)
        result = method.to_tuple()
        assert ("name", "foo") in result
        assert ("return_type", "Int") in result

    def test_to_readable(self):
        method = AST.ClassMethod(name="foo", formal_params=(), return_type="Int", body=None)
        readable = method.to_readable()
        assert "foo" in readable


class TestClassAttribute:
    """Tests for ClassAttribute node."""

    def test_to_tuple(self):
        attr = AST.ClassAttribute(name="x", attr_type="Int", init_expr=None)
        result = attr.to_tuple()
        assert ("name", "x") in result
        assert ("attr_type", "Int") in result

    def test_to_readable(self):
        attr = AST.ClassAttribute(name="x", attr_type="Int", init_expr=None)
        readable = attr.to_readable()
        assert "x" in readable


class TestFormalParameter:
    """Tests for FormalParameter node."""

    def test_to_tuple(self):
        param = AST.FormalParameter(name="x", param_type="Int")
        result = param.to_tuple()
        assert ("name", "x") in result
        assert ("param_type", "Int") in result

    def test_to_readable(self):
        param = AST.FormalParameter(name="x", param_type="Int")
        readable = param.to_readable()
        assert "x" in readable


class TestLiterals:
    """Tests for literal nodes."""

    def test_integer_to_tuple(self):
        node = AST.Integer(content=42)
        result = node.to_tuple()
        assert ("content", 42) in result

    def test_integer_to_readable(self):
        node = AST.Integer(content=42)
        assert "42" in node.to_readable()

    def test_string_to_tuple(self):
        node = AST.String(content="hello")
        result = node.to_tuple()
        assert ("content", "hello") in result

    def test_string_to_readable(self):
        node = AST.String(content="hello")
        assert "hello" in node.to_readable()

    def test_boolean_to_tuple(self):
        node = AST.Boolean(content=True)
        result = node.to_tuple()
        assert ("content", True) in result

    def test_boolean_to_readable(self):
        node = AST.Boolean(content=True)
        assert "True" in node.to_readable()


class TestObject:
    """Tests for Object node."""

    def test_to_tuple(self):
        node = AST.Object(name="x")
        result = node.to_tuple()
        assert ("name", "x") in result

    def test_to_readable(self):
        node = AST.Object(name="x")
        assert "x" in node.to_readable()


class TestSelf:
    """Tests for Self node."""

    def test_to_tuple(self):
        node = AST.Self()
        result = node.to_tuple()
        assert ("class_name", "Self") in result

    def test_to_readable(self):
        node = AST.Self()
        assert "Self" in node.to_readable()


class TestArithmetic:
    """Tests for arithmetic operation nodes."""

    def test_addition_to_tuple(self):
        node = AST.Addition(first=AST.Integer(1), second=AST.Integer(2))
        result = node.to_tuple()
        assert "first" in [k for k, v in result]

    def test_addition_to_readable(self):
        node = AST.Addition(first=AST.Integer(1), second=AST.Integer(2))
        assert "Addition" in node.to_readable()

    def test_subtraction_to_readable(self):
        node = AST.Subtraction(first=AST.Integer(1), second=AST.Integer(2))
        assert "Subtraction" in node.to_readable()

    def test_multiplication_to_readable(self):
        node = AST.Multiplication(first=AST.Integer(1), second=AST.Integer(2))
        assert "Multiplication" in node.to_readable()

    def test_division_to_readable(self):
        node = AST.Division(first=AST.Integer(1), second=AST.Integer(2))
        assert "Division" in node.to_readable()


class TestComparisons:
    """Tests for comparison operation nodes."""

    def test_less_than_to_readable(self):
        node = AST.LessThan(first=AST.Integer(1), second=AST.Integer(2))
        assert "LessThan" in node.to_readable()

    def test_less_than_or_equal_to_readable(self):
        node = AST.LessThanOrEqual(first=AST.Integer(1), second=AST.Integer(2))
        assert "LessThanOrEqual" in node.to_readable()

    def test_equal_to_readable(self):
        node = AST.Equal(first=AST.Integer(1), second=AST.Integer(2))
        assert "Equal" in node.to_readable()


class TestUnaryOperations:
    """Tests for unary operation nodes."""

    def test_integer_complement_to_readable(self):
        node = AST.IntegerComplement(integer_expr=AST.Integer(5))
        assert "IntegerComplement" in node.to_readable()

    def test_boolean_complement_to_readable(self):
        node = AST.BooleanComplement(boolean_expr=AST.Boolean(True))
        assert "BooleanComplement" in node.to_readable()


class TestControlFlow:
    """Tests for control flow nodes."""

    def test_if_to_readable(self):
        node = AST.If(
            predicate=AST.Boolean(True), then_body=AST.Integer(1), else_body=AST.Integer(0)
        )
        assert "If" in node.to_readable()

    def test_while_to_readable(self):
        node = AST.WhileLoop(predicate=AST.Boolean(True), body=AST.Integer(1))
        assert "WhileLoop" in node.to_readable()

    def test_block_to_readable(self):
        node = AST.Block(expr_list=(AST.Integer(1), AST.Integer(2)))
        assert "Block" in node.to_readable()


class TestLet:
    """Tests for Let node."""

    def test_to_tuple(self):
        node = AST.Let(instance="x", return_type="Int", init_expr=None, body=AST.Object("x"))
        result = node.to_tuple()
        assert ("instance", "x") in result

    def test_to_readable(self):
        node = AST.Let(instance="x", return_type="Int", init_expr=None, body=AST.Object("x"))
        assert "Let" in node.to_readable()


class TestCase:
    """Tests for Case node."""

    def test_to_readable(self):
        node = AST.Case(expr=AST.Self(), actions=(("x", "Object", AST.Object("x")),))
        assert "Case" in node.to_readable()


class TestDispatch:
    """Tests for dispatch nodes."""

    def test_dynamic_dispatch_to_readable(self):
        node = AST.DynamicDispatch(instance=AST.Self(), method="foo", arguments=())
        assert "DynamicDispatch" in node.to_readable()

    def test_static_dispatch_to_readable(self):
        node = AST.StaticDispatch(
            instance=AST.Self(), dispatch_type="Object", method="foo", arguments=()
        )
        assert "StaticDispatch" in node.to_readable()


class TestNewObject:
    """Tests for NewObject node."""

    def test_to_tuple(self):
        node = AST.NewObject(new_type="Foo")
        result = node.to_tuple()
        assert ("type", "Foo") in result

    def test_to_readable(self):
        node = AST.NewObject(new_type="Foo")
        assert "NewObject" in node.to_readable()


class TestIsVoid:
    """Tests for IsVoid node."""

    def test_to_readable(self):
        node = AST.IsVoid(expr=AST.Self())
        assert "IsVoid" in node.to_readable()


class TestAssignment:
    """Tests for Assignment node."""

    def test_to_readable(self):
        node = AST.Assignment(instance=AST.Object("x"), expr=AST.Integer(5))
        assert "Assignment" in node.to_readable()


class TestAction:
    """Tests for Action node."""

    def test_to_readable(self):
        node = AST.Action(name="x", action_type="Int", body=AST.Object("x"))
        assert "Action" in node.to_readable()
