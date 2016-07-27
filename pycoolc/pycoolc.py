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


USAGE = """pycoolc [--tokens] [--ast] [--semantics] [-o assembly_program.s] <program files>

    --tokens:                   Displays the result of lexical analysis of the input program(s) to stdout.
    --ast:                      Displays the result of syntax analysis (abstract syntax tree) of the input program(s)
                                to stdout.
    --semantics:                Displays the result of semantic analysis of the input program(s) to stdout.
    --optimizations:            Runs the compiler up-to the level of Optimization stage and displays the optimized
                                IR (intermediate representation) to stdout.
    -o, --outfile <output.s>:   Name and path of the compiled assembly program file.
    <program files>:            One or more cool source code files ending with *.cl extension. Space separated.

    -h, --help:                 Shows this message.
"""


def create_arg_parser():
    global USAGE

    arg_parser = argparse.ArgumentParser(USAGE)
    arg_parser.add_argument("-o", "--outfile", type=str, action="store", nargs=1, default=None)
    arg_parser.add_argument("--tokens", action="store_true", default=False)
    arg_parser.add_argument("--ast", action="store_true", default=False)
    arg_parser.add_argument("--semantics", action="store_true", default=False)
    arg_parser.add_argument("--optimizations", action="store_true", default=False)
    arg_parser.add_argument("program_files", type=str, nargs="+",
                            help="One or more cool source code files ending with *.cl extension. Space separated.")

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
    print(result)


def semantic_analysis(program):
    """
    TODO
    :param program: TODO
    :return: TODO
    """
    semanter = make_semanter()
    semanter.check(program)


def main():
    global USAGE
    arg_parser = create_arg_parser()
    args = arg_parser.parse_args()

    cool_program_code = ""
    programs = args.program_files

    # Check all programs have the *.cl extension
    for program in programs:
        if not str(program).endswith(".cl"):
            print("Cool program files must end with a \`.cl\` extension.\r\n")
            print(USAGE)
            exit()

    # Read all programs source codes and store it in memory
    for program in programs:
        with open(program, encoding="utf-8") as file:
            cool_program_code += file.read()

    # If the user asked for the list of tokens, run lexical analysis
    if args.tokens:
        print("Running Lexical Analysis...")
        print("===========================")
        lexical_analysis(cool_program_code)

    # If the user asked for the AST repr, run syntax analysis
    if args.ast:
        print("Running Syntax Analysis...")
        print("==========================")
        syntax_analysis(cool_program_code)

    # If the user asked for the semantics, run semantic analysis
    if args.semantics:
        print("Running Semantic Analysis...")
        print("============================")
        semantic_analysis(cool_program_code)


if __name__ == "__main__":
    main()

