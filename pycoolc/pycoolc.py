#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# parser.py
#
# Author:       Ahmad Alhour (aalhour.com).
# Date:         TODO
# Description:  The Compiler driver. Drives the whole compilation process.
# -----------------------------------------------------------------------------

import sys
from pycoolc.lexer import make_lexer
from pycoolc.parser import make_parser
from pycoolc.semanter import make_semanter


def print_usage():
    print("Usage: pycoolc <program.cl> [<program2.cl> [, <program3.cl>] ...]")


def run_compiler():
    programs = []
    cool_program_code = ""

    if len(sys.argv) < 2:
        print_usage()
        exit()
    else:
        for program in sys.argv[1:]:
            if not str(program).endswith(".cl"):
                print("Cool program files must end with a \`.cl\` extension.")
                print_usage()
                exit()
            else:
                programs.append(program)

    for program in programs:
        with open(program, encoding="utf-8") as file:
            cool_program_code += file.read()

    # Lexer output
    lexer = make_lexer()
    lexer.input(cool_program_code)
    for token in lexer:
        print(token)

    # Parser output
    parser = make_parser()
    result = parser.parse(cool_program_code)
    print(result)

    # Semantic Analysis output
    semanter = make_semanter()
    semanter.check(cool_program_code)


if __name__ == "__main__":
    run_compiler()

