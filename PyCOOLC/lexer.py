#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# lexer.py
#
# Author:       Ahmad Alhour (git.io/aalhour; aalhour.com).
# Date:         May 23rd, 2016.
# Description:  The Lexer module. Implements lexical analysis of COOL programs.
# -----------------------------------------------------------------------------

import sys
import ply.lex as lex
from ply.lex import TOKEN


class PyCoolLexer(object):
    """
    PyCoolLexer class implements a PLY Lexer by specifying tokens list, reserved keywords map in addition to Tokens
    Matching Rules as regular expressions.
    The Rules need to be in the order of their appearance.
    """
    def __init__(self, post_init_build=False):
        self.lexer = None
        self.tokens = []
        if post_init_build is True:
            self.build()

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
            "loop": "LOOP",
            "pool": "POOL",
            "class": "CLASS",
            "def": "DEF",
            "let": "LET",
            "in": "IN",
            "override": "OVERRIDE",
            "super": "SUPER",
            "this": "THIS",
            "inherits": "INHERITS",
            "self": "SELF",
            "Int": "INT_TYPE",
            "String": "STRING_TYPE",
            "Object": "OBJECT_TYPE",
            "SELF_TYPE": "SELF_TYPE"
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
        :return: list.
        """
        return [
            "INTEGER", "STRING", "LCOMMENT", "RCOMMENT", "SLCOMMENT", "LPAREN", "RPAREN", "LCBRACE", "RCBRACE",
            "COLON", "COMMA", "DOT", "SEMICOLON", "PLUS", "MINUS", "TIMES", "DIVIDE", "EQUALS", "DBEQUALS", "LTHAN",
            "ARROW", "LTEQ", "BANG", "NEG", "ID"
        ]

    # ################### START OF LEXICAL TOKENS RULES DECLARATION ####################

    # SIMPLE TOKENS RULES
    t_LCOMMENT  = r'\(\*'   # (*    Multi-line comment start
    t_RCOMMENT  = r'\*\)'   # *)    Multi-line comment end
    t_SLCOMMENT = r'\-\-'   # --    Single-line comment
    t_LPAREN    = r'\)'     # (
    t_RPAREN    = r'\('     # )
    t_LCBRACE   = r'\{'     # {
    t_RCBRACE   = r'\}'     # }
    t_COLON     = r'\:'     # :
    t_COMMA     = r'\,'     # ,
    t_DOT       = r'\.'     # .
    t_SEMICOLON = r'\;'     # ;
    t_TIMES     = r'\*'     # *
    t_DIVIDE    = r'\/'     # /
    t_PLUS      = r'\+'     # +
    t_MINUS     = r'\-'     # -
    t_NEG       = r'~'      # ~
    t_DBEQUALS  = r'\=\='   # ==
    t_EQUALS    = r'\='     # =
    t_LTEQ      = r'\<\='   # <=
    t_ARROW     = r'\<\-'   # <-
    t_LTHAN     = r'\<'     # <
    t_BANG      = r'\!'     # !

    # COMPLEX TOKENS LEXING RULES.
    integer_rule    = r'\d+'
    string_rule     = r'\"(\\.|[^"])*\"'
    identifier_rule = r'[a-zA-Z_][a-zA-Z_0-9]*'
    newline_rule    = r'\n+'
    whitespace_rule = r'[\ \t\s]+'

    @TOKEN(integer_rule)
    def t_INTEGER(self, t):
        """
        The Integer Token Rule.
        """
        t.value = int(t.value)
        return t

    @TOKEN(string_rule)
    def t_STRING(self, t):
        """
        The String Token Rule.
        """
        t.value = str(t.value)
        return t

    @TOKEN(identifier_rule)
    def t_ID(self, t):
        """
        The Identifier Token Rule.
        """
        # Check for reserved words
        t.type = self.basic_reserved.get(t.value, 'ID')
        return t

    @TOKEN(whitespace_rule)
    def t_WHITESPACE(self, t):
        """
        The Whitespace Token Rule.
        This rule replaces the PLY t_ignore simple regex rule (t_ignore = r' \t').
        """
        pass

    @TOKEN(newline_rule)
    def t_newline(self, t):
        """
        The Newline Token Rule.
        """
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        """
        Error Handling Rule.
        """
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # ################### END OF LEXICAL TOKENS RULES DECLARATION ####################

    def build(self, **kwargs):
        """
        The PLY Lexer Builder method. Used to build lexer post-initilization.
        """
        self.tokens = self.tokens_list + list(self.basic_reserved.values())
        self.lexer = lex.lex(module=self, **kwargs)

    def tokenize(self, cool_program_source_code):
        """
        Given a cool program source code as a string, tokenize the data.
        :param cool_program_source_code: COOL program source code as a string.
        :return: None.
        """
        if self.lexer is None:
            raise Exception("Lexer was not built. Try calling the build() method first, and then tokenize().")

        self.lexer.input(cool_program_source_code)

    def next_token(self):
        """
        Advances the lexer token pointer one token ahead and return the token.
        :return: Token.
        """
        if self.lexer is None:
            raise Exception("Lexer was not built. Try building the lexer with the build() method.")

        return self.lexer.token()

    def test(self, program_source_code):
        """
        Given a string program source code, try to lexically analyse it printing the results to stdout.
        :param program_source_code: String.
        :return: None.
        """
        if self.lexer is None:
            raise Exception("Lexer was not built. Try calling the build() method first, and then test().")

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

        lexer = PyCoolLexer(post_init_build=True)
        lexer.test(cool_program)

