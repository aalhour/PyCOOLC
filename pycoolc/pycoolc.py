#!/usr/bin/env python3

import sys
from parser import PyCoolParser


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./parser.py program.cl")
        exit()
    elif not str(sys.argv[1]).endswith(".cl"):
        print("Cool program source code files must end with .cl extension.")
        print("Usage: ./parser.py program.cl")
        exit()

    input_file = sys.argv[1]
    with open(input_file, encoding="utf-8") as file:
        cool_program_code = file.read()

    parser = PyCoolParser()
    parser.build()

    # Lexing output
    parser.lexer.input(cool_program_code)
    for token in parser.lexer:
        print(token)

    # Parsing output
    result = parser.parse(cool_program_code)
    print(result)

