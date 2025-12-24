"""
Tests for utility functions (utils.py).
"""

from pycoolc import ast as AST
from pycoolc.utils import print_readable_ast


class TestPrintReadableAST:
    """Tests for the print_readable_ast function."""

    def test_prints_simple_class(self, capsys):
        program = AST.Program(classes=(AST.Class(name="Main", parent="Object", features=()),))
        print_readable_ast(program)
        captured = capsys.readouterr()
        assert "Program" in captured.out
        assert "Main" in captured.out

    def test_prints_integer_literal(self, capsys):
        expr = AST.Integer(content=42)
        print_readable_ast(expr)
        captured = capsys.readouterr()
        assert "Integer" in captured.out
        assert "42" in captured.out

    def test_prints_string_literal(self, capsys):
        expr = AST.String(content="hello")
        print_readable_ast(expr)
        captured = capsys.readouterr()
        assert "String" in captured.out
        assert "hello" in captured.out

    def test_prints_boolean_true(self, capsys):
        expr = AST.Boolean(content=True)
        print_readable_ast(expr)
        captured = capsys.readouterr()
        assert "Boolean" in captured.out
        assert "True" in captured.out

    def test_prints_empty_tuple(self, capsys):
        print_readable_ast(())
        captured = capsys.readouterr()
        assert "()" in captured.out

    def test_prints_empty_list(self, capsys):
        print_readable_ast([])
        captured = capsys.readouterr()
        assert "[]" in captured.out

    def test_prints_tuple_with_elements(self, capsys):
        print_readable_ast((1, 2, 3))
        captured = capsys.readouterr()
        assert "1" in captured.out
        assert "2" in captured.out
        assert "3" in captured.out

    def test_prints_list_with_elements(self, capsys):
        print_readable_ast([1, 2, 3])
        captured = capsys.readouterr()
        assert "1" in captured.out
        assert "2" in captured.out
        assert "3" in captured.out

    def test_prints_primitive_types(self, capsys):
        print_readable_ast(42)
        captured = capsys.readouterr()
        assert "42" in captured.out

    def test_prints_string_primitives(self, capsys):
        print_readable_ast("hello")
        captured = capsys.readouterr()
        assert "'hello'" in captured.out

    def test_handles_nested_ast(self, capsys):
        program = AST.Program(
            classes=(
                AST.Class(
                    name="Main",
                    parent="Object",
                    features=(
                        AST.ClassMethod(
                            name="main",
                            formal_params=(),
                            return_type="Object",
                            body=AST.Object(name="self"),
                        ),
                    ),
                ),
            )
        )
        print_readable_ast(program)
        captured = capsys.readouterr()
        assert "Program" in captured.out
        assert "ClassMethod" in captured.out
        assert "main" in captured.out

    def test_handles_binary_operation(self, capsys):
        expr = AST.Addition(
            first=AST.Integer(content=1),
            second=AST.Integer(content=2),
        )
        print_readable_ast(expr)
        captured = capsys.readouterr()
        assert "Addition" in captured.out
        assert "1" in captured.out
        assert "2" in captured.out

    def test_inline_parameter_works(self, capsys):
        expr = AST.Integer(content=42)
        print_readable_ast(expr, level=0, inline=True)
        captured = capsys.readouterr()
        # Should not have leading whitespace when inline=True
        assert captured.out.startswith("Integer")

    def test_level_parameter_adds_indentation(self, capsys):
        expr = AST.Integer(content=42)
        print_readable_ast(expr, level=2, inline=False)
        captured = capsys.readouterr()
        # Should have leading whitespace from level=2
        assert captured.out.startswith("        ")  # 2 levels * 4 spaces

    def test_handles_node_with_no_attributes(self, capsys):
        # Self is a node with minimal attributes
        expr = AST.Self()
        print_readable_ast(expr)
        captured = capsys.readouterr()
        assert "Self" in captured.out

    def test_skips_class_name_attribute(self, capsys):
        # class_name should be skipped in output
        klass = AST.Class(name="Foo", parent="Object", features=())
        print_readable_ast(klass)
        captured = capsys.readouterr()
        # Should show the class name as a value but not as an attribute label
        assert "name=" in captured.out
        # class_name attribute should be skipped
        lines = captured.out.split("\n")
        assert not any("class_name=" in line for line in lines)

    def test_handles_complex_expression(self, capsys):
        expr = AST.If(
            predicate=AST.Boolean(content=True),
            then_body=AST.Integer(content=1),
            else_body=AST.Integer(content=0),
        )
        print_readable_ast(expr)
        captured = capsys.readouterr()
        assert "If" in captured.out
        assert "predicate=" in captured.out
        assert "then_body=" in captured.out
        assert "else_body=" in captured.out

    def test_handles_let_expression(self, capsys):
        expr = AST.Let(
            instance="x",
            return_type="Int",
            init_expr=AST.Integer(content=0),
            body=AST.Object(name="x"),
        )
        print_readable_ast(expr)
        captured = capsys.readouterr()
        assert "Let" in captured.out
        assert "instance=" in captured.out
        assert "'x'" in captured.out
