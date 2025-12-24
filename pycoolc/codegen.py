#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# codegen.py
#
# Author:       Ahmad Alhour (aalhour.com).
# Date:         2024
# Description:  MIPS 32-bit code generator for COOL programs.
#
# This module translates a type-checked COOL AST into MIPS assembly that
# can be executed on the SPIM simulator.
# -----------------------------------------------------------------------------

"""
# COOL Object Layout (MIPS 32-bit)

Each COOL object has the following memory layout:

    Offset  Field
    ------  -----
    0       Class tag (unique integer per class)
    4       Object size (in bytes)
    8       Dispatch pointer (address of dispatch table)
    12+     Attributes (4 bytes each, in inheritance order)

# Dispatch Tables

Each class has a dispatch table containing pointers to method implementations.
Methods are ordered by first appearance in inheritance chain.

# Register Conventions

    $a0     Self pointer (current object)
    $a1-$a3 Method arguments
    $sp     Stack pointer
    $fp     Frame pointer
    $ra     Return address
    $v0     Return value / syscall number
    $t0-$t9 Temporaries (caller-saved)
    $s0-$s7 Saved registers (callee-saved)

# Stack Frame Layout

    Higher addresses
    +---------------+
    | Argument n    |
    | ...           |
    | Argument 1    |
    | Return address|
    | Old $fp       | <- $fp points here
    | Local 1       |
    | ...           |
    | Local n       |
    | Temporaries   | <- $sp points here
    +---------------+
    Lower addresses
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TextIO

import pycoolc.ast as AST
from pycoolc.semanalyser import (
    BOOLEAN_CLASS,
    INTEGER_CLASS,
    IO_CLASS,
    OBJECT_CLASS,
    SELF_TYPE,
    STRING_CLASS,
    PyCoolSemanticAnalyser,
)

# -----------------------------------------------------------------------------
#                           CONSTANTS
# -----------------------------------------------------------------------------

# Word size in bytes (MIPS 32-bit)
WORD_SIZE = 4

# Object header size: class_tag + size + dispatch_ptr
OBJECT_HEADER_SIZE = 3 * WORD_SIZE

# Default values for primitive types
DEFAULT_INT = 0
DEFAULT_BOOL = False
DEFAULT_STRING = ""

# Label prefixes
CLASS_INIT_PREFIX = "_init_"
CLASS_PROTOBJ_PREFIX = "_protObj_"
CLASS_DISPTAB_PREFIX = "_dispTab_"
METHOD_PREFIX = "_method_"
STRING_CONST_PREFIX = "_str_const_"
INT_CONST_PREFIX = "_int_const_"
BOOL_CONST_PREFIX = "_bool_const_"


# -----------------------------------------------------------------------------
#                           DATA STRUCTURES
# -----------------------------------------------------------------------------


@dataclass
class ClassInfo:
    """Information about a class needed for code generation."""

    name: str
    tag: int  # Unique class identifier
    size: int  # Object size in bytes
    parent: str | None
    attributes: list[tuple[str, str]]  # (name, type) pairs in order
    methods: list[tuple[str, str]]  # (name, defining_class) pairs in order


@dataclass
class StringConstant:
    """A string constant in the data segment."""

    label: str
    value: str
    length: int


@dataclass
class IntConstant:
    """An integer constant in the data segment."""

    label: str
    value: int


# -----------------------------------------------------------------------------
#                           CODE GENERATOR
# -----------------------------------------------------------------------------


class MIPSCodeGenerator:
    """
    MIPS code generator for COOL programs.

    Takes a semantically analyzed COOL program and generates MIPS assembly
    that can be run on the SPIM simulator.
    """

    def __init__(self, analyzer: PyCoolSemanticAnalyser) -> None:
        self.analyzer = analyzer
        self.program: AST.Program | None = None

        # Class information indexed by name
        self.class_info: dict[str, ClassInfo] = {}

        # Class tags (for runtime type checking)
        self.class_tags: dict[str, int] = {}

        # Constants pool
        self.string_constants: dict[str, StringConstant] = {}
        self.int_constants: dict[int, IntConstant] = {}

        # Label counter for unique labels
        self._label_counter = 0

        # Output buffer
        self._output: list[str] = []

        # Current class/method context
        self._current_class: str = ""
        self._current_method: str = ""

        # Local variable offsets from $fp
        self._locals: dict[str, int] = {}
        self._next_local_offset = 0

        # Local variable types for dispatch type resolution
        self._local_types: dict[str, str] = {}

        # Self offset from $fp (depends on frame size)
        self._self_offset = 0

    def _get_expr_type(self, expr: AST.AST) -> str:
        """
        Get the static type of an expression for method dispatch.

        This is a simplified version of type inference for codegen purposes.
        We only need to handle the cases that affect method lookup.
        """
        match expr:
            case AST.Self():
                return self._current_class

            case AST.Object(name=name):
                # Check local variables first
                if name in self._local_types:
                    return self._local_types[name]
                # Check attributes
                info = self.class_info.get(self._current_class)
                if info:
                    for attr_name, attr_type in info.attributes:
                        if attr_name == name:
                            return attr_type
                return OBJECT_CLASS

            case AST.NewObject(type=type_name):
                return type_name if type_name != SELF_TYPE else self._current_class

            case AST.DynamicDispatch(instance=obj, method=method_name):
                # Get the type of the object, then find the method return type
                obj_type = self._get_expr_type(obj)
                return_type = self._find_method_return_type(obj_type, method_name)
                return return_type if return_type != SELF_TYPE else obj_type

            case AST.StaticDispatch(instance=obj, dispatch_type=dtype, method=method_name):
                return_type = self._find_method_return_type(dtype, method_name)
                return return_type if return_type != SELF_TYPE else self._get_expr_type(obj)

            case AST.Integer():
                return INTEGER_CLASS

            case AST.String():
                return STRING_CLASS

            case AST.Boolean():
                return BOOLEAN_CLASS

            case _:
                return OBJECT_CLASS

    def _find_method_return_type(self, class_name: str, method_name: str) -> str:
        """Find the return type of a method in a class or its ancestors."""
        if self.program is None:
            return OBJECT_CLASS

        # Search up the inheritance chain
        current = class_name
        while current:
            for klass in self.program.classes:
                if klass.name == current:
                    for feature in klass.features:
                        if isinstance(feature, AST.ClassMethod) and feature.name == method_name:
                            return feature.return_type
                    # Move to parent
                    current = klass.parent
                    break
            else:
                # Class not found in program (might be builtin)
                break

        # Check builtin methods
        builtin_methods = {
            ("Object", "abort"): OBJECT_CLASS,
            ("Object", "copy"): SELF_TYPE,
            ("Object", "type_name"): STRING_CLASS,
            ("IO", "out_string"): SELF_TYPE,
            ("IO", "out_int"): SELF_TYPE,
            ("IO", "in_string"): STRING_CLASS,
            ("IO", "in_int"): INTEGER_CLASS,
            ("String", "length"): INTEGER_CLASS,
            ("String", "concat"): STRING_CLASS,
            ("String", "substr"): STRING_CLASS,
        }

        # Check if method is inherited from a builtin
        ancestors = self._get_ancestors(class_name)
        for ancestor in ancestors:
            if (ancestor, method_name) in builtin_methods:
                return builtin_methods[(ancestor, method_name)]

        return OBJECT_CLASS

    def _get_ancestors(self, class_name: str) -> list[str]:
        """Get list of ancestors including the class itself."""
        result = [class_name]
        current = class_name

        if self.program is None:
            return result

        while current and current != OBJECT_CLASS:
            for klass in self.program.classes:
                if klass.name == current:
                    if klass.parent:
                        result.append(klass.parent)
                        current = klass.parent
                    else:
                        current = None
                    break
            else:
                # Check builtin parents
                builtin_parents = {
                    IO_CLASS: OBJECT_CLASS,
                    INTEGER_CLASS: OBJECT_CLASS,
                    STRING_CLASS: OBJECT_CLASS,
                    BOOLEAN_CLASS: OBJECT_CLASS,
                }
                if current in builtin_parents:
                    result.append(builtin_parents[current])
                    current = builtin_parents[current]
                else:
                    break

        return result

    def generate(self, program: AST.Program) -> str:
        """
        Generate MIPS assembly for a COOL program.

        Returns the complete assembly as a string.
        """
        self.program = program
        self._output = []

        # Build class information
        self._build_class_info()

        # Collect all constants from the program BEFORE generating code
        # This is necessary because we emit .data before .text
        self._collect_all_constants()

        # Generate data segment
        self._emit_data_segment()

        # Generate text segment
        self._emit_text_segment()

        return "\n".join(self._output)

    def _collect_all_constants(self) -> None:
        """
        Traverse the entire AST to collect all string and integer constants.

        This must be done before emitting the data segment so that all
        constant labels are available when generating code.
        """
        if self.program is None:
            return

        for klass in self.program.classes:
            # Skip built-in classes
            if klass.name in {OBJECT_CLASS, IO_CLASS, INTEGER_CLASS, BOOLEAN_CLASS, STRING_CLASS}:
                continue

            for feature in klass.features:
                if isinstance(feature, AST.ClassAttribute):
                    if feature.init_expr is not None:
                        self._collect_constants_from_expr(feature.init_expr)
                elif isinstance(feature, AST.ClassMethod):
                    if feature.body is not None:
                        self._collect_constants_from_expr(feature.body)

    def _collect_constants_from_expr(self, expr: AST.AST) -> None:
        """Recursively collect all constants from an expression."""
        match expr:
            case AST.Integer(content=value):
                if value not in self.int_constants:
                    label = f"{INT_CONST_PREFIX}{len(self.int_constants)}"
                    self.int_constants[value] = IntConstant(label=label, value=value)

            case AST.String(content=value):
                if value not in self.string_constants:
                    label = f"{STRING_CONST_PREFIX}{len(self.string_constants)}"
                    self.string_constants[value] = StringConstant(
                        label=label, value=value, length=len(value)
                    )

            case AST.Block(expr_list=exprs):
                for e in exprs:
                    self._collect_constants_from_expr(e)

            case AST.If(predicate=pred, then_body=then_expr, else_body=else_expr):
                self._collect_constants_from_expr(pred)
                self._collect_constants_from_expr(then_expr)
                self._collect_constants_from_expr(else_expr)

            case AST.WhileLoop(predicate=pred, body=body):
                self._collect_constants_from_expr(pred)
                self._collect_constants_from_expr(body)

            case AST.Let(init_expr=init, body=body):
                if init is not None:
                    self._collect_constants_from_expr(init)
                self._collect_constants_from_expr(body)

            case AST.Case(expr=case_expr, actions=actions):
                self._collect_constants_from_expr(case_expr)
                for action in actions:
                    # Actions can be either Action objects or tuples (name, type, body)
                    if isinstance(action, AST.Action):
                        self._collect_constants_from_expr(action.body)
                    elif isinstance(action, tuple) and len(action) == 3:
                        _, _, body = action
                        self._collect_constants_from_expr(body)

            case AST.DynamicDispatch(instance=obj, arguments=args):
                self._collect_constants_from_expr(obj)
                if args:
                    for arg in args:
                        self._collect_constants_from_expr(arg)

            case AST.StaticDispatch(instance=obj, arguments=args):
                self._collect_constants_from_expr(obj)
                if args:
                    for arg in args:
                        self._collect_constants_from_expr(arg)

            case AST.Assignment(expr=value):
                self._collect_constants_from_expr(value)

            case AST.NewObject():
                pass

            case AST.IsVoid(expr=inner):
                self._collect_constants_from_expr(inner)

            case AST.IntegerComplement(integer_expr=operand):
                self._collect_constants_from_expr(operand)

            case AST.BooleanComplement(boolean_expr=operand):
                self._collect_constants_from_expr(operand)

            case AST.Addition(first=left, second=right):
                self._collect_constants_from_expr(left)
                self._collect_constants_from_expr(right)

            case AST.Subtraction(first=left, second=right):
                self._collect_constants_from_expr(left)
                self._collect_constants_from_expr(right)

            case AST.Multiplication(first=left, second=right):
                self._collect_constants_from_expr(left)
                self._collect_constants_from_expr(right)

            case AST.Division(first=left, second=right):
                self._collect_constants_from_expr(left)
                self._collect_constants_from_expr(right)

            case AST.LessThan(first=left, second=right):
                self._collect_constants_from_expr(left)
                self._collect_constants_from_expr(right)

            case AST.LessThanOrEqual(first=left, second=right):
                self._collect_constants_from_expr(left)
                self._collect_constants_from_expr(right)

            case AST.Equal(first=left, second=right):
                self._collect_constants_from_expr(left)
                self._collect_constants_from_expr(right)

            case _:
                # Boolean, Self, Object, etc. - no nested expressions
                pass

    def generate_to_file(self, program: AST.Program, output_file: TextIO) -> None:
        """Generate MIPS assembly to a file."""
        code = self.generate(program)
        output_file.write(code)

    # =========================================================================
    #                     CLASS INFO BUILDING
    # =========================================================================

    def _build_class_info(self) -> None:
        """Build class information for all classes."""
        if self.program is None:
            return

        # Assign class tags in inheritance order
        # Object = 0, then children in DFS order
        self._assign_class_tags()

        # Build info for each class
        for klass in self.program.classes:
            self._build_single_class_info(klass)

    def _assign_class_tags(self) -> None:
        """Assign unique tags to each class."""
        # Built-in classes get fixed tags
        self.class_tags = {
            OBJECT_CLASS: 0,
            IO_CLASS: 1,
            INTEGER_CLASS: 2,
            BOOLEAN_CLASS: 3,
            STRING_CLASS: 4,
        }

        next_tag = 5
        if self.program is None:
            return

        for klass in self.program.classes:
            if klass.name not in self.class_tags:
                self.class_tags[klass.name] = next_tag
                next_tag += 1

    def _build_single_class_info(self, klass: AST.Class) -> None:
        """Build info for a single class."""
        # Collect all attributes including inherited
        attrs = self._collect_attributes(klass.name)

        # Collect all methods including inherited
        methods = self._collect_methods(klass.name)

        # Calculate object size
        size = OBJECT_HEADER_SIZE + len(attrs) * WORD_SIZE

        self.class_info[klass.name] = ClassInfo(
            name=klass.name,
            tag=self.class_tags[klass.name],
            size=size,
            parent=klass.parent,
            attributes=attrs,
            methods=methods,
        )

    def _collect_attributes(self, class_name: str) -> list[tuple[str, str]]:
        """Collect all attributes for a class, including inherited ones."""
        attrs: list[tuple[str, str]] = []

        # Get inheritance chain (child to Object)
        chain = self.analyzer.get_ancestors(class_name)

        # Process from Object down to child
        for ancestor_name in reversed(chain):
            klass = self.analyzer._classes_map.get(ancestor_name)
            if klass is None:
                continue

            for feature in klass.features:
                if isinstance(feature, AST.ClassAttribute):
                    attrs.append((feature.name, feature.attr_type))

        return attrs

    def _collect_methods(self, class_name: str) -> list[tuple[str, str]]:
        """
        Collect all methods for a class in dispatch table order.

        Returns (method_name, defining_class) pairs.
        """
        methods: list[tuple[str, str]] = []
        method_names_seen: set[str] = set()

        # Get inheritance chain (child to Object)
        chain = self.analyzer.get_ancestors(class_name)

        # Process from Object down to child
        for ancestor_name in reversed(chain):
            klass = self.analyzer._classes_map.get(ancestor_name)
            if klass is None:
                continue

            for feature in klass.features:
                if isinstance(feature, AST.ClassMethod):
                    if feature.name not in method_names_seen:
                        # New method
                        methods.append((feature.name, ancestor_name))
                        method_names_seen.add(feature.name)
                    else:
                        # Override - update defining class
                        for i, (name, _) in enumerate(methods):
                            if name == feature.name:
                                methods[i] = (feature.name, ancestor_name)
                                break

        return methods

    # =========================================================================
    #                     LABEL GENERATION
    # =========================================================================

    def _new_label(self, prefix: str = "label") -> str:
        """Generate a unique label."""
        self._label_counter += 1
        return f"_{prefix}_{self._label_counter}"

    # =========================================================================
    #                     OUTPUT HELPERS
    # =========================================================================

    def _emit(self, line: str) -> None:
        """Emit a line of assembly."""
        self._output.append(line)

    def _emit_label(self, label: str) -> None:
        """Emit a label."""
        self._emit(f"{label}:")

    def _emit_comment(self, comment: str) -> None:
        """Emit a comment."""
        self._emit(f"# {comment}")

    def _emit_blank(self) -> None:
        """Emit a blank line."""
        self._emit("")

    def _emit_instr(self, op: str, *args: str) -> None:
        """Emit an instruction."""
        if args:
            self._emit(f"    {op} {', '.join(args)}")
        else:
            self._emit(f"    {op}")

    # =========================================================================
    #                     DATA SEGMENT
    # =========================================================================

    def _emit_data_segment(self) -> None:
        """Emit the .data segment with class objects and constants."""
        self._emit(".data")
        self._emit_blank()

        # Emit class name strings
        self._emit_comment("Class name strings")
        self._emit_class_name_strings()
        self._emit_blank()

        # Emit class dispatch tables
        self._emit_comment("Dispatch tables")
        self._emit_dispatch_tables()
        self._emit_blank()

        # Emit prototype objects
        self._emit_comment("Prototype objects")
        self._emit_prototype_objects()
        self._emit_blank()

        # Emit string constants
        self._emit_comment("String constants")
        self._emit_string_constants()
        self._emit_blank()

        # Emit integer constants
        self._emit_comment("Integer constants")
        self._emit_int_constants()
        self._emit_blank()

        # Emit boolean constants
        self._emit_comment("Boolean constants")
        self._emit_bool_constants()
        self._emit_blank()

        # Heap pointer
        self._emit_comment("Heap management")
        self._emit("_heap_start:")
        self._emit("    .word 0")
        self._emit_blank()

    def _emit_class_name_strings(self) -> None:
        """Emit string constants for class names (for type_name)."""
        # Emit String objects for each class name
        for class_name, _info in self.class_info.items():
            name_len = len(class_name)
            self._emit_label(f"_class_name_{class_name}")
            self._emit(f"    .word {self.class_tags[STRING_CLASS]}")  # String tag
            self._emit(f"    .word {OBJECT_HEADER_SIZE + WORD_SIZE + name_len + 1}")  # Size
            self._emit(f"    .word {CLASS_DISPTAB_PREFIX}{STRING_CLASS}")  # Dispatch
            self._emit(f"    .word {name_len}")  # Length
            self._emit(f'    .asciiz "{class_name}"')
            self._emit("    .align 2")

        # Emit lookup table: class_tag -> class_name_string
        self._emit_label("_class_name_table")
        # Emit in tag order (0 = Object, 1 = IO, 2 = Int, 3 = Bool, 4 = String, then user classes)
        sorted_classes = sorted(self.class_info.items(), key=lambda x: x[1].tag)
        for class_name, _info in sorted_classes:
            self._emit(f"    .word _class_name_{class_name}")

    def _emit_dispatch_tables(self) -> None:
        """Emit dispatch tables for all classes."""
        for class_name, info in self.class_info.items():
            self._emit_label(f"{CLASS_DISPTAB_PREFIX}{class_name}")
            for method_name, defining_class in info.methods:
                self._emit(f"    .word {METHOD_PREFIX}{defining_class}_{method_name}")

    def _emit_prototype_objects(self) -> None:
        """Emit prototype objects for object creation."""
        for class_name, info in self.class_info.items():
            self._emit_label(f"{CLASS_PROTOBJ_PREFIX}{class_name}")
            self._emit(f"    .word {info.tag}")  # Class tag
            self._emit(f"    .word {info.size}")  # Object size
            self._emit(f"    .word {CLASS_DISPTAB_PREFIX}{class_name}")  # Dispatch table

            # Attribute slots (initialized to 0/void)
            for attr_name, attr_type in info.attributes:
                if attr_type in (INTEGER_CLASS, BOOLEAN_CLASS):
                    self._emit(f"    .word 0  # {attr_name}")
                elif attr_type == STRING_CLASS:
                    self._emit(f"    .word _str_const_empty  # {attr_name}")
                else:
                    self._emit(f"    .word 0  # {attr_name} (void)")

    def _emit_string_constants(self) -> None:
        """Emit string constants."""
        # Always emit empty string
        self._emit("_str_const_empty:")
        self._emit(f"    .word {self.class_tags[STRING_CLASS]}")  # Class tag
        self._emit(f"    .word {OBJECT_HEADER_SIZE + WORD_SIZE}")  # Size
        self._emit(f"    .word {CLASS_DISPTAB_PREFIX}{STRING_CLASS}")  # Dispatch
        self._emit("    .word 0")  # Length
        self._emit('    .asciiz ""')
        self._emit("    .align 2")

        # Emit collected string constants
        for value, const in self.string_constants.items():
            self._emit_label(const.label)
            self._emit(f"    .word {self.class_tags[STRING_CLASS]}")
            self._emit(f"    .word {OBJECT_HEADER_SIZE + 2 * WORD_SIZE}")
            self._emit(f"    .word {CLASS_DISPTAB_PREFIX}{STRING_CLASS}")
            self._emit(f"    .word {const.length}")
            # Escape the string for MIPS/SPIM
            # SPIM doesn't interpret \\ as escaped backslash - it outputs literally
            # So we only escape quotes, newlines, and tabs
            # For backslashes, we use .byte directives for problematic cases
            if "\\" in value and (value.endswith("\\") or '\\"' in value):
                # Use .byte for strings with problematic backslash positions
                self._emit_string_as_bytes(value)
            else:
                escaped = value.replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
                self._emit(f'    .asciiz "{escaped}"')
            self._emit("    .align 2")

    def _emit_string_as_bytes(self, value: str) -> None:
        """Emit a string using .byte directives for problematic escape sequences."""
        bytes_list = [str(ord(c)) for c in value]
        bytes_list.append("0")  # Null terminator
        # Emit in chunks of 16 bytes per line
        for i in range(0, len(bytes_list), 16):
            chunk = bytes_list[i : i + 16]
            self._emit(f"    .byte {', '.join(chunk)}")

    def _emit_int_constants(self) -> None:
        """Emit integer constants."""
        for value, const in self.int_constants.items():
            self._emit_label(const.label)
            self._emit(f"    .word {self.class_tags[INTEGER_CLASS]}")
            self._emit(f"    .word {OBJECT_HEADER_SIZE + WORD_SIZE}")
            self._emit(f"    .word {CLASS_DISPTAB_PREFIX}{INTEGER_CLASS}")
            self._emit(f"    .word {value}")

    def _emit_bool_constants(self) -> None:
        """Emit boolean constants (true and false)."""
        # False
        self._emit("_bool_const_false:")
        self._emit(f"    .word {self.class_tags[BOOLEAN_CLASS]}")
        self._emit(f"    .word {OBJECT_HEADER_SIZE + WORD_SIZE}")
        self._emit(f"    .word {CLASS_DISPTAB_PREFIX}{BOOLEAN_CLASS}")
        self._emit("    .word 0")

        # True
        self._emit("_bool_const_true:")
        self._emit(f"    .word {self.class_tags[BOOLEAN_CLASS]}")
        self._emit(f"    .word {OBJECT_HEADER_SIZE + WORD_SIZE}")
        self._emit(f"    .word {CLASS_DISPTAB_PREFIX}{BOOLEAN_CLASS}")
        self._emit("    .word 1")

    # =========================================================================
    #                     TEXT SEGMENT
    # =========================================================================

    def _emit_text_segment(self) -> None:
        """Emit the .text segment with all code."""
        self._emit(".text")
        self._emit_blank()

        # Entry point
        self._emit_entry_point()
        self._emit_blank()

        # Runtime support routines
        self._emit_runtime_support()
        self._emit_blank()

        # Built-in methods
        self._emit_builtin_methods()
        self._emit_blank()

        # Class initializers
        self._emit_class_initializers()
        self._emit_blank()

        # User-defined methods
        self._emit_user_methods()

    def _emit_entry_point(self) -> None:
        """Emit the program entry point."""
        self._emit_comment("Program entry point")
        self._emit(".globl main")
        self._emit_label("main")

        # Set up heap
        self._emit_instr("la", "$t0", "_heap_start")
        self._emit_instr("sw", "$gp", "0($t0)")

        # Create Main object
        self._emit_instr("la", "$a0", f"{CLASS_PROTOBJ_PREFIX}Main")
        self._emit_instr("jal", "_Object_copy")

        # Initialize Main object
        self._emit_instr("jal", f"{CLASS_INIT_PREFIX}Main")

        # Call main method
        self._emit_instr("jal", f"{METHOD_PREFIX}Main_main")

        # Exit
        self._emit_instr("li", "$v0", "10")
        self._emit_instr("syscall")

    def _emit_runtime_support(self) -> None:
        """Emit runtime support routines."""
        self._emit_comment("Runtime support routines")

        # Object.copy - allocate and copy an object
        self._emit_label("_Object_copy")
        # $a0 = prototype object pointer
        # Returns new object in $a0

        # Get object size
        self._emit_instr("lw", "$t0", "4($a0)")  # Size is at offset 4

        # Allocate memory (using sbrk syscall)
        self._emit_instr("move", "$t1", "$a0")  # Save prototype pointer
        self._emit_instr("move", "$a0", "$t0")  # Size to allocate
        self._emit_instr("li", "$v0", "9")  # sbrk syscall
        self._emit_instr("syscall")
        # $v0 now has new object address

        # Copy prototype to new object
        self._emit_instr("move", "$t2", "$v0")  # New object pointer
        self._emit_instr("lw", "$t3", "4($t1)")  # Get size again

        self._emit_label("_Object_copy_loop")
        self._emit_instr("beqz", "$t3", "_Object_copy_done")
        self._emit_instr("lw", "$t4", "0($t1)")
        self._emit_instr("sw", "$t4", "0($t2)")
        self._emit_instr("addiu", "$t1", "$t1", "4")
        self._emit_instr("addiu", "$t2", "$t2", "4")
        self._emit_instr("addiu", "$t3", "$t3", "-4")
        self._emit_instr("j", "_Object_copy_loop")

        self._emit_label("_Object_copy_done")
        self._emit_instr("move", "$a0", "$v0")
        self._emit_instr("jr", "$ra")
        self._emit_blank()

        # Equality comparison for objects
        self._emit_label("_equality_test")
        # $a0 = first object, $a1 = second object
        # Returns boolean in $a0
        self._emit_instr("beq", "$a0", "$a1", "_eq_true")  # Same pointer

        # Check if both are Int, Bool, or String for value comparison
        self._emit_instr("beqz", "$a0", "_eq_false")
        self._emit_instr("beqz", "$a1", "_eq_false")

        self._emit_instr("lw", "$t0", "0($a0)")  # Class tag of first
        self._emit_instr("lw", "$t1", "0($a1)")  # Class tag of second
        self._emit_instr("bne", "$t0", "$t1", "_eq_false")  # Different types

        # Check if Int (tag 2) - compare values
        self._emit_instr("li", "$t2", "2")
        self._emit_instr("bne", "$t0", "$t2", "_eq_check_bool")
        self._emit_instr("lw", "$t0", "12($a0)")
        self._emit_instr("lw", "$t1", "12($a1)")
        self._emit_instr("beq", "$t0", "$t1", "_eq_true")
        self._emit_instr("j", "_eq_false")

        # Check if Bool (tag 3) - compare values
        self._emit_label("_eq_check_bool")
        self._emit_instr("li", "$t2", "3")
        self._emit_instr("bne", "$t0", "$t2", "_eq_check_string")
        self._emit_instr("lw", "$t0", "12($a0)")
        self._emit_instr("lw", "$t1", "12($a1)")
        self._emit_instr("beq", "$t0", "$t1", "_eq_true")
        self._emit_instr("j", "_eq_false")

        # Check if String (tag 4) - compare contents
        self._emit_label("_eq_check_string")
        self._emit_instr("li", "$t2", "4")
        self._emit_instr("bne", "$t0", "$t2", "_eq_false")
        # String comparison - compare lengths first
        self._emit_instr("lw", "$t0", "12($a0)")  # Length of first
        self._emit_instr("lw", "$t1", "12($a1)")  # Length of second
        self._emit_instr("bne", "$t0", "$t1", "_eq_false")
        # Compare string contents byte by byte
        # $t0 = length (same for both), $a0/$a1 = string objects
        self._emit_instr("addiu", "$t2", "$a0", "16")  # ptr to first string data
        self._emit_instr("addiu", "$t3", "$a1", "16")  # ptr to second string data
        self._emit_label("_eq_string_loop")
        self._emit_instr("beqz", "$t0", "_eq_true")  # All bytes matched
        self._emit_instr("lb", "$t4", "0($t2)")
        self._emit_instr("lb", "$t5", "0($t3)")
        self._emit_instr("bne", "$t4", "$t5", "_eq_false")
        self._emit_instr("addiu", "$t2", "$t2", "1")
        self._emit_instr("addiu", "$t3", "$t3", "1")
        self._emit_instr("addiu", "$t0", "$t0", "-1")
        self._emit_instr("j", "_eq_string_loop")

        self._emit_label("_eq_true")
        self._emit_instr("la", "$a0", "_bool_const_true")
        self._emit_instr("jr", "$ra")

        self._emit_label("_eq_false")
        self._emit_instr("la", "$a0", "_bool_const_false")
        self._emit_instr("jr", "$ra")
        self._emit_blank()

        # Dispatch on void error
        self._emit_label("_dispatch_void")
        self._emit_instr("la", "$a0", "_dispatch_void_msg")
        self._emit_instr("li", "$v0", "4")
        self._emit_instr("syscall")
        self._emit_instr("li", "$v0", "10")
        self._emit_instr("syscall")

        self._emit(".data")
        self._emit("_dispatch_void_msg:")
        self._emit('    .asciiz "Error: Dispatch on void\\n"')
        self._emit(".text")
        self._emit_blank()

    def _emit_builtin_methods(self) -> None:
        """Emit built-in methods for Object, IO, String, Int, Bool."""
        self._emit_comment("Built-in methods")

        # Object.abort
        self._emit_label(f"{METHOD_PREFIX}Object_abort")
        self._emit_instr("li", "$v0", "10")  # Exit syscall
        self._emit_instr("syscall")

        # Object.type_name - returns String with class name
        self._emit_label(f"{METHOD_PREFIX}Object_type_name")
        self._emit_instr("lw", "$t0", "0($a0)")  # Get class tag
        self._emit_instr("sll", "$t0", "$t0", "2")  # Multiply by 4 (word size)
        self._emit_instr("la", "$t1", "_class_name_table")
        self._emit_instr("add", "$t0", "$t0", "$t1")  # Address in table
        self._emit_instr("lw", "$a0", "0($t0)")  # Load String object pointer
        self._emit_instr("jr", "$ra")

        # Object.copy - already defined as _Object_copy
        self._emit_label(f"{METHOD_PREFIX}Object_copy")
        self._emit_instr("j", "_Object_copy")

        # IO.out_string
        self._emit_label(f"{METHOD_PREFIX}IO_out_string")
        # $a0 = self, $a1 = string object
        self._emit_instr("move", "$t0", "$a0")  # Save self
        self._emit_instr("addiu", "$a0", "$a1", "16")  # String data starts at offset 16
        self._emit_instr("li", "$v0", "4")  # Print string syscall
        self._emit_instr("syscall")
        self._emit_instr("move", "$a0", "$t0")  # Return self
        self._emit_instr("jr", "$ra")

        # IO.out_int
        self._emit_label(f"{METHOD_PREFIX}IO_out_int")
        # $a0 = self, $a1 = int object
        self._emit_instr("move", "$t0", "$a0")  # Save self
        self._emit_instr("lw", "$a0", "12($a1)")  # Get int value
        self._emit_instr("li", "$v0", "1")  # Print int syscall
        self._emit_instr("syscall")
        self._emit_instr("move", "$a0", "$t0")  # Return self
        self._emit_instr("jr", "$ra")

        # IO.in_string
        # String object layout: [tag, size, dispatch, length, ...chars..., null]
        # We allocate a String object inline with the chars after it
        self._emit_label(f"{METHOD_PREFIX}IO_in_string")
        # Save $ra and self
        self._emit_instr("addiu", "$sp", "$sp", "-16")
        self._emit_instr("sw", "$ra", "12($sp)")
        self._emit_instr("sw", "$a0", "8($sp)")  # Save self

        # Allocate buffer for input (1024 bytes)
        self._emit_instr("li", "$a0", "1024")
        self._emit_instr("li", "$v0", "9")  # sbrk syscall
        self._emit_instr("syscall")
        self._emit_instr("sw", "$v0", "4($sp)")  # Save buffer address

        # Read string into buffer (syscall 8)
        self._emit_instr("move", "$a0", "$v0")  # Buffer address
        self._emit_instr("li", "$a1", "1024")  # Max length
        self._emit_instr("li", "$v0", "8")  # Read string syscall
        self._emit_instr("syscall")

        # Calculate string length (find null or newline)
        self._emit_instr("lw", "$t0", "4($sp)")  # Buffer address
        self._emit_instr("move", "$t1", "$t0")  # Current position
        self._emit_instr("li", "$t2", "0")  # Length counter
        self._emit_label("_in_string_len_loop")
        self._emit_instr("lb", "$t3", "0($t1)")
        self._emit_instr("beqz", "$t3", "_in_string_len_done")
        self._emit_instr("li", "$t4", "10")  # Newline
        self._emit_instr("beq", "$t3", "$t4", "_in_string_len_done")
        self._emit_instr("addiu", "$t1", "$t1", "1")
        self._emit_instr("addiu", "$t2", "$t2", "1")
        self._emit_instr("j", "_in_string_len_loop")
        self._emit_label("_in_string_len_done")
        self._emit_instr("sb", "$zero", "0($t1)")  # Null terminate
        self._emit_instr("sw", "$t2", "0($sp)")  # Save length

        # Allocate String object: 16 bytes header + string + 1 null + padding
        # Size = 16 (header) + length + 1, rounded up to 4
        self._emit_instr("addiu", "$t2", "$t2", "20")  # 16 + len + 1 + 3 for align
        self._emit_instr("li", "$t3", "-4")
        self._emit_instr("and", "$a0", "$t2", "$t3")  # Round down to 4
        self._emit_instr("li", "$v0", "9")  # sbrk
        self._emit_instr("syscall")
        self._emit_instr("move", "$a0", "$v0")  # String object address

        # Fill in String object header
        self._emit_instr("li", "$t0", "4")  # String class tag
        self._emit_instr("sw", "$t0", "0($a0)")
        self._emit_instr("sw", "$t2", "4($a0)")  # Size
        self._emit_instr("la", "$t0", f"{CLASS_DISPTAB_PREFIX}String")
        self._emit_instr("sw", "$t0", "8($a0)")  # Dispatch table
        self._emit_instr("lw", "$t0", "0($sp)")  # Length
        self._emit_instr("sw", "$t0", "12($a0)")  # Store length

        # Copy string data to offset 16
        self._emit_instr("lw", "$t1", "4($sp)")  # Source buffer
        self._emit_instr("addiu", "$t2", "$a0", "16")  # Dest (after header)
        self._emit_label("_in_string_copy_loop")
        self._emit_instr("lb", "$t3", "0($t1)")
        self._emit_instr("sb", "$t3", "0($t2)")
        self._emit_instr("beqz", "$t3", "_in_string_copy_done")
        self._emit_instr("addiu", "$t1", "$t1", "1")
        self._emit_instr("addiu", "$t2", "$t2", "1")
        self._emit_instr("j", "_in_string_copy_loop")
        self._emit_label("_in_string_copy_done")

        # Restore and return (String object already in $a0)
        self._emit_instr("lw", "$ra", "12($sp)")
        self._emit_instr("addiu", "$sp", "$sp", "16")
        self._emit_instr("jr", "$ra")

        # IO.in_int
        self._emit_label(f"{METHOD_PREFIX}IO_in_int")
        # Save $ra before calling _Object_copy
        self._emit_instr("addiu", "$sp", "$sp", "-8")
        self._emit_instr("sw", "$ra", "4($sp)")
        self._emit_instr("li", "$v0", "5")  # Read int syscall
        self._emit_instr("syscall")
        # Create Int object with the value
        self._emit_instr("sw", "$v0", "0($sp)")  # Save value on stack
        self._emit_instr("la", "$a0", f"{CLASS_PROTOBJ_PREFIX}Int")
        self._emit_instr("jal", "_Object_copy")
        self._emit_instr("lw", "$t0", "0($sp)")  # Restore value
        self._emit_instr("sw", "$t0", "12($a0)")  # Store in Int object
        # Restore $ra and return
        self._emit_instr("lw", "$ra", "4($sp)")
        self._emit_instr("addiu", "$sp", "$sp", "8")
        self._emit_instr("jr", "$ra")

        # String.length
        self._emit_label(f"{METHOD_PREFIX}String_length")
        # Save $ra before calling _Object_copy
        self._emit_instr("addiu", "$sp", "$sp", "-8")
        self._emit_instr("sw", "$ra", "4($sp)")
        self._emit_instr("lw", "$t0", "12($a0)")  # Get length field
        self._emit_instr("sw", "$t0", "0($sp)")  # Save length on stack
        # Create Int object
        self._emit_instr("la", "$a0", f"{CLASS_PROTOBJ_PREFIX}Int")
        self._emit_instr("jal", "_Object_copy")
        self._emit_instr("lw", "$t0", "0($sp)")  # Restore length
        self._emit_instr("sw", "$t0", "12($a0)")  # Store in Int object
        # Restore $ra and return
        self._emit_instr("lw", "$ra", "4($sp)")
        self._emit_instr("addiu", "$sp", "$sp", "8")
        self._emit_instr("jr", "$ra")

        # String.concat - simplified
        self._emit_label(f"{METHOD_PREFIX}String_concat")
        self._emit_instr("jr", "$ra")  # Return self for now

        # String.substr(i: Int, l: Int) -> String
        # $a0 = self (String), $a1 = i (Int object), $a2 = l (Int object)
        # String layout: [tag, size, disp, length, chars...]
        self._emit_label(f"{METHOD_PREFIX}String_substr")
        self._emit_instr("addiu", "$sp", "$sp", "-20")
        self._emit_instr("sw", "$ra", "16($sp)")
        self._emit_instr("sw", "$a0", "12($sp)")  # Save self
        self._emit_instr("lw", "$t0", "12($a1)")  # i value from Int object
        self._emit_instr("sw", "$t0", "8($sp)")  # Save i
        self._emit_instr("lw", "$t1", "12($a2)")  # l value from Int object
        self._emit_instr("sw", "$t1", "4($sp)")  # Save l

        # Allocate new String: 16 header + l + 1 null, rounded to 4
        self._emit_instr("addiu", "$t2", "$t1", "20")  # 16 + l + 1 + 3
        self._emit_instr("li", "$t3", "-4")
        self._emit_instr("and", "$a0", "$t2", "$t3")  # Round down to 4
        self._emit_instr("sw", "$a0", "0($sp)")  # Save size
        self._emit_instr("li", "$v0", "9")  # sbrk
        self._emit_instr("syscall")
        self._emit_instr("move", "$a0", "$v0")  # New String object

        # Fill header
        self._emit_instr("li", "$t0", "4")  # String tag
        self._emit_instr("sw", "$t0", "0($a0)")
        self._emit_instr("lw", "$t0", "0($sp)")  # Size
        self._emit_instr("sw", "$t0", "4($a0)")
        self._emit_instr("la", "$t0", f"{CLASS_DISPTAB_PREFIX}String")
        self._emit_instr("sw", "$t0", "8($a0)")
        self._emit_instr("lw", "$t0", "4($sp)")  # l
        self._emit_instr("sw", "$t0", "12($a0)")  # Length

        # Copy l chars from self starting at i
        self._emit_instr("lw", "$t1", "12($sp)")  # self
        self._emit_instr("addiu", "$t1", "$t1", "16")  # Point to chars
        self._emit_instr("lw", "$t2", "8($sp)")  # i
        self._emit_instr("add", "$t1", "$t1", "$t2")  # src = self.chars + i
        self._emit_instr("addiu", "$t2", "$a0", "16")  # dest = new.chars
        self._emit_instr("lw", "$t3", "4($sp)")  # l (counter)
        self._emit_label("_substr_copy_loop")
        self._emit_instr("blez", "$t3", "_substr_copy_done")
        self._emit_instr("lb", "$t4", "0($t1)")
        self._emit_instr("sb", "$t4", "0($t2)")
        self._emit_instr("addiu", "$t1", "$t1", "1")
        self._emit_instr("addiu", "$t2", "$t2", "1")
        self._emit_instr("addiu", "$t3", "$t3", "-1")
        self._emit_instr("j", "_substr_copy_loop")
        self._emit_label("_substr_copy_done")
        self._emit_instr("sb", "$zero", "0($t2)")  # Null terminate

        # Return new string (already in $a0)
        self._emit_instr("lw", "$ra", "16($sp)")
        self._emit_instr("addiu", "$sp", "$sp", "20")
        self._emit_instr("jr", "$ra")

        self._emit_blank()

    def _emit_class_initializers(self) -> None:
        """Emit class initialization methods."""
        self._emit_comment("Class initializers")

        if self.program is None:
            return

        for klass in self.program.classes:
            self._emit_class_initializer(klass)

    def _emit_class_initializer(self, klass: AST.Class) -> None:
        """Emit initializer for a single class."""
        self._emit_label(f"{CLASS_INIT_PREFIX}{klass.name}")

        # Prologue
        self._emit_instr("addiu", "$sp", "$sp", "-12")
        self._emit_instr("sw", "$fp", "8($sp)")
        self._emit_instr("sw", "$ra", "4($sp)")
        self._emit_instr("sw", "$a0", "0($sp)")
        self._emit_instr("move", "$fp", "$sp")

        # Call parent initializer
        if klass.parent and klass.parent != OBJECT_CLASS:
            self._emit_instr("jal", f"{CLASS_INIT_PREFIX}{klass.parent}")
            self._emit_instr("lw", "$a0", "0($fp)")  # Restore self

        # Initialize attributes with init expressions
        self._current_class = klass.name
        self._self_offset = 0  # Self is at 0($fp) in initializer
        self._locals = {}
        self._local_types = {}
        info = self.class_info.get(klass.name)

        for feature in klass.features:
            if isinstance(feature, AST.ClassAttribute) and feature.init_expr is not None:
                # Generate init expression
                self._generate_expr(feature.init_expr)

                # Store result in attribute slot
                # Find attribute offset
                if info:
                    for i, (attr_name, _) in enumerate(info.attributes):
                        if attr_name == feature.name:
                            offset = OBJECT_HEADER_SIZE + i * WORD_SIZE
                            self._emit_instr("lw", "$t0", "0($fp)")  # Load self
                            self._emit_instr("sw", "$a0", f"{offset}($t0)")  # Store in attr
                            break

        # Epilogue
        self._emit_instr("lw", "$a0", "0($fp)")  # Return self
        self._emit_instr("lw", "$ra", "4($fp)")
        self._emit_instr("lw", "$fp", "8($fp)")
        self._emit_instr("addiu", "$sp", "$sp", "12")
        self._emit_instr("jr", "$ra")
        self._emit_blank()

    def _emit_user_methods(self) -> None:
        """Emit all user-defined methods."""
        self._emit_comment("User-defined methods")

        if self.program is None:
            return

        for klass in self.program.classes:
            # Skip builtins
            if klass.name in {OBJECT_CLASS, IO_CLASS, INTEGER_CLASS, BOOLEAN_CLASS, STRING_CLASS}:
                continue

            for feature in klass.features:
                if isinstance(feature, AST.ClassMethod):
                    self._emit_method(klass.name, feature)

    def _emit_method(self, class_name: str, method: AST.ClassMethod) -> None:
        """Emit code for a method."""
        self._current_class = class_name
        self._current_method = method.name
        self._locals = {}
        self._local_types = {}
        self._next_local_offset = 0

        self._emit_label(f"{METHOD_PREFIX}{class_name}_{method.name}")

        # Prologue - save $fp, $ra, and self
        frame_size = 12 + len(method.formal_params) * WORD_SIZE
        self._self_offset = frame_size - 12  # self is stored at this offset from $fp
        self._emit_instr("addiu", "$sp", "$sp", f"-{frame_size}")
        self._emit_instr("sw", "$fp", f"{frame_size - 4}($sp)")
        self._emit_instr("sw", "$ra", f"{frame_size - 8}($sp)")
        self._emit_instr("sw", "$a0", f"{self._self_offset}($sp)")  # self
        self._emit_instr("move", "$fp", "$sp")

        # Store formals in frame with their types
        for i, formal in enumerate(method.formal_params):
            offset = frame_size - 16 - i * WORD_SIZE
            self._locals[formal.name] = offset
            self._local_types[formal.name] = formal.param_type
            # Arguments come in $a1, $a2, $a3 or on stack
            if i < 3:
                self._emit_instr("sw", f"$a{i + 1}", f"{offset}($sp)")

        # Generate code for body
        if method.body is not None:
            self._generate_expr(method.body)

        # Epilogue
        self._emit_instr("lw", "$ra", f"{frame_size - 8}($fp)")
        self._emit_instr("lw", "$fp", f"{frame_size - 4}($fp)")
        self._emit_instr("addiu", "$sp", "$sp", f"{frame_size}")
        self._emit_instr("jr", "$ra")
        self._emit_blank()

    # =========================================================================
    #                     EXPRESSION CODE GENERATION
    # =========================================================================

    def _generate_expr(self, expr: AST.AST) -> None:
        """Generate code for an expression. Result in $a0."""
        match expr:
            case AST.Integer(content=value):
                self._generate_int_literal(value)

            case AST.String(content=value):
                self._generate_string_literal(value)

            case AST.Boolean(content=value):
                self._generate_bool_literal(value)

            case AST.Self():
                # Load self from frame (offset depends on frame size)
                self._emit_instr("lw", "$a0", f"{self._self_offset}($fp)")

            case AST.Object(name=name):
                self._generate_object_ref(name)

            case AST.Assignment(instance=instance, expr=value):
                self._generate_assignment(instance.name, value)

            case AST.Addition(first=left, second=right):
                self._generate_arith(left, right, "add")

            case AST.Subtraction(first=left, second=right):
                self._generate_arith(left, right, "sub")

            case AST.Multiplication(first=left, second=right):
                self._generate_arith(left, right, "mul")

            case AST.Division(first=left, second=right):
                self._generate_arith(left, right, "div")

            case AST.LessThan(first=left, second=right):
                self._generate_comparison(left, right, "slt")

            case AST.LessThanOrEqual(first=left, second=right):
                self._generate_comparison(left, right, "sle")

            case AST.Equal(first=left, second=right):
                self._generate_equality(left, right)

            case AST.IntegerComplement(integer_expr=operand):
                self._generate_expr(operand)
                self._emit_instr("lw", "$t0", "12($a0)")
                self._emit_instr("neg", "$t0", "$t0")
                self._generate_int_object("$t0")

            case AST.BooleanComplement(boolean_expr=operand):
                self._generate_expr(operand)
                self._emit_instr("lw", "$t0", "12($a0)")
                self._emit_instr("xori", "$t0", "$t0", "1")
                self._generate_bool_object("$t0")

            case AST.NewObject(type=new_type):
                self._generate_new(new_type)

            case AST.IsVoid(expr=inner):
                self._generate_isvoid(inner)

            case AST.Block(expr_list=exprs):
                for e in exprs:
                    self._generate_expr(e)

            case AST.If(predicate=pred, then_body=then_expr, else_body=else_expr):
                self._generate_if(pred, then_expr, else_expr)

            case AST.WhileLoop(predicate=pred, body=body):
                self._generate_while(pred, body)

            case AST.Let(instance=var, return_type=var_type, init_expr=init, body=body):
                self._generate_let(var, var_type, init, body)

            case AST.Case(expr=case_expr, actions=actions):
                self._generate_case(case_expr, actions)

            case AST.DynamicDispatch(instance=obj, method=method_name, arguments=args):
                self._generate_dispatch(obj, None, method_name, args or ())

            case AST.StaticDispatch(
                instance=obj, dispatch_type=static_type, method=method_name, arguments=args
            ):
                self._generate_dispatch(obj, static_type, method_name, args or ())

            case _:
                self._emit_comment(f"TODO: {type(expr).__name__}")
                self._emit_instr("li", "$a0", "0")

    def _generate_int_literal(self, value: int) -> None:
        """Generate an Int object for a literal."""
        # Get or create constant
        if value not in self.int_constants:
            label = f"{INT_CONST_PREFIX}{len(self.int_constants)}"
            self.int_constants[value] = IntConstant(label=label, value=value)

        const = self.int_constants[value]
        self._emit_instr("la", "$a0", const.label)

    def _generate_string_literal(self, value: str) -> None:
        """Generate a String object for a literal."""
        if value not in self.string_constants:
            # This should never happen - all constants should be collected first
            raise RuntimeError(
                f"String constant not collected during first pass: {value!r}. "
                f"This indicates a bug in _collect_constants_from_expr."
            )

        const = self.string_constants[value]
        self._emit_instr("la", "$a0", const.label)

    def _generate_bool_literal(self, value: bool) -> None:
        """Generate a Bool object for a literal."""
        if value:
            self._emit_instr("la", "$a0", "_bool_const_true")
        else:
            self._emit_instr("la", "$a0", "_bool_const_false")

    def _generate_object_ref(self, name: str) -> None:
        """Generate code to load a variable."""
        if name == "self":
            self._emit_instr("lw", "$a0", f"{self._self_offset}($fp)")
        elif name in self._locals:
            offset = self._locals[name]
            self._emit_instr("lw", "$a0", f"{offset}($fp)")
        else:
            # Must be an attribute - load from self
            info = self.class_info.get(self._current_class)
            if info:
                for i, (attr_name, _) in enumerate(info.attributes):
                    if attr_name == name:
                        offset = OBJECT_HEADER_SIZE + i * WORD_SIZE
                        self._emit_instr("lw", "$t0", f"{self._self_offset}($fp)")  # Load self
                        self._emit_instr("lw", "$a0", f"{offset}($t0)")
                        return
            self._emit_comment(f"Unknown variable: {name}")
            self._emit_instr("li", "$a0", "0")

    def _generate_assignment(self, name: str, value: AST.AST) -> None:
        """Generate code for assignment."""
        self._generate_expr(value)

        if name in self._locals:
            offset = self._locals[name]
            self._emit_instr("sw", "$a0", f"{offset}($fp)")
        else:
            # Attribute assignment
            info = self.class_info.get(self._current_class)
            if info:
                for i, (attr_name, _) in enumerate(info.attributes):
                    if attr_name == name:
                        offset = OBJECT_HEADER_SIZE + i * WORD_SIZE
                        self._emit_instr("lw", "$t0", f"{self._self_offset}($fp)")  # Load self
                        self._emit_instr("sw", "$a0", f"{offset}($t0)")
                        return

    def _generate_arith(self, left: AST.AST, right: AST.AST, op: str) -> None:
        """Generate arithmetic operation."""
        # Evaluate left
        self._generate_expr(left)
        self._emit_instr("lw", "$t0", "12($a0)")  # Get int value
        self._emit_instr("addiu", "$sp", "$sp", "-4")
        self._emit_instr("sw", "$t0", "0($sp)")

        # Evaluate right
        self._generate_expr(right)
        self._emit_instr("lw", "$t1", "12($a0)")  # Get int value

        # Pop left
        self._emit_instr("lw", "$t0", "0($sp)")
        self._emit_instr("addiu", "$sp", "$sp", "4")

        # Perform operation
        if op == "div":
            self._emit_instr("div", "$t0", "$t1")
            self._emit_instr("mflo", "$t0")
        else:
            self._emit_instr(op, "$t0", "$t0", "$t1")

        # Create new Int object
        self._generate_int_object("$t0")

    def _generate_int_object(self, value_reg: str) -> None:
        """Create an Int object with value in register."""
        self._emit_instr("sw", value_reg, "-4($sp)")
        self._emit_instr("addiu", "$sp", "$sp", "-4")

        self._emit_instr("la", "$a0", f"{CLASS_PROTOBJ_PREFIX}Int")
        self._emit_instr("jal", "_Object_copy")

        self._emit_instr("addiu", "$sp", "$sp", "4")
        self._emit_instr("lw", "$t0", "-4($sp)")
        self._emit_instr("sw", "$t0", "12($a0)")

    def _generate_bool_object(self, value_reg: str) -> None:
        """Create a Bool object with value in register."""
        false_label = self._new_label("bool_false")
        done = self._new_label("bool_done")
        self._emit_instr("beqz", value_reg, false_label)
        self._emit_instr("la", "$a0", "_bool_const_true")
        self._emit_instr("j", done)
        self._emit_label(false_label)
        self._emit_instr("la", "$a0", "_bool_const_false")
        self._emit_label(done)

    def _generate_comparison(self, left: AST.AST, right: AST.AST, op: str) -> None:
        """Generate comparison operation."""
        # Evaluate left
        self._generate_expr(left)
        self._emit_instr("lw", "$t0", "12($a0)")
        self._emit_instr("addiu", "$sp", "$sp", "-4")
        self._emit_instr("sw", "$t0", "0($sp)")

        # Evaluate right
        self._generate_expr(right)
        self._emit_instr("lw", "$t1", "12($a0)")

        # Pop left
        self._emit_instr("lw", "$t0", "0($sp)")
        self._emit_instr("addiu", "$sp", "$sp", "4")

        # Compare
        if op == "sle":
            # a <= b is !(b < a)
            self._emit_instr("slt", "$t0", "$t1", "$t0")  # b < a
            self._emit_instr("xori", "$t0", "$t0", "1")  # negate
        else:
            self._emit_instr(op, "$t0", "$t0", "$t1")

        self._generate_bool_object("$t0")

    def _generate_equality(self, left: AST.AST, right: AST.AST) -> None:
        """Generate equality test."""
        # Evaluate left
        self._generate_expr(left)
        self._emit_instr("addiu", "$sp", "$sp", "-4")
        self._emit_instr("sw", "$a0", "0($sp)")

        # Evaluate right
        self._generate_expr(right)
        self._emit_instr("move", "$a1", "$a0")

        # Pop left
        self._emit_instr("lw", "$a0", "0($sp)")
        self._emit_instr("addiu", "$sp", "$sp", "4")

        # Call equality test
        self._emit_instr("jal", "_equality_test")

    def _generate_new(self, type_name: str) -> None:
        """Generate new object creation."""
        if type_name == SELF_TYPE:
            # Get prototype from class tag
            self._emit_comment("new SELF_TYPE")
            self._emit_instr("lw", "$t0", f"{self._self_offset}($fp)")  # Load self
            # Would need class_objTab lookup - simplified
            self._emit_instr("la", "$a0", f"{CLASS_PROTOBJ_PREFIX}{self._current_class}")
        else:
            self._emit_instr("la", "$a0", f"{CLASS_PROTOBJ_PREFIX}{type_name}")

        self._emit_instr("jal", "_Object_copy")
        self._emit_instr(
            "jal",
            f"{CLASS_INIT_PREFIX}{type_name if type_name != SELF_TYPE else self._current_class}",
        )

    def _generate_isvoid(self, expr: AST.AST) -> None:
        """Generate isvoid test."""
        self._generate_expr(expr)
        true_label = self._new_label("isvoid_true")
        done_label = self._new_label("isvoid_done")

        self._emit_instr("beqz", "$a0", true_label)
        self._emit_instr("la", "$a0", "_bool_const_false")
        self._emit_instr("j", done_label)
        self._emit_label(true_label)
        self._emit_instr("la", "$a0", "_bool_const_true")
        self._emit_label(done_label)

    def _generate_if(self, pred: AST.AST, then_expr: AST.AST, else_expr: AST.AST) -> None:
        """Generate if-then-else."""
        else_label = self._new_label("if_else")
        done_label = self._new_label("if_done")

        self._generate_expr(pred)
        self._emit_instr("lw", "$t0", "12($a0)")  # Get bool value
        self._emit_instr("beqz", "$t0", else_label)

        self._generate_expr(then_expr)
        self._emit_instr("j", done_label)

        self._emit_label(else_label)
        self._generate_expr(else_expr)

        self._emit_label(done_label)

    def _generate_while(self, pred: AST.AST, body: AST.AST) -> None:
        """Generate while loop."""
        loop_label = self._new_label("while_loop")
        done_label = self._new_label("while_done")

        self._emit_label(loop_label)
        self._generate_expr(pred)
        self._emit_instr("lw", "$t0", "12($a0)")
        self._emit_instr("beqz", "$t0", done_label)

        self._generate_expr(body)
        self._emit_instr("j", loop_label)

        self._emit_label(done_label)
        self._emit_instr("li", "$a0", "0")  # While returns void

    def _generate_let(self, var: str, var_type: str, init: AST.AST | None, body: AST.AST) -> None:
        """Generate let expression."""
        # Allocate space for local
        self._emit_instr("addiu", "$sp", "$sp", "-4")
        local_offset = -self._next_local_offset - 4
        self._next_local_offset += 4

        # Save old binding if exists
        old_offset = self._locals.get(var)
        old_type = self._local_types.get(var)
        self._locals[var] = local_offset
        self._local_types[var] = var_type

        # Initialize
        if init is not None:
            self._generate_expr(init)
        else:
            # Default initialization
            if var_type == INTEGER_CLASS:
                self._emit_instr("la", "$a0", f"{CLASS_PROTOBJ_PREFIX}Int")
            elif var_type == BOOLEAN_CLASS:
                self._emit_instr("la", "$a0", "_bool_const_false")
            elif var_type == STRING_CLASS:
                self._emit_instr("la", "$a0", "_str_const_empty")
            else:
                self._emit_instr("li", "$a0", "0")  # void

        self._emit_instr("sw", "$a0", f"{local_offset}($fp)")

        # Generate body
        self._generate_expr(body)

        # Restore
        self._emit_instr("addiu", "$sp", "$sp", "4")
        self._next_local_offset -= 4
        if old_offset is not None:
            self._locals[var] = old_offset
        else:
            del self._locals[var]
        if old_type is not None:
            self._local_types[var] = old_type
        elif var in self._local_types:
            del self._local_types[var]

    def _generate_case(self, expr: AST.AST, actions: tuple) -> None:
        """Generate case expression."""
        self._emit_comment("case expression")

        # Evaluate expression
        self._generate_expr(expr)

        # Check for void
        void_label = self._new_label("case_void")
        self._emit_instr("beqz", "$a0", void_label)

        # Get class tag
        self._emit_instr("lw", "$t0", "0($a0)")  # Class tag

        # Store expression result
        self._emit_instr("sw", "$a0", "0($sp)")
        self._emit_instr("addiu", "$sp", "$sp", "-4")

        done_label = self._new_label("case_done")

        # Generate branches (simplified - should sort by class tag)
        for action in actions:
            if isinstance(action, AST.Action):
                branch_name = action.name
                branch_type = action.action_type
                branch_body = action.body
            else:
                branch_name, branch_type, branch_body = action

            self._new_label("case_branch")
            next_label = self._new_label("case_next")

            # Check if class matches
            if branch_type in self.class_tags:
                tag = self.class_tags[branch_type]
                self._emit_instr("li", "$t1", str(tag))
                self._emit_instr("bne", "$t0", "$t1", next_label)

            # Bind variable
            old_offset = self._locals.get(branch_name)
            local_offset = -self._next_local_offset - 4
            self._locals[branch_name] = local_offset
            self._next_local_offset += 4

            self._emit_instr("addiu", "$sp", "$sp", "-4")
            self._emit_instr("lw", "$t0", "4($sp)")  # Get case expr
            self._emit_instr("sw", "$t0", f"{local_offset}($fp)")

            # Generate branch body
            self._generate_expr(branch_body)

            # Cleanup
            self._emit_instr("addiu", "$sp", "$sp", "4")
            self._next_local_offset -= 4
            if old_offset is not None:
                self._locals[branch_name] = old_offset
            else:
                del self._locals[branch_name]

            self._emit_instr("j", done_label)
            self._emit_label(next_label)

        # No match error
        self._emit_label(void_label)
        self._emit_comment("Case on void error")
        self._emit_instr("j", "_dispatch_void")

        self._emit_label(done_label)
        # Pop case expression
        self._emit_instr("addiu", "$sp", "$sp", "4")

    def _generate_dispatch(
        self,
        obj: AST.AST,
        static_type: str | None,
        method_name: str,
        args: tuple[AST.AST, ...],
    ) -> None:
        """Generate method dispatch."""
        # Evaluate arguments (in reverse order for stack)
        for arg in reversed(args):
            self._generate_expr(arg)
            self._emit_instr("addiu", "$sp", "$sp", "-4")
            self._emit_instr("sw", "$a0", "0($sp)")

        # Evaluate object
        self._generate_expr(obj)

        # Check for void dispatch
        self._emit_instr("beqz", "$a0", "_dispatch_void")

        # Get dispatch table
        if static_type:
            # Static dispatch - use static type's dispatch table
            self._emit_instr("la", "$t0", f"{CLASS_DISPTAB_PREFIX}{static_type}")
        else:
            # Dynamic dispatch - get from object
            self._emit_instr("lw", "$t0", "8($a0)")  # Dispatch pointer

        # Find method offset in dispatch table
        # For dynamic dispatch, use the static type of the object expression
        if static_type:
            lookup_type = static_type
        else:
            lookup_type = self._get_expr_type(obj)
        info = self.class_info.get(lookup_type)
        method_offset = 0
        if info:
            for i, (name, _) in enumerate(info.methods):
                if name == method_name:
                    method_offset = i * WORD_SIZE
                    break

        # Load method address and call
        self._emit_instr("lw", "$t1", f"{method_offset}($t0)")

        # Set up arguments in registers
        # Arguments are pushed in reverse order, so arg[0] is at top of stack
        for i, _ in enumerate(args):
            if i < 3:
                self._emit_instr("lw", f"$a{i + 1}", f"{i * 4}($sp)")

        self._emit_instr("jalr", "$t1")

        # Pop arguments
        if args:
            self._emit_instr("addiu", "$sp", "$sp", f"{len(args) * 4}")


# -----------------------------------------------------------------------------
#
#                Factory Function
#
# -----------------------------------------------------------------------------


def make_code_generator(analyzer: PyCoolSemanticAnalyser) -> MIPSCodeGenerator:
    """Create a code generator from a semantic analyzer."""
    return MIPSCodeGenerator(analyzer)


# -----------------------------------------------------------------------------
#
#                Standalone Execution
#
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    import sys

    from pycoolc.parser import make_parser
    from pycoolc.semanalyser import make_semantic_analyser

    if len(sys.argv) != 2:
        print("Usage: python codegen.py program.cl")
        sys.exit(1)

    input_file = sys.argv[1]
    with open(input_file, encoding="utf-8") as f:
        source = f.read()

    # Parse
    parser = make_parser()
    ast = parser.parse(source)

    # Semantic analysis
    analyzer = make_semantic_analyser()
    analyzed_ast = analyzer.transform(ast)

    # Code generation
    codegen = make_code_generator(analyzer)
    code = codegen.generate(analyzed_ast)

    # Output to .s file
    output_file = input_file.replace(".cl", ".s")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"Generated {output_file}")
