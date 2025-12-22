#!/usr/bin/env python3

"""
Tests for AST to TAC translation.

These tests verify that COOL AST nodes are correctly translated
to Three-Address Code instructions.
"""

import pytest

from pycoolc.parser import make_parser
from pycoolc.ir.translator import ASTToTACTranslator, translate_to_tac
from pycoolc.ir.tac import (
    Instruction, Operand, Temp, Var, Const, Label,
    BinaryOp, UnaryOperation, Copy,
    LabelInstr, Jump, CondJump, CondJumpNot,
    Param, Return,
    New, Dispatch, StaticDispatch, IsVoid, GetAttr, SetAttr,
    BinOp, UnaryOp,
    TACProgram,
)


@pytest.fixture
def parser():
    return make_parser()


@pytest.fixture
def translator():
    return ASTToTACTranslator()


class TestConstants:
    """Test translation of constant expressions."""
    
    def test_integer_constant(self, parser, translator):
        ast = parser.parse("class Main { foo(): Int { 42 }; };")
        tac = translator.translate(ast)
        
        assert len(tac.methods) == 1
        method = tac.methods[0]
        assert method.class_name == "Main"
        assert method.method_name == "foo"
        
        # Should have: comment, copy (const to temp), return
        instrs = [i for i in method.instructions if not str(i).startswith("#")]
        assert any(isinstance(i, Copy) and isinstance(i.source, Const) 
                   and i.source.value == 42 for i in instrs)
    
    def test_string_constant(self, parser, translator):
        ast = parser.parse('class Main { foo(): String { "hello" }; };')
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, Copy) and isinstance(i.source, Const) 
                   and i.source.value == "hello" for i in instrs)
    
    def test_boolean_constants(self, parser, translator):
        ast = parser.parse("class Main { foo(): Bool { true }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, Copy) and isinstance(i.source, Const) 
                   and i.source.value is True for i in instrs)


class TestArithmetic:
    """Test translation of arithmetic expressions."""
    
    def test_addition(self, parser, translator):
        ast = parser.parse("class Main { foo(): Int { 1 + 2 }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        # Should have: copy 1, copy 2, add
        assert any(isinstance(i, BinaryOp) and i.op == BinOp.ADD for i in instrs)
    
    def test_subtraction(self, parser, translator):
        ast = parser.parse("class Main { foo(): Int { 5 - 3 }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, BinaryOp) and i.op == BinOp.SUB for i in instrs)
    
    def test_multiplication(self, parser, translator):
        ast = parser.parse("class Main { foo(): Int { 4 * 5 }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, BinaryOp) and i.op == BinOp.MUL for i in instrs)
    
    def test_division(self, parser, translator):
        ast = parser.parse("class Main { foo(): Int { 10 / 2 }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, BinaryOp) and i.op == BinOp.DIV for i in instrs)
    
    def test_complex_expression(self, parser, translator):
        # (1 + 2) * 3
        ast = parser.parse("class Main { foo(): Int { (1 + 2) * 3 }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        # Should have both ADD and MUL
        has_add = any(isinstance(i, BinaryOp) and i.op == BinOp.ADD for i in instrs)
        has_mul = any(isinstance(i, BinaryOp) and i.op == BinOp.MUL for i in instrs)
        assert has_add and has_mul


class TestComparisons:
    """Test translation of comparison expressions."""
    
    def test_less_than(self, parser, translator):
        ast = parser.parse("class Main { foo(): Bool { 1 < 2 }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, BinaryOp) and i.op == BinOp.LT for i in instrs)
    
    def test_less_than_or_equal(self, parser, translator):
        ast = parser.parse("class Main { foo(): Bool { 1 <= 2 }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, BinaryOp) and i.op == BinOp.LE for i in instrs)
    
    def test_equality(self, parser, translator):
        ast = parser.parse("class Main { foo(): Bool { 1 = 2 }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, BinaryOp) and i.op == BinOp.EQ for i in instrs)


class TestUnaryOperations:
    """Test translation of unary operations."""
    
    def test_integer_complement(self, parser, translator):
        ast = parser.parse("class Main { foo(): Int { ~5 }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, UnaryOperation) and i.op == UnaryOp.NEG for i in instrs)
    
    def test_boolean_not(self, parser, translator):
        ast = parser.parse("class Main { foo(): Bool { not true }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, UnaryOperation) and i.op == UnaryOp.NOT for i in instrs)


class TestControlFlow:
    """Test translation of control flow expressions."""
    
    def test_if_then_else(self, parser, translator):
        ast = parser.parse("class Main { foo(): Int { if true then 1 else 2 fi }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        # Should have: CondJumpNot, labels, Jump
        assert any(isinstance(i, CondJumpNot) for i in instrs)
        assert any(isinstance(i, LabelInstr) for i in instrs)
        assert any(isinstance(i, Jump) for i in instrs)
    
    def test_while_loop(self, parser, translator):
        ast = parser.parse("class Main { foo(): Object { while true loop 1 pool }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        # Should have: label (loop), CondJumpNot (exit), Jump (back)
        labels = [i for i in instrs if isinstance(i, LabelInstr)]
        assert len(labels) >= 2  # loop start and end
        assert any(isinstance(i, CondJumpNot) for i in instrs)
        assert any(isinstance(i, Jump) for i in instrs)


class TestLet:
    """Test translation of let expressions."""
    
    def test_simple_let(self, parser, translator):
        ast = parser.parse("class Main { foo(): Int { let x: Int <- 5 in x }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        # Should have copy for initialization
        copies = [i for i in instrs if isinstance(i, Copy)]
        assert len(copies) >= 1
    
    def test_multi_binding_let(self, parser, translator):
        ast = parser.parse("""
            class Main { 
                foo(): Int { 
                    let x: Int <- 1, y: Int <- 2 in x + y 
                }; 
            };
        """)
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        # Should have copies for x and y, then add
        copies = [i for i in instrs if isinstance(i, Copy)]
        assert len(copies) >= 2
        assert any(isinstance(i, BinaryOp) and i.op == BinOp.ADD for i in instrs)


class TestDispatch:
    """Test translation of method dispatch."""
    
    def test_self_dispatch(self, parser, translator):
        ast = parser.parse("class Main { foo(): Int { bar() }; bar(): Int { 0 }; };")
        tac = translator.translate(ast)
        
        # Find the foo method
        foo_method = next(m for m in tac.methods if m.method_name == "foo")
        instrs = foo_method.instructions
        
        # Should have dispatch on self
        assert any(isinstance(i, Dispatch) for i in instrs)
    
    def test_dynamic_dispatch_with_args(self, parser, translator):
        ast = parser.parse("""
            class Main { 
                foo(): Int { bar(1, 2) }; 
                bar(a: Int, b: Int): Int { a }; 
            };
        """)
        tac = translator.translate(ast)
        
        foo_method = next(m for m in tac.methods if m.method_name == "foo")
        instrs = foo_method.instructions
        
        # Should have params then dispatch
        params = [i for i in instrs if isinstance(i, Param)]
        assert len(params) == 2
        dispatch = next(i for i in instrs if isinstance(i, Dispatch))
        assert dispatch.num_args == 2


class TestObjectOperations:
    """Test translation of object-oriented operations."""
    
    def test_new_object(self, parser, translator):
        ast = parser.parse("class Main { foo(): Main { new Main }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, New) and i.type_name == "Main" for i in instrs)
    
    def test_isvoid(self, parser, translator):
        ast = parser.parse("class Main { foo(): Bool { isvoid self }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, IsVoid) for i in instrs)


class TestBlock:
    """Test translation of block expressions."""
    
    def test_block(self, parser, translator):
        ast = parser.parse("class Main { foo(): Int { { 1; 2; 3; } }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        # Should have copies for all three values
        copies = [i for i in instrs if isinstance(i, Copy) and isinstance(i.source, Const)]
        assert len(copies) >= 3


class TestReturn:
    """Test that methods properly return."""
    
    def test_method_has_return(self, parser, translator):
        ast = parser.parse("class Main { foo(): Int { 42 }; };")
        tac = translator.translate(ast)
        
        instrs = tac.methods[0].instructions
        assert any(isinstance(i, Return) for i in instrs)


class TestConvenienceFunction:
    """Test the translate_to_tac convenience function."""
    
    def test_translate_to_tac(self, parser):
        ast = parser.parse("class Main { foo(): Int { 42 }; };")
        tac = translate_to_tac(ast)
        
        assert isinstance(tac, TACProgram)
        assert len(tac.methods) == 1

