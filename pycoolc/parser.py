#!/usr/bin/env python3

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
        # Initialize self.parser to None
        self.parser = None

        # Instantiate the internal lexer and build it.
        self.lexer = PyCoolLexer()

    def build(self, **kwargs):
        self.lexer.build(**kwargs)
        self.parser = yacc.yacc(module=self, **kwargs)

