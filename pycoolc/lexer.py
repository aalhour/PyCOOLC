#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# lexer.py
#
# Author:       Ahmad Alhour (aalhour.com).
# Date:         May 23rd, 2016.
# Description:  The Lexer module. Implements lexical analysis of COOL programs.
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import ply.lex as lex
from ply.lex import TOKEN, LexToken


class PyCoolLexer:
    """
    PyCoolLexer class.

    Responsible for Lexical Analysis and tokenization of COOL Programs. The lexer works by creating an object from it,
     (optionally) building it, and then calling the input() method feeding it a COOL program source code as a string.

    The Lexer implements the iterator protocol which enables iterating over the list of analysed tokens with trivial
     for loops, example:

        for token in lexer:
            print(token)

    PyCoolLexer provides the following Public APIs:
     * build(): Builds the lexer.
     * input(): Run lexical analysis on a given cool program source code string.
     * token(): Advances the lexers tokens tape by 1 place and returns the current token.
     * test():  Runs lexer on a given cool program source code string and prints all tokens to stdout.
     * clone_ply_lexer(): Clones the internal PLY's lex-generated lexer instance.

    The lexer is built using Python's lex (ply.lex) via specifying a tokens list, reserved keywords maps and tokenization
    regex rules.
    """
    def __init__(
        self,
        build_lexer: bool = True,
        debug: bool = False,
        lextab: str = "pycoolc.lextab",
        optimize: bool = True,
        outputdir: str = "",
        debuglog: Any = None,
        errorlog: Any = None,
    ) -> None:
        """
        Initialize the COOL lexer.

        Args:
            build_lexer: If True, build the lexer immediately after initialization.
            debug: Enable debug mode.
            optimize: Enable optimization mode.
            lextab: Module name for cached lexer tables.
            outputdir: Output directory for lexer tables.
            debuglog: Debug log file path (defaults to stderr).
            errorlog: Error log file path (defaults to stderr).
        """
        self.lexer: Any = None
        self.tokens: tuple[str, ...] = ()
        self.reserved: dict[str, str] = {}
        self.last_token: LexToken | None = None

        # Configuration - stored for rebuild
        self._debug = debug
        self._lextab = lextab
        self._optimize = optimize
        self._outputdir = outputdir
        self._debuglog = debuglog
        self._errorlog = errorlog

        if build_lexer:
            self.build(
                debug=debug,
                lextab=lextab,
                optimize=optimize,
                outputdir=outputdir,
                debuglog=debuglog,
                errorlog=errorlog,
            )

    # #################################  READONLY  #####################################

    @property
    def tokens_collection(self) -> tuple[str, ...]:
        """Collection of COOL syntax token names."""
        return (
            # Identifiers
            "ID", "TYPE",

            # Primitive Types
            "INTEGER", "STRING", "BOOLEAN",

            # Literals
            "LPAREN", "RPAREN", "LBRACE", "RBRACE", "COLON", "COMMA", "DOT", "SEMICOLON", "AT",

            # Operators
            "PLUS", "MINUS", "MULTIPLY", "DIVIDE", "EQ", "LT", "LTEQ", "ASSIGN", "INT_COMP",

            # Special Operators
            "ARROW"
        )

    @property
    def basic_reserved(self) -> dict[str, str]:
        """
        Map of COOL reserved keywords (lowercase) to token types.
        
        Per COOL Manual §2: Keywords are case-insensitive, except for true/false
        which must be lowercase. We store all keywords in lowercase and do
        case-insensitive lookups in the token rules.
        """
        return {
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
            "not": "NOT",  # Boolean negation operator
            "of": "OF",
            "pool": "POOL",
            "self": "SELF",
            "then": "THEN",
            "while": "WHILE",
        }

    @property
    def extended_reserved(self) -> dict[str, str]:
        """Map of Extended-COOL reserved keywords (not currently used)."""
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
            "override": "OVERRIDE",
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
    def builtin_types(self) -> dict[str, str]:
        """Map of built-in type names to token types (not currently used)."""
        return {
            "Bool": "BOOL_TYPE",
            "Int": "INT_TYPE",
            "IO": "IO_TYPE",
            "Main": "MAIN_TYPE",
            "Object": "OBJECT_TYPE",
            "String": "STRING_TYPE",
            "SELF_TYPE": "SELF_TYPE"
        }

    # ################################  PRIVATE  #######################################

    # ################# START OF LEXICAL ANALYSIS RULES DECLARATION ####################

    # Ignore rule for single line comments
    t_ignore_SINGLE_LINE_COMMENT = r"\-\-[^\n]*"

    ###
    # SIMPLE TOKENS
    t_LPAREN = r'\('        # (
    t_RPAREN = r'\)'        # )
    t_LBRACE = r'\{'        # {
    t_RBRACE = r'\}'        # }
    t_COLON = r'\:'         # :
    t_COMMA = r'\,'         # ,
    t_DOT = r'\.'           # .
    t_SEMICOLON = r'\;'     # ;
    t_AT = r'\@'            # @
    t_MULTIPLY = r'\*'      # *
    t_DIVIDE = r'\/'        # /
    t_PLUS = r'\+'          # +
    t_MINUS = r'\-'         # -
    t_INT_COMP = r'~'       # ~
    t_LT = r'\<'            # <
    t_EQ = r'\='            # =
    t_LTEQ = r'\<\='        # <=
    t_ASSIGN = r'\<\-'      # <-
    t_ARROW = r'\=\>'       # =>

    @TOKEN(r"(true|false)")
    def t_BOOLEAN(self, token):
        """
        The Bool Primitive Type Token Rule.
        """
        token.value = True if token.value == "true" else False
        return token

    @TOKEN(r"\d+")
    def t_INTEGER(self, token):
        """
        The Integer Primitive Type Token Rule.
        """
        token.value = int(token.value)
        return token

    @TOKEN(r"[A-Z][a-zA-Z_0-9]*")
    def t_TYPE(self, token):
        """
        The Type Token Rule.
        
        Type names start with uppercase. However, keywords are case-insensitive
        in COOL (e.g., 'Class' = 'class'), so we check lowercase version.
        """
        # Case-insensitive keyword lookup
        token.type = self.basic_reserved.get(token.value.lower(), 'TYPE')
        return token

    @TOKEN(r"[a-z_][a-zA-Z_0-9]*")
    def t_ID(self, token):
        """
        The Identifier Token Rule.
        
        Identifiers start with lowercase. Keywords are case-insensitive,
        so we check lowercase version against reserved words.
        """
        token.type = self.basic_reserved.get(token.value.lower(), 'ID')
        return token

    @TOKEN(r"\n+")
    def t_newline(self, token):
        """
        The Newline Token Rule.
        """
        token.lexer.lineno += len(token.value)

    # Ignore Whitespace Character Rule
    t_ignore = ' \t\r\f'

    # ################# STATEFUL LEXICAL ANALYSIS ######################################

    @property
    def states(self) -> tuple[tuple[str, str], ...]:
        """Lexer states for string and comment parsing."""
        return (
            ("STRING", "exclusive"),
            ("COMMENT", "exclusive"),
        )

    ###
    # THE STRING STATE
    @TOKEN(r"\"")
    def t_start_string(self, token):
        token.lexer.push_state("STRING")
        token.lexer.string_backslashed = False
        token.lexer.stringbuf = ""

    @TOKEN(r"\n")
    def t_STRING_newline(self, token):
        token.lexer.lineno += 1
        if not token.lexer.string_backslashed:
            print("String newline not escaped")
            token.lexer.skip(1)
        else:
            token.lexer.string_backslashed = False

    @TOKEN(r"\"")
    def t_STRING_end(self, token):
        if not token.lexer.string_backslashed:
            token.lexer.pop_state()
            token.value = token.lexer.stringbuf
            token.type = "STRING"
            return token
        else:
            token.lexer.stringbuf += '"'
            token.lexer.string_backslashed = False

    @TOKEN(r"[^\n]")
    def t_STRING_anything(self, token):
        if token.lexer.string_backslashed:
            if token.value == 'b':
                token.lexer.stringbuf += '\b'
            elif token.value == 't':
                token.lexer.stringbuf += '\t'
            elif token.value == 'n':
                token.lexer.stringbuf += '\n'
            elif token.value == 'f':
                token.lexer.stringbuf += '\f'
            elif token.value == '\\':
                token.lexer.stringbuf += '\\'
            else:
                token.lexer.stringbuf += token.value
            token.lexer.string_backslashed = False
        else:
            if token.value != '\\':
                token.lexer.stringbuf += token.value
            else:
                token.lexer.string_backslashed = True

    # STRING ignored characters
    t_STRING_ignore = ''

    # STRING error handler
    def t_STRING_error(self, token):
        print("Illegal character! Line: {0}, character: {1}".format(token.lineno, token.value[0]))
        token.lexer.skip(1)

    ###
    # THE COMMENT STATE
    @TOKEN(r"\(\*")
    def t_start_comment(self, token):
        token.lexer.push_state("COMMENT")
        token.lexer.comment_count = 0

    @TOKEN(r"\(\*")
    def t_COMMENT_startanother(self, t):
        t.lexer.comment_count += 1

    @TOKEN(r"\*\)")
    def t_COMMENT_end(self, token):
        if token.lexer.comment_count == 0:
            token.lexer.pop_state()
        else:
            token.lexer.comment_count -= 1

    # COMMENT ignored characters
    t_COMMENT_ignore = ''

    # COMMENT error handler
    def t_COMMENT_error(self, token):
        token.lexer.skip(1)

    def t_error(self, token):
        """
        Error Handling and Reporting Rule.
        """
        print("Illegal character! Line: {0}, character: {1}".format(token.lineno, token.value[0]))
        token.lexer.skip(1)

    # ################# END OF LEXICAL ANALYSIS RULES DECLARATION ######################

    # #################################  PUBLIC  #######################################

    def build(self, **kwargs: Any) -> None:
        """
        Build the PLY lexer instance.

        This binds the tokens list and reserved keywords map, then calls ply.lex.lex().
        Can be called with the same kwargs as __init__ to override settings.
        """
        if not kwargs:
            debug, lextab, optimize, outputdir, debuglog, errorlog = \
                self._debug, self._lextab, self._optimize, self._outputdir, self._debuglog, self._errorlog
        else:
            debug = kwargs.get("debug", self._debug)
            lextab = kwargs.get("lextab", self._lextab)
            optimize = kwargs.get("optimize", self._optimize)
            outputdir = kwargs.get("outputdir", self._outputdir)
            debuglog = kwargs.get("debuglog", self._debuglog)
            errorlog = kwargs.get("errorlog", self._errorlog)

        # Expose the reserved map and tokens tuple to the class scope for ply.lex
        self.reserved = self.basic_reserved.keys()
        self.tokens = self.tokens_collection + tuple(self.basic_reserved.values())

        # Build internal ply.lex instance
        self.lexer = lex.lex(module=self, lextab=lextab, debug=debug, optimize=optimize, outputdir=outputdir,
                             debuglog=debuglog, errorlog=errorlog)

    def input(self, source_code: str) -> None:
        """
        Feed source code to the lexer for tokenization.

        Args:
            source_code: COOL program source code as a string.

        Raises:
            RuntimeError: If the lexer hasn't been built yet.
        """
        if self.lexer is None:
            raise RuntimeError("Lexer was not built. Call build() first.")
        self.lexer.input(source_code)

    def token(self) -> LexToken | None:
        """
        Return the next token from the input stream.

        Returns:
            The next token, or None if no more tokens.

        Raises:
            RuntimeError: If the lexer hasn't been built yet.
        """
        if self.lexer is None:
            raise RuntimeError("Lexer was not built. Call build() first.")
        self.last_token = self.lexer.token()
        return self.last_token

    def clone_ply_lexer(self) -> Any:
        """Clone the internal PLY lexer instance."""
        return self.lexer.clone()

    @staticmethod
    def test(source_code: str) -> Iterator[LexToken]:
        """
        Convenience method to tokenize source code and return an iterator of tokens.

        Args:
            source_code: COOL program source code.

        Returns:
            Iterator of tokens.
        """
        lexer = PyCoolLexer()
        lexer.input(source_code)
        return iter(list(lexer))

    # ################### ITERATOR PROTOCOL ############################################

    def __iter__(self) -> Iterator[LexToken]:
        return self

    def __next__(self) -> LexToken:
        t = self.token()
        if t is None:
            raise StopIteration
        return t


# -----------------------------------------------------------------------------
#
#                     Lexer as a Standalone Python Program
#                     Usage: ./lexer.py cool_program.cl
#
# -----------------------------------------------------------------------------

def make_lexer(**kwargs) -> PyCoolLexer:
    """
    Utility function.
    :return: PyCoolLexer object.
    """
    a_lexer = PyCoolLexer(**kwargs)
    a_lexer.build()
    return a_lexer


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: ./lexer.py program.cl")
        exit()
    elif not str(sys.argv[1]).endswith(".cl"):
        print("Cool program source code files must end with .cl extension.")
        print("Usage: ./lexer.py program.cl")
        exit()

    input_file = sys.argv[1]
    with open(input_file, encoding="utf-8") as file:
        cool_program_code = file.read()

    lexer = make_lexer()
    lexer.input(cool_program_code)
    for token in lexer:
        print(token)

