#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# pycoolc.py
#
# Author:       Ahmad Alhour (aalhour.com).
# Date:         2016
# Description:  The Compiler driver. Drives the whole compilation process.
# -----------------------------------------------------------------------------

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pycoolc.codegen import make_code_generator
from pycoolc.lexer import make_lexer
from pycoolc.parser import make_parser
from pycoolc.semanalyser import make_semantic_analyser
from pycoolc.utils import print_readable_ast


def create_arg_parser() -> argparse.ArgumentParser:
    """Create and return the command-line argument parser."""
    arg_parser = argparse.ArgumentParser(
        prog="pycoolc",
        description="PyCOOLC - A COOL to MIPS compiler written in Python",
    )

    # Cool program source file(s)
    arg_parser.add_argument(
        "cool_program",
        type=str,
        nargs="+",
        help="One or more COOL source files (*.cl)",
    )

    # Output file argument
    arg_parser.add_argument(
        "-o",
        "--outfile",
        type=str,
        default=None,
        help="Output file name for the compiled MIPS assembly",
    )

    # Debug flags
    arg_parser.add_argument(
        "--tokens",
        action="store_true",
        help="Print the result of lexical analysis",
    )

    arg_parser.add_argument(
        "--ast",
        action="store_true",
        help="Print the abstract syntax tree after parsing",
    )

    arg_parser.add_argument(
        "--semantics",
        action="store_true",
        help="Print the AST after semantic analysis",
    )

    arg_parser.add_argument(
        "--no-codegen",
        action="store_true",
        help="Skip code generation (useful for type checking only)",
    )

    return arg_parser


def lexical_analysis(source: str, print_results: bool = True) -> list:
    """Run lexical analysis on source code."""
    lexer = make_lexer()
    lexer.input(source)
    tokens = list(lexer)
    if print_results:
        for token in tokens:
            print(token)
    return tokens


def syntax_analysis(source: str, print_results: bool = True):
    """Run syntax analysis (parsing) on source code."""
    parser = make_parser()
    ast = parser.parse(source)
    if print_results:
        print_readable_ast(ast)
    return ast


def semantic_analysis(ast, print_results: bool = True):
    """Run semantic analysis on the AST."""
    analyzer = make_semantic_analyser()
    result = analyzer.transform(ast)
    if print_results:
        print_readable_ast(result)
    return result, analyzer


def code_generation(ast, analyzer, output_file: str | None = None) -> str:
    """Generate MIPS assembly from the analyzed AST."""
    codegen = make_code_generator(analyzer)
    code = codegen.generate(ast)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Generated {output_file}")

    return code


def compile_program(
    source: str,
    output_file: str | None = None,
    print_tokens: bool = False,
    print_ast: bool = False,
    print_semantics: bool = False,
    skip_codegen: bool = False,
) -> str | None:
    """
    Compile a COOL program to MIPS assembly.

    Args:
        source: COOL source code.
        output_file: Path to write the output assembly.
        print_tokens: Print lexer output.
        print_ast: Print parser output.
        print_semantics: Print semantic analysis output.
        skip_codegen: Skip code generation phase.

    Returns:
        The generated MIPS assembly, or None if skipping codegen.
    """
    if print_tokens:
        print("# " + "=" * 40)
        print("# Lexical Analysis")
        print("# " + "=" * 40)
        lexical_analysis(source)
        print()

    if print_ast:
        print("# " + "=" * 40)
        print("# Syntax Analysis (AST)")
        print("# " + "=" * 40)
        syntax_analysis(source)
        print()

    # Parse
    parser = make_parser()
    ast = parser.parse(source)

    if ast is None:
        print("Error: Parsing failed", file=sys.stderr)
        return None

    # Semantic analysis
    if print_semantics:
        print("# " + "=" * 40)
        print("# Semantic Analysis")
        print("# " + "=" * 40)

    analyzed_ast, analyzer = semantic_analysis(ast, print_results=print_semantics)

    if print_semantics:
        print()

    if skip_codegen:
        return None

    # Code generation
    return code_generation(analyzed_ast, analyzer, output_file)


def main() -> int:
    """Compiler entry point."""
    arg_parser = create_arg_parser()
    args = arg_parser.parse_args()

    # Validate input files
    source_files = args.cool_program
    for program in source_files:
        if not program.endswith(".cl"):
            print(f"Error: COOL files must have .cl extension: {program}", file=sys.stderr)
            return 1

    # Read all source files
    source_code = ""
    for program in source_files:
        try:
            source_code += Path(program).read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"Error: File not found: {program}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error reading {program}: {e}", file=sys.stderr)
            return 1

    # Determine output file name
    output_file = args.outfile
    if output_file is None and not args.no_codegen:
        # Default: first input file with .s extension
        output_file = source_files[0].replace(".cl", ".s")

    try:
        compile_program(
            source=source_code,
            output_file=output_file,
            print_tokens=args.tokens,
            print_ast=args.ast,
            print_semantics=args.semantics,
            skip_codegen=args.no_codegen,
        )
        return 0
    except Exception as e:
        print(f"Compilation error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
