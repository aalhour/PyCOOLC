#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# parser.py
#
# Author:       Ahmad Alhour (aalhour.com).
# Date:         TODO
# Description:  The Compiler driver. Drives the whole compilation process.
# -----------------------------------------------------------------------------

# std
import argparse

# compiler stages
from pycoolc.lexer import make_lexer
from pycoolc.parser import make_parser
from pycoolc.semanter import make_semanter

# compiler utils
from pycoolc.utils import print_readable_ast


def create_arg_parser():
    """
    Returns an ArgumentParser instance.
    """
    arg_parser = argparse.ArgumentParser(prog="pycoolc")

    # Cool program(s) source file(s)
    arg_parser.add_argument(
        "cool_program",
        type=str, nargs="+",
        help="One or more cool program source code files ending with *.cl extension; space separated.")
        

    # Output file argument
    arg_parser.add_argument(
        "-o", "--outfile",
        type=str, action="store", nargs=1, default=None,
        help="Desired name of the output compiled assembly program.")
    
    # Print tokens argument
    arg_parser.add_argument(
        "--tokens", 
        action="store_true", default=False,
        help="Displays the result of lexical analysis of the input program(s) on stdout.")

    # Print AST argument
    arg_parser.add_argument(
        "--ast", 
        action="store_true", default=False,
        help="Displays the result of syntax analysis (abstract syntax tree) of the input program(s) on stdout.")
    
    # Print semantic analysis result argument
    arg_parser.add_argument(
        "--semantics",
        action="store_true", default=False,
        help="Displays the result of semantic analysis of the input program(s) to stdout.")
    
    # Print optimized IR argument
    arg_parser.add_argument(
        "--optimizations",
        action="store_true", default=False,
        help="Runs the compiler up-to the level of Optimization stage and displays the optimized IR on stdout.")

    return arg_parser


def lexical_analysis(program):
    """
    TODO
    :param program: TODO
    :return: TODO
    """
    lexer = make_lexer()
    lexer.input(program)
    for token in lexer:
        print(token)


def syntax_analysis(program):
    """
    TODO
    :param program: TODO
    :return: TODO
    """
    parser = make_parser()
    result = parser.parse(program)
    print_readable_ast(result)


def semantic_analysis(program):
    """
    TODO
    :param program: TODO
    :return: TODO
    """
    semanter = make_semanter()
    semanter.check(program)


def main():
    """
    Compiler entry point.
    """
    # Create an ArgumentParser instance.
    arg_parser = create_arg_parser()

    # Parse command line arguments.
    args = arg_parser.parse_args()
    tokens_were_requested = args.tokens
    ast_was_requested = args.ast
    semantics_were_requested = args.semantics
    programs = args.cool_program

    # Initialize the master program source code string.
    cool_program_code = ""
    
    # Check all programs have the *.cl extension.
    for program in programs:
        if not str(program).endswith(".cl"):
            print("Cool program files must end with a \`.cl\` extension.\r\n")
            arg_parser.print_usage()
            exit(1)

    # Read all programs source codes and store it in memory.
    for program in programs:
        try:
            with open(program, encoding="utf-8") as file:
                cool_program_code += file.read()
        except (IOError, FileNotFoundError):
            print("Error! File \"{0}\" was not found. Are you sure the file exists?".format(program))
        except Exception:
            print("An unexpected error occurred!")

    # If the user asked for the list of tokens, run lexical analysis
    if args.tokens:
        print("{bar}\r\n# Running Lexical Analysis...\r\n{bar}".format(
            bar="# ==========================="))
        lexical_analysis(cool_program_code)

    # If the user asked for the AST repr, run syntax analysis
    if args.ast:
        print("{bar}\r\n# Running Syntax Analysis...\r\n{bar}".format(
            bar="# =========================="))
        syntax_analysis(cool_program_code)

    # If the user asked for the semantics, run semantic analysis
    if args.semantics:
        print("{bar}\r\n# Running Semantic Analysis...\r\n{bar}".format(
            bar="# ============================"))
        semantic_analysis(cool_program_code)


if __name__ == "__main__":
    main()

