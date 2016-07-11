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

    # ################################# PRIVATE ########################################

    # ################### START OF FORMAL GRAMMAR RULES DECLARATION ####################

    def p_program(self, parse):
        """
        program : class_seq
        """
        parse[0] = Program(classes=parse[1])

    def p_class_seq_many(self, parse):
        """
        class_seq : class_seq class SEMICOLON
        """
        parse[0] = parse[1] + (parse[2],)

    def p_class_seq_single(self, parse):
        """
        class_seq : class SEMICOLON
        """
        parse[0] = parse[1]

    def p_class(self, parse):
        """
        class : CLASS TYPE LBRACE features_seq RBRACE
        """
        parse[0] = Type(name=parse[2], base_type="OBJECT_TYPE", features=parse[5])

    def p_class_with_inheritance(self, parse):
        """
        class : CLASS TYPE INHERITS some_type LBRACE features_seq RBRACE
        """
        parse[0] = Type(name=parse[2], inherits=parse[3], features=parse[5])

    def p_some_type(self, parse):
        """
        some_type   : TYPE
                    | SELF_TYPE
                    | OBJECT_TYPE
                    | MAIN_TYPE
                    | IO_TYPE
                    | INT_TYPE
                    | BOOL_TYPE
                    | STRING_TYPE
        """
        parse[0] = parse[1]

    def p_features_seq_many(self, parse):
        """
        features_seq    : features_seq feature SEMICOLON
        """
        parse[0] = parse[1] + (parse[2],)

    def p_features_seq_single(self, parse):
        """
        features_seq    : feature SEMICOLON
        """
        parse[0] = (parse[1],)

    def p_features_seq_empty(self, parse):
        """
        features_seq    : empty
        """
        parse[0] = tuple()

    def p_feature_method_with_formal_params(self, parse):
        """
        feature :   ID LPAREN formal_params_seq RPAREN COLON some_type LBRACE expr RBRACE
        """
        parse[0] = ClassMethod(identifier=parse[1], formal_params=parse[3], return_type=parse[6], method_body=parse[8])

    def p_feature_method(self, parse):
        """
        feature :   ID LPAREN RPAREN COLON some_type LBRACE expr RBRACE
        """
        parse[0] = ClassMethod(identifier=parse[1], formal_params=tuple(), return_type=parse[5], method_body=parse[7])

    def p_feature_attr_with_assignment(self, parse):
        """
        feature : ID COLON some_type ASSIGN expr
        """
        parse[0] = ClassAttribute(identifier=parse[1], attribute_type=parse[3], assignment_expr=parse[5])

    def p_feature_attr(self, parse):
        """
        feature : ID COLON some_type
        """
        parse[0] = ClassAttribute(identifier=parse[1], attribute_type=parse[3], assignment_expr=None)
    
    def p_formal_params_seq_many(self, parse):
        """
        formal_params_seq   : formal_params_seq COMMA formal_param
        """
        parse[0] = parse[1] + (parse[2],)

    def p_formal_params_seq_single(self, parse):
        """
        formal_params_seq   : formal_param
        """
        parse[0] = (parse[1],)

    def p_formal_param(self, parse):
        """
        formal_param : ID COLON some_type
        """
        parse[0] = FormalParameter(identifier=parse[1], param_type=parse[3])

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

    def p_expr_block(self, parse):
        """
        expr     : LBRACE block_expr_seq RBRACE
        """
        parse[0] = BlockExpr(parse[2])

    def p_block_expr_seq_many(self, parse):
        """
        block_expr_seq    : block_expr_seq expr SEMICOLON
        """
        parse[0] = parse[1] + (parse[2],)

    def p_block_expr_seq_single(self, parse):
        """
        block_expr_seq    : expr SEMICOLON
        """
        parse[0] = (parse[1],)

    def p_expr_assignment(self, parse):
        """
        expr    : ID ASSIGN expr
        """
        parse[0] = AssignmentExpr(instance=Object(parse[1]), expression=parse[3])

    def p_expr_dynamic_dispatch(self, parse):
        """
        expr : expr DOT ID LPAREN arguments_seq RPAREN
        """
        parse[0] = DynamicDispatchExpr(instance=parse[1], method=parse[3], arguments=parse[5])

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

    def p_arguments_seq_empty(self, parse):
        """
        arguments_seq : empty
        """
        parse[0] = tuple()

    def p_expr_static_dispatch(self, parse):
        """
        expr : expr AT some_type DOT ID LPAREN arguments_seq RPAREN
        """
        p[0] = StaticDispatchExpr(instance=parse[1], dispatch_type=parse[3], method=parse[5], arguments=parse[7])

    def p_expr_self_dispatch(self, parse):
        """
        expr : ID LPAREN arguments_seq RPAREN
        """
        parse[0] = DynamicDispatchExpr(instance="self", method=parse[1], arguments=parse[3])

    def p_expr_math_operations(self, parse):
        """
        expr    : expr PLUS expr
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
        expr    : expr LT expr
                | expr LTEQ expr
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
        expr    : LPAREN expr RPAREN
        """
        parse[0] = parse[2]

    def p_expr_if_then_else(self, parse):
        """
        expr    : IF expr THEN expr ELSE expr FI
        """
        parse[0] = ConditionalExpr(predicate=parse[2], then_expression=parse[4], else_expression=parse[6])

    def p_expr_while_loop(self, parse):
        """
        expr    : WHILE expr LOOP expr POOL
        """
        parse[0] = LoopExpr(predicate=parse[2], body=parse[4])

    # ############### LET EXPRESSION ###############

    def p_expr_let(self, parse):
        """
        expr    : LET ID COLON some_type IN expr
        expr    : LET ID COLON some_type COMMA inner_lets
        """
        parse[0] = LetExpr(parse[2], parse[4], None, parse[6])

    def p_expr_let_with_assignment(self, parse):
        """
        expr    : LET ID COLON some_type ASSIGN expr IN expr
        expr    : LET ID COLON some_type ASSIGN expr COMMA inner_lets
        """
        parse[0] = LetExpr(parse[2], parse[4], parse[6], parse[8])

    def p_expr_let_with_error(self, parse):
        """
        expr    : LET error COMMA ID COLON some_type IN expr
        expr    : LET error COMMA ID COLON some_type COMMA inner_lets
        """
        parse[0] = LetExpr(parse[4], parse[6], None, parse[8])

    def p_expr_let_with_assignemnt_and_error(self, parse):
        """
        expr    : LET error COMMA ID COLON some_type ASSIGN expr IN expr
        expr    : LET error COMMA ID COLON some_type ASSIGN expr COMMA inner_lets
        """
        parse[0] = LetExpr(parse[4], parse[6], parse[8], parse[10])

    def p_inner_lets_simple(self, parse):
        """
        inner_lets  : ID COLON some_type IN expr
        inner_lets  : ID COLON some_type COMMA inner_lets
        """
        parse[0] = LetExpr(parse[1], parse[3], None, parse[5])

    def p_inner_lets_with_assignments(self, parse):
        """
        inner_lets  : ID COLON some_type ASSIGN expr IN expr
        inner_lets  : ID COLON some_type ASSIGN expr COMMA inner_lets
        """
        parse[0] = LetExpr(parse[1], parse[3], parse[5], parse[7])

    # ############### CASE EXPRESSION ###############

    def p_expr_case(self, parse):
        """
        expr    : CASE expr OF actions_seq ESAC
        """
        parse[0] = CaseExpr(expression=parse[2], actions=parse[4])

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
        action  : ID COLON some_type ARROW expr SEMICOLON
        """
        parse[0] = Action(identifier=parse[1], action_type=parse[3], body=parse[5])

    #  ############### NEW, ISVOID, INT_COMP AND NOT EXPRESSIONS ###############

    def p_expr_new(self, parse):
        """
        expr    : NEW some_type
        """
        parse[0] = NewTypeExpr(new_type=parse[2])

    def p_expr_isvoid(self, parse):
        """
        expr    : ISVOID expr
        """
        parse[0] = IsVoidExpr(expression=parse[2])

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

