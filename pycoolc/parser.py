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

    @property
    def precedence(self):
        return (
            ('right', 'ASSIGN'),
            ('right', 'NOT'),
            ('nonassoc', 'LTEQ', 'LTHAN', 'EQUALS'),
            ('left', 'PLUS', 'MINUS'),
            ('left', 'TIMES', 'DIVIDE'),
            ('right', 'ISVOID'),
            ('right', 'INT_COMP'),
            ('left', 'AT'),
            ('left', 'DOT')
        )

    def p_program(self, parse):
        """
        program : classes
        """
        parse[0] = Program(classes=parse[1])

    def p_classes(self, parse):
        """
        classes : classes class
                | class
        """
        if len(parse) == 2:
            parse[0] = (parse[1],)
        else:
            parse[0] = parse[1] + (parse[2],)

    def p_class(self, parse):
        """
        class : CLASS TYPE inheritance_opt LBRACE features_opt RBRACE SEMICOLON
        """
        parse[0] = Type(name=parse[2], inherits=parse[3], features=parse[5])

    def p_inheritance_opt(self, parse):
        """
        inheritance_opt : INHERITS some_type
                        | empty
        """
        if len(parse) == 2:
            parse[0] = Inheritance(parent_type="OBJECT_TYPE")
        else:
            parse[0] = Inheritance(parent_type=parse[2])

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

    def p_features_opt(self, parse):
        """
        features_opt    : features
                        | empty
        """
        if parse.slice[1].type == "empty":
            parse[0] = tuple()
        else:
            parse[0] = parse[1]

    def p_features(self, parse):
        """
        features : features feature
                 | feature
        """
        if len(parse) == 2:
            parse[0] = (parse[1],)
        else:
            parse[0] = parse[1] + (parse[2],)

    def p_feature(self, parse):
        """
        feature : method_def
                | attribute_def
        """
        parse[0] = parse[1]

    def p_method_def(self, parse):
        """
        method_def : ID LPAREN formal_params_seq_opt RPAREN COLON some_type LBRACE expr RBRACE SEMICOLON
        """
        parse[0] = ClassMethod(identifier=parse[1], formal_params=parse[3], return_type=parse[6], method_body=parse[8])

    def p_attribute_def(self, parse):
        """
        attribute_def : ID COLON some_type assignment_opt SEMICOLON
        """
        assign_expr = None if parse.slice[4].type == "empty" else parse[4]
        parse[0] = ClassAttribute(identifier=parse[1], attribute_type=parse[3], assignment_expr=assign_expr)

    def p_assignment_opt(self, parse):
        """
        assignment_opt  : ASSIGN expr
                        | empty
        """
        if len(parse) == 2:
            parse[0] = None
        else:
            parse[0] = parse[2]
    
    def p_formal_params_seq_opt(self, parse):
        """
        formal_params_seq_opt   : formal_params_seq
                                | empty
        """
        if parse.slice[1].type == "empty":
            parse[0] = tuple()
        else:
            parse[0] = parse[1]

    def p_formal_params_seq(self, parse):
        """
        formal_params_seq   : formal_params_seq formal_param
                            | formal_param
        """
        if len(parse) == 2:
            parse[0] = (parse[1],)
        else:
            parse[0] = parse[1] + (parse[2],)

    def p_formal_param(self, parse):
        """
        formal_param : ID COLON some_type
        """
        parse[0] = FormalParameter(identifier=parse[1], param_type=parse[3])

    def p_formal(self, parse):
        """
        formal : ID COLON some_type assignment_opt
        """
        assign_expr = None if parse.slice[4].type == "empty" else parse[4]
        parse[0] = Formal(identifier=parse[1], formal_type=parse[3], assignment_expr=assign_expr)

    def p_expressions_seq(self, parse):
        """
        expressions_seq : expressions_seq expr SEMICOLON
                        | expr SEMICOLON
        """
        if len(parse) == 3:
            parse[0] = (parse[1],)
        else:
            parse[0] = parse[1] + (parse[2],)

    def p_arguments_seq_opt(self, parse):
        """
        arguments_seq_opt   : arguments_seq
                            | empty
        """
        if parse.slice[1].type == "empty":
            parse[0] = tuple()
        else:
            parse[0] = (parse[1],)

    def p_arguments_seq(self, parse):
        """
        arguments_seq   : arguments_seq COMMA expr
                        | expr
        """
        if len(parse) == 2:
            parse[0] = (parse[1],)
        else:
            parse[0] = (parse[1],) + parse[3]

    def p_expr(self, parse):
        """
        expr    :   ID ASSIGN expr
                |   dynamic_dispatch_expr
                |   static_dispatch_expr
                |   ID LPAREN arguments_seq_opt RPAREN
                |   if_then_fi
                |   if_then_else_fi
                |   while_loop_pool
                |   LBRACE expressions_seq RBRACE
                |   let
                |   case_esac
                |   NEW some_type
                |   ISVOID ID
                |   math_arith_operation
                |   int_comp_operation
                |   math_comp_operation
                |   bool_neg_operation
                |   LPAREN expr RPAREN
                |   ID
                |   INTEGER
                |   STRING
                |   BOOLEAN
        """
        if len(parse) == 2:
            ptype = parse.slice[1].type
            if ptype in ["ID", "STRING", "INTEGER", "BOOLEAN"]:
                if ptype == "ID":
                    parse[0] = IdentifierExpr(identifier=parse.slice[1].value)
                elif ptype == "STRING":
                    parse[0] = StringConstant(value=parse.slice[1].value)
                elif ptype == "INTEGER":
                    parse[0] = IntegerContant(value=parse.slice[1].value)
                elif ptype == "BOOLEAN":
                    parse[0] = BooleanConstant(value=parse.slice[1].value)
            else:
                parse[0] = parse[1]
        # "new Type" or "isvoid(ID)"
        elif len(parse) == 3:
            if parse.slice[1].type == "NEW":
                parse[0] = NewTypeExpr(new_type=parse[2])
            elif parse.slice[1].type == "ISVOID":
                parse[0] = IsVoidExpr(expression=parse[2])
        # Parenthesized Expr, Block Expr or Assignment
        elif len(parse) == 4:
            # ( expr )
            if parse.slice[1].type == "LPAREN" and parse.slice[3].type == "RPAREN":
                parse[0] = parse[2]
            # { expressions }
            elif parse.slice[1].type == "LBRACE" and parse.slice[3].type == "RBRACE":
                parse[0] = BlockExpr(expressions=parse[2])
            # ID <- expr
            else:
                parse[0] = AssignmentExpr(identifier=parse[1], expression=parse[3])
        # ID ( arguments_seq_opt )
        elif len(parse) == 5:
            parse[0] = DynamicDispatchExpr(identifier_expr=IdentifierExpr("self"), method_id=parse[1], arguments=parse[3])

    def p_let(self, parse):
        """
        let : LET let_formals_seq IN expr
        """
        parse[0] = LetExpr(formals=parse[2], expression=parse[4])

    def p_let_formals_seq(self, parse):
        """
        let_formals_seq : let_formals_seq COMMA formal
                        | formal
        """
        if len(parse) == 2:
            parse[0] = (parse[1],)
        elif len(parse) == 4:
            parse[0] = (parse[1],) + parse[3]

    def p_if_then_fi(self, parse):
        """
        if_then_fi : IF expr THEN expr FI
        """
        parse[0] = ConditionalExpr(predicate=parse[2], then_expression=parse[4], else_expression=None)

    def p_if_then_else_fi(self, parse):
        """
        if_then_else_fi : IF expr THEN expr ELSE expr FI
        """
        parse[0] = ConditionalExpr(predicate=parse[2], then_expression=parse[4], else_expression=parse[6])

    def p_while_loop_pool(self, parse):
        """
        while_loop_pool : WHILE expr LOOP expr POOL
        """
        parse[0] = LoopExpr(predicate=parse[2], body=parse[4])

    def p_case_esac(self, parse):
        """
        case_esac : CASE expr OF actions ESAC
        """
        parse[0] = CaseExpr(expression=parse[2], actions=parse[4])

    def p_actions(self, parse):
        """
        actions : actions action
                | action
        """
        if len(parse) == 2:
            parse[0] = (parse[1],)
        else:
            parse[0] = parse[1] + (parse[2],)

    def p_action(self, parse):
        """
        action : ID COLON some_type ARROW expr SEMICOLON
        """
        parse[0] = Action(identifier=parse[1], action_type=parse[3], body=parse[5])

    def p_math_arith_operation(self, parse):
        """
        math_arith_operation    :   expr PLUS expr
                                |   expr MINUS expr
                                |   expr TIMES expr
                                |   expr DIVIDE expr
        """
        parse[0] = BinaryOperation(left_expression=parse[1], right_expression=parse[3],
                                   operation=get_operation(parse.slice[2].type))

    def p_math_comp_operation(self, parse):
        """
        math_comp_operation : expr LTHAN expr
                            | expr LTEQ expr
                            | expr EQUALS expr
        """
        parse[0] = BinaryOperation(left_expression=parse[1], right_expression=parse[3],
                                   operation=get_operation(parse.slice[2].type))

    def p_int_comp_operation(self, parse):
        """
        int_comp_operation  : INT_COMP expr
        """
        parse[0] = UnaryOperation(operation=get_operation(parse.slice[1].type), expression=parse[2])

    def p_bool_neg_operation(self, parse):
        """
        bool_neg_operation  : NOT expr
        """
        parse[0] = UnaryOperation(operation=get_operation(parse.slice[1].type), expression=parse[2])

    def p_dynamic_dispatch_expr(self, parse):
        """
        dynamic_dispatch_expr : expr DOT ID LPAREN arguments_seq_opt RPAREN
        """
        parse[0] = DynamicDispatchExpr(identifier_expr=parse[1], method_id=parse[3], arguments=parse[5])

    def p_static_dispatch_expr(self, parse):
        """
        static_dispatch_expr : expr AT some_type DOT ID LPAREN arguments_seq_opt RPAREN
        """
        parse[0] = StaticDispatchExpr(identifier_expr=parse[1], dispatch_type=parse[3], method_id=parse[5],
                                      arguments=parse[7])

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

