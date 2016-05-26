#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# lexer.py
#
# Author:       Ahmad Alhour (github.com/aalhour; aalhour.com).
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
        self.lexer = None               # ply lexer instance
        self.tokens = ()                # ply tokens collection
        self.reserved = {}              # ply reserved keywords map
        if post_init_build is True:     # build right after instantiation?
            self.build()

    @property
    def basic_reserved(self):
        """
        Map of Basic-Cool reserved keywords.
        :return: dict.
        """
        return {
            # KEYWORDS - alphabetical order
            "case": "CASE",
            "class": "CLASS",
            "else": "ELSE",
            "esac": "ESAC",
            "fi": "FI",
            "if": "IF",
            "in": "IN",
            "inherits": "INHERITS",
            "isvoid": "ISVOID",
            "let": "LET",
            "loop": "LOOP",
            "new": "NEW",
            "of": "OF",
            "override": "OVERRIDE",
            "pool": "POOL",
            "self": "SELF",
            "while": "WHILE",

            # BASIC TYPES - alphabetical order
            "Bool": "BOOL_TYPE",
            "Int": "INT_TYPE",
            "IO": "IO_CLASS",
            "Object": "OBJECT_TYPE",
            "String": "STRING_TYPE",
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
            "def": "DEF",
            "final": "FINAL",
            "finally": "FINALLY",
            "for": "FOR",
            "forSome": "FORSOME",
            "explicit": "IMPLICIT",
            "implicit": "IMPORT",
            "lazy": "LAZY",
            "match": "MATCH",
            "native": "NATIVE",
            "null": "NULL",
            "object": "OBJECT",
            "package": "PACKAGE",
            "private": "PRIVATE",
            "protected": "PROTECTED",
            "requires": "REQUIRES",
            "return": "RETURN",
            "sealed": "SEALED",
            "super": "SUPER",
            "this": "THIS",
            "throw": "THROW",
            "trait": "TRAIT",
            "try": "TRY",
            "type": "TYPE",
            "val": "VAL",
            "var": "VAR",
            "with": "WITH",
            "yield": "YIELD"
        }

    @property
    def tokens_collection(self):
        """
        List of Cool Syntax Tokens.
        :return: Tuple.
        """
        return (
            # Identifiers
            "ID", "TYPE",

            # Primitive Types
            "INTEGER", "STRING", "BOOLEAN",

            # Discarded
            "COMMENT",

            # Literals
            "LEFT_PAREN", "RIGHT_PAREN", "LEFT_BRACE", "RIGHT_BRACE", "COLON", "COMMA", "DOT", "SEMICOLON",

            # Operators
            "PLUS", "MINUS", "TIMES", "DIVIDE", "EQUALS", "DOUBLE_EQUALS", "LESS_THAN", "LESS_THAN_EQUAL",
            "ASSIGNMENT", "BANG", "INT_COMPLEMENT", "NOT",
            
            # Special Operators
            "ACTION"
        )

    # ################### START OF LEXICAL TOKENS RULES DECLARATION ####################

    # SIMPLE TOKENS RULES
    t_LEFT_PAREN = r'\)'            # (
    t_RIGHT_PAREN = r'\('          # )
    t_LEFT_BRACE = r'\{'            # {
    t_RIGHT_BRACE = r'\}'           # }
    t_COLON = r'\:'                 # :
    t_COMMA = r'\,'                 # ,
    t_DOT = r'\.'                   # .
    t_SEMICOLON = r'\;'             # ;
    t_TIMES = r'\*'                 # *
    t_DIVIDE = r'\/'                # /
    t_PLUS = r'\+'                  # +
    t_MINUS = r'\-'                 # -
    t_INT_COMPLEMENT = r'~'         # ~
    t_DOUBLE_EQUALS = r'\=\='       # ==
    t_LESS_THAN = r'\<'             # <
    t_EQUALS = r'\='                # =
    t_LESS_THAN_EQUAL = r'\<\='     # <=
    t_ASSIGNMENT = r'\<\-'          # <-
    t_BANG = r'\!'                  # !
    t_NOT = r'not|NOT'              # not
    t_ACTION = r'\=\>'              # =>

    # COMPLEX TOKENS LEXING RULES.
    integer_rule = r'\d+'
    boolean_rule = r'true|false'
    string_rule = r'\"(\\.|[^"])*\"'
    type_rule = r'[A-Z][a-zA-Z_0-9]*'
    identifier_rule = r'[a-z_][a-zA-Z_0-9]*'
    newline_rule = r'\n+'
    whitespace_rule = r'[\ \t\s]+'
    comments_rule = r'(\(\*(.|\n)*?\*\))|(\-\-.*)'

    @TOKEN(boolean_rule)
    def t_BOOLEAN(self, token):
        """
        The Bool Primitive Type Token Rule.
        """
        token.value = True if token.value == "true" else False
        return token

    @TOKEN(integer_rule)
    def t_INTEGER(self, token):
        """
        The Integer Primitive Type Token Rule.
        """
        token.value = int(token.value)
        return token

    @TOKEN(string_rule)
    def t_STRING(self, token):
        """
        The String Primitive Type Token Rule.
        """
        token.value = str(token.value)
        return token

    @TOKEN(type_rule)
    def t_TYPE(self, token):
        """
        The Type Token Rule.
        """
        token.type = self.basic_reserved.get(token.value, 'TYPE')
        return token

    @TOKEN(identifier_rule)
    def t_ID(self, token):
        """
        The Identifier Token Rule.
        """
        # Check for reserved words
        token.type = self.basic_reserved.get(token.value, 'ID')
        return token

    @TOKEN(comments_rule)
    def t_COMMENT(self, token):
        """
        The Single-Line and Multi-Line Comments Rule. It ignores all comments lines.
        """
        pass

    @TOKEN(whitespace_rule)
    def t_WHITESPACE(self, token):
        """
        The Whitespace Token Rule.
        This rule replaces the PLY t_ignore simple regex rule (t_ignore = r' \t').
        """
        pass

    # # Empty Ignored Characters Rule
    t_ignore = r''

    @TOKEN(newline_rule)
    def t_newline(self, token):
        """
        The Newline Token Rule.
        """
        token.lexer.lineno += len(token.value)

    def t_error(self, token):
        """
        Error Handling Rule.
        """
        print("Illegal character {0}".format(token.value[0]))
        token.lexer.skip(1)

    # ################### END OF LEXICAL TOKENS RULES DECLARATION ####################

    def build(self, **kwargs):
        """
        Builds the PyCoolLexer instance with lex.lex() by binding the tokens list, reserved keywords map and lexer
        object in the current instance scope.
        :param kwargs: lex.lex() config parameters.
        :return: None
        """
        self.reserved = self.basic_reserved
        self.tokens = self.tokens_collection + tuple(self.basic_reserved.values())
        self.lexer = lex.lex(module=self, **kwargs)

    def get_ply_lex(self):
        """
        Returns a reference to the internal PLY lexer (self.lexer) object.
        :return: self.lexer
        """
        return self.lexer

    def input(self, cool_program_source_code):
        """
        A wrapper around the internal self.lexer.input() method.
        :param cool_program_source_code: COOL program source code as a string.
        :return: None.
        """
        if self.lexer is None:
            raise Exception("Lexer was not built. Try calling the build() method first, and then tokenize().")

        self.lexer.input(cool_program_source_code)

    def token(self):
        """
        A wrapper around the internal self.lexer.token() method.
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

        self.input(program_source_code)
        for token in self.lexer:
            print(token)

    ###
    # Iterator Interface
    def __iter__(self):
        return self

    def __next__(self):
        t = self.token()
        if t is None:
            raise StopIteration
        return t


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

    lexer = PyCoolLexer()
    lexer.build()
    lexer.input(cool_program_code)
    for token in lexer:
        print(token)

