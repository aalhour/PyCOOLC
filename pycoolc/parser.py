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
from pycoolc.ast import *
from pycoolc.lexer import PyCoolLexer


class PyCoolParser(object):
    """
    TODO
    """
    def __init__(self):
        """
        TODO
        :return:
        """
        # Instantiate the internal lexer and build it.
        self.lexer = PyCoolLexer()

        # Initialize self.parser and self.tokens to None
        self.parser = None
        self.tokens = None

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
        """
        TODO
        :param program_source_code: TODO
        :return: TODO
        """
        if self.parser is None:
            raise ValueError("Parser was not build, try building it first with the build() method.")

        return self.parser.parse(program_source_code)

    # ################### START OF FORMAL GRAMMAR RULES DECLARATION ##################

    # <program> ::= <classes>
    def p_program(self, parse):
        """
        program : classes
        """
        parse[0] = Program(classes=parse[1])

    # <classes> ::= <class> | <class> <classes>
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
            raise SyntaxError("Unexpected number of symbols: {0}, while parsing grammar rule: {1}".format(
                parse, bnf_rule))

    # <class> ::= CLASS TYPE <inheritance> { <features_optional> } ;
    def p_class(self, parse):
        """
        class : CLASS TYPE inheritance LBRACE features_optional RBRACE SEMICOLON
        """
        parse[0] = Type(name=parse[2], inherits=parse[3], features=parse[5])

    # <inheritance> ::= INHERITS TYPE | <empty>
    def p_inheritance(self, parse):
        """
        inheritance : INHERITS TYPE
                    | empty
        """
        bnf_rule = "<inheritance> ::= inherits TYPE | empty"

        # Case of second rhs (empty)
        if len(parse) == 1:
            parse[0] = None
        # Case of first rhs (inherits Type)
        elif len(parse) == 2:
            parse[0] = Inheritance(inheritance_type=p[2])
        # Unexpected production
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while parsing grammar rule: {1}".format(
                parse, bnf_rule))

    # <features_optional> ::= <features> | <empty>
    def p_features_optional(self, parse):
        """
        features_optional   : features
                            | empty
        """
        if parse[1].type == "empty":
            parse[0] = None
        else:
            parse[0] = Features(features=parse[1])

    # <features> ::= <feature> | <feature> <features>
    def p_features(self, parse):
        """
        features    : feature
                    | feature features
        """
        bnf_rule = "<features> ::= <feature> | <feature> <features>"

        if len(parse) == 2:
            parse[0] = (parse[1],)
        elif len(parse) == 3:
            parse[0] = (parse[1],) + parse[2]
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while parsing grammar rule: {1}".format(
                parse, bnf_rule))

    # <featue> ::= <attribute> | <formal>
    def p_feature(self, parse):
        """
        feature : attribute
                | formal
        """
        parse[0] = parse[1]

    # <attribute> : ID ( <formals_wo_assign_optional> ) : TYPE { expr } ;
    def p_attribute(self, parse):
        """
        attribute : ID LPAREN formals_wo_assign_optional RPAREN COLON TYPE LBRACE expr RBRACE SEMICOLON
        """
        p[0] = Attribute(identifier=parse[1], attr_type=parse[6], formals=parse[3], expression=parse[8])

    # <formal> : ID : TYPE <assignment_optional> ;
    def p_formal(self, parse):
        """
        formal : ID COLON TYPE assignment_optional SEMICOLON
        """
        assign_expr = None if parse[4].type == "empty" else parse[4]
        parse[0] = Formal(identifier=parse[1], formal_type=parse[3], assignment_expr=assign_expr)

    # <assignment_optional> : "<-" <expr>
    def p_assignment_optional(self, parse):
        """
        assignment_optional : ASSIGNMENT expr
                            | empty
        """
        bnf_rule = "<assignment_optional> : \"<-\" <expr>"

        if len(parse) == 2 and parse[1].type is "empty":
            parse[0] = None
        elif len(parse) == 3:
            parse[0] = parse[1]
        else:
            raise SyntaxError("Unexpected sequence of symbols: {0}, while parsing grammar rule: {1}".format(
                parse, bnf_rule))

    # <formals> ::= <formal> | <formal> <formals>
    def p_formals(self, parse):
        """
        formals : formal
                | formal formals
        """
        bnf_rule = "<formals> ::= <formal> | <formal> <formals>"

        if len(parse) == 2:
            parse[0] = (parse[1],)
        elif len(parse) == 3:
            parse[0] = (parse[1],) + parse[2]
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while processing grammar rule: {1}".format(
                parse, bnf_rule))

    # <formals_wo_assign_optional> ::= <formal_wo_assign> | <formal_wo_assign> <formals_wo_assign> | <empty>
    def p_formals_wo_assign_optional(self, parse):
        """
        formals_wo_assign_optional  : formal_wo_assign
                                    | formal_wo_assign formals_wo_assign
                                    | empty
        """
        bnf_rule = \
            "<formals_wo_assign_optional> ::= <formal_wo_assign> | <formal_wo_assign> <formals_wo_assign> | <empty>"

        if len(parse) == 2:
            if parse[1].type == "empty":
                parse[0] = None
            else:
                parse[0] = parse[1]
        elif len(parse) == 3:
            parse[0] = (parse[1],) + parse[2]
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while processing grammar rule: {1}".format(
                parse, bnf_rule))

    # <formals_wo_assign> ::= <formal_wo_assign> | <formal_wo_assign> <formals_wo_assign>
    def p_formals_wo_assign(self, parse):
        """
        formals_wo_assign   : formal_wo_assign
                            | formal_wo_assign formals_wo_assign
        """
        bnf_rule = "<formals_wo_assign> ::= <formal_wo_assign> | <formal_wo_assign> <formals_wo_assign>"
        if len(parse) == 2:
            parse[0] = (parse[1],)
        elif len(parse) == 3:
            parse[0] = (parse[1],) + parse[2]
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while processing grammar rule: {1}".format(
                parse, bnf_rule))

    # <formal_wo_assign> ::= ID : TYPE
    def p_formal_wo_assign(self, parse):
        """
        formal_wo_assign : ID COLON TYPE
        """
        parse[0] = Formal(identifier=parse[1], formal_type=parse[3], assignment_expr=None)

    # <expressions_optional> ::= <expr> | <expr> , <expressions> | <empty>
    def p_expressions_optional(self, parse):
        """
        expressions_optional    : expr
                                | expr COMMA expressions
                                | empty
        """
        bnf_rule = "<expressions_optional> ::= <expr> | <expr> , <expressions> | <empty>"

        if len(parse) == 2:
            if parse[1].type == "empty":
                parse[0] = None
            else:
                parse[0] = (parse[1],)
        elif len(parse) == 4:
            parse[0] = (parse[1],) + parse[3]
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while parsing grammar rule: {1}".format(
                parse, bnf_rule))

    # <expressions> ::= <expr> | <expr> , <expressions>
    def p_expressions(self, parse):
        """
        expressions : expr
                    | expr COMMA expressions
        """
        bnf_rule = "<expressions> ::= <expr> | <expr> , <expressions>"

        if len(parse) == 2:
            parse[0] = (parse[1],)
        elif len(parse) == 4:
            parse[0] = (parse[1],) + parse[3]
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while parsing grammar rule: {1}".format(
                parse, bnf_rule))

    def p_expr(self, parse):
        """
        expr    :   ID
                |   STRING
                |   INTEGER
                |   BOOLEAN
                |   let
                |   case_esac
                |   if_then_else_fi
                |   while_loop_pool
                |   unary_operation
                |   binary_operation
                |   NEW TYPE
                |   ID ASSIGNMENT expr
                |   LPAREN expr RPAREN
                |   LBRACE expressions RBRACE
                |   expr at_type DOT ID LPAREN expressions_optional RPAREN
        """
        if len(parse) == 2:
            parse[0] = parse[1]
        elif len(parse) == 3 and parse[1].type == "NEW":
            parse[0] = NewTypeExpr(new_type=parse[2])
        elif len(parse) == 4:
            # LPAREN expr RPAREN
            if parse[1].type == "LPAREN" and parse[3].type == "RPAREN":
                parse[0] = parse[2]
            # LBRACE expressions RBRACE
            elif parse[1].type == "LBRACE" and parse[3].type == "RBRACE":
                parse[0] = BlockExpr(expressions_block=parse[2])
            # ID ASSIGNMENT expr
            else:
                parse[0] = AssignmentExpr(identifier=parse[1], expression=parse[2])
        elif len(parse) == 8:
            parse[0] = MethodCallExp(expression=parse[1], statically_dispatched_type=parse[2],
                                     method_identifier=parse[4], call_params=parse[6])
        else:
            raise SyntaxError("Unexpected number of symbols: {0}".format(parse))

    # <at_type> ::= AT TYPE | empty
    def p_at_type(self, parse):
        """
        at_type : AT TYPE
                | empty
        """
        bnf_rule = "<at_type> ::= AT TYPE | empty"

        if len(parse) == 2 and parse[1].type == "empty":
            p[0] = None
        elif len(parse) == 3:
            parse[0] = parse[2]
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while parsing grammar rule: {1}".format(
                parse, bnf_rule))

    # if_then_else_fi ::= FI expr THEN expr ELSE expr FI
    def p_if_then_else_fi(self, parse):
        """
        if_then_else_fi : FI expr THEN expr ELSE expr FI
        """
        pass

    # while_loop_pool ::= WHILE expr LOOP expr POOL
    def p_while_loop_pool(self, parse):
        """
        while_loop_pool : WHILE expr LOOP expr POOL
        """
        pass

    # let ::= LET formals IN expr
    def p_let(self, parse):
        """
        let : LET formals IN expr
        """
        pass

    # case_esac ::= CASE expr OF actions ESAC
    def p_case_esac(self, parse):
        """
        case_esac : CASE expr OF actions ESAC
        """
        pass

    # actions ::= action | action actions
    def p_actions(self, parse):
        """
        actions : action
                | action actions
        """
        pass

    # action ::= D : TYPE ACTION expr
    def p_action(self, parse):
        """
        action : ID COLON TYPE ARROW expr
        """
        pass

    def p_unary_operation(self, parse):
        """
        unary_operation :   ISVOID expr
                        |   INT_COMP expr
                        |   NOT expr
        """
        pass

    def p_binary_operation(self, parse):
        """
        binary_operation    :   expr PLUS expr
                            |   expr MINUS expr
                            |   expr TIMES expr
                            |   expr DIVIDE expr
                            |   expr LTHAN expr
                            |   expr LTEQ expr
                            |   expr EQUALS expr
        """
        pass

    # Empty Production
    def p_empty(self, parse):
        """
        empty :
        """
        parse[0] = None

    # yaac error rule for syntax errors
    def p_error(self, parse):
        print("Syntax error in input program source code!")

    # ################### END OF FORMAL GRAMMAR RULES DECLARATION ####################


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

