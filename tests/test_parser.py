"""
Tests for the COOL parser.

These tests verify that the parser correctly builds AST nodes
from valid COOL programs and handles syntax errors appropriately.
"""

import pytest

import pycoolc.ast as AST
from pycoolc.parser import make_parser


@pytest.fixture
def parser():
    """Create a fresh parser for each test."""
    return make_parser()


class TestProgramStructure:
    """Tests for top-level program and class parsing."""

    def test_empty_class(self, parser):
        result = parser.parse("class Main { };")
        assert isinstance(result, AST.Program)
        assert len(result.classes) == 1
        assert result.classes[0].name == "Main"
        assert result.classes[0].parent == "Object"
        assert result.classes[0].features == ()

    def test_class_with_inheritance(self, parser):
        result = parser.parse("class Child inherits Parent { };")
        assert result.classes[0].name == "Child"
        assert result.classes[0].parent == "Parent"

    def test_multiple_classes(self, parser):
        result = parser.parse("""
            class A { };
            class B { };
            class C { };
        """)
        assert len(result.classes) == 3
        names = [c.name for c in result.classes]
        assert names == ["A", "B", "C"]


class TestClassAttributes:
    """Tests for class attribute parsing."""

    def test_simple_attribute(self, parser):
        result = parser.parse("class Main { x : Int; };")
        attr = result.classes[0].features[0]
        assert isinstance(attr, AST.ClassAttribute)
        assert attr.name == "x"
        assert attr.attr_type == "Int"
        assert attr.init_expr is None

    def test_initialized_attribute(self, parser):
        result = parser.parse("class Main { x : Int <- 42; };")
        attr = result.classes[0].features[0]
        assert attr.name == "x"
        assert attr.attr_type == "Int"
        assert isinstance(attr.init_expr, AST.Integer)
        assert attr.init_expr.content == 42

    def test_multiple_attributes(self, parser):
        result = parser.parse("""
            class Main {
                x : Int;
                y : String <- "hello";
                z : Bool <- true;
            };
        """)
        features = result.classes[0].features
        assert len(features) == 3
        assert features[0].name == "x"
        assert features[1].name == "y"
        assert features[2].name == "z"


class TestClassMethods:
    """Tests for class method parsing."""

    def test_method_no_params(self, parser):
        result = parser.parse("class Main { foo() : Int { 42 }; };")
        method = result.classes[0].features[0]
        assert isinstance(method, AST.ClassMethod)
        assert method.name == "foo"
        assert method.formal_params == ()
        assert method.return_type == "Int"
        assert isinstance(method.body, AST.Integer)

    def test_method_with_params(self, parser):
        result = parser.parse("class Main { add(x : Int, y : Int) : Int { x }; };")
        method = result.classes[0].features[0]
        assert method.name == "add"
        assert len(method.formal_params) == 2
        assert method.formal_params[0].name == "x"
        assert method.formal_params[0].param_type == "Int"
        assert method.formal_params[1].name == "y"

    def test_method_returning_self_type(self, parser):
        result = parser.parse("class Main { myself() : SELF_TYPE { self }; };")
        method = result.classes[0].features[0]
        assert method.return_type == "SELF_TYPE"
        assert isinstance(method.body, AST.Self)


class TestLiteralExpressions:
    """Tests for literal expression parsing."""

    def test_integer_literal(self, parser):
        result = parser.parse("class Main { x : Int <- 123; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.Integer)
        assert expr.content == 123

    def test_string_literal(self, parser):
        result = parser.parse('class Main { x : String <- "hello"; };')
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.String)
        assert expr.content == "hello"

    def test_boolean_true(self, parser):
        result = parser.parse("class Main { x : Bool <- true; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.Boolean)
        assert expr.content is True

    def test_boolean_false(self, parser):
        result = parser.parse("class Main { x : Bool <- false; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.Boolean)
        assert expr.content is False


class TestArithmeticExpressions:
    """Tests for arithmetic expression parsing."""

    def test_addition(self, parser):
        result = parser.parse("class Main { x : Int <- 1 + 2; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.Addition)
        assert isinstance(expr.first, AST.Integer)
        assert isinstance(expr.second, AST.Integer)

    def test_subtraction(self, parser):
        result = parser.parse("class Main { x : Int <- 5 - 3; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.Subtraction)

    def test_multiplication(self, parser):
        result = parser.parse("class Main { x : Int <- 2 * 3; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.Multiplication)

    def test_division(self, parser):
        result = parser.parse("class Main { x : Int <- 10 / 2; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.Division)

    def test_precedence_mult_over_add(self, parser):
        # 1 + 2 * 3 should parse as 1 + (2 * 3)
        result = parser.parse("class Main { x : Int <- 1 + 2 * 3; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.Addition)
        assert isinstance(expr.first, AST.Integer)
        assert isinstance(expr.second, AST.Multiplication)

    def test_parentheses_override_precedence(self, parser):
        # (1 + 2) * 3
        result = parser.parse("class Main { x : Int <- (1 + 2) * 3; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.Multiplication)
        assert isinstance(expr.first, AST.Addition)

    def test_integer_complement(self, parser):
        result = parser.parse("class Main { x : Int <- ~42; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.IntegerComplement)
        assert isinstance(expr.integer_expr, AST.Integer)


class TestComparisonExpressions:
    """Tests for comparison expression parsing."""

    def test_less_than(self, parser):
        result = parser.parse("class Main { x : Bool <- 1 < 2; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.LessThan)

    def test_less_than_or_equal(self, parser):
        result = parser.parse("class Main { x : Bool <- 1 <= 2; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.LessThanOrEqual)

    def test_equality(self, parser):
        result = parser.parse("class Main { x : Bool <- 1 = 2; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.Equal)


class TestBooleanExpressions:
    """Tests for boolean expression parsing."""

    def test_boolean_not(self, parser):
        result = parser.parse("class Main { x : Bool <- not true; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.BooleanComplement)

    def test_boolean_not_case_insensitive(self, parser):
        # COOL keywords are case-insensitive
        result = parser.parse("class Main { x : Bool <- NOT false; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.BooleanComplement)


class TestAssignment:
    """Tests for assignment expression parsing."""

    def test_simple_assignment(self, parser):
        result = parser.parse("class Main { foo() : Int { x <- 42 }; };")
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.Assignment)
        assert expr.instance.name == "x"
        assert isinstance(expr.expr, AST.Integer)


class TestMethodDispatch:
    """Tests for method dispatch parsing."""

    def test_dynamic_dispatch(self, parser):
        result = parser.parse("class Main { foo() : Int { obj.method() }; };")
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.DynamicDispatch)
        assert expr.method == "method"
        assert isinstance(expr.instance, AST.Object)
        assert expr.instance.name == "obj"

    def test_dispatch_with_arguments(self, parser):
        result = parser.parse("class Main { foo() : Int { obj.method(1, 2, 3) }; };")
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.DynamicDispatch)
        assert len(expr.arguments) == 3

    def test_static_dispatch(self, parser):
        result = parser.parse("class Main { foo() : Object { self@Object.abort() }; };")
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.StaticDispatch)
        assert expr.dispatch_type == "Object"
        assert expr.method == "abort"

    def test_self_dispatch(self, parser):
        # Method call without explicit receiver implies self
        result = parser.parse("class Main { foo() : Int { bar() }; };")
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.DynamicDispatch)
        assert isinstance(expr.instance, AST.Self)
        assert expr.method == "bar"


class TestControlFlow:
    """Tests for control flow expression parsing."""

    def test_if_then_else(self, parser):
        result = parser.parse("""
            class Main {
                foo() : Int { if true then 1 else 2 fi };
            };
        """)
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.If)
        assert isinstance(expr.predicate, AST.Boolean)
        assert isinstance(expr.then_body, AST.Integer)
        assert isinstance(expr.else_body, AST.Integer)

    def test_while_loop(self, parser):
        result = parser.parse("""
            class Main {
                foo() : Object { while true loop 0 pool };
            };
        """)
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.WhileLoop)
        assert isinstance(expr.predicate, AST.Boolean)
        assert isinstance(expr.body, AST.Integer)


class TestBlockExpressions:
    """Tests for block expression parsing."""

    def test_single_expression_block(self, parser):
        result = parser.parse("class Main { foo() : Int { { 42; } }; };")
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.Block)
        assert len(expr.expr_list) == 1

    def test_multi_expression_block(self, parser):
        result = parser.parse("""
            class Main {
                foo() : Int { { 1; 2; 3; } };
            };
        """)
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.Block)
        assert len(expr.expr_list) == 3


class TestLetExpressions:
    """Tests for let expression parsing."""

    def test_simple_let(self, parser):
        result = parser.parse("class Main { foo() : Int { let x : Int in x }; };")
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.Let)
        assert expr.instance == "x"
        assert expr.return_type == "Int"
        assert expr.init_expr is None

    def test_let_with_initialization(self, parser):
        result = parser.parse("class Main { foo() : Int { let x : Int <- 42 in x }; };")
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.Let)
        assert expr.init_expr is not None
        assert isinstance(expr.init_expr, AST.Integer)

    def test_multi_binding_let(self, parser):
        """Test let with multiple comma-separated bindings."""
        result = parser.parse("""
            class Main {
                foo() : Int {
                    let x : Int <- 1, y : Int <- 2, z : Int <- 3 in
                        x + y + z
                };
            };
        """)
        # Should produce nested Let nodes
        let1 = result.classes[0].features[0].body
        assert isinstance(let1, AST.Let)
        assert let1.instance == "x"
        assert let1.return_type == "Int"

        let2 = let1.body
        assert isinstance(let2, AST.Let)
        assert let2.instance == "y"

        let3 = let2.body
        assert isinstance(let3, AST.Let)
        assert let3.instance == "z"

        # Innermost body should be the addition
        assert isinstance(let3.body, AST.Addition)

    def test_multi_binding_let_mixed_init(self, parser):
        """Test let with mix of initialized and uninitialized bindings."""
        result = parser.parse("""
            class Main {
                foo() : Int {
                    let x : Int, y : Int <- 2 in y
                };
            };
        """)
        let1 = result.classes[0].features[0].body
        assert let1.instance == "x"
        assert let1.init_expr is None

        let2 = let1.body
        assert let2.instance == "y"
        assert let2.init_expr is not None


class TestCaseExpressions:
    """Tests for case expression parsing."""

    def test_simple_case(self, parser):
        result = parser.parse("""
            class Main {
                foo() : Int {
                    case x of
                        y : Int => 1;
                    esac
                };
            };
        """)
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.Case)
        assert len(expr.actions) == 1

    def test_multi_branch_case(self, parser):
        result = parser.parse("""
            class Main {
                foo() : Int {
                    case x of
                        a : Int => 1;
                        b : String => 2;
                        c : Bool => 3;
                    esac
                };
            };
        """)
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.Case)
        assert len(expr.actions) == 3


class TestNewAndIsvoid:
    """Tests for new and isvoid expressions."""

    def test_new_object(self, parser):
        result = parser.parse("class Main { x : Foo <- new Foo; };")
        expr = result.classes[0].features[0].init_expr
        assert isinstance(expr, AST.NewObject)
        assert expr.type == "Foo"

    def test_isvoid(self, parser):
        result = parser.parse("class Main { foo() : Bool { isvoid x }; };")
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.IsVoid)


class TestSelfExpression:
    """Tests for self expression parsing."""

    def test_self_keyword(self, parser):
        result = parser.parse("class Main { foo() : SELF_TYPE { self }; };")
        expr = result.classes[0].features[0].body
        assert isinstance(expr, AST.Self)


class TestComplexPrograms:
    """Integration tests with realistic COOL programs."""

    def test_hello_world(self, parser):
        program = """
            class Main inherits IO {
                main(): SELF_TYPE {
                    out_string("Hello, World.\\n")
                };
            };
        """
        result = parser.parse(program)
        assert result.classes[0].name == "Main"
        assert result.classes[0].parent == "IO"
        method = result.classes[0].features[0]
        assert method.name == "main"
        assert isinstance(method.body, AST.DynamicDispatch)

    def test_factorial(self, parser):
        program = """
            class Main {
                factorial(n : Int) : Int {
                    if n = 0 then 1 else n * factorial(n - 1) fi
                };
            };
        """
        result = parser.parse(program)
        method = result.classes[0].features[0]
        assert method.name == "factorial"
        assert isinstance(method.body, AST.If)

    def test_class_with_multiple_features(self, parser):
        program = """
            class Counter {
                count : Int <- 0;

                increment() : Int {
                    count <- count + 1
                };

                get() : Int {
                    count
                };
            };
        """
        result = parser.parse(program)
        assert len(result.classes[0].features) == 3


class TestParserAPI:
    """Tests for parser's public API."""

    def test_parse_returns_program(self, parser):
        result = parser.parse("class Main { };")
        assert isinstance(result, AST.Program)

    def test_unbuilt_parser_raises(self):
        from pycoolc.parser import PyCoolParser

        p = PyCoolParser(build_parser=False)
        with pytest.raises(ValueError, match="Parser was not build"):
            p.parse("class Main { };")
