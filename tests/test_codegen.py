"""
Tests for the MIPS code generator.

These tests verify that the code generator produces valid MIPS assembly
for various COOL programs.
"""

import pytest
from pycoolc.parser import make_parser
from pycoolc.semanalyser import make_semantic_analyser
from pycoolc.codegen import make_code_generator, MIPSCodeGenerator


@pytest.fixture
def parser():
    """Create a parser for tests."""
    return make_parser()


@pytest.fixture
def analyzer():
    """Create a semantic analyzer for tests."""
    return make_semantic_analyser()


def compile_to_mips(source: str) -> str:
    """Helper to compile COOL source to MIPS assembly."""
    parser = make_parser()
    analyzer = make_semantic_analyser()
    
    ast = parser.parse(source)
    analyzed_ast = analyzer.transform(ast)
    
    codegen = make_code_generator(analyzer)
    return codegen.generate(analyzed_ast)


class TestCodeGeneratorBasics:
    """Basic tests for code generator infrastructure."""

    def test_generates_data_segment(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert ".data" in code

    def test_generates_text_segment(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert ".text" in code

    def test_generates_main_entry_point(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert "main:" in code

    def test_generates_dispatch_tables(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert "_dispTab_Main:" in code
        assert "_dispTab_Object:" in code

    def test_generates_prototype_objects(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert "_protObj_Main:" in code


class TestClassGeneration:
    """Tests for class-related code generation."""

    def test_class_initializer_generated(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert "_init_Main:" in code

    def test_inherited_class_calls_parent_init(self):
        code = compile_to_mips("""
            class Parent { };
            class Main inherits Parent {
                main() : Object { self };
            };
        """)
        # Main's init should call Parent's init
        assert "_init_Main:" in code
        assert "_init_Parent:" in code


class TestMethodGeneration:
    """Tests for method code generation."""

    def test_method_label_generated(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
                foo() : Int { 42 };
            };
        """)
        assert "_method_Main_main:" in code
        assert "_method_Main_foo:" in code

    def test_method_returns_value(self):
        code = compile_to_mips("""
            class Main {
                main() : Int { 42 };
            };
        """)
        # Should have code to return
        assert "jr" in code


class TestLiteralGeneration:
    """Tests for literal code generation."""

    def test_integer_literal(self):
        code = compile_to_mips("""
            class Main {
                x : Int <- 42;
                main() : Object { self };
            };
        """)
        # Should have an integer constant
        assert ".word" in code

    def test_string_literal(self):
        code = compile_to_mips("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    out_string("Hello, World!")
                };
            };
        """)
        assert "Hello, World!" in code

    def test_boolean_constants(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert "_bool_const_true:" in code
        assert "_bool_const_false:" in code


class TestBuiltinMethods:
    """Tests for built-in method generation."""

    def test_object_abort_generated(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert "_method_Object_abort:" in code

    def test_io_out_string_generated(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert "_method_IO_out_string:" in code

    def test_io_out_int_generated(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert "_method_IO_out_int:" in code


class TestRuntimeSupport:
    """Tests for runtime support routines."""

    def test_object_copy_generated(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert "_Object_copy:" in code

    def test_equality_test_generated(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert "_equality_test:" in code

    def test_dispatch_void_handler(self):
        code = compile_to_mips("""
            class Main {
                main() : Object { self };
            };
        """)
        assert "_dispatch_void:" in code


class TestExpressionGeneration:
    """Tests for expression code generation."""

    def test_if_then_else(self):
        code = compile_to_mips("""
            class Main {
                main() : Int {
                    if true then 1 else 0 fi
                };
            };
        """)
        # Should have conditional branches
        assert "beqz" in code

    def test_while_loop(self):
        code = compile_to_mips("""
            class Main {
                main() : Object {
                    while false loop 0 pool
                };
            };
        """)
        # Should have loop structure
        assert "_while_loop" in code or "j" in code

    def test_block_expression(self):
        code = compile_to_mips("""
            class Main {
                main() : String {
                    {
                        1;
                        "hello";
                    }
                };
            };
        """)
        assert "hello" in code

    def test_new_expression(self):
        code = compile_to_mips("""
            class Foo { };
            class Main {
                main() : Foo { new Foo };
            };
        """)
        # Should call object copy
        assert "_Object_copy" in code

    def test_method_dispatch(self):
        code = compile_to_mips("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    out_string("test")
                };
            };
        """)
        # Should have dispatch code
        assert "jalr" in code or "jal" in code


class TestCompletePrograms:
    """Integration tests with complete programs."""

    def test_hello_world_compiles(self):
        code = compile_to_mips("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    out_string("Hello, World!\\n")
                };
            };
        """)
        assert len(code) > 0
        assert ".data" in code
        assert ".text" in code
        assert "main:" in code
        assert "Hello, World!" in code

    def test_factorial_compiles(self):
        code = compile_to_mips("""
            class Main inherits IO {
                fact(n : Int) : Int {
                    if n = 0 then 1 else n * fact(n - 1) fi
                };
                main() : SELF_TYPE {
                    out_int(fact(5))
                };
            };
        """)
        assert len(code) > 0
        assert "_method_Main_fact:" in code
        assert "_method_Main_main:" in code

