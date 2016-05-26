#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# parser.py
#
# Author:       Ahmad Alhour (github.com/aalhour; aalhour.com).
# Date:         May 26rd, 2016.
# Description:  The Parser module. Implements syntax analysis and parsing rules
#               of the COOL CFG.
# -----------------------------------------------------------------------------

import sys
import ply.yacc as yacc
import ast as AbstractSyntaxTree
from lexer import PyCoolLexer


class PyCoolParser(object):
    def __init__(self):
        # Instantiate the internal lexer and build it.
        self.lexer = PyCoolLexer()

        # Initialize self.parser and self.tokens to None
        self.parser = None
        self.tokens = None

    # ################### START OF FORMAL GRAMMAR RULES DECLARATION ##################

    def p_program(self, parse):
        """
        program : classes
        """
        parse[0] = AbstractSyntaxTree.Program(classes=parse[1])

    def p_classes(self, parse):
        """
        classes : class
                | class classes
        """
        bnf_rule = "<classes> ::= <class> | <class> <classes>"

        # Case of first rhs terminal production
        if len(parse) == 2:
            parse[0] = (parse[1],)
        # Case of second rhs production
        elif len(parse) == 3:
            parse[0] = (parse[1],) + parse[2]
        # Unexpected production
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while processing grammar rule: {1}".format(
                parse, bnf_rule))

    def p_class(self, parse):
        """
        class : CLASS TYPE inheritance '{' features '}' ';'
        """
        parse[0] = AbstractSyntaxTree.Class(name=parse[2], inherits=parse[3], features=parse[5])

    def p_inheritance(self, parse):
        """
        inheritance : inherits TYPE
                    | empty
        """
        bnf_rule = "<inheritance> ::= inherits TYPE | empty"

        # Case of first rhs (inherits Type)
        if len(parse) == 2:
            parse[0] = AbstractSyntaxTree.Inheritance(inheritance_type=p[2])
        # Case of second rhs (empty)
        elif len(parse) == 1:
            parse[0] = AbstractSyntaxTree.Inheritance(inheritance_type=p[1])
        # Unexpected production
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while processing grammar rule: {1}".format(
                parse, bnf_rule))

    def p_empty(self, parse):
        """
        empty :
        """
        parse[0] = None

    # yaac error rule for syntax errors
    def p_error(self, parse):
        print("Syntax error in input program source code!")

    # ################### END OF FORMAL GRAMMAR RULES DECLARATION ####################

    def build(self, **kwargs):
        """
        Builds the PyCoolParser instance with yaac.yaac() by binding the lexer object and it tokens list in the
        current instance scope.
        :param kwargs: yaac.yaac() config parameters.
        :return: None
        """
        # Build PyCoolLexer
        self.lexer.build(**kwargs)
        # Expose tokens collections to this instance scope
        self.tokens = self.lexer.tokens

        self.parser = yacc.yacc(module=self, **kwargs)

    def parse(self, program_source_code):
        if self.parser is None:
            raise ValueError("Parser was not build, try building it first with the build() method.")

        return self.parser.parse(program_source_code)


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
    parser.build(debug=True)
    parse_result = parser.parse(cool_program_code)
    print(parse_result)

