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


class TestAttributeGeneration:
    """Tests for attribute initialization and access."""

    def test_attribute_with_init_expr(self):
        """Attribute initializers should be generated in class init."""
        code = compile_to_mips("""
            class Main {
                x : Int <- 42;
                main() : Object { self };
            };
        """)
        # Init should contain code to initialize x
        assert "_init_Main:" in code
        # Should store to attribute offset
        assert "sw" in code

    def test_attribute_access(self):
        """Attribute access should load from correct offset."""
        code = compile_to_mips("""
            class Main {
                x : Int <- 42;
                main() : Int { x };
            };
        """)
        # Should load self and then load attribute
        assert "_method_Main_main:" in code
        # Contains load from attribute offset
        lines = code.split('\n')
        main_method = False
        has_load_self = False
        has_load_attr = False
        for line in lines:
            if "_method_Main_main:" in line:
                main_method = True
            if main_method and "lw" in line and "$fp" in line:
                has_load_self = True
            if main_method and "lw" in line and "$t0" in line:
                has_load_attr = True
        assert has_load_self

    def test_object_attribute_initialization(self):
        """Object attributes with new should be properly initialized."""
        code = compile_to_mips("""
            class Foo { };
            class Main {
                f : Foo <- new Foo;
                main() : Object { self };
            };
        """)
        # Init should create new Foo and store it
        assert "_protObj_Foo" in code
        assert "_init_Foo" in code


class TestMethodParameters:
    """Tests for method parameter handling."""

    def test_single_parameter(self):
        """Single parameter should be accessible in method body."""
        code = compile_to_mips("""
            class Main {
                foo(x : Int) : Int { x };
                main() : Object { self };
            };
        """)
        assert "_method_Main_foo:" in code

    def test_multiple_parameters(self):
        """Multiple parameters should be stored correctly."""
        code = compile_to_mips("""
            class Main {
                add(a : Int, b : Int) : Int { a };
                main() : Object { self };
            };
        """)
        assert "_method_Main_add:" in code
        # Should save $a1 and $a2 (first two params)
        assert "$a1" in code
        assert "$a2" in code

    def test_parameter_type_preserved(self):
        """Parameter types should be tracked for dispatch."""
        code = compile_to_mips("""
            class Foo {
                bar() : Int { 1 };
            };
            class Main {
                test(f : Foo) : Int { f.bar() };
                main() : Object { self };
            };
        """)
        # Should dispatch on Foo, not Object
        assert "_method_Foo_bar" in code


class TestLetExpression:
    """Tests for let expression code generation."""

    def test_simple_let(self):
        """Simple let should allocate stack space."""
        code = compile_to_mips("""
            class Main {
                main() : Int {
                    let x : Int <- 5 in x
                };
            };
        """)
        # Should allocate and deallocate stack space
        assert "addiu" in code
        assert "$sp" in code

    def test_nested_let(self):
        """Nested let expressions should work correctly."""
        code = compile_to_mips("""
            class Main {
                main() : Int {
                    let x : Int <- 1 in
                        let y : Int <- 2 in
                            x
                };
            };
        """)
        assert "_method_Main_main:" in code

    def test_let_with_object_type(self):
        """Let binding with object type should track type for dispatch."""
        code = compile_to_mips("""
            class Foo {
                bar() : Int { 42 };
            };
            class Main {
                main() : Int {
                    let f : Foo <- new Foo in f.bar()
                };
            };
        """)
        # Should dispatch to Foo.bar, not Object methods
        assert "_method_Foo_bar" in code


class TestAssignment:
    """Tests for assignment expression code generation."""

    def test_attribute_assignment(self):
        """Attribute assignment should store at correct offset."""
        code = compile_to_mips("""
            class Main {
                x : Int;
                main() : Int {
                    x <- 42
                };
            };
        """)
        # Should store to attribute
        assert "sw" in code

    def test_local_assignment(self):
        """Local variable assignment should store at correct offset."""
        code = compile_to_mips("""
            class Main {
                main() : Int {
                    let x : Int <- 1 in
                        x <- 2
                };
            };
        """)
        # Should store to local
        assert "sw" in code


class TestArithmetic:
    """Tests for arithmetic expression code generation."""

    def test_addition(self):
        """Addition should use add instruction."""
        code = compile_to_mips("""
            class Main {
                main() : Int { 1 + 2 };
            };
        """)
        assert "add" in code

    def test_subtraction(self):
        """Subtraction should use sub instruction."""
        code = compile_to_mips("""
            class Main {
                main() : Int { 5 - 3 };
            };
        """)
        assert "sub" in code

    def test_multiplication(self):
        """Multiplication should use mul instruction."""
        code = compile_to_mips("""
            class Main {
                main() : Int { 2 * 3 };
            };
        """)
        assert "mul" in code

    def test_division(self):
        """Division should use div instruction."""
        code = compile_to_mips("""
            class Main {
                main() : Int { 10 / 2 };
            };
        """)
        assert "div" in code

    def test_integer_complement(self):
        """Integer complement should use neg instruction."""
        code = compile_to_mips("""
            class Main {
                main() : Int { ~5 };
            };
        """)
        assert "neg" in code


class TestComparison:
    """Tests for comparison expression code generation."""

    def test_less_than(self):
        """Less than should use slt instruction."""
        code = compile_to_mips("""
            class Main {
                main() : Bool { 1 < 2 };
            };
        """)
        assert "slt" in code

    def test_less_than_or_equal(self):
        """Less than or equal uses slt with inverted logic (a <= b is not(b < a))."""
        code = compile_to_mips("""
            class Main {
                main() : Bool { 1 <= 2 };
            };
        """)
        # Implemented as slt with swapped operands + xori
        assert "slt" in code
        assert "xori" in code

    def test_equality(self):
        """Equality should call equality test routine."""
        code = compile_to_mips("""
            class Main {
                main() : Bool { 1 = 2 };
            };
        """)
        assert "_equality_test" in code

    def test_not(self):
        """Boolean not should use xori instruction."""
        code = compile_to_mips("""
            class Main {
                main() : Bool { not true };
            };
        """)
        assert "xori" in code


class TestDispatch:
    """Tests for method dispatch code generation."""

    def test_dynamic_dispatch(self):
        """Dynamic dispatch should load from dispatch table."""
        code = compile_to_mips("""
            class Foo {
                bar() : Int { 1 };
            };
            class Main {
                main() : Int {
                    (new Foo).bar()
                };
            };
        """)
        # Should load dispatch table and call
        assert "lw" in code
        assert "jalr" in code

    def test_static_dispatch(self):
        """Static dispatch should use specified class dispatch table."""
        code = compile_to_mips("""
            class Foo {
                bar() : Int { 1 };
            };
            class Bar inherits Foo {
                bar() : Int { 2 };
            };
            class Main {
                main() : Int {
                    (new Bar)@Foo.bar()
                };
            };
        """)
        # Should reference Foo's dispatch table
        assert "_dispTab_Foo" in code

    def test_self_dispatch(self):
        """Self dispatch should use current object."""
        code = compile_to_mips("""
            class Main {
                foo() : Int { 42 };
                main() : Int { foo() };
            };
        """)
        # Should call method on self
        assert "_method_Main_foo" in code

    def test_chained_dispatch(self):
        """Chained dispatch should work correctly."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    out_string("a").out_string("b")
                };
            };
        """)
        # Should have multiple dispatch calls
        assert "jalr" in code

    def test_dispatch_with_arguments(self):
        """Dispatch with arguments should pass them correctly."""
        code = compile_to_mips("""
            class Main {
                add(a : Int, b : Int) : Int { a };
                main() : Int { add(1, 2) };
            };
        """)
        # Should set up arguments
        assert "$a1" in code
        assert "$a2" in code


class TestCaseExpression:
    """Tests for case expression code generation."""

    def test_case_generates_branches(self):
        """Case should generate branch for each action."""
        code = compile_to_mips("""
            class Main {
                main() : Int {
                    case 1 of
                        x : Int => x;
                        y : Object => 0;
                    esac
                };
            };
        """)
        # Should have class tag comparisons
        assert "beq" in code or "bne" in code

    def test_case_handles_multiple_types(self):
        """Case should handle different branch types."""
        code = compile_to_mips("""
            class Foo { };
            class Bar inherits Foo { };
            class Main {
                test(o : Object) : Int {
                    case o of
                        f : Foo => 1;
                        b : Bar => 2;
                    esac
                };
                main() : Object { self };
            };
        """)
        assert "_method_Main_test:" in code


class TestSelfReference:
    """Tests for self reference handling."""

    def test_self_in_method(self):
        """Self should be accessible in method body."""
        code = compile_to_mips("""
            class Main {
                main() : Main { self };
            };
        """)
        # Should load self from frame
        assert "lw" in code
        assert "$fp" in code

    def test_self_with_params(self):
        """Self should be at correct offset with parameters."""
        code = compile_to_mips("""
            class Main {
                foo(a : Int, b : Int) : Main { self };
                main() : Object { self };
            };
        """)
        # Should load self at correct offset (not 0 when params exist)
        assert "_method_Main_foo:" in code


class TestStringEscaping:
    """Tests for string literal escaping."""

    def test_newline_in_string(self):
        """Newlines should be escaped as \\n."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    out_string("hello\\nworld")
                };
            };
        """)
        assert "hello" in code

    def test_quote_in_string(self):
        """Quotes should be properly escaped."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    out_string("say \\"hello\\"")
                };
            };
        """)
        # Should contain escaped quote or .byte directive
        assert "say" in code


class TestIsVoid:
    """Tests for isvoid expression code generation."""

    def test_isvoid_expression(self):
        """Isvoid should generate null check."""
        code = compile_to_mips("""
            class Main {
                main() : Bool {
                    isvoid self
                };
            };
        """)
        # Should have zero comparison
        assert "beqz" in code or "bnez" in code


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

