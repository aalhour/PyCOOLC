#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# parser.py
#
# Author:       Ahmad Alhour (aalhour.com).
# Date:         TODO
# Description:  The Compiler driver. Drives the whole compilation process.
# -----------------------------------------------------------------------------


import sys
from lexer import make_lexer
from parser import make_parser
from semanter import make_semanter


def print_usage():
    print("Usage: ./pycoolc.py program.cl [program2.cl program3.cl ...]")


if __name__ == "__main__":
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
        input_file = sys.argv[1]
        with open(input_file, encoding="utf-8") as file:
            cool_program_code += file.read()

    # Lexing output
    lexer = make_lexer()
    lexer.input(cool_program_code)
    for token in lexer:
        print(token)

    # Parsing output
    parser = make_parser()
    result = parser.parse(cool_program_code)
    print(result)

    # Semantic Analysis output
    semanter = make_semanter()
    semanter.check(cool_program_code)

