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
from ast import *
from lexer import PyCoolLexer


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
        self.tokens = None
        self.parser = None

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

    # ################################# PRIVATE ########################################

    # ################################ PRECEDENCE RULES ################################

    @property
    def precedence(self):
        return (
            ('right', 'ASSIGN'),
            ('left', 'NOT'),
            ('nonassoc', 'LTEQ', 'LT', 'EQ'),
            ('left', 'PLUS', 'MINUS'),
            ('left', 'MULTIPLY', 'DIVIDE'),
            ('left', 'ISVOID'),
            ('left', 'INT_COMP'),
            ('left', 'AT'),
            ('left', 'DOT')
        )

    # ################### START OF FORMAL GRAMMAR RULES DECLARATION ####################

    def p_program(self, parse):
        """
        program : class_seq
        """
        parse[0] = Program(classes=parse[1])

    def p_class_seq(self, parse):
        """
        class_seq   : class_seq class SEMICOLON
                    | class SEMICOLON
        """
        if len(parse) == 3:
            parse[0] = (parse[1],)
        else:
            parse[0] = parse[1] + (parse[2],)

    def p_class(self, parse):
        """
        class : CLASS TYPE LBRACE features_seq_opt RBRACE
        """
        parse[0] = Class(name=parse[2], parent="Object", features=parse[4])

    def p_class_inheritance(self, parse):
        """
        class : CLASS TYPE INHERITS TYPE LBRACE features_seq RBRACE
        """
        parse[0] = Class(name=parse[2], parent=parse[4], features=parse[6])

    def p_features_seq_opt(self, parse):
        """
        features_seq_opt    : features_seq
                            | empty
        """
        if parse.slice[1].type == "empty":
            parse[0] = tuple()
        else:
            parse[0] = parse[1]

    def p_features_seq(self, parse):
        """
        features_seq    : features_seq feature SEMICOLON
                        | feature SEMICOLON
        """
        if len(parse) == 3:
            parse[0] = (parse[1],)
        else:
            parse[0] = parse[1] + (parse[2],)

    def p_feature_method(self, parse):
        """
        feature :   ID LPAREN RPAREN COLON TYPE LBRACE expr RBRACE
        """
        parse[0] = ClassMethod(name=parse[1], formal_params=tuple(), return_type=parse[5], body=parse[7])

    def p_feature_method_formal_params(self, parse):
        """
        feature :   ID LPAREN formal_params_seq RPAREN COLON TYPE LBRACE expr RBRACE
        """
        parse[0] = ClassMethod(name=parse[1], formal_params=parse[3], return_type=parse[6], body=parse[8])

    def p_feature_attr_with_assignment(self, parse):
        """
        feature : ID COLON TYPE ASSIGN expr
        """
        parse[0] = ClassAttribute(name=parse[1], attr_type=parse[3], init_expr=parse[5])

    def p_feature_attr(self, parse):
        """
        feature : ID COLON TYPE
        """
        parse[0] = ClassAttribute(name=parse[1], attr_type=parse[3], init_expr=None)

    def p_formal_params_seq(self, parse):
        """
        formal_params_seq   : formal_params_seq COMMA formal_param
                            | formal_param
        """
        if len(parse) == 2:
            parse[0] = (parse[1],)
        else:
            parse[0] = parse[1] + (parse[3],)

    def p_formal_param(self, parse):
        """
        formal_param : ID COLON TYPE
        """
        parse[0] = FormalParameter(name=parse[1], param_type=parse[3])

    def p_expr_object_identifier(self, parse):
        """
        expr : ID
        """
        parse[0] = Object(parse[1])

    def p_expr_integer(self, parse):
        """
        expr    : INTEGER
        """
        parse[0] = Integer(parse[1])

    def p_expr_boolean(self, parse):
        """
        expr    : BOOLEAN
        """
        parse[0] = Boolean(parse[1])

    def p_expr_string(self, parse):
        """
        expr    : STRING
        """
        parse[0] = String(parse[1])

    def p_expr_self(self, parse):
        """
        expr    : SELF
        """
        parse[0] = Self()

    def p_expr_block(self, parse):
        """
        expr     : LBRACE block_expr_seq RBRACE
        """
        parse[0] = Block(expr_list=parse[2])

    def p_block_expr_seq(self, parse):
        """
        block_expr_seq  : block_expr_seq expr SEMICOLON
                        | expr SEMICOLON
        """
        if len(parse) == 3:
            parse[0] = (parse[1],)
        else:
            parse[0] = parse[1] + (parse[2],)

    def p_expr_assignment(self, parse):
        """
        expr    : ID ASSIGN expr
        """
        parse[0] = Assignment(instance=Object(parse[1]), expr=parse[3])

    def p_expr_dynamic_dispatch(self, parse):
        """
        expr : expr DOT ID LPAREN arguments_seq_opt RPAREN
        """
        parse[0] = DynamicDispatch(instance=parse[1], method=parse[3], arguments=parse[5])

    def p_arguments_seq_opt(self, parse):
        """
        arguments_seq_opt : arguments_seq
        """
        parse[0] = parse[1]

    def p_arguments_seq_opt_empty(self, parse):
        """
        arguments_seq_opt : empty
        """
        parse[0] = tuple()

    def p_arguments_seq_many(self, parse):
        """
        arguments_seq : arguments_seq COMMA expr
        """
        parse[0] = parse[1] + (parse[3],)

    def p_arguments_seq_single(self, parse):
        """
        arguments_seq : expr
        """
        parse[0] = (parse[1],)

    def p_expr_static_dispatch(self, parse):
        """
        expr : expr AT TYPE DOT ID LPAREN arguments_seq RPAREN
        """
        p[0] = StaticDispatch(instance=parse[1], dispatch_type=parse[3], method=parse[5], arguments=parse[7])

    def p_expr_self_dispatch(self, parse):
        """
        expr : ID LPAREN arguments_seq RPAREN
        """
        parse[0] = DynamicDispatch(instance=Self(), method=parse[1], arguments=parse[3])

    def p_expr_math_operations(self, parse):
        """
        expr : expr PLUS expr
             | expr MINUS expr
             | expr MULTIPLY expr
             | expr DIVIDE expr
        """
        if parse[2] == '+':
            parse[0] = Addition(parse[1], parse[3])
        elif parse[2] == '-':
            parse[0] = Subtraction(parse[1], parse[3])
        elif parse[2] == '*':
            parse[0] = Multiplication(parse[1], parse[3])
        elif parse[2] == '/':
            parse[0] = Division(parse[1], parse[3])

    def p_expr_math_comparisons(self, parse):
        """
        expr : expr LTEQ expr
             | expr LT expr
             | expr EQ expr
        """
        if parse[2] == '<':
            parse[0] = LessThan(parse[1], parse[3])
        elif parse[2] == '<=':
            parse[0] = LessThanOrEqual(parse[1], parse[3])
        elif parse[2] == '=':
            parse[0] = Equal(parse[1], parse[3])

    def p_expr_parenthesized(self, parse):
        """
        expr : LPAREN expr RPAREN
        """
        parse[0] = parse[2]

    def p_expr_if_then_else(self, parse):
        """
        expr : IF expr THEN expr ELSE expr FI
        """
        parse[0] = If(predicate=parse[2], then_body=parse[4], else_body=parse[6])

    def p_expr_while_loop(self, parse):
        """
        expr : WHILE expr LOOP expr POOL
        """
        parse[0] = WhileLoop(predicate=parse[2], body=parse[4])

    # ############### LET EXPRESSION ###############
    def p_expr_master(self, parse):
        """
        expr    : let_expr
        """
    def p_expr_let(self, parse):
        """
        let_expr    : LET ID COLON TYPE IN expr
                    | inner_lets COMMA LET ID COLON TYPE
        """
        parse[0] = Let(instance=parse[2], let_type=parse[4], init_expr=None, body=parse[6])

    def p_expr_let_with_assignment(self, parse):
        """
        let_expr    : LET ID COLON TYPE ASSIGN expr IN expr
                    | inner_lets COMMA LET ID COLON TYPE ASSIGN expr
        """
        parse[0] = Let(instance=parse[2], let_type=parse[4], init_expr=parse[6], body=parse[8])

    def p_inner_lets_simple(self, parse):
        """
        inner_lets  : ID COLON TYPE IN expr
                    | inner_lets COMMA ID COLON TYPE
        """
        parse[0] = Let(instance=parse[1], let_type=parse[3], init_expr=None, body=parse[5])

    def p_inner_lets_with_assignments(self, parse):
        """
        inner_lets  : ID COLON TYPE ASSIGN expr IN expr
                    | inner_lets COMMA ID COLON TYPE ASSIGN expr
        """
        parse[0] = Let(instance=parse[1], let_type=parse[3], init_expr=parse[5], body=parse[7])

    # ############### CASE EXPRESSION ###############

    def p_expr_case(self, parse):
        """
        expr    : CASE expr OF actions_seq ESAC
        """
        parse[0] = Case(expr=parse[2], actions=parse[4])

    def p_action_seq_many(self, parse):
        """
        actions_seq : actions_seq action
        """
        parse[0] = parse[1] + (parse[2],)

    def p_action_seq_one(self, parse):
        """
        actions_seq : action
        """
        parse[0] = (parse[1],)

    def p_action_expr(self, parse):
        """
        action  : ID COLON TYPE ARROW expr SEMICOLON
        """
        parse[0] = Action(name=parse[1], action_type=parse[3], body=parse[5])

    #  ############### NEW, ISVOID, INT_COMP AND NOT EXPRESSIONS ###############

    def p_expr_new(self, parse):
        """
        expr    : NEW TYPE
        """
        parse[0] = NewObject(new_type=parse[2])

    def p_expr_isvoid(self, parse):
        """
        expr    : ISVOID expr
        """
        parse[0] = IsVoid(expr=parse[2])

    def p_expr_integer_complement(self, parse):
        """
        expr    : INT_COMP expr
        """
        parse[0] = IntegerComplement(integer_expr=parse[2])

    def p_expr_boolean_complement(self, parse):
        """
        expr    : NOT expr
        """
        parse[0] = BooleanComplement(boolean_expr=parse[2])

    # The Empty Production Rule
    def p_empty(self, parse):
        """
        empty :
        """
        parse[0] = None

    # yaac error rule for syntax errors
    def p_error(self, parse):
        print("Syntax error in input program at token: {!r}".format(parse))

    # ################### END OF FORMAL GRAMMAR RULES DECLARATION ######################


# ----------------------------------------------------------------------
#                Parser as a Standalone Python Program
#                Usage: ./parser.py cool_program.cl
# ----------------------------------------------------------------------

def make_parser():
    """
    Utility function.
    :return: PyCoolParser object.
    """
    a_parser = PyCoolParser()
    a_parser.build()
    return a_parser


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

    parser = make_parser()
    parse_result = parser.parse(cool_program_code)
    print(parse_result)

