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
    PyCoolLexer class.

    Responsible for Lexical Analysis and tokenization of COOL Programs. The lexer works by creating an object from it,
     (optionally) building it, and then calling the input() method feeding it a COOL program source code as a string.

    The Lexer implements the iterator protocol which enables iterating over the list of analysed tokens with trivial
     for loops, example:

        for token in lexer:
            print(token)

    PyCoolLexer provides the following Public APIs:
     * build(): Build the lexer in case it was specified upon initialization that the lexer shouldn't be built eagerly.
     * input(): Run lexical analysis on a given cool program source code string.
     * token(): Advances the lexers tokens tape by 1 place and returns the current token.
     * test():  Runs lexer on a given cool program source code string and prints all tokens to stdout.
     * clone_ply_lex(): Clones the internal ply.lex lexer instance.

    The lexer is built using Python's lex (ply.lex) via specifying a tokens list, reserved keywords maps and tokenization
    regex rules.
    """
    def __init__(self, build_lexer=True, debug=False, optimize=False, outputdir=None, debuglog=None, errorlog=None):
        """
        Initializer.
        :param debug: Debug mode flag.
        :param optimize: Optimize mode flag.
        :param outputdir: Output directory of lexing output; by default the .out file goes in the same directory.
        :param debuglog: Debug log file path; by default lexer prints to stderr.
        :param errorlog: Error log file path; by default lexer print to stderr.
        :param build_lexer: If this is set to True the internal lexer will be built right after initialization,
         which makes it convenient for direct use. If it's set to False, then an empty lexer instance will be
         initialized and the lexer object will have to be built via called lexer.build() method after initialization.

        Example:
         lexer = PyCoolLexer(post_init_build=False)
         ...
         lexer.build()
         lexer.input(...)
         ...

        :return: None
        """
        self.lexer = None               # ply lexer instance
        self.tokens = ()                # ply tokens collection
        self.reserved = {}              # ply reserved keywords map
        self.last_token = None          # last returned token

        # Save Flags - PRIVATE PROPERTIES
        self._debug = debug
        self._optimize = optimize
        self._outputdir = outputdir
        self._debuglog = debuglog
        self._errorlog = errorlog

        # Build lexer if build_lexer flag is set to True
        if build_lexer is True:
            self.build(debug=debug, optimize=optimize, outputdir=outputdir, debuglog=debuglog, errorlog=errorlog)

    # ################################# PUBLIC #########################################

    def build(self, **kwargs):
        """
        Builds the PyCoolLexer instance with lex.lex() by binding the tokens list, reserved keywords map and lexer
        object in the current instance scope.
        :param kwargs: config parameters map, complete list:
            * debug: Debug mode flag.
            * optimize: Optimize mode flag.
            * debuglog: Debug log file path; by default lexer prints to stderr.
            * errorlog: Error log file path; by default lexer print to stderr.
            * outputdir: Output directory of lexing output; by default the .out file goes in the same directory.
        :return: None
        """
        # Parse the parameters
        if kwargs is None or len(kwargs) == 0:
            debug, optimize, outputdir, debuglog, errorlog = \
                self._debug, self._optimize, self._outputdir, self._debuglog, self._errorlog
        else:
            debug = kwargs.get("debug", self._debug)
            optimize = kwargs.get("optimize", self._optimize)
            outputdir = kwargs.get("outputdir", self._outputdir)
            debuglog = kwargs.get("debuglog", self._debuglog)
            errorlog = kwargs.get("errorlog", self._errorlog)

        # Expose the reserved map and tokens tuple to the class scope for ply.lex
        self.reserved = self.basic_reserved
        self.tokens = self.tokens_collection + tuple(self.reserved.values())

        # Build internal ply.lex instance
        self.lexer = lex.lex(
            module=self, debug=debug, optimize=optimize, outputdir=outputdir, debuglog=debuglog, errorlog=errorlog)

    def input(self, cool_program_source_code):
        """
        Run lexical analysis on a given COOL program source code string.
        :param cool_program_source_code: COOL program source code as a string.
        :return: None.
        """
        if self.lexer is None:
            raise Exception("Lexer was not built. Try calling the build() method first, and then tokenize().")

        self.lexer.input(cool_program_source_code)

    def token(self):
        """
        Advanced the lexers tokens tape one place and returns the current token.
        :side-effects: Modifies self.last_token.
        :return: Token.
        """
        if self.lexer is None:
            raise Exception("Lexer was not built. Try building the lexer with the build() method.")

        self.last_token = self.lexer.token()
        return self.last_token

    def clone_ply_lex(self):
        """
        Clones the internal ply.lex instance, returns a new copy.
        :return: ply.lex clone.
        """
        a_clone = self.lexer.clone()
        return a_clone

    @staticmethod
    def test(program_source_code):
        """
        Given a cool program source code string try to run lexical analysis on it and return all tokens as an iterator.
        :param program_source_code: String.
        :return: Iterator.
        """
        temp_lexer = PyCoolLexer()
        temp_lexer.input(program_source_code)
        iter_token_stream = iter([some_token for some_token in temp_lexer])
        del temp_lexer
        return iter_token_stream
            

    # ################### ITERATOR PROTOCOL ######################################################

    def __iter__(self):
        return self

    def __next__(self):
        t = self.token()
        if t is None:
            raise StopIteration
        return t

    def next(self):
        return self.__next__()

    # ################### READONLY PROPERTIES: TOKENS, STATES AND RESERVED KEYWORDS ############

    @property
    def tokens_collection(self):
        """
        Collection of COOL Syntax Tokens.
        :return: Tuple.
        """
        return (
            # Identifiers
            "ID", "TYPE",

            # Primitive Types
            "INTEGER", "STRING", "BOOLEAN",

            # Literals
            "LPAREN", "RPAREN", "LBRACE", "RBRACE", "COLON", "COMMA", "DOT", "SEMICOLON", "AT",

            # Operators
            "PLUS", "MINUS", "MULTIPLY", "DIVIDE", "EQ", "LT", "LTEQ", "ASSIGN", "INT_COMP", "NOT",

            # Special Operators
            "ARROW"
        )

    @property
    def basic_reserved(self):
        """
        Map of Basic-COOL reserved keywords.
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
            "pool": "POOL",
            "self": "SELF",
            "then": "THEN",
            "while": "WHILE",

            # BASIC TYPES - alphabetical order
            "Bool": "BOOL_TYPE",
            "Int": "INT_TYPE",
            "IO": "IO_TYPE",
            "Main": "MAIN_TYPE",
            "Object": "OBJECT_TYPE",
            "String": "STRING_TYPE",
            "SELF_TYPE": "SELF_TYPE"
        }

    @property
    def extended_reserved(self):
        """
        Map of Extended-COOL reserved keywords.
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

    # ################################# PRIVATE ########################################

    # ################# START OF LEXICAL ANALYSIS RULES DECLARATION ####################

    # LEXER STATES
    @property
    def states(self):
        return (
            ("STRING", "exclusive"),
            ("COMMENT", "exclusive")
        )

    # SIMPLE TOKENS RULES
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
    t_NOT = r'not'          # not
    t_ARROW = r'\=\>'       # =>

    # COMPLEX TOKENS LEXING RULES.
    integer_rule = r'\d+'
    boolean_rule = r'(true|false)'
    type_rule = r'[A-Z][a-zA-Z_0-9]*'
    identifier_rule = r'[a-z_][a-zA-Z_0-9]*'
    newline_rule = r'\n+'
    whitespace_rule = r'[\ \t\s\f\v\r]+'
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

    # THE STRING STATE
    @TOKEN(r"\"")
    def t_start_string(self, t):
        t.lexer.push_state("STRING")
        t.lexer.string_backslashed = False
        t.lexer.stringbuf = ""

    @TOKEN(r"\n")
    def t_STRING_newline(self, t):
        t.lexer.lineno += 1
        if not t.lexer.string_backslashed:
            print("String newline not escaped")
            t.lexer.skip(1)
        else:
            t.lexer.string_backslashed = False

    @TOKEN(r"\"")
    def t_STRING_end(self, t):
        if not t.lexer.string_backslashed:
            t.lexer.pop_state()
            # TODO: insert checks
            t.value = t.lexer.stringbuf
            t.type = "STRING"
            return t
        else:
            t.lexer.stringbuf += '"'
            t.lexer.string_backslashed = False

    @TOKEN(r"[^\n]")
    def t_STRING_anything(self, t):
        if t.lexer.string_backslashed:
            if t.value == 'b':
                t.lexer.stringbuf += '\b'
            elif t.value == 't':
                t.lexer.stringbuf += '\t'
            elif t.value == 'n':
                t.lexer.stringbuf += '\n'
            elif t.value == 'f':
                t.lexer.stringbuf += '\f'
            elif t.value == '\\':
                t.lexer.stringbuf += '\\'
            else:
                t.lexer.stringbuf += t.value
            t.lexer.string_backslashed = False
        else:
            if t.value != '\\':
                t.lexer.stringbuf += t.value
            else:
                t.lexer.string_backslashed = True

    # STRING ignored characters
    t_STRING_ignore = ''

    # STRING error handler
    def t_STRING_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # THE COMMENT STATE
    @TOKEN(r"\(\*")
    def t_start_comment(self, t):
        t.lexer.push_state("COMMENT")
        t.lexer.comment_count = 0

    @TOKEN(r"\(\*")
    def t_COMMENT_startanother(self, t):
        t.lexer.comment_count += 1

    @TOKEN(r"\*\)")
    def t_COMMENT_end(self, t):
        if t.lexer.comment_count == 0:
            t.lexer.pop_state()
        else:
            t.lexer.comment_count -= 1

    # COMMENT ignored characters
    t_COMMENT_ignore = ''

    # COMMENT error handler
    def t_COMMENT_error(self, t):
        t.lexer.skip(1)

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

    # ################# END OF LEXICAL ANALYSIS RULES DECLARATION ######################


# ----------------------------------------------------------------------
#                Lexer as a Standalone Python Program
#                Usage: ./lexer.py cool_program.cl
# ----------------------------------------------------------------------

def make_lexer():
    """
    Utility function.
    :return: PyCoolLexer object.
    """
    a_lexer = PyCoolLexer()
    a_lexer.build()
    return a_lexer


if __name__ == "__main__":
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

