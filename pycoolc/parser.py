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

    # <class> ::= CLASS TYPE <inheritance> { <features_opt> } ;
    def p_class(self, parse):
        """
        class : CLASS TYPE inheritance_opt LBRACE features_opt RBRACE SEMICOLON
        """
        parse[0] = Type(name=parse[2], inherits=parse[3], features_seq=parse[5])

    # <inheritance> ::= INHERITS TYPE | <empty>
    def p_inheritance_opt(self, parse):
        """
        inheritance_opt : INHERITS TYPE
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

    # <features_opt> ::= <features> | <empty>
    def p_features_opt(self, parse):
        """
        features_opt    : features
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

    # <attribute> : ID ( <formals_wo_assign_opt> ) : TYPE { expr } ;
    def p_attribute(self, parse):
        """
        attribute : ID LPAREN formals_wo_assign_opt RPAREN COLON TYPE LBRACE expr RBRACE SEMICOLON
        """
        p[0] = Attribute(identifier=parse[1], attr_type=parse[6], formals_seq=parse[3], expression=parse[8])

    # <formal> : ID : TYPE <assignment_opt> ;
    def p_formal(self, parse):
        """
        formal : ID COLON TYPE assignment_opt SEMICOLON
        """
        assign_expr = None if parse[4].type == "empty" else parse[4]
        parse[0] = Formal(identifier=parse[1], formal_type=parse[3], assignment_expr=assign_expr)

    # <assignment_opt> : "<-" <expr>
    def p_assignment_opt(self, parse):
        """
        assignment_opt  : ASSIGN expr
                        | empty
        """
        bnf_rule = "<assignment_opt> : \"<-\" <expr>"

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

    # <formals_wo_assign_opt> ::= <formal_wo_assign> | <formal_wo_assign> <formals_wo_assign> | <empty>
    def p_formals_wo_assign_opt(self, parse):
        """
        formals_wo_assign_opt   : formal_wo_assign
                                | formal_wo_assign formals_wo_assign
                                | empty
        """
        bnf_rule = \
            "<formals_wo_assign_opt> ::= <formal_wo_assign> | <formal_wo_assign> <formals_wo_assign> | <empty>"

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

    # <expressions> ::= <expr> | <expr> , <expressions>
    def p_expressions_seq(self, parse):
        """
        expressions_seq : expr SEMICOLON
                        | expr SEMICOLON expressions_seq
        """
        bnf_rule = "<expressions_seq> ::= <expr> | <expr> ; <expressions_seq>"

        if len(parse) == 2:
            parse[0] = (parse[1],)
        elif len(parse) == 4:
            parse[0] = (parse[1],) + parse[3]
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while parsing grammar rule: {1}".format(
                parse, bnf_rule))

    # <arguments_seq_opt> ::= <expr> | <expr> COMMA arguments_seq | <empty>
    def p_arguments_seq_opt(self, parse):
        """
        arguments_seq_opt   : expr
                            | expr COMMA arguments_seq
                            | empty
        """
        bnf_rule = "<arguments_seq_opt> ::= <expr> | <expr> , <arguments_seq> | <empty>"

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

    # <arguments_seq> ::= <expr> | <expr> COMMA arguments_seq
    def p_arguments_seq(self, parse):
        """
        arguments_seq   : expr
                        | expr COMMA arguments_seq
        """
        bnf_rule = "<arguments_seq> ::= <expr> | <expr> COMMA arguments_seq"

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
                |   ISVOID ID
                |   ID ASSIGN expr
                |   LPAREN expr RPAREN
                |   LBRACE expressions_seq RBRACE
                |   ID LPAREN arguments_seq_opt RPAREN
                |   expr at_type DOT ID LPAREN arguments_seq_opt RPAREN
        """
        if len(parse) == 2:
            T = parse[1].type
            if T in ["ID", "STRING", "INTEGER", "BOOLEAN"]:
                if T == "ID":
                    parse[0] = IdentifierExpr(identifier=parse[1].value)
                elif T == "STRING":
                    parse[0] = StringExpr(value=parse[1].value)
                elif T == "INTEGER":
                    parse[0] = IntegerExpr(value=parse[1].value)
                elif T == "BOOLEAN":
                    parse[0] = BooleanExpr(value=parse[1].value)
            else:
                parse[0] = parse[1]

        # New Type or isvoid ID
        elif len(parse) == 3:
            if parse[1].type == "NEW":
                parse[0] = NewTypeExpr(new_type=parse[2])
            elif parse[1].type == "ISVOID":
                raise NotImplementedError()

        # Parenthesized Expr, Block Expr or Assignment
        elif len(parse) == 4:
            # ( expr )
            if parse[1].type == "LPAREN" and parse[3].type == "RPAREN":
                parse[0] = parse[2]

            # { expressions }
            elif parse[1].type == "LBRACE" and parse[3].type == "RBRACE":
                parse[0] = BlockExpr(expressions_block=parse[2])

            # ID <- expr
            else:
                parse[0] = AssignmentExpr(identifier=parse[1], expression=parse[2])

        # ID ( arguments_seq_opt )
        elif len(parse) == 5:
            DispatchExpr(
                identifier_expr=IdentifierExpr("self"), attribute_id=parse[1], arguments_seq=parse[2],
                statically_dispatched_type=None)

        # expr[@TYPE].ID(expressions_opt)
        elif len(parse) == 8:
            parse[0] = DispatchExpr(
                identifier_expr=parse[1], statically_dispatched_type=parse[2], attribute_id=parse[4],
                arguments_seq=parse[6])
        else:
            raise SyntaxError("Unexpected number of symbols: {0}".format(parse))

    def p_let(self, parse):
        """
        let : LET let_formals_seq IN expr
        """
        parse[0] = LetExpr(formals_seq=parse[2], in_expr=parse[4])

    # <let_seq> ::= ID COLON TYPE <assignment_opt> <let_seq_opt>
    def p_let_seq(self, parse):
        """
        let_formals_seq : ID COLON TYPE assignment_opt let_formals_seq_opt
        """
        parse[0] = (Formal(identifier=parse[1], formal_type=parse[3], assignment_expr=parse[4]),) + parse[5]

    # <let_seq_opt> ::= ID COLON TYPE <assignment_opt> | ID COLON TYPE <assignment_opt> COMMA <let_seq_opt> | <empty>
    def p_let_seq_opt(self, parse):
        """
        let_formals_seq_opt : ID COLON TYPE assignment_opt
                            | ID COLON TYPE assignment_opt COMMA let_formals_seq_opt
                            | empty
        """
        bnf_rule = "<let_seq_opt> ::= ID COLON TYPE <assignment_opt> " + \
                   "| ID COLON TYPE <assignment_opt> COMMA <let_seq_opt> " + \
                   "| <empty>"

        if len(parse) == 2 and parse[1].type == "empty":
            parse[0] = tuple()
        elif len(parse) == 5:
            parse[0] = (Formal(identifier=parse[1], formal_type=parse[3], assignment_expr=parse[4]),)
        elif len(parse) == 7:
            (Formal(identifier=parse[1], formal_type=parse[3], assignment_expr=parse[4]),) + parse[6]
        else:
            raise SyntaxError("Unexpected number of symbols: {0}, while parsing grammar rule: {1}".format(
                parse, bnf_rule))

    # case_esac ::= CASE expr OF actions ESAC
    def p_case_esac(self, parse):
        """
        case_esac : CASE expr OF actions ESAC
        """
        pass

    # if_then_else_fi ::= FI expr THEN expr ELSE expr FI
    def p_if_then_else_fi(self, parse):
        """
        if_then_else_fi : FI expr THEN expr ELSE expr FI
        """
        parse[0] = ConditionalExpr(condition=parse[2], true_eval=parse[4], false_eval=parse[6])

    # while_loop_pool ::= WHILE expr LOOP expr POOL
    def p_while_loop_pool(self, parse):
        """
        while_loop_pool : WHILE expr LOOP expr POOL
        """
        pass

    # actions ::= action | action actions
    def p_actions(self, parse):
        """
        actions : action
                | action actions
        """
        pass

    # action ::= D : TYPE ARROW expr
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

    # Empty Production
    def p_empty(self, parse):
        """
        empty :
        """
        parse[0] = None

    # yaac error rule for syntax errors
    def p_error(self, parse):
        print("Syntax error in input program source code!")
    
    # ################### END OF FORMAL GRAMMAR RULES DECLARATION ######################


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

