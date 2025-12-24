"""
Tests for the COOL semantic analyzer.

These tests verify the currently implemented semantic analysis features:
- Builtin type installation
- Inheritance graph construction
- Cyclic inheritance detection
- Invalid inheritance from Int/Bool/String
"""

import pytest

import pycoolc.ast as AST
from pycoolc.parser import make_parser
from pycoolc.semanalyser import (
    OBJECT_CLASS,
    SELF_TYPE,
    MethodSignature,
    SemanticAnalysisError,
    TypeEnvironment,
    make_semantic_analyser,
)


@pytest.fixture
def parser():
    """Create a parser for test programs."""
    return make_parser()


@pytest.fixture
def analyzer():
    """Create a semantic analyzer."""
    return make_semantic_analyser()


def parse_and_analyze(source: str):
    """Helper to parse and analyze a COOL program."""
    parser = make_parser()
    analyzer = make_semantic_analyser()
    ast = parser.parse(source)
    return analyzer.transform(ast)


# Minimal valid Main class for tests that don't focus on Main
MAIN_CLASS = "class Main { main() : Object { self }; };"


class TestBuiltinTypes:
    """Tests for builtin type installation."""

    def test_object_class_is_installed(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        class_names = [c.name for c in result.classes]
        assert "Object" in class_names

    def test_io_class_is_installed(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        class_names = [c.name for c in result.classes]
        assert "IO" in class_names

    def test_int_class_is_installed(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        class_names = [c.name for c in result.classes]
        assert "Int" in class_names

    def test_bool_class_is_installed(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        class_names = [c.name for c in result.classes]
        assert "Bool" in class_names

    def test_string_class_is_installed(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        class_names = [c.name for c in result.classes]
        assert "String" in class_names

    def test_builtin_classes_come_before_user_classes(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        # First 5 classes should be builtins
        builtin_names = [c.name for c in result.classes[:5]]
        assert set(builtin_names) == {"Object", "IO", "Int", "Bool", "String"}
        # User class comes after
        assert result.classes[5].name == "Main"

    def test_object_has_abort_method(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        object_class = next(c for c in result.classes if c.name == "Object")
        method_names = [f.name for f in object_class.features if isinstance(f, AST.ClassMethod)]
        assert "abort" in method_names

    def test_object_has_copy_method(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        object_class = next(c for c in result.classes if c.name == "Object")
        method_names = [f.name for f in object_class.features if isinstance(f, AST.ClassMethod)]
        assert "copy" in method_names

    def test_object_has_type_name_method(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        object_class = next(c for c in result.classes if c.name == "Object")
        method_names = [f.name for f in object_class.features if isinstance(f, AST.ClassMethod)]
        assert "type_name" in method_names

    def test_io_has_input_methods(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        io_class = next(c for c in result.classes if c.name == "IO")
        method_names = [f.name for f in io_class.features if isinstance(f, AST.ClassMethod)]
        assert "in_int" in method_names
        assert "in_string" in method_names

    def test_io_has_output_methods(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        io_class = next(c for c in result.classes if c.name == "IO")
        method_names = [f.name for f in io_class.features if isinstance(f, AST.ClassMethod)]
        assert "out_int" in method_names
        assert "out_string" in method_names

    def test_string_has_length_method(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        string_class = next(c for c in result.classes if c.name == "String")
        method_names = [f.name for f in string_class.features if isinstance(f, AST.ClassMethod)]
        assert "length" in method_names

    def test_string_has_concat_method(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        string_class = next(c for c in result.classes if c.name == "String")
        method_names = [f.name for f in string_class.features if isinstance(f, AST.ClassMethod)]
        assert "concat" in method_names

    def test_string_has_substr_method(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        string_class = next(c for c in result.classes if c.name == "String")
        method_names = [f.name for f in string_class.features if isinstance(f, AST.ClassMethod)]
        assert "substr" in method_names


class TestInheritanceGraph:
    """Tests for inheritance graph construction."""

    def test_class_without_parent_defaults_to_object(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        main_class = next(c for c in result.classes if c.name == "Main")
        assert main_class.parent == "Object"

    def test_class_with_explicit_parent(self, parser, analyzer):
        ast = parser.parse(f"class Child inherits Parent {{ }}; class Parent {{ }}; {MAIN_CLASS}")
        result = analyzer.transform(ast)
        child_class = next(c for c in result.classes if c.name == "Child")
        assert child_class.parent == "Parent"

    def test_undefined_parent_defaults_to_object(self, parser, analyzer):
        # If parent doesn't exist, it should default to Object
        ast = parser.parse(f"class Child inherits NonExistent {{ }}; {MAIN_CLASS}")
        result = analyzer.transform(ast)
        child_class = next(c for c in result.classes if c.name == "Child")
        assert child_class.parent == "Object"


class TestInheritanceRestrictions:
    """Tests for inheritance restrictions on builtin types."""

    def test_cannot_inherit_from_int(self, parser, analyzer):
        ast = parser.parse(f"class MyInt inherits Int {{ }}; {MAIN_CLASS}")
        with pytest.raises(SemanticAnalysisError, match="cannot inherit from built-in class"):
            analyzer.transform(ast)

    def test_cannot_inherit_from_bool(self, parser, analyzer):
        ast = parser.parse(f"class MyBool inherits Bool {{ }}; {MAIN_CLASS}")
        with pytest.raises(SemanticAnalysisError, match="cannot inherit from built-in class"):
            analyzer.transform(ast)

    def test_cannot_inherit_from_string(self, parser, analyzer):
        ast = parser.parse(f"class MyString inherits String {{ }}; {MAIN_CLASS}")
        with pytest.raises(SemanticAnalysisError, match="cannot inherit from built-in class"):
            analyzer.transform(ast)

    def test_can_inherit_from_io(self, parser, analyzer):
        # IO is a valid parent class
        ast = parser.parse("class Main inherits IO { main() : Object { self }; };")
        result = analyzer.transform(ast)
        main_class = next(c for c in result.classes if c.name == "Main")
        assert main_class.parent == "IO"

    def test_can_inherit_from_object(self, parser, analyzer):
        # Object is a valid parent class
        ast = parser.parse("class Main inherits Object { main() : Object { self }; };")
        result = analyzer.transform(ast)
        main_class = next(c for c in result.classes if c.name == "Main")
        assert main_class.parent == "Object"


class TestCyclicInheritance:
    """Tests for cyclic inheritance detection."""

    def test_self_inheritance_detected(self, parser, analyzer):
        ast = parser.parse(f"class A inherits A {{ }}; {MAIN_CLASS}")
        with pytest.raises(SemanticAnalysisError, match="inheritance cycle"):
            analyzer.transform(ast)

    def test_two_class_cycle_detected(self, parser, analyzer):
        ast = parser.parse(f"""
            class A inherits B {{ }};
            class B inherits A {{ }};
            {MAIN_CLASS}
        """)
        with pytest.raises(SemanticAnalysisError, match="inheritance cycle"):
            analyzer.transform(ast)

    def test_three_class_cycle_detected(self, parser, analyzer):
        ast = parser.parse(f"""
            class A inherits B {{ }};
            class B inherits C {{ }};
            class C inherits A {{ }};
            {MAIN_CLASS}
        """)
        with pytest.raises(SemanticAnalysisError, match="inheritance cycle"):
            analyzer.transform(ast)

    def test_valid_chain_is_allowed(self, parser, analyzer):
        # A -> B -> C -> Object (no cycle)
        ast = parser.parse(f"""
            class C {{ }};
            class B inherits C {{ }};
            class A inherits B {{ }};
            {MAIN_CLASS}
        """)
        result = analyzer.transform(ast)
        a_class = next(c for c in result.classes if c.name == "A")
        assert a_class.parent == "B"


class TestDuplicateClasses:
    """Tests for duplicate class detection."""

    def test_duplicate_class_raises_error(self, parser, analyzer):
        ast = parser.parse(f"""
            class Foo {{ }};
            class Foo {{ }};
            {MAIN_CLASS}
        """)
        with pytest.raises(SemanticAnalysisError, match="already defined"):
            analyzer.transform(ast)


class TestAnalyzerAPI:
    """Tests for semantic analyzer's public API."""

    def test_transform_returns_program(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_transform_with_none_raises_error(self, analyzer):
        with pytest.raises(ValueError, match="cannot be None"):
            analyzer.transform(None)

    def test_transform_with_wrong_type_raises_error(self, analyzer):
        with pytest.raises(TypeError, match="not of type"):
            analyzer.transform("not an AST")


class TestValidPrograms:
    """Integration tests with valid COOL programs."""

    def test_hello_world(self):
        result = parse_and_analyze("""
            class Main inherits IO {
                main(): SELF_TYPE {
                    out_string("Hello, World.\\n")
                };
            };
        """)
        assert isinstance(result, AST.Program)

    def test_multiple_classes_with_inheritance(self):
        result = parse_and_analyze(f"""
            class Animal {{ }};
            class Dog inherits Animal {{ }};
            class Cat inherits Animal {{ }};
            {MAIN_CLASS}
        """)
        assert isinstance(result, AST.Program)
        # All classes should be present (5 builtins + 4 user)
        assert len(result.classes) == 9


class TestTypeEnvironment:
    """Tests for the TypeEnvironment class."""

    def test_define_and_lookup_object(self):
        env = TypeEnvironment(current_class="Main")
        env.define_object("x", "Int")
        assert env.lookup_object("x") == "Int"

    def test_undefined_object_returns_none(self):
        env = TypeEnvironment(current_class="Main")
        assert env.lookup_object("undefined") is None

    def test_nested_scope_inherits_parent(self):
        env = TypeEnvironment(current_class="Main")
        env.define_object("x", "Int")

        inner = env.enter_scope()
        # Can see parent's variables
        assert inner.lookup_object("x") == "Int"

        # Can define new variables
        inner.define_object("y", "Bool")
        assert inner.lookup_object("y") == "Bool"

        # Parent doesn't see inner's variables
        assert env.lookup_object("y") is None

    def test_resolve_self_type(self):
        env = TypeEnvironment(current_class="MyClass")
        assert env.resolve_self_type(SELF_TYPE) == "MyClass"
        assert env.resolve_self_type("Int") == "Int"


class TestMethodSignature:
    """Tests for the MethodSignature class."""

    def test_repr(self):
        sig = MethodSignature(
            name="add",
            param_types=("Int", "Int"),
            return_type="Int",
            defining_class="Math",
        )
        assert "add" in repr(sig)
        assert "Int" in repr(sig)


class TestTypeHierarchy:
    """Tests for type hierarchy operations (subtype, LUB, ancestors)."""

    @pytest.fixture
    def analyzed_program(self):
        """Create an analyzed program with a class hierarchy."""
        parser = make_parser()
        analyzer = make_semantic_analyser()
        ast = parser.parse(f"""
            class Animal {{ }};
            class Dog inherits Animal {{ }};
            class Cat inherits Animal {{ }};
            class Poodle inherits Dog {{ }};
            {MAIN_CLASS}
        """)
        analyzer.transform(ast)
        return analyzer

    def test_get_ancestors_of_object(self, analyzed_program):
        ancestors = analyzed_program.get_ancestors(OBJECT_CLASS)
        assert ancestors == [OBJECT_CLASS]

    def test_get_ancestors_of_dog(self, analyzed_program):
        ancestors = analyzed_program.get_ancestors("Dog")
        assert ancestors == ["Dog", "Animal", OBJECT_CLASS]

    def test_get_ancestors_of_poodle(self, analyzed_program):
        ancestors = analyzed_program.get_ancestors("Poodle")
        assert ancestors == ["Poodle", "Dog", "Animal", OBJECT_CLASS]

    def test_is_subtype_same_type(self, analyzed_program):
        assert analyzed_program.is_subtype("Dog", "Dog") is True

    def test_is_subtype_child_of_parent(self, analyzed_program):
        assert analyzed_program.is_subtype("Dog", "Animal") is True
        assert analyzed_program.is_subtype("Poodle", "Animal") is True

    def test_is_subtype_not_reverse(self, analyzed_program):
        assert analyzed_program.is_subtype("Animal", "Dog") is False

    def test_is_subtype_all_subtype_of_object(self, analyzed_program):
        assert analyzed_program.is_subtype("Dog", OBJECT_CLASS) is True
        assert analyzed_program.is_subtype("Int", OBJECT_CLASS) is True

    def test_lub_same_type(self, analyzed_program):
        assert analyzed_program.lub("Dog", "Dog") == "Dog"

    def test_lub_siblings(self, analyzed_program):
        # Dog and Cat have common ancestor Animal
        assert analyzed_program.lub("Dog", "Cat") == "Animal"

    def test_lub_child_and_parent(self, analyzed_program):
        assert analyzed_program.lub("Poodle", "Animal") == "Animal"

    def test_lub_with_object(self, analyzed_program):
        # Int and Dog have no common ancestor other than Object
        assert analyzed_program.lub("Int", "Dog") == OBJECT_CLASS

    def test_lub_self_type(self, analyzed_program):
        assert analyzed_program.lub(SELF_TYPE, SELF_TYPE) == SELF_TYPE


class TestMethodTable:
    """Tests for method table building and lookup."""

    def test_object_methods_inherited(self, parser, analyzer):
        ast = parser.parse(MAIN_CLASS)
        analyzer.transform(ast)

        # Main should have Object's methods
        abort_sig = analyzer.lookup_method("Main", "abort")
        assert abort_sig is not None
        assert abort_sig.return_type == OBJECT_CLASS

    def test_io_methods_inherited(self, parser, analyzer):
        ast = parser.parse("class Main inherits IO { main() : Object { self }; };")
        analyzer.transform(ast)

        # Main should have IO's methods
        out_string_sig = analyzer.lookup_method("Main", "out_string")
        assert out_string_sig is not None
        assert out_string_sig.return_type == SELF_TYPE

    def test_method_defined_in_class(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                main() : Object { self };
                foo(x : Int, y : Bool) : String { "hello" };
            };
        """)
        analyzer.transform(ast)

        foo_sig = analyzer.lookup_method("Main", "foo")
        assert foo_sig is not None
        assert foo_sig.param_types == ("Int", "Bool")
        assert foo_sig.return_type == "String"


class TestAttributeTable:
    """Tests for attribute table building and lookup."""

    def test_attribute_defined_in_class(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                x : Int;
                y : Bool <- true;
                main() : Object { self };
            };
        """)
        analyzer.transform(ast)

        assert analyzer.lookup_attribute("Main", "x") == "Int"
        assert analyzer.lookup_attribute("Main", "y") == "Bool"

    def test_inherited_attributes(self, parser, analyzer):
        ast = parser.parse("""
            class Parent {
                x : Int;
            };
            class Main inherits Parent {
                y : Bool;
                main() : Object { self };
            };
        """)
        analyzer.transform(ast)

        # Main (Child) has both its own and parent's attributes
        assert analyzer.lookup_attribute("Main", "x") == "Int"
        assert analyzer.lookup_attribute("Main", "y") == "Bool"

        # Parent only has its own
        assert analyzer.lookup_attribute("Parent", "x") == "Int"
        assert analyzer.lookup_attribute("Parent", "y") is None


class TestMainClass:
    """Tests for Main class validation."""

    def test_missing_main_class_raises_error(self, parser, analyzer):
        ast = parser.parse("class Foo { };")
        with pytest.raises(SemanticAnalysisError, match="must contain a class 'Main'"):
            analyzer.transform(ast)

    def test_main_class_without_main_method_raises_error(self, parser, analyzer):
        ast = parser.parse("class Main { x : Int; };")
        with pytest.raises(SemanticAnalysisError, match="must have a 'main\\(\\)' method"):
            analyzer.transform(ast)

    def test_main_method_with_args_raises_error(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                main(x : Int) : Object { self };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="must take no arguments"):
            analyzer.transform(ast)

    def test_valid_main_class_passes(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                main() : Object { self };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)


class TestMethodOverriding:
    """Tests for method overriding validation."""

    def test_valid_override_same_signature(self, parser, analyzer):
        ast = parser.parse("""
            class Parent {
                foo(x : Int) : Bool { true };
            };
            class Main inherits Parent {
                foo(x : Int) : Bool { false };
                main() : Object { self };
            };
        """)
        # Should not raise
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_override_wrong_param_count(self, parser, analyzer):
        ast = parser.parse("""
            class Parent {
                foo(x : Int) : Bool { true };
            };
            class Main inherits Parent {
                foo(x : Int, y : Int) : Bool { false };
                main() : Object { self };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="wrong number of parameters"):
            analyzer.transform(ast)

    def test_override_wrong_param_type(self, parser, analyzer):
        ast = parser.parse("""
            class Parent {
                foo(x : Int) : Bool { true };
            };
            class Main inherits Parent {
                foo(x : Bool) : Bool { false };
                main() : Object { self };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="parameter.*type"):
            analyzer.transform(ast)

    def test_override_wrong_return_type(self, parser, analyzer):
        ast = parser.parse("""
            class Parent {
                foo(x : Int) : Bool { true };
            };
            class Main inherits Parent {
                foo(x : Int) : Int { 0 };
                main() : Object { self };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="return type"):
            analyzer.transform(ast)


class TestAttributeRedefinition:
    """Tests for attribute redefinition validation."""

    def test_attribute_redefinition_raises_error(self, parser, analyzer):
        ast = parser.parse("""
            class Parent {
                x : Int;
            };
            class Main inherits Parent {
                x : Bool;
                main() : Object { self };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="already defined in ancestor"):
            analyzer.transform(ast)

    def test_different_attribute_name_allowed(self, parser, analyzer):
        ast = parser.parse("""
            class Parent {
                x : Int;
            };
            class Main inherits Parent {
                y : Bool;
                main() : Object { self };
            };
        """)
        # Should not raise
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)


class TestTypeChecking:
    """Tests for expression type checking."""

    def test_integer_literal_has_type_int(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                x : Int <- 42;
                main() : Object { self };
            };
        """)
        # Should not raise
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_string_literal_has_type_string(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                x : String <- "hello";
                main() : Object { self };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_boolean_literal_has_type_bool(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                x : Bool <- true;
                main() : Object { self };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_type_mismatch_in_attribute_raises_error(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                x : Int <- "hello";
                main() : Object { self };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="declared type.*initialization"):
            analyzer.transform(ast)

    def test_arithmetic_with_ints_valid(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                x : Int <- 1 + 2 * 3;
                main() : Object { self };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_arithmetic_with_non_int_raises_error(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                x : Int <- 1 + true;
                main() : Object { self };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="must be Int"):
            analyzer.transform(ast)

    def test_comparison_returns_bool(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                x : Bool <- 1 < 2;
                main() : Object { self };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_if_predicate_must_be_bool(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                main() : Object {
                    if 42 then self else self fi
                };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="must be Bool"):
            analyzer.transform(ast)

    def test_if_returns_lub_of_branches(self, parser, analyzer):
        ast = parser.parse("""
            class Animal { };
            class Dog inherits Animal { };
            class Cat inherits Animal { };
            class Main {
                main() : Animal {
                    if true then new Dog else new Cat fi
                };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_while_returns_object(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                main() : Object {
                    while false loop 42 pool
                };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_let_creates_new_scope(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                main() : Int {
                    let x : Int <- 10 in x + 5
                };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_undefined_variable_raises_error(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                main() : Int { y };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="Undefined variable 'y'"):
            analyzer.transform(ast)

    def test_method_dispatch_valid(self, parser, analyzer):
        ast = parser.parse("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    out_string("hello")
                };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_method_dispatch_wrong_arg_type(self, parser, analyzer):
        ast = parser.parse("""
            class Main inherits IO {
                main() : SELF_TYPE {
                    out_string(42)
                };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="has type 'Int'.*expected 'String'"):
            analyzer.transform(ast)

    def test_method_return_type_mismatch(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                main() : Int { "hello" };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="declared return type.*body has type"):
            analyzer.transform(ast)

    def test_new_creates_object(self, parser, analyzer):
        ast = parser.parse("""
            class Foo { };
            class Main {
                main() : Foo { new Foo };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_self_type_in_new(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                copy_self() : SELF_TYPE { new SELF_TYPE };
                main() : Object { self };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_block_returns_last_expression_type(self, parser, analyzer):
        ast = parser.parse("""
            class Main {
                main() : String {
                    {
                        1;
                        true;
                        "result";
                    }
                };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_case_expression_type_checks(self, parser, analyzer):
        ast = parser.parse("""
            class Main inherits IO {
                main() : Object {
                    case self of
                        x : Main => out_string("Main");
                        y : IO => out_string("IO");
                    esac
                };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)


class TestAdditionalTypeChecking:
    """Additional tests for edge cases in type checking."""

    def test_subtraction_type_check(self, parser, analyzer):
        """Subtraction requires Int operands."""
        ast = parser.parse("""
            class Main {
                main() : Int { 5 - 3 };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_division_type_check(self, parser, analyzer):
        """Division requires Int operands."""
        ast = parser.parse("""
            class Main {
                main() : Int { 10 / 2 };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_less_than_or_equal_type_check(self, parser, analyzer):
        """LessThanOrEqual requires Int operands."""
        ast = parser.parse("""
            class Main {
                main() : Bool { 3 <= 5 };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_assignment_to_attribute(self, parser, analyzer):
        """Assignment to a class attribute."""
        ast = parser.parse("""
            class Main {
                x : Int <- 0;
                main() : Int {
                    x <- 42
                };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_assignment_type_mismatch(self, parser, analyzer):
        """Assignment with incompatible type."""
        ast = parser.parse("""
            class Main {
                x : Int <- 0;
                main() : String {
                    x <- "hello"
                };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="Cannot assign.*type 'String'.*type 'Int'"):
            analyzer.transform(ast)

    def test_assignment_undefined_variable(self, parser, analyzer):
        """Assignment to undefined variable."""
        ast = parser.parse("""
            class Main {
                main() : Int {
                    undefined_var <- 42
                };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="Undefined variable 'undefined_var'"):
            analyzer.transform(ast)

    def test_equality_primitive_type_mismatch(self, parser, analyzer):
        """Equality between Int and String is not allowed."""
        ast = parser.parse("""
            class Main {
                main() : Bool { 42 = "hello" };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="Cannot compare 'Int' with 'String'"):
            analyzer.transform(ast)

    def test_equality_bool_with_int(self, parser, analyzer):
        """Equality between Bool and Int is not allowed."""
        ast = parser.parse("""
            class Main {
                main() : Bool { true = 1 };
            };
        """)
        with pytest.raises(SemanticAnalysisError, match="Cannot compare 'Bool' with 'Int'"):
            analyzer.transform(ast)

    def test_integer_complement_wrong_type(self, parser, analyzer):
        """Integer complement on non-Int."""
        ast = parser.parse("""
            class Main {
                main() : Int { ~true };
            };
        """)
        with pytest.raises(
            SemanticAnalysisError, match="Integer complement.*requires Int.*got 'Bool'"
        ):
            analyzer.transform(ast)

    def test_boolean_complement_wrong_type(self, parser, analyzer):
        """Boolean complement on non-Bool."""
        ast = parser.parse("""
            class Main {
                main() : Bool { not 42 };
            };
        """)
        with pytest.raises(
            SemanticAnalysisError, match="Boolean complement.*requires Bool.*got 'Int'"
        ):
            analyzer.transform(ast)

    def test_new_undefined_class(self, parser, analyzer):
        """New with undefined class name."""
        ast = parser.parse("""
            class Main {
                main() : Object { new UndefinedClass };
            };
        """)
        with pytest.raises(
            SemanticAnalysisError, match="Cannot instantiate undefined class 'UndefinedClass'"
        ):
            analyzer.transform(ast)

    def test_isvoid_expression(self, parser, analyzer):
        """isvoid expression returns Bool."""
        ast = parser.parse("""
            class Main {
                main() : Bool { isvoid self };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_static_dispatch_valid(self, parser, analyzer):
        """Valid static dispatch."""
        ast = parser.parse("""
            class Main inherits IO {
                main() : Object {
                    self@IO.out_string("hello")
                };
            };
        """)
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)

    def test_static_dispatch_invalid_type(self, parser, analyzer):
        """Static dispatch with non-supertype."""
        ast = parser.parse("""
            class Foo { };
            class Main {
                main() : Object {
                    self@Foo.abort()
                };
            };
        """)
        with pytest.raises(
            SemanticAnalysisError, match="Static dispatch type 'Foo' is not a supertype"
        ):
            analyzer.transform(ast)

    def test_arithmetic_left_operand_wrong_type(self, parser, analyzer):
        """Arithmetic with non-Int left operand."""
        ast = parser.parse("""
            class Main {
                main() : Int { "hello" + 5 };
            };
        """)
        with pytest.raises(
            SemanticAnalysisError, match="Left operand of '\\+' must be Int.*got 'String'"
        ):
            analyzer.transform(ast)

    def test_arithmetic_right_operand_wrong_type(self, parser, analyzer):
        """Arithmetic with non-Int right operand."""
        ast = parser.parse("""
            class Main {
                main() : Int { 5 + "hello" };
            };
        """)
        with pytest.raises(
            SemanticAnalysisError, match="Right operand of '\\+' must be Int.*got 'String'"
        ):
            analyzer.transform(ast)

    def test_comparison_left_operand_wrong_type(self, parser, analyzer):
        """Comparison with non-Int left operand."""
        ast = parser.parse("""
            class Main {
                main() : Bool { "hello" < 5 };
            };
        """)
        with pytest.raises(
            SemanticAnalysisError, match="Left operand of '<' must be Int.*got 'String'"
        ):
            analyzer.transform(ast)

    def test_comparison_right_operand_wrong_type(self, parser, analyzer):
        """Comparison with non-Int right operand."""
        ast = parser.parse("""
            class Main {
                main() : Bool { 5 < "hello" };
            };
        """)
        with pytest.raises(
            SemanticAnalysisError, match="Right operand of '<' must be Int.*got 'String'"
        ):
            analyzer.transform(ast)
