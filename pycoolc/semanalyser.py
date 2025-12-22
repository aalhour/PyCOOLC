#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# semanalyser.py
#
# Author:       Ahmad Alhour (aalhour.com).
# Date:         Drafted on 2016, wrote between 2018 - 2024
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
  * Method definitions (introduce method names) - Let expressions (introduce object id's)
  * Formal parameters (introduce object id's)
  * Attribute definitions (introduce object id's)
  * Case expressions (introduce object id's)

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

from __future__ import annotations

from collections import defaultdict
from logging import warning
from typing import Any

import pycoolc.ast as AST


# -----------------------------------------------------------------------------
#                           CONSTANTS
# -----------------------------------------------------------------------------

# Built-in COOL type names
OBJECT_CLASS = "Object"
IO_CLASS = "IO"
INTEGER_CLASS = "Int"
BOOLEAN_CLASS = "Bool"
STRING_CLASS = "String"
SELF_TYPE = "SELF_TYPE"

# Classes that cannot be inherited from (per COOL spec §3.1)
UNINHERITABLE_CLASSES = frozenset({INTEGER_CLASS, BOOLEAN_CLASS, STRING_CLASS})

# Un-boxed primitive value type marker (internal use for codegen)
UNBOXED_PRIMITIVE_VALUE_TYPE = "__prim_slot"


# -----------------------------------------------------------------------------
#                           EXCEPTIONS
# -----------------------------------------------------------------------------


class SemanticAnalysisError(Exception):
    """Raised when a semantic error is detected in a COOL program."""
    pass


class SemanticAnalysisWarning(Warning):
    """Raised for non-fatal semantic issues."""
    pass


# -----------------------------------------------------------------------------
#                         TYPE ENVIRONMENT
# -----------------------------------------------------------------------------


class MethodSignature:
    """
    Represents a method signature for type checking.
    
    Per COOL type rules, we need to track parameter types and return type
    for method dispatch validation.
    """
    
    def __init__(
        self,
        name: str,
        param_types: tuple[str, ...],
        return_type: str,
        defining_class: str,
    ) -> None:
        self.name = name
        self.param_types = param_types
        self.return_type = return_type
        self.defining_class = defining_class
    
    def __repr__(self) -> str:
        params = ", ".join(self.param_types)
        return f"{self.name}({params}) : {self.return_type}"


class TypeEnvironment:
    """
    Type environment for COOL type checking.
    
    Per COOL Manual §12, type checking uses three environments:
    - O: Object identifier → Type mapping (local variables, attributes)
    - M: Method signature lookup (class → method → signature)
    - C: Current class name (for SELF_TYPE resolution)
    
    This class provides a scoped environment that can be pushed/popped
    for nested scopes (let expressions, case branches, method bodies).
    """
    
    def __init__(
        self,
        current_class: str,
        parent: TypeEnvironment | None = None,
    ) -> None:
        self.current_class = current_class
        self.parent = parent
        self._object_types: dict[str, str] = {}
    
    def lookup_object(self, name: str) -> str | None:
        """
        Look up an object identifier's type.
        
        Searches the current scope, then parent scopes.
        Returns None if not found.
        """
        if name in self._object_types:
            return self._object_types[name]
        if self.parent is not None:
            return self.parent.lookup_object(name)
        return None
    
    def define_object(self, name: str, type_name: str) -> None:
        """Define an object identifier with its type in the current scope."""
        self._object_types[name] = type_name
    
    def enter_scope(self) -> TypeEnvironment:
        """Create a new nested scope for let/case expressions."""
        return TypeEnvironment(current_class=self.current_class, parent=self)
    
    def resolve_self_type(self, type_name: str) -> str:
        """
        Resolve SELF_TYPE to the current class name.
        
        Per COOL Manual §7.3: SELF_TYPE is a static type that resolves
        to the class in which the expression appears.
        """
        if type_name == SELF_TYPE:
            return self.current_class
        return type_name


# -----------------------------------------------------------------------------
#                    MAIN SEMANTIC ANALYSER
# -----------------------------------------------------------------------------


class PyCoolSemanticAnalyser:
    """
    Semantic analyzer for COOL programs.

    Currently implements:
    - Builtin type installation (Object, IO, Int, Bool, String)
    - Inheritance graph construction
    - Cyclic inheritance detection
    - Validation against inheriting from Int/Bool/String
    - Type environment and method table (Phase 1)
    """

    def __init__(self) -> None:
        self._program_ast: AST.Program | None = None
        self._classes_map: dict[str, AST.Class] = {}
        self._inheritance_graph: defaultdict[str, set[str]] = defaultdict(set)
        # Method table: class_name → method_name → MethodSignature
        self._method_table: dict[str, dict[str, MethodSignature]] = {}
        # Attribute table: class_name → attr_name → type
        self._attribute_table: dict[str, dict[str, str]] = {}
    
    def transform(self, program_ast: AST.Program) -> AST.Program:
        """
        Run semantic analysis on a COOL program AST.

        This performs inheritance checking, cycle detection, and will
        eventually include type checking.

        Args:
            program_ast: The parsed COOL program.

        Returns:
            The transformed AST with builtin types installed.

        Raises:
            ValueError: If program_ast is None.
            TypeError: If program_ast is not an AST.Program.
            SemanticAnalysisError: If semantic errors are detected.
        """
        if program_ast is None:
            raise ValueError("Program AST object cannot be None!")
        if not isinstance(program_ast, AST.Program):
            raise TypeError("Program AST object is not of type 'AST.Program'!")

        self._init_collections(program_ast)
        self._default_undefined_parent_classes_to_object()
        self._invalidate_inheritance_from_builtin_classes()
        self._check_cyclic_inheritance_relations()
        
        # Build method and attribute tables for type checking
        self._build_method_table()
        self._build_attribute_table()
        
        # Validate Main class exists with main() method
        self._check_main_class()
        
        # Validate method overriding rules
        self._check_method_overriding()
        
        # Validate no attribute redefinition
        self._check_attribute_redefinition()
        
        # Type check all classes (optional - can be disabled for partial analysis)
        self._type_check_program()

        return self._program_ast  # type: ignore[return-value]
    
    def _init_collections(self, program_ast: AST.Program) -> None:
        """Initialize internal data structures from the program AST."""
        self._program_ast = self._install_builtin_types_to_ast(program_ast)
        self._classes_map, self._inheritance_graph = \
            self._build_classes_map_and_inheritance_graph(self._program_ast)

    @staticmethod
    def _install_builtin_types_to_ast(program_ast: AST.Program) -> AST.Program:
        """
        Install the COOL builtin classes into the program AST.

        Creates and prepends Object, IO, Int, Bool, and String classes
        to the program's class list.
        """
        if program_ast is None:
            raise SemanticAnalysisError("Program AST cannot be None.")
        if not isinstance(program_ast, AST.Program):
            raise SemanticAnalysisError(
                f"Expected AST.Program, got {type(program_ast).__name__}"
            )

        # Object Class
        object_class = AST.Class(name=OBJECT_CLASS, parent=None, features=[
            # Abort method: halts the program.
            AST.ClassMethod(name="abort", formal_params=[], return_type="Object", body=None),

            # Copy method: copies the object.
            AST.ClassMethod(name="copy", formal_params=[], return_type="SELF_TYPE", body=None),

            # type_name method: returns a string representation of the class name.
            AST.ClassMethod(name="type_name", formal_params=[], return_type="String", body=None)
        ])

        # IO Class
        io_class = AST.Class(name=IO_CLASS, parent="Object", features=[
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
        int_class = AST.Class(name=INTEGER_CLASS, parent=object_class.name, features=[
            # _val attribute: integer un-boxed value
            AST.ClassAttribute(name="_val", attr_type=UNBOXED_PRIMITIVE_VALUE_TYPE, init_expr=None)
        ])

        # Bool Class
        bool_class = AST.Class(name=BOOLEAN_CLASS, parent=object_class.name, features=[
            # _val attribute: boolean un-boxed value
            AST.ClassAttribute(name="_val", attr_type=UNBOXED_PRIMITIVE_VALUE_TYPE, init_expr=None)
        ])

        # String Class
        string_class = AST.Class(name=STRING_CLASS, parent=object_class.name, features=[
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
        
        return AST.Program(classes=all_classes)

    @staticmethod
    def _build_classes_map_and_inheritance_graph(
        program_ast: AST.Program,
    ) -> tuple[dict[str, AST.Class], defaultdict[str, set[str]]]:
        """
        Build the class name → AST.Class map and the parent → children graph.

        Also validates that no class is defined twice.
        """
        if program_ast is None:
            raise SemanticAnalysisError("Program AST cannot be None.")
        if not isinstance(program_ast, AST.Program):
            raise SemanticAnalysisError(
                f"Expected AST.Program, got {type(program_ast).__name__}"
            )

        classes_map: dict[str, AST.Class] = {}
        inheritance_graph: defaultdict[str, set[str]] = defaultdict(set)

        for klass in program_ast.classes:
            if klass.name in classes_map:
                raise SemanticAnalysisError(f"Class '{klass.name}' is already defined!")
            classes_map[klass.name] = klass

            # Object has no parent
            if klass.name == OBJECT_CLASS:
                continue

            # Default to Object if no parent specified
            klass.parent = klass.parent if klass.parent else OBJECT_CLASS
            inheritance_graph[klass.parent].add(klass.name)

        return classes_map, inheritance_graph

    def _traverse_inheritance_graph(self, starting_node: str, seen: dict[str, bool]) -> bool:
        """
        Perform depth-first traversal of the inheritance graph.

        Marks all reachable nodes in the 'seen' dict.
        """
        seen[starting_node] = True

        if starting_node not in self._inheritance_graph:
            return True

        for child_node in self._inheritance_graph[starting_node]:
            self._traverse_inheritance_graph(starting_node=child_node, seen=seen)

        return True

    def _default_undefined_parent_classes_to_object(self) -> None:
        """
        Default any undefined parent classes to Object.

        If a class inherits from an undefined class, we assume it meant Object.
        """
        if not self._inheritance_graph:
            warning("Inheritance Graph is empty!")

        if not self._classes_map:
            warning("Classes Map is empty!")

        # Assume self._inheritance_graph and self._classes_map are initialized
        non_existing_parents = [
            klass for klass in self._inheritance_graph.keys() 
            if klass not in self._classes_map and klass != OBJECT_CLASS
        ]

        for parent_klass in non_existing_parents:
            # Warn the user about this
            warning(
                "Found an undefined parent class: \"{0}\". Defaulting all its children's to the Object parent class."
                .format(parent_klass))

            # Add the child classes of this nonexisting parent class to the set of classes
            #   that inherit from the "Object" class.
            self._inheritance_graph[OBJECT_CLASS] |= self._inheritance_graph[parent_klass]
            
            # For every child class that inherits from the nonexisting parent, modify their
            #   parent attribute in their AST Node to have "Object" instead.
            for child_klass in self._inheritance_graph[parent_klass]:
                self._classes_map[child_klass].parent = OBJECT_CLASS
            
            # Delete this nonexistent parent class from the inheritance map
            del self._inheritance_graph[parent_klass]

    def _invalidate_inheritance_from_builtin_classes(self) -> None:
        """
        Raise an error if any class inherits from Int, Bool, or String.

        Per COOL spec, these primitive types cannot be inherited from
        because their internal representation is unboxed.
        """
        if not self._inheritance_graph:
            warning("Inheritance Graph is empty!")
        if not self._classes_map:
            warning("Classes Map is empty!")

        for parent_klass in UNINHERITABLE_CLASSES:
            for child_klass in self._inheritance_graph[parent_klass]:
                raise SemanticAnalysisError(
                    f"Class '{child_klass}' cannot inherit from built-in class '{parent_klass}'."
                )

    def _check_cyclic_inheritance_relations(self) -> None:
        """
        Detect and report cyclic inheritance.

        Uses DFS from Object to find all reachable classes. Any class
        not reached is part of an inheritance cycle.
        """
        # Mark all classes as not seen
        seen = {class_name: False for class_name in self._classes_map}

        # Traverse from Object, marking reachable classes
        self._traverse_inheritance_graph(OBJECT_CLASS, seen)

        for class_name, was_seen in seen.items():
            if not was_seen:
                raise SemanticAnalysisError(
                    f"Class '{class_name}' is part of an inheritance cycle!"
                )

    # =========================================================================
    #                     TYPE HIERARCHY OPERATIONS
    # =========================================================================

    def get_parent(self, type_name: str) -> str | None:
        """
        Get the parent type of a class.
        
        Returns None for Object (the root of the hierarchy).
        """
        if type_name == OBJECT_CLASS:
            return None
        if type_name not in self._classes_map:
            return None
        return self._classes_map[type_name].parent

    def get_ancestors(self, type_name: str) -> list[str]:
        """
        Get all ancestors of a type, from the type itself up to Object.
        
        Returns [type_name, parent, grandparent, ..., Object].
        """
        ancestors = []
        current = type_name
        while current is not None:
            ancestors.append(current)
            current = self.get_parent(current)
        return ancestors

    def is_subtype(self, child: str, parent: str, current_class: str | None = None) -> bool:
        """
        Check if child is a subtype of parent (child <= parent).
        
        Per COOL Manual §3.2: A type T is a subtype of T' if T = T' or
        T inherits from a class that is a subtype of T'.
        
        Handles SELF_TYPE:
        - SELF_TYPE_C <= SELF_TYPE_C (same class)
        - SELF_TYPE_C <= T if C <= T
        - T <= SELF_TYPE_C is false unless T = SELF_TYPE_C
        """
        # Handle SELF_TYPE
        if child == SELF_TYPE and parent == SELF_TYPE:
            return True
        if child == SELF_TYPE:
            if current_class is None:
                return False
            child = current_class
        if parent == SELF_TYPE:
            # T <= SELF_TYPE_C only if T = SELF_TYPE_C
            return False
        
        # Standard subtype check via ancestry
        return parent in self.get_ancestors(child)

    def lub(self, type_a: str, type_b: str, current_class: str | None = None) -> str:
        """
        Compute the Least Upper Bound of two types.
        
        The LUB is the most specific common ancestor in the class hierarchy.
        
        Per COOL Manual §7.5, used for:
        - If expression: lub(then_type, else_type)
        - Case expression: lub of all branch types
        
        Handles SELF_TYPE per COOL spec:
        - lub(SELF_TYPE_C, SELF_TYPE_C) = SELF_TYPE_C
        - lub(SELF_TYPE_C, T) = lub(C, T)
        - lub(T, SELF_TYPE_C) = lub(C, T)
        """
        # SELF_TYPE handling
        if type_a == SELF_TYPE and type_b == SELF_TYPE:
            return SELF_TYPE
        
        resolved_a = current_class if type_a == SELF_TYPE else type_a
        resolved_b = current_class if type_b == SELF_TYPE else type_b
        
        if resolved_a is None or resolved_b is None:
            return OBJECT_CLASS
        
        # Get ancestors of both types
        ancestors_a = set(self.get_ancestors(resolved_a))
        ancestors_b = self.get_ancestors(resolved_b)
        
        # Find first common ancestor (walking up from B)
        for ancestor in ancestors_b:
            if ancestor in ancestors_a:
                return ancestor
        
        # Should never reach here if hierarchy is rooted at Object
        return OBJECT_CLASS

    def _build_method_table(self) -> None:
        """
        Build the method table for all classes.
        
        For each class, collects methods including inherited ones.
        Used for method dispatch type checking.
        """
        # Process classes in inheritance order (parents before children)
        processed: set[str] = set()
        
        def process_class(class_name: str) -> None:
            if class_name in processed:
                return
            
            klass = self._classes_map.get(class_name)
            if klass is None:
                return
            
            # Process parent first
            if klass.parent and klass.parent not in processed:
                process_class(klass.parent)
            
            # Start with inherited methods
            self._method_table[class_name] = {}
            if klass.parent and klass.parent in self._method_table:
                self._method_table[class_name] = dict(self._method_table[klass.parent])
            
            # Add/override with class's own methods
            for feature in klass.features:
                if isinstance(feature, AST.ClassMethod):
                    param_types = tuple(p.param_type for p in feature.formal_params)
                    sig = MethodSignature(
                        name=feature.name,
                        param_types=param_types,
                        return_type=feature.return_type,
                        defining_class=class_name,
                    )
                    self._method_table[class_name][feature.name] = sig
            
            processed.add(class_name)
        
        for class_name in self._classes_map:
            process_class(class_name)

    def _build_attribute_table(self) -> None:
        """
        Build the attribute table for all classes.
        
        For each class, collects attributes including inherited ones.
        """
        processed: set[str] = set()
        
        def process_class(class_name: str) -> None:
            if class_name in processed:
                return
            
            klass = self._classes_map.get(class_name)
            if klass is None:
                return
            
            # Process parent first
            if klass.parent and klass.parent not in processed:
                process_class(klass.parent)
            
            # Start with inherited attributes
            self._attribute_table[class_name] = {}
            if klass.parent and klass.parent in self._attribute_table:
                self._attribute_table[class_name] = dict(self._attribute_table[klass.parent])
            
            # Add class's own attributes
            for feature in klass.features:
                if isinstance(feature, AST.ClassAttribute):
                    self._attribute_table[class_name][feature.name] = feature.attr_type
            
            processed.add(class_name)
        
        for class_name in self._classes_map:
            process_class(class_name)

    def lookup_method(self, class_name: str, method_name: str) -> MethodSignature | None:
        """Look up a method in a class's method table."""
        if class_name not in self._method_table:
            return None
        return self._method_table[class_name].get(method_name)

    def lookup_attribute(self, class_name: str, attr_name: str) -> str | None:
        """Look up an attribute's type in a class's attribute table."""
        if class_name not in self._attribute_table:
            return None
        return self._attribute_table[class_name].get(attr_name)

    # =========================================================================
    #                     VALIDATION PASSES
    # =========================================================================

    def _check_main_class(self) -> None:
        """
        Verify that a Main class exists with a main() method.
        
        Per COOL Manual §3: Every program must have a class Main with a
        method main that takes no arguments.
        """
        if "Main" not in self._classes_map:
            raise SemanticAnalysisError("Program must contain a class 'Main'.")
        
        main_method = self.lookup_method("Main", "main")
        if main_method is None:
            raise SemanticAnalysisError(
                "Class 'Main' must have a 'main()' method."
            )
        
        if len(main_method.param_types) > 0:
            raise SemanticAnalysisError(
                "Method 'main' in class 'Main' must take no arguments."
            )

    def _check_method_overriding(self) -> None:
        """
        Validate method overriding rules.
        
        Per COOL Manual §5: When a method is overridden, it must have:
        - The same number of formal parameters
        - The same types for all formal parameters
        - The same return type
        """
        for class_name, klass in self._classes_map.items():
            if klass.parent is None:
                continue  # Object has no parent
            
            for feature in klass.features:
                if not isinstance(feature, AST.ClassMethod):
                    continue
                
                # Check if this method overrides a parent method
                parent_method = self._get_inherited_method(
                    klass.parent, feature.name
                )
                
                if parent_method is None:
                    continue  # Not an override
                
                # Get current method signature
                current_params = tuple(p.param_type for p in feature.formal_params)
                
                # Check parameter count
                if len(current_params) != len(parent_method.param_types):
                    raise SemanticAnalysisError(
                        f"Method '{feature.name}' in class '{class_name}' overrides "
                        f"parent method but has wrong number of parameters. "
                        f"Expected {len(parent_method.param_types)}, "
                        f"got {len(current_params)}."
                    )
                
                # Check parameter types match exactly
                for i, (cur_type, parent_type) in enumerate(
                    zip(current_params, parent_method.param_types)
                ):
                    if cur_type != parent_type:
                        raise SemanticAnalysisError(
                            f"Method '{feature.name}' in class '{class_name}' "
                            f"has parameter {i + 1} of type '{cur_type}' but parent "
                            f"method has type '{parent_type}'."
                        )
                
                # Check return type matches
                if feature.return_type != parent_method.return_type:
                    raise SemanticAnalysisError(
                        f"Method '{feature.name}' in class '{class_name}' "
                        f"has return type '{feature.return_type}' but parent "
                        f"method has return type '{parent_method.return_type}'."
                    )

    def _get_inherited_method(self, class_name: str, method_name: str) -> MethodSignature | None:
        """Look up a method in parent classes only (not including the class itself)."""
        klass = self._classes_map.get(class_name)
        if klass is None:
            return None
        
        # Check this class
        if class_name in self._method_table:
            if method_name in self._method_table[class_name]:
                sig = self._method_table[class_name][method_name]
                # Only return if defined in this class or ancestor
                if sig.defining_class == class_name:
                    return sig
                # It's inherited, so check if parent has it
                if klass.parent:
                    return self._get_inherited_method(klass.parent, method_name)
        
        # Check parent
        if klass.parent:
            return self.lookup_method(klass.parent, method_name)
        
        return None

    def _check_attribute_redefinition(self) -> None:
        """
        Validate that attributes are not redefined in subclasses.
        
        Per COOL Manual §5: Attributes cannot be redefined in subclasses.
        A class may only define an attribute if no ancestor already has
        an attribute with that name.
        """
        for class_name, klass in self._classes_map.items():
            if klass.parent is None:
                continue  # Object has no parent
            
            # Get parent's attributes
            parent_attrs = self._attribute_table.get(klass.parent, {})
            
            for feature in klass.features:
                if not isinstance(feature, AST.ClassAttribute):
                    continue
                
                if feature.name in parent_attrs:
                    raise SemanticAnalysisError(
                        f"Attribute '{feature.name}' in class '{class_name}' "
                        f"is already defined in ancestor class."
                    )

    # =========================================================================
    #                     TYPE CHECKING
    # =========================================================================

    def _type_check_program(self) -> None:
        """
        Type check all classes in the program.
        
        For each class:
        - Type check each attribute's initialization expression
        - Type check each method's body
        """
        if self._program_ast is None:
            return
        
        for klass in self._program_ast.classes:
            # Skip builtin classes (no body to check)
            if klass.name in {OBJECT_CLASS, IO_CLASS, INTEGER_CLASS, BOOLEAN_CLASS, STRING_CLASS}:
                continue
            
            self._type_check_class(klass)

    def _type_check_class(self, klass: AST.Class) -> None:
        """Type check all features in a class."""
        for feature in klass.features:
            if isinstance(feature, AST.ClassAttribute):
                self._type_check_attribute(klass.name, feature)
            elif isinstance(feature, AST.ClassMethod):
                self._type_check_method(klass.name, feature)

    def _type_check_attribute(self, class_name: str, attr: AST.ClassAttribute) -> None:
        """
        Type check an attribute initialization expression.
        
        Per COOL Manual §5: The type of the init expression must conform
        to the declared type of the attribute.
        """
        if attr.init_expr is None:
            return  # No initialization, uses default
        
        # Create environment with self and class attributes
        env = self._create_class_env(class_name)
        
        # Infer type of init expression
        init_type = self._infer_type(attr.init_expr, env)
        
        # Check conformance
        if not self.is_subtype(init_type, attr.attr_type, class_name):
            raise SemanticAnalysisError(
                f"Attribute '{attr.name}' in class '{class_name}' has declared type "
                f"'{attr.attr_type}' but initialization expression has type '{init_type}'."
            )

    def _type_check_method(self, class_name: str, method: AST.ClassMethod) -> None:
        """
        Type check a method body.
        
        Per COOL Manual §5: The type of the method body must conform
        to the declared return type.
        """
        if method.body is None:
            return  # Builtin methods have no body
        
        # Create environment with self, formals, and class attributes
        env = self._create_method_env(class_name, method)
        
        # Infer type of body
        body_type = self._infer_type(method.body, env)
        
        # Handle SELF_TYPE return
        declared_return = method.return_type
        
        # Check conformance
        if not self.is_subtype(body_type, declared_return, class_name):
            raise SemanticAnalysisError(
                f"Method '{method.name}' in class '{class_name}' has declared return type "
                f"'{declared_return}' but body has type '{body_type}'."
            )

    def _create_class_env(self, class_name: str) -> TypeEnvironment:
        """Create a type environment for a class context."""
        env = TypeEnvironment(current_class=class_name)
        
        # Add 'self' with SELF_TYPE
        env.define_object("self", SELF_TYPE)
        
        # Add all attributes (including inherited)
        attrs = self._attribute_table.get(class_name, {})
        for attr_name, attr_type in attrs.items():
            env.define_object(attr_name, attr_type)
        
        return env

    def _create_method_env(self, class_name: str, method: AST.ClassMethod) -> TypeEnvironment:
        """Create a type environment for a method body."""
        env = self._create_class_env(class_name)
        
        # Add formal parameters
        for formal in method.formal_params:
            env.define_object(formal.name, formal.param_type)
        
        return env

    def _infer_type(self, expr: AST.AST, env: TypeEnvironment) -> str:
        """
        Infer the type of an expression.
        
        Per COOL Manual §7: Type inference rules for each expression form.
        """
        match expr:
            # Constants
            case AST.Integer():
                return INTEGER_CLASS
            
            case AST.String():
                return STRING_CLASS
            
            case AST.Boolean():
                return BOOLEAN_CLASS
            
            # Identifiers
            case AST.Self():
                return SELF_TYPE
            
            case AST.Object(name=name):
                obj_type = env.lookup_object(name)
                if obj_type is None:
                    raise SemanticAnalysisError(
                        f"Undefined variable '{name}' in class '{env.current_class}'."
                    )
                return obj_type
            
            # Assignment
            case AST.Assignment(instance=instance, expr=value_expr):
                # Look up the variable type
                var_type = env.lookup_object(instance.name)
                if var_type is None:
                    raise SemanticAnalysisError(
                        f"Undefined variable '{instance.name}' in assignment."
                    )
                
                # Infer type of value
                value_type = self._infer_type(value_expr, env)
                
                # Check conformance
                if not self.is_subtype(value_type, var_type, env.current_class):
                    raise SemanticAnalysisError(
                        f"Cannot assign expression of type '{value_type}' "
                        f"to variable '{instance.name}' of type '{var_type}'."
                    )
                
                return value_type  # Assignment returns the assigned value's type
            
            # Arithmetic operations
            case AST.Addition(first=left, second=right):
                return self._check_arithmetic(left, right, "+", env)
            
            case AST.Subtraction(first=left, second=right):
                return self._check_arithmetic(left, right, "-", env)
            
            case AST.Multiplication(first=left, second=right):
                return self._check_arithmetic(left, right, "*", env)
            
            case AST.Division(first=left, second=right):
                return self._check_arithmetic(left, right, "/", env)
            
            # Comparisons
            case AST.LessThan(first=left, second=right):
                return self._check_comparison(left, right, "<", env)
            
            case AST.LessThanOrEqual(first=left, second=right):
                return self._check_comparison(left, right, "<=", env)
            
            case AST.Equal(first=left, second=right):
                # Equality is special - if one side is Int/Bool/String,
                # both must be the same type
                left_type = self._infer_type(left, env)
                right_type = self._infer_type(right, env)
                
                primitives = {INTEGER_CLASS, BOOLEAN_CLASS, STRING_CLASS}
                if left_type in primitives or right_type in primitives:
                    if left_type != right_type:
                        raise SemanticAnalysisError(
                            f"Cannot compare '{left_type}' with '{right_type}' using '='."
                        )
                
                return BOOLEAN_CLASS
            
            # Unary operations
            case AST.IntegerComplement(integer_expr=operand):
                operand_type = self._infer_type(operand, env)
                if operand_type != INTEGER_CLASS:
                    raise SemanticAnalysisError(
                        f"Integer complement (~) requires Int, got '{operand_type}'."
                    )
                return INTEGER_CLASS
            
            case AST.BooleanComplement(boolean_expr=operand):
                operand_type = self._infer_type(operand, env)
                if operand_type != BOOLEAN_CLASS:
                    raise SemanticAnalysisError(
                        f"Boolean complement (not) requires Bool, got '{operand_type}'."
                    )
                return BOOLEAN_CLASS
            
            # New object
            case AST.NewObject(type=new_type):
                if new_type == SELF_TYPE:
                    return SELF_TYPE
                if new_type not in self._classes_map:
                    raise SemanticAnalysisError(
                        f"Cannot instantiate undefined class '{new_type}'."
                    )
                return new_type
            
            # IsVoid
            case AST.IsVoid():
                # Type check the expression, but isvoid always returns Bool
                self._infer_type(expr.expr, env)
                return BOOLEAN_CLASS
            
            # Block
            case AST.Block(expr_list=exprs):
                if not exprs:
                    raise SemanticAnalysisError("Empty block expression.")
                
                # Type check all expressions, return type of last
                result_type = OBJECT_CLASS
                for e in exprs:
                    result_type = self._infer_type(e, env)
                return result_type
            
            # If-then-else
            case AST.If(predicate=pred, then_body=then_expr, else_body=else_expr):
                pred_type = self._infer_type(pred, env)
                if pred_type != BOOLEAN_CLASS:
                    raise SemanticAnalysisError(
                        f"If predicate must be Bool, got '{pred_type}'."
                    )
                
                then_type = self._infer_type(then_expr, env)
                else_type = self._infer_type(else_expr, env)
                
                return self.lub(then_type, else_type, env.current_class)
            
            # While loop
            case AST.WhileLoop(predicate=pred, body=body):
                pred_type = self._infer_type(pred, env)
                if pred_type != BOOLEAN_CLASS:
                    raise SemanticAnalysisError(
                        f"While predicate must be Bool, got '{pred_type}'."
                    )
                
                self._infer_type(body, env)
                return OBJECT_CLASS  # While always returns Object
            
            # Let expression
            case AST.Let(instance=var_name, return_type=var_type, init_expr=init, body=body):
                # Check init expression if present
                if init is not None:
                    init_type = self._infer_type(init, env)
                    if not self.is_subtype(init_type, var_type, env.current_class):
                        raise SemanticAnalysisError(
                            f"Let variable '{var_name}' has type '{var_type}' but "
                            f"initialization has type '{init_type}'."
                        )
                
                # Create new scope with the variable
                inner_env = env.enter_scope()
                inner_env.define_object(var_name, var_type)
                
                return self._infer_type(body, inner_env)
            
            # Case expression
            case AST.Case(expr=case_expr, actions=actions):
                # Type check the expression being cased on
                self._infer_type(case_expr, env)
                
                # Check all branches and compute LUB
                if not actions:
                    raise SemanticAnalysisError("Case expression has no branches.")
                
                branch_types: list[str] = []
                seen_types: set[str] = set()
                
                for action in actions:
                    # action is a tuple (name, type, body) or AST.Action
                    if isinstance(action, AST.Action):
                        branch_name = action.name
                        branch_type = action.action_type
                        branch_body = action.body
                    else:
                        branch_name, branch_type, branch_body = action
                    
                    # Check for duplicate branch types
                    if branch_type in seen_types:
                        raise SemanticAnalysisError(
                            f"Duplicate branch type '{branch_type}' in case expression."
                        )
                    seen_types.add(branch_type)
                    
                    # Create scope with branch variable
                    branch_env = env.enter_scope()
                    branch_env.define_object(branch_name, branch_type)
                    
                    body_type = self._infer_type(branch_body, branch_env)
                    branch_types.append(body_type)
                
                # Compute LUB of all branch types
                result = branch_types[0]
                for t in branch_types[1:]:
                    result = self.lub(result, t, env.current_class)
                return result
            
            # Dynamic dispatch
            case AST.DynamicDispatch(instance=obj, method=method_name, arguments=args):
                obj_type = self._infer_type(obj, env)
                return self._check_dispatch(obj_type, None, method_name, args or (), env)
            
            # Static dispatch
            case AST.StaticDispatch(instance=obj, dispatch_type=static_type, method=method_name, arguments=args):
                obj_type = self._infer_type(obj, env)
                
                # Check obj conforms to static type
                if not self.is_subtype(obj_type, static_type, env.current_class):
                    raise SemanticAnalysisError(
                        f"Static dispatch type '{static_type}' is not a supertype "
                        f"of expression type '{obj_type}'."
                    )
                
                return self._check_dispatch(obj_type, static_type, method_name, args or (), env)
            
            case _:
                raise SemanticAnalysisError(
                    f"Type inference not implemented for {type(expr).__name__}."
                )

    def _check_arithmetic(self, left: AST.AST, right: AST.AST, op: str, env: TypeEnvironment) -> str:
        """Check arithmetic operation types."""
        left_type = self._infer_type(left, env)
        right_type = self._infer_type(right, env)
        
        if left_type != INTEGER_CLASS:
            raise SemanticAnalysisError(
                f"Left operand of '{op}' must be Int, got '{left_type}'."
            )
        if right_type != INTEGER_CLASS:
            raise SemanticAnalysisError(
                f"Right operand of '{op}' must be Int, got '{right_type}'."
            )
        
        return INTEGER_CLASS

    def _check_comparison(self, left: AST.AST, right: AST.AST, op: str, env: TypeEnvironment) -> str:
        """Check comparison operation types."""
        left_type = self._infer_type(left, env)
        right_type = self._infer_type(right, env)
        
        if left_type != INTEGER_CLASS:
            raise SemanticAnalysisError(
                f"Left operand of '{op}' must be Int, got '{left_type}'."
            )
        if right_type != INTEGER_CLASS:
            raise SemanticAnalysisError(
                f"Right operand of '{op}' must be Int, got '{right_type}'."
            )
        
        return BOOLEAN_CLASS

    def _check_dispatch(
        self,
        obj_type: str,
        static_type: str | None,
        method_name: str,
        args: tuple[AST.AST, ...],
        env: TypeEnvironment,
    ) -> str:
        """
        Check a method dispatch and return the result type.
        
        For dynamic dispatch, look up method in obj_type.
        For static dispatch, look up method in static_type.
        """
        # Resolve SELF_TYPE to actual class for method lookup
        lookup_type = static_type if static_type else obj_type
        if lookup_type == SELF_TYPE:
            lookup_type = env.current_class
        
        # Look up method
        method_sig = self.lookup_method(lookup_type, method_name)
        if method_sig is None:
            raise SemanticAnalysisError(
                f"Method '{method_name}' not found in class '{lookup_type}'."
            )
        
        # Check argument count
        if len(args) != len(method_sig.param_types):
            raise SemanticAnalysisError(
                f"Method '{method_name}' expects {len(method_sig.param_types)} arguments, "
                f"got {len(args)}."
            )
        
        # Check argument types
        for i, (arg, expected_type) in enumerate(zip(args, method_sig.param_types)):
            arg_type = self._infer_type(arg, env)
            if not self.is_subtype(arg_type, expected_type, env.current_class):
                raise SemanticAnalysisError(
                    f"Argument {i + 1} to method '{method_name}' has type '{arg_type}' "
                    f"but expected '{expected_type}'."
                )
        
        # Handle SELF_TYPE return
        return_type = method_sig.return_type
        if return_type == SELF_TYPE:
            # SELF_TYPE in return position resolves to the type of the object
            return obj_type
        
        return return_type


# -----------------------------------------------------------------------------
#
#                Semantic Analyser as a Standalone Python Program
#                Usage: ./semanalyser.py cool_program.cl
#
# -----------------------------------------------------------------------------


def make_semantic_analyser(**kwargs: Any) -> PyCoolSemanticAnalyser:
    """Factory function to create a semantic analyzer."""
    return PyCoolSemanticAnalyser()


if __name__ == '__main__':
    import sys
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
    sema_result = sema_analyser.transform(parse_result)
    print_readable_ast(sema_result)

