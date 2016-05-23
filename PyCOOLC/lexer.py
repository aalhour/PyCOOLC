#!/usr/bin/env python3

"""
File: lexer.py
Author: Ahmad Alhour (git.io/aalhour)
Date: May 23rd, 2016.
Description: The Lexer module. Implements lexical analysis and tokenization of COOL programs.
"""

import sys
import ply.lex as lex
from ply.lex import TOKEN


class PyCoolCLexer(object):
    def __init__(self):
        self.lexer = None
        self.tokens = []

    @property
    def basic_reserved(self):
        """
        Map of Basic-Cool reserved keywords.
        :return: dict.
        """
        return {
            "if": "IF",
            "fi": "FI",
            "else": "ELSE",
            "case": "CASE",
            "esac": "ESAC",
            "true": "TRUE",
            "false": "FALSE",
            "match": "MATCH",
            "native": "NATIVE",
            "new": "NEW",
            "null": "NULL",
            "var": "VAR",
            "while": "WHILE",
            "class": "CLASS",
            "def": "DEF",
            "override": "OVERRIDE",
            "super": "SUPER",
            "this": "THIS",
            "inherits": "INHERITS"
        }

    @property
    def extended_reserved(self):
        """
        Map of Extended-Cool reserved keywords.
        :return: dict.
        """
        return {
            "abstract": "ABSTRACT",
            "catch": "CATCH",
            "do": "DO",
            "final": "FINAL",
            "finally": "FINALLY",
            "for": "FOR",
            "forSome": "FORSOME",
            "explicit": "IMPLICIT",
            "implicit": "IMPORT",
            "lazy": "LAZY",
            "object": "OBJECT",
            "package": "PACKAGE",
            "private": "PRIVATE",
            "protected": "PROTECTED",
            "requires": "REQUIRES",
            "return": "RETURN",
            "sealed": "SEALED",
            "throw": "THROW",
            "trait": "TRAIT",
            "try": "TRY",
            "type": "TYPE",
            "val": "VAL",
            "with": "WITH",
            "yield": "YIELD"
        }

    @property
    def tokens_list(self):
        """
        List of Cool Syntax Tokens.
        :return:
        """
        return [
            "INTEGER", "STRING", "LPAREN", "RPAREN", "LCBRACE", "RCBRACE", "COLON", "COMMA", "DOT", "SEMICOLON",
            "PLUS", "MINUS", "TIMES", "DIVIDE", "EQUALS", "DBEQUALS", "LTHAN", "LTEQ", "BANG", "ID"
        ]

    # ################### START OF LEXICAL TOKENS RULES DECLARATION ####################

    # SIMPLE TOKENS RULES
    t_LPAREN    = r'\)'
    t_RPAREN    = r'\('
    t_LCBRACE   = r'{'
    t_RCBRACE   = r'}'
    t_COLON     = r':'
    t_COMMA     = r','
    t_DOT       = r'\.'
    t_SEMICOLON = r';'
    t_PLUS      = r'\+'
    t_MINUS     = r'\-'
    t_TIMES     = r'\*'
    t_DIVIDE    = r'/'
    t_EQUALS    = r'='
    t_DBEQUALS  = r'=='
    t_LTHAN     = r'<'
    t_LTEQ      = r'<='
    t_BANG      = r'!'

    integer_rule    = r'\d+'
    string_rule     = r'\"(\\.|[^"])*\"'
    identifier_rule = r'[a-zA-Z_][a-zA-Z_0-9]*'

    # COMPLEX TOKENS LEXING METHODS.
    @TOKEN(integer_rule)
    def t_INTEGER(self, t):
        """The Integer Token Rule."""
        t.value = int(t.value)
        return t

    @TOKEN(string_rule)
    def t_STRING(self, t):
        """The String Token Rule."""
        t.value = str(t.value)
        return t

    @TOKEN(identifier_rule)
    def t_ID(self, t):
        """The Identifier Token Rule."""
        # Check for reserved words
        t.type = self.basic_reserved.get(t.value, 'ID')
        return t

    # NEW-LINES TOKENS RULES. WE MATCH THEM TO KEEP TRACK OF LINE NUMBERS.
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # IGNORE WHITESPACE TOKENS RULE.
    t_ignore = r' \t'

    # ERROR HANDLING RULE.
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # ################### END OF LEXICAL TOKENS RULES DECLARATION ####################

    # Build the lexer
    def build(self, **kwargs):
        """
        The PLY Lexer Builder method.
        """
        self.tokens = self.tokens_list + list(self.basic_reserved.values())
        self.lexer = lex.lex(module=self, **kwargs)

    def test(self, program_source_code):
        """
        Given a string program source code, try to lexically analyse it printing the results to stdout.
        :param program_source_code: String.
        :return: None.
        """
        self.lexer.input(program_source_code)
        while True:
            token = self.lexer.token()
            if not token:
                break
            print(token)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./lexer.py program.cl")
        exit()
    else:
        cl_file = sys.argv[1]

    with open(cl_file, 'r', encoding='utf-8') as source_code:
        cool_program = source_code.read()

    lexer = PyCoolCLexer()
    lexer.build()
    lexer.test(cool_program)

