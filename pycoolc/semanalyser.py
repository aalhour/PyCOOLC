#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# semanalyser.py
#
# Author:       Ahmad Alhour (aalhour.com).
# Date:         TODO
# Description:  The Semantic Analyser module. Implements Semantic Analysis and
#               Type Checking.
# -----------------------------------------------------------------------------


"""
# Semantic Analysis

## Checks

  1. All identifiers are declared.
  2. Types.
  3. Inheritance relationships.
  4. Classes defined only once.
  5. Methods in a class defined only once.
  6. Reserved identifiers are not misused.


## Scope

### Identifier Bindings:

Cool Identifier Bindings are introduced by:

  * Class declarations (introduce class names)
  * Method definitions (introduce method names) – Let expressions (introduce object id’s)
  * Formal parameters (introduce object id’s)
  * Attribute definitions (introduce object id’s)
  * Case expressions (introduce object id’s)

### Class Definitions:

  * Cannot be nested.
  * Are globally visible throughout the program.
  * Class names can be used before they are defined.

### Class Attributes:

  * Attribute names are global within the class in which they are defined

### Class Methods:

  * Method names have complex rules.
  * A method need not be defined in the class in which it is used, but in some parent class.
  * Methods may also be redefined (overridden).


## Type System

### Type Operations:

  * Type Checking. The process of verifying fully typed programs
  * Type Inference. The process of filling in missing type information

### Types in Cool:

  1. Class names: Builtins (Int; String; Bool; Object; IO) and User Defined.
  2. SELF_TYPE.

### Sub-Typing:

  * Types can be thought of as sets of attributes and operations defined on these sets.
  * All types are subtypes of the `Object` type.
  * Types can inherit from other types other than the `Object` type.
  * No type is allowed to inherit from the following types only: `Int`, `Bool`, `String` and `SELF_TYPE`.
  * All type relations can be thought of as a tree where `Object` is at the root and all other types branching down from
    it, this is also called the `inheritance tree`.
  * A least upper bound (`lub`) relation of two types is their least common ancestor in the inheritance tree.
  * Subclasses only add attributes or methods.
  * Methods can be redefined but with same type.
  * All operations that can be used on type `C` can also be used on type `C'`, where `C'` <= `C`, meaning `C'` is a
    subtype of `C`.

### Typing Methods:

  * Method and Object identifiers live in different name spaces.
    + A method `foo` and an object `foo` can coexist in the same scope.
  * Logically, Cool Type Checking needs the following 2 Type Environments:
    + `O`: a function providing mapping from types to Object Identifiers and vice versa.
    + `M`: a function providing mapping from types to Method Names and vice versa.
  * Due to `SELF_TYPE`, we need to know the class name at all points of Type Checking methods.
    + `C`: a function providing the name of the current class (Type).

### SELF_TYPE:

`SELF_TYPE` is not a Dynamic Type, it is a Static Type.

`SELF_TYPE` is the type of the `self` parameter in an instance. In a method dispatch, `SELF_TYPE` might be a subtype of
the class in which the subject method appears.

#### Usage:

  * `SELF_TYPE` can be used with `new T` expressions.
  * `SELF_TYPE` can be used as the return type of class methods.
  * `SELF_TYPE` can be used as the type of expressions (i.e. let expressions: `let x : T in expr`).
  * `SELF_TYPE` can be used as the type of the actual arguments in a method dispatch.
  * `SELF_TYPE` can **not** be used as the type of class attributes.
  * `SELF_TYPE` can **not** be used with Static Dispatch (i.e. `T` in `m@T(expr1,...,exprN)`).
  * `SELF_TYPE` can **not** be used as the type of Formal Parameters.

#### Least-Upper Bound Relations:

  * `lub(SELF_TYPE.c, SELF_TYPE.c) = SELF_TYPE.c`.
  * `lub(SELF_TYPE.c, T) = lub(C, T)`.
  * `lub(T, SELF_TYPE.c) = lub(C, T)`.


## Semantic Analysis Passes

**[incomplete]**

  1. Gather all class names.
  2. Gather all identifier names.
  3. Ensure no undeclared identifier is referenced.
  4. Ensure no undeclared class is referenced.
  3. Ensure all Scope Rules are satisfied (see: above).
  4. Compute Types in a bottom-up pass over the AST.


## Error Recovery

Two solutions:

  1. Assign the type `Object` to ill-typed expressions.
  2. Introduce a new type called `No_Type` for use with ill-typed expressions.

Solution 1 is easy to implement and will enforce the type inheritance and class hierarchy tree structures.

Solution 2 will introduce further adjustments. First, every operation will be treated as defined for `No_Type`. Second,
the inheritance tree and class hierarchy will change from being Trees to Graphs. The reason for that is that expressions
will ultimately either be of type `Object` or `No_Type`, which will make the whole representation look like a graph with
two roots.
"""

import sys
import pycoolc.ast as AST


# -----------------------------------------------------------------------------
#                HELPERS: Errors, Symbol Tables, Setup Methods
# -----------------------------------------------------------------------------

# Un-boxed Primitive Value Type
UNBOXED_PRIMITIVE_VALUE_TYPE = "__prim_slot"


class SemanticAnalysisError(Exception):
    pass


class SemanticAnalysisWarning(Exception):
    pass


def setup_builtin_classes(program_ast):
    """
    Installs new classes into the Program AST instance.
    :param program_ast: an AST.Program class instance.
    :return: a new AST.Program class instance.
    """
    global UNBOXED_PRIMITIVE_VALUE_TYPE

    if program_ast is None:
        raise SemanticAnalysisError("Program AST cannot be None.")

    if not isinstance(program_ast, AST.Program):
        raise SemanticAnalysisError("Expected argument to be of type AST.Program, but got {} instead.".
                                    format(type(program_ast)))

    # Object Class
    object_class = AST.Class(name="Object", parent=None, features=[
        # Abort method: halts the program.
        AST.ClassMethod(name="abort", formal_params=[], return_type="Object", body=None),

        # Copy method: copies the object.
        AST.ClassMethod(name="copy", formal_params=[], return_type="SELF_TYPE", body=None),

        # type_name method: returns a string representation of the class name.
        AST.ClassMethod(name="type_name", formal_params=[], return_type="String", body=None)
    ])

    # IO Class
    io_class = AST.Class(name="IO", parent="Object", features=[
        # in_int: reads an integer from stdio
        AST.ClassMethod(name="in_int", formal_params=[], return_type="Int", body=None),

        # in_string: reads a string from stdio
        AST.ClassMethod(name="in_string", formal_params=[], return_type="String", body=None),

        # out_int: outputs an integer to stdio
        AST.ClassMethod(name="out_int",
                        formal_params=[AST.FormalParameter("arg", "Int")],
                        return_type="SELF_TYPE",
                        body=None),

        # out_string: outputs a string to stdio
        AST.ClassMethod(name="out_string",
                        formal_params=[AST.FormalParameter("arg", "String")],
                        return_type="SELF_TYPE",
                        body=None)
    ])

    # Int Class
    int_class = AST.Class(name="Int", parent=object_class.name, features=[
        # _val attribute: integer un-boxed value
        AST.ClassAttribute(name="_val", attr_type=UNBOXED_PRIMITIVE_VALUE_TYPE, init_expr=None)
    ])

    # Bool Class
    bool_class = AST.Class(name="Bool", parent=object_class.name, features=[
        # _val attribute: boolean un-boxed value
        AST.ClassAttribute(name="_val", attr_type=UNBOXED_PRIMITIVE_VALUE_TYPE, init_expr=None)
    ])

    # String Class
    string_class = AST.Class(name="String", parent=object_class.name, features=[
        # _val attribute: string length
        AST.ClassAttribute(name='_val', attr_type='Int', init_expr=None),

        # _str_field attribute: an un-boxed, untyped string value
        AST.ClassAttribute('_str_field', UNBOXED_PRIMITIVE_VALUE_TYPE, None),

        # length method: returns the string's length
        AST.ClassMethod(name='length', formal_params=[], return_type='Int', body=None),

        # concat method: concatenates this string with another
        AST.ClassMethod(name='concat',
                        formal_params=[AST.FormalParameter('arg', 'String')],
                        return_type='String',
                        body=None),

        # substr method: returns the substring between two integer indices
        AST.ClassMethod(name='substr',
                        formal_params=[AST.FormalParameter('arg1', 'Int'), AST.FormalParameter('arg2', 'Int')],
                        return_type='String',
                        body=None)
    ])

    # Built in classes collection
    builtin_classes = (object_class, io_class, int_class, bool_class, string_class)

    # All classes
    all_classes = builtin_classes + program_ast.classes

    # Return a new object
    return AST.Program(classes=all_classes)


# -----------------------------------------------------------------------------
#                MAIN SEMANTIC ANALYSER API
# -----------------------------------------------------------------------------

class SemanticAnalyser(object):
    def __init__(self):
        pass

    def check(self, program_ast):
        """
        TODO
        :param program_ast: TODO
        :return: TODO
        """
        program_ast = setup_builtin_classes(program_ast)
        return program_ast


# -----------------------------------------------------------------------------
#                Semantic Analyser as a Standalone Python Program
#                Usage: ./semanalyser.py cool_program.cl
# -----------------------------------------------------------------------------


def make_semantic_analyser(**kwargs):
    """
    Utility function.
    :return: PyCoolSemanter object.
    """
    _semantic_analyser = SemanticAnalyser()
    return _semantic_analyser


if __name__ == '__main__':
    from pycoolc.parser import make_parser
    from pycoolc.utils import print_readable_ast

    if len(sys.argv) != 2:
        print("Usage: ./semanalyser.py program.cl")
        exit()
    elif not str(sys.argv[1]).endswith(".cl"):
        print("Cool program source code files must end with .cl extension.")
        print("Usage: ./semanalyser.py program.cl")
        exit()

    input_file = sys.argv[1]
    with open(input_file, encoding="utf-8") as file:
        cool_program_code = file.read()

    parser = make_parser()
    parse_result = parser.parse(cool_program_code)
    sema_analyser = make_semantic_analyser()
    sema_result = sema_analyser.check(parse_result)
    print_readable_ast(sema_result)

