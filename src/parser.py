# -----------------------------------------------------------------------------
# parser.py
#
# Author:       Ahmad Alhour (git.io/aalhour; aalhour.com).
# Date:         May 25rd, 2016.
# Description:  The Parser module. Implements syntax analysis and parsing rules
#               of the COOL CFG.
# -----------------------------------------------------------------------------

import ply.yacc as yacc
from lexer import PyCoolLexer


class PyCoolParser(object):
    def __init__(self):
        self.lexer = PyCoolLexer()
        self.lexer.build()


