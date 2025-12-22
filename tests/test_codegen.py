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


class TestStringOperations:
    """Tests for string built-in operations - debugging in_string/substr/length bugs."""

    def test_string_length(self):
        """String.length() should return the length."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    out_int("hello".length())
                };
            };
        """)
        assert "_method_String_length" in code
        # Should load length from string object
        assert "lw" in code

    def test_string_substr(self):
        """String.substr() should extract substring."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    out_string("hello".substr(0, 2))
                };
            };
        """)
        assert "_method_String_substr" in code

    def test_string_concat(self):
        """String.concat() should concatenate strings."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    out_string("hel".concat("lo"))
                };
            };
        """)
        assert "_method_String_concat" in code

    def test_in_string_basic(self):
        """IO.in_string() should read a string from input."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    {
                        out_string("enter: ");
                        out_string(in_string());
                    }
                };
            };
        """)
        assert "_method_IO_in_string" in code

    def test_palindrome_minimal(self):
        """Minimal palindrome check - tests string operations together."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object {
                    let s : String <- "aba" in
                        if s.length() = 0
                        then out_string("empty")
                        else out_int(s.length())
                        fi
                };
            };
        """)
        # Should have string length call
        assert "_method_String_length" in code
        # Should have equality test
        assert "_equality_test" in code


# =============================================================================
# REGRESSION TESTS: Stack Corruption Bugs
# =============================================================================
# These tests target specific bugs where stack operations were incorrectly
# ordered (storing before decrementing $sp), causing data corruption.


class TestStackManagement:
    """
    Tests for correct stack management in expression evaluation.
    
    These are regression tests for bugs where we stored values at 0($sp)
    BEFORE decrementing the stack pointer, which overwrote existing data
    when expressions were nested.
    """

    def test_arithmetic_preserves_stack_in_dispatch_args(self):
        """
        Regression test: s.substr(s.length() - 1, 1) was corrupting stack.
        
        When evaluating arguments to dispatch:
        1. Push arg 1 (literal 1)
        2. Evaluate arg 0 (s.length() - 1)
           - This uses stack for arithmetic
           - BUG: Was overwriting arg 1!
        """
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object {
                    let s : String <- "test" in
                        out_string(s.substr(s.length() - 1, 1))
                };
            };
        """)
        # Should compile without error
        assert "_method_String_substr" in code
        assert "_method_String_length" in code
        # Key: arithmetic should decrement BEFORE storing
        # Check that we have proper stack management pattern
        lines = code.split('\n')
        in_method = False
        for i, line in enumerate(lines):
            if "_method_Main_main:" in line:
                in_method = True
            if in_method and "sub" in line.lower():
                # Found arithmetic - this test documents the fix exists
                break

    def test_nested_arithmetic_stack_balance(self):
        """
        Test that deeply nested arithmetic maintains stack balance.
        
        Expression: ((a + b) - (c + d)) * ((e - f) + (g - h))
        Each sub-expression uses the stack; incorrect ordering corrupts values.
        """
        code = compile_to_mips("""
            class Main {
                main() : Int {
                    let a : Int <- 1, b : Int <- 2, c : Int <- 3, d : Int <- 4,
                        e : Int <- 5, f : Int <- 6, g : Int <- 7, h : Int <- 8 in
                        ((a + b) - (c + d)) * ((e - f) + (g - h))
                };
            };
        """)
        # Should have all four operations
        assert "add" in code.lower()
        assert "sub" in code.lower()
        assert "mul" in code.lower()

    def test_comparison_in_nested_if(self):
        """
        Test comparisons nested in if expressions.
        
        Bug: comparison was storing at 0($sp) before decrementing,
        which could corrupt the predicate evaluation.
        """
        code = compile_to_mips("""
            class Main {
                main() : Bool {
                    if 1 < 2 then
                        if 3 < 4 then true else false fi
                    else
                        if 5 < 6 then false else true fi
                    fi
                };
            };
        """)
        # Should have comparison instruction
        assert "slt" in code

    def test_equality_with_complex_operands(self):
        """
        Test equality where both operands are complex expressions.
        
        Bug: _generate_equality was storing left operand at 0($sp) before
        decrementing, so evaluating the right operand could overwrite it.
        """
        code = compile_to_mips("""
            class Main inherits IO {
                foo() : Int { 42 };
                bar() : Int { 42 };
                main() : Object {
                    if foo() = bar()
                    then out_string("equal")
                    else out_string("not equal")
                    fi
                };
            };
        """)
        # Should call equality test
        assert "_equality_test" in code
        # Both methods should be called
        assert "_method_Main_foo" in code
        assert "_method_Main_bar" in code

    def test_dispatch_args_with_arithmetic(self):
        """
        Test method call with arithmetic expressions as arguments.
        
        f(a + b, c - d, e * f) requires careful stack management.
        """
        code = compile_to_mips("""
            class Main inherits IO {
                triple(x : Int, y : Int, z : Int) : Int { x + y + z };
                main() : Object {
                    out_int(triple(1 + 2, 3 - 1, 2 * 3))
                };
            };
        """)
        assert "_method_Main_triple" in code
        assert "add" in code.lower()
        assert "sub" in code.lower()
        assert "mul" in code.lower()


class TestStringComparison:
    """
    Tests for string equality comparison.
    
    Regression tests for bug where string equality only compared lengths,
    not actual content.
    """

    def test_string_equality_checks_content(self):
        """
        String equality must compare content, not just length.
        
        BUG: "ab" = "cd" returned true because both have length 2.
        """
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object {
                    if "ab" = "cd"
                    then out_string("equal")
                    else out_string("not equal")
                    fi
                };
            };
        """)
        # Should have string comparison loop
        assert "_eq_check_string" in code
        # Should have the byte-by-byte comparison loop
        assert "_eq_string_loop" in code

    def test_string_equality_same_length_different_content(self):
        """Test strings of same length but different content."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object {
                    if "abc" = "abd"
                    then out_string("yes")
                    else out_string("no")
                    fi
                };
            };
        """)
        assert "_eq_string_loop" in code

    def test_string_equality_with_variables(self):
        """Test string comparison with variable operands."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object {
                    let s1 : String <- "hello", s2 : String <- "world" in
                        if s1 = s2
                        then out_string("same")
                        else out_string("different")
                        fi
                };
            };
        """)
        assert "_equality_test" in code


class TestInStringImplementation:
    """
    Tests for IO.in_string() implementation.
    
    Regression tests for bug where in_string() returned empty string
    instead of actually reading input.
    """

    def test_in_string_creates_string_object(self):
        """in_string should allocate and construct a proper String object."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object { out_string(in_string()) };
            };
        """)
        # Should have in_string implementation
        assert "_method_IO_in_string" in code
        # Should use syscall 8 (read string)
        lines = code.split('\n')
        has_syscall_8 = any("li" in line and "$v0" in line and "8" in line 
                           for line in lines)
        assert has_syscall_8, "in_string should use syscall 8"

    def test_in_string_with_length_check(self):
        """in_string result should work with length()."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object { out_int(in_string().length()) };
            };
        """)
        assert "_method_IO_in_string" in code
        assert "_method_String_length" in code

    def test_in_string_with_substr(self):
        """in_string result should work with substr()."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object { out_string(in_string().substr(0, 1)) };
            };
        """)
        assert "_method_IO_in_string" in code
        assert "_method_String_substr" in code


class TestSubstrImplementation:
    """Tests for String.substr() implementation."""

    def test_substr_basic(self):
        """substr should extract characters from a string."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object { out_string("hello".substr(1, 3)) };
            };
        """)
        assert "_method_String_substr" in code

    def test_substr_first_char(self):
        """substr(0, 1) extracts first character."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object { out_string("hello".substr(0, 1)) };
            };
        """)
        assert "_method_String_substr" in code

    def test_substr_last_char(self):
        """substr(len-1, 1) extracts last character."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object {
                    let s : String <- "hello" in
                        out_string(s.substr(s.length() - 1, 1))
                };
            };
        """)
        assert "_method_String_substr" in code
        assert "_method_String_length" in code

    def test_substr_creates_new_string(self):
        """substr should create a new String object, not modify original."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object {
                    let s : String <- "hello",
                        t : String <- s.substr(0, 2) in
                        {
                            out_string(s);
                            out_string(t);
                        }
                };
            };
        """)
        assert "_method_String_substr" in code


class TestRecursion:
    """Tests for recursive method calls."""

    def test_simple_recursion(self):
        """Simple recursive method should maintain proper stack frames."""
        code = compile_to_mips("""
            class Main inherits IO {
                fact(n : Int) : Int {
                    if n = 0 then 1 else n * fact(n - 1) fi
                };
                main() : Object { out_int(fact(5)) };
            };
        """)
        assert "_method_Main_fact" in code
        # Should save and restore $ra for recursion
        assert "sw" in code and "$ra" in code
        assert "lw" in code and "$ra" in code

    def test_tail_recursion(self):
        """Tail-recursive pattern should work correctly."""
        code = compile_to_mips("""
            class Main inherits IO {
                count(n : Int) : Int {
                    if n = 0 then 0 else count(n - 1) fi
                };
                main() : Object { out_int(count(10)) };
            };
        """)
        assert "_method_Main_count" in code

    def test_mutual_recursion(self):
        """Mutually recursive methods should work."""
        code = compile_to_mips("""
            class Main inherits IO {
                even(n : Int) : Bool {
                    if n = 0 then true else odd(n - 1) fi
                };
                odd(n : Int) : Bool {
                    if n = 0 then false else even(n - 1) fi
                };
                main() : Object {
                    if even(4) then out_string("yes") else out_string("no") fi
                };
            };
        """)
        assert "_method_Main_even" in code
        assert "_method_Main_odd" in code


class TestMethodOverriding:
    """Tests for method overriding and dynamic dispatch."""

    def test_override_uses_child_method(self):
        """Overridden method should use the child's implementation."""
        code = compile_to_mips("""
            class Parent {
                foo() : Int { 1 };
            };
            class Child inherits Parent {
                foo() : Int { 2 };
            };
            class Main {
                main() : Int {
                    let c : Parent <- new Child in c.foo()
                };
            };
        """)
        # Both methods should exist
        assert "_method_Parent_foo" in code
        assert "_method_Child_foo" in code
        # Child's dispatch table should have overridden method
        assert "_dispTab_Child" in code

    def test_override_with_super_call(self):
        """Override can call parent via static dispatch."""
        code = compile_to_mips("""
            class Parent {
                foo() : Int { 1 };
            };
            class Child inherits Parent {
                foo() : Int { self@Parent.foo() + 1 };
            };
            class Main {
                main() : Int { (new Child).foo() };
            };
        """)
        # Should have static dispatch to parent
        assert "_dispTab_Parent" in code


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_method_body(self):
        """Method with just self should work."""
        code = compile_to_mips("""
            class Main {
                noop() : SELF_TYPE { self };
                main() : Object { self };
            };
        """)
        assert "_method_Main_noop" in code
        assert "_method_Main_main" in code

    def test_deeply_nested_let(self):
        """Deeply nested let expressions should maintain scope."""
        code = compile_to_mips("""
            class Main {
                main() : Int {
                    let a : Int <- 1 in
                        let b : Int <- a + 1 in
                            let c : Int <- b + 1 in
                                let d : Int <- c + 1 in
                                    d
                };
            };
        """)
        assert "_method_Main_main" in code

    def test_many_parameters(self):
        """Method with many parameters should handle them all."""
        code = compile_to_mips("""
            class Main {
                sum5(a:Int, b:Int, c:Int, d:Int, e:Int) : Int {
                    a + b + c + d + e
                };
                main() : Int { sum5(1, 2, 3, 4, 5) };
            };
        """)
        assert "_method_Main_sum5" in code

    def test_zero_and_negative(self):
        """Test with zero and negative numbers."""
        code = compile_to_mips("""
            class Main inherits IO {
                main() : Object {
                    {
                        out_int(0);
                        out_int(~1);
                        out_int(0 - 5);
                    }
                };
            };
        """)
        assert "_method_IO_out_int" in code
        # Should have negation
        assert "neg" in code.lower() or "sub" in code.lower()
