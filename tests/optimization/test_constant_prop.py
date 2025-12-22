"""
Tests for constant propagation analysis.

These tests verify the constant propagation algorithm from the user's notes:
- Transfer functions for different statement types
- Meet operation at join points
- Constant folding transformation
"""

import pytest
from pycoolc.ir.tac import (
    Temp, Var, Const, Label, BinOp, UnaryOp,
    Copy, BinaryOp, UnaryOperation, LabelInstr, Jump, CondJump, Return,
    TACMethod,
)
from pycoolc.ir.cfg import build_cfg
from pycoolc.optimization.constant_prop import (
    ConstValue,
    ConstEnv,
    ConstantPropagation,
    run_constant_propagation,
    fold_constants,
)


class TestConstEnv:
    """Tests for the constant environment."""

    def test_empty_env(self):
        env = ConstEnv()
        # Unknown variables default to bottom
        assert env.get("x").is_bottom()

    def test_set_and_get(self):
        env = ConstEnv()
        env2 = env.set("x", ConstValue.constant(42))
        
        assert env.get("x").is_bottom()  # Original unchanged
        assert env2.get("x").get_constant() == 42

    def test_meet_envs(self):
        """Meeting environments should meet each variable."""
        env1 = ConstEnv().set("x", ConstValue.constant(1))
        env2 = ConstEnv().set("x", ConstValue.constant(1))
        
        result = env1.meet(env2)
        assert result.get("x").get_constant() == 1

    def test_meet_envs_different_values(self):
        """Different values meet to top."""
        env1 = ConstEnv().set("x", ConstValue.constant(1))
        env2 = ConstEnv().set("x", ConstValue.constant(2))
        
        result = env1.meet(env2)
        assert result.get("x").is_top()

    def test_meet_envs_disjoint_vars(self):
        """Variables in only one env should be preserved."""
        env1 = ConstEnv().set("x", ConstValue.constant(1))
        env2 = ConstEnv().set("y", ConstValue.constant(2))
        
        result = env1.meet(env2)
        # x is in env1 (constant) and env2 (bottom) → constant
        assert result.get("x").get_constant() == 1
        # y is in env1 (bottom) and env2 (constant) → constant
        assert result.get("y").get_constant() == 2


class TestConstantPropagationTransfer:
    """Tests for constant propagation transfer functions."""

    def test_copy_constant(self):
        """x = 42 should set C(x) = 42."""
        analysis = ConstantPropagation()
        env = ConstEnv()
        
        instr = Copy(dest=Var("x"), source=Const(42, "Int"))
        result = analysis.transfer(env, instr)
        
        assert result.get("x").get_constant() == 42

    def test_copy_variable_known(self):
        """y = x when x = 5 should set C(y) = 5."""
        analysis = ConstantPropagation()
        env = ConstEnv().set("x", ConstValue.constant(5))
        
        instr = Copy(dest=Var("y"), source=Var("x"))
        result = analysis.transfer(env, instr)
        
        assert result.get("y").get_constant() == 5

    def test_copy_variable_unknown(self):
        """y = x when x = ⊤ should set C(y) = ⊤."""
        analysis = ConstantPropagation()
        env = ConstEnv().set("x", ConstValue.top())
        
        instr = Copy(dest=Var("y"), source=Var("x"))
        result = analysis.transfer(env, instr)
        
        assert result.get("y").is_top()

    def test_binop_both_constants(self):
        """a + b when both are constants → constant result."""
        analysis = ConstantPropagation()
        env = ConstEnv()
        env = env.set("a", ConstValue.constant(2))
        env = env.set("b", ConstValue.constant(3))
        
        instr = BinaryOp(dest=Temp(0), op=BinOp.ADD, left=Var("a"), right=Var("b"))
        result = analysis.transfer(env, instr)
        
        assert result.get("t0").get_constant() == 5

    def test_binop_one_unknown(self):
        """a + b when a = ⊤ → ⊤."""
        analysis = ConstantPropagation()
        env = ConstEnv()
        env = env.set("a", ConstValue.top())
        env = env.set("b", ConstValue.constant(3))
        
        instr = BinaryOp(dest=Temp(0), op=BinOp.ADD, left=Var("a"), right=Var("b"))
        result = analysis.transfer(env, instr)
        
        assert result.get("t0").is_top()

    def test_binop_multiplication(self):
        """2 * 3 = 6."""
        analysis = ConstantPropagation()
        env = ConstEnv()
        
        instr = BinaryOp(
            dest=Temp(0),
            op=BinOp.MUL,
            left=Const(2, "Int"),
            right=Const(3, "Int"),
        )
        result = analysis.transfer(env, instr)
        
        assert result.get("t0").get_constant() == 6

    def test_binop_division(self):
        """10 / 2 = 5."""
        analysis = ConstantPropagation()
        env = ConstEnv()
        
        instr = BinaryOp(
            dest=Temp(0),
            op=BinOp.DIV,
            left=Const(10, "Int"),
            right=Const(2, "Int"),
        )
        result = analysis.transfer(env, instr)
        
        assert result.get("t0").get_constant() == 5

    def test_binop_comparison(self):
        """3 < 5 = true."""
        analysis = ConstantPropagation()
        env = ConstEnv()
        
        instr = BinaryOp(
            dest=Temp(0),
            op=BinOp.LT,
            left=Const(3, "Int"),
            right=Const(5, "Int"),
        )
        result = analysis.transfer(env, instr)
        
        assert result.get("t0").get_constant() is True

    def test_unaryop_negation(self):
        """~5 = -5."""
        analysis = ConstantPropagation()
        env = ConstEnv().set("x", ConstValue.constant(5))
        
        instr = UnaryOperation(dest=Temp(0), op=UnaryOp.NEG, operand=Var("x"))
        result = analysis.transfer(env, instr)
        
        assert result.get("t0").get_constant() == -5

    def test_unaryop_not(self):
        """not true = false."""
        analysis = ConstantPropagation()
        env = ConstEnv().set("b", ConstValue.constant(True))
        
        instr = UnaryOperation(dest=Temp(0), op=UnaryOp.NOT, operand=Var("b"))
        result = analysis.transfer(env, instr)
        
        assert result.get("t0").get_constant() is False


class TestConstantPropagationAnalysis:
    """Integration tests for constant propagation on CFGs."""

    def test_simple_straight_line(self):
        """
        a = 2
        b = 3
        c = a + b
        return c
        
        Should determine c = 5.
        """
        method = TACMethod(
            class_name="Test",
            method_name="simple",
            params=[],
            instructions=[
                Copy(dest=Var("a"), source=Const(2, "Int")),
                Copy(dest=Var("b"), source=Const(3, "Int")),
                BinaryOp(dest=Var("c"), op=BinOp.ADD, left=Var("a"), right=Var("b")),
                Return(Var("c")),
            ],
        )
        cfg = build_cfg(method)
        result, _ = run_constant_propagation(cfg, fold=False)
        
        # After all instructions, c should be 5
        block_out = result.block_out.get(0, ConstEnv())
        assert block_out.get("c").get_constant() == 5

    def test_parameter_is_unknown(self):
        """
        Parameters start as ⊤ (unknown).
        
        def foo(x):
            y = x + 1
            return y
        
        y should be ⊤.
        """
        method = TACMethod(
            class_name="Test",
            method_name="foo",
            params=["x"],
            instructions=[
                BinaryOp(dest=Var("y"), op=BinOp.ADD, left=Var("x"), right=Const(1, "Int")),
                Return(Var("y")),
            ],
        )
        cfg = build_cfg(method)
        result, _ = run_constant_propagation(cfg, params=["x"], fold=False)
        
        block_out = result.block_out.get(0, ConstEnv())
        # x is unknown, so y = x + 1 is unknown
        assert block_out.get("y").is_top()

    def test_if_else_same_value(self):
        """
        if cond goto L1
        x = 5
        goto L2
        L1:
        x = 5
        L2:
        return x
        
        x should be 5 at L2 (both paths assign same value).
        """
        method = TACMethod(
            class_name="Test",
            method_name="if_else_same",
            params=[],
            instructions=[
                CondJump(condition=Var("cond"), target=Label("L1")),
                Copy(dest=Var("x"), source=Const(5, "Int")),
                Jump(target=Label("L2")),
                LabelInstr(Label("L1")),
                Copy(dest=Var("x"), source=Const(5, "Int")),
                LabelInstr(Label("L2")),
                Return(Var("x")),
            ],
        )
        cfg = build_cfg(method)
        result, _ = run_constant_propagation(cfg, fold=False)
        
        # Find L2 block
        l2_block = cfg.get_block_by_label("L2")
        if l2_block:
            block_out = result.block_out.get(l2_block.id, ConstEnv())
            assert block_out.get("x").get_constant() == 5

    def test_if_else_different_values(self):
        """
        if cond goto L1
        x = 1
        goto L2
        L1:
        x = 2
        L2:
        return x
        
        x should be ⊤ at L2 (different values from each path).
        """
        method = TACMethod(
            class_name="Test",
            method_name="if_else_diff",
            params=[],
            instructions=[
                CondJump(condition=Var("cond"), target=Label("L1")),
                Copy(dest=Var("x"), source=Const(1, "Int")),
                Jump(target=Label("L2")),
                LabelInstr(Label("L1")),
                Copy(dest=Var("x"), source=Const(2, "Int")),
                LabelInstr(Label("L2")),
                Return(Var("x")),
            ],
        )
        cfg = build_cfg(method)
        result, _ = run_constant_propagation(cfg, fold=False)
        
        # Find L2 block
        l2_block = cfg.get_block_by_label("L2")
        if l2_block:
            block_out = result.block_out.get(l2_block.id, ConstEnv())
            # meet(1, 2) = ⊤
            assert block_out.get("x").is_top()


class TestConstantFolding:
    """Tests for constant folding transformation."""

    def test_fold_addition(self):
        """Replace t0 = 2 + 3 with t0 = 5."""
        method = TACMethod(
            class_name="Test",
            method_name="fold",
            params=[],
            instructions=[
                BinaryOp(dest=Temp(0), op=BinOp.ADD, left=Const(2, "Int"), right=Const(3, "Int")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        result, changes = run_constant_propagation(cfg, fold=True)
        
        assert changes >= 1
        # Check that the instruction was folded
        block = cfg.blocks[0]
        # First instruction should now be a copy
        first_instr = block.instructions[0]
        assert isinstance(first_instr, Copy)
        assert first_instr.source == Const(5, "Int")

    def test_propagate_and_fold(self):
        """
        a = 2
        b = 3
        c = a + b  →  c = 5
        """
        method = TACMethod(
            class_name="Test",
            method_name="prop_fold",
            params=[],
            instructions=[
                Copy(dest=Var("a"), source=Const(2, "Int")),
                Copy(dest=Var("b"), source=Const(3, "Int")),
                BinaryOp(dest=Var("c"), op=BinOp.ADD, left=Var("a"), right=Var("b")),
                Return(Var("c")),
            ],
        )
        cfg = build_cfg(method)
        result, changes = run_constant_propagation(cfg, fold=True)
        
        # The addition should have been folded
        assert changes >= 1

