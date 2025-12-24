"""
Tests for constant propagation analysis.

These tests verify the constant propagation algorithm from the user's notes:
- Transfer functions for different statement types
- Meet operation at join points
- Constant folding transformation
"""

from pycoolc.ir.cfg import build_cfg
from pycoolc.ir.tac import (
    BinaryOp,
    BinOp,
    Call,
    CondJump,
    Const,
    Copy,
    Dispatch,
    GetAttr,
    IsVoid,
    Jump,
    Label,
    LabelInstr,
    New,
    Phi,
    Return,
    StaticDispatch,
    TACMethod,
    Temp,
    UnaryOp,
    UnaryOperation,
    Var,
)
from pycoolc.optimization.constant_prop import (
    ConstantPropagation,
    ConstEnv,
    _eval_const_binop,
    _eval_const_unaryop,
    _fold_operand,
    _type_of,
    run_constant_propagation,
)
from pycoolc.optimization.dataflow import ConstValue


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

    def test_eq_with_non_env(self):
        """Equality with non-ConstEnv returns False."""
        env = ConstEnv()
        assert env != "not an env"
        assert env != 42

    def test_eq_different_values(self):
        """Environments with different values are not equal."""
        env1 = ConstEnv().set("x", ConstValue.constant(1))
        env2 = ConstEnv().set("x", ConstValue.constant(2))
        assert env1 != env2

    def test_hash(self):
        """Test that environments can be hashed."""
        env = ConstEnv().set("x", ConstValue.constant(1))
        h = hash(env)
        assert isinstance(h, int)

    def test_str_empty(self):
        """String representation of empty env."""
        env = ConstEnv()
        assert str(env) == "{}"

    def test_str_with_values(self):
        """String representation with values."""
        env = ConstEnv().set("x", ConstValue.constant(1))
        s = str(env)
        assert "x:" in s
        assert "{" in s

    def test_copy(self):
        """Test copy method."""
        env = ConstEnv().set("x", ConstValue.constant(1))
        copy = env.copy()
        assert copy.get("x").get_constant() == 1
        # Modify original shouldn't affect copy
        env.values["y"] = ConstValue.constant(2)
        assert copy.get("y").is_bottom()


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

    def test_call_returns_unknown(self):
        """Function calls return unknown values."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = Call(dest=Temp(0), target="f", num_args=0)
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_top()

    def test_dispatch_returns_unknown(self):
        """Method dispatch returns unknown values."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = Dispatch(dest=Temp(0), obj=Var("self"), method="foo", num_args=0)
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_top()

    def test_static_dispatch_returns_unknown(self):
        """Static dispatch returns unknown values."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = StaticDispatch(
            dest=Temp(0), obj=Var("self"), static_type="A", method="foo", num_args=0
        )
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_top()

    def test_new_returns_unknown(self):
        """New object is not a constant."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = New(dest=Temp(0), type_name="Foo")
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_top()

    def test_isvoid_returns_unknown(self):
        """isvoid result is treated as unknown."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = IsVoid(dest=Temp(0), operand=Var("x"))
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_top()

    def test_getattr_returns_unknown(self):
        """Attribute loads are unknown."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = GetAttr(dest=Temp(0), obj=Var("self"), attr="x")
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_top()

    def test_phi_meet_values(self):
        """Phi function meets source values."""
        analysis = ConstantPropagation()
        env = ConstEnv()
        env = env.set("x", ConstValue.constant(5))
        env = env.set("y", ConstValue.constant(5))

        instr = Phi(dest=Temp(0), sources=[(Var("x"), Label("L1")), (Var("y"), Label("L2"))])
        result = analysis.transfer(env, instr)

        assert result.get("t0").get_constant() == 5

    def test_phi_different_values_gives_top(self):
        """Phi with different values gives top."""
        analysis = ConstantPropagation()
        env = ConstEnv()
        env = env.set("x", ConstValue.constant(1))
        env = env.set("y", ConstValue.constant(2))

        instr = Phi(dest=Temp(0), sources=[(Var("x"), Label("L1")), (Var("y"), Label("L2"))])
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_top()

    def test_phi_empty_sources(self):
        """Phi with no sources gives bottom."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = Phi(dest=Temp(0), sources=[])
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_bottom()

    def test_binop_bottom_gives_bottom(self):
        """Operations on bottom values give bottom."""
        analysis = ConstantPropagation()
        env = ConstEnv()  # x is bottom by default

        instr = BinaryOp(dest=Temp(0), op=BinOp.ADD, left=Var("x"), right=Const(1, "Int"))
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_bottom()

    def test_binop_subtraction(self):
        """5 - 3 = 2."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = BinaryOp(dest=Temp(0), op=BinOp.SUB, left=Const(5, "Int"), right=Const(3, "Int"))
        result = analysis.transfer(env, instr)

        assert result.get("t0").get_constant() == 2

    def test_binop_le(self):
        """3 <= 5 = true."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = BinaryOp(dest=Temp(0), op=BinOp.LE, left=Const(3, "Int"), right=Const(5, "Int"))
        result = analysis.transfer(env, instr)

        assert result.get("t0").get_constant() is True

    def test_binop_eq(self):
        """3 = 3 = true."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = BinaryOp(dest=Temp(0), op=BinOp.EQ, left=Const(3, "Int"), right=Const(3, "Int"))
        result = analysis.transfer(env, instr)

        assert result.get("t0").get_constant() is True

    def test_binop_string_eq(self):
        """String equality."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = BinaryOp(
            dest=Temp(0), op=BinOp.EQ, left=Const("a", "String"), right=Const("a", "String")
        )
        result = analysis.transfer(env, instr)

        assert result.get("t0").get_constant() is True

    def test_binop_div_by_zero(self):
        """Division by zero gives top."""
        analysis = ConstantPropagation()
        env = ConstEnv()

        instr = BinaryOp(dest=Temp(0), op=BinOp.DIV, left=Const(5, "Int"), right=Const(0, "Int"))
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_top()

    def test_unaryop_neg_non_int(self):
        """Negation of non-int gives top."""
        analysis = ConstantPropagation()
        env = ConstEnv().set("x", ConstValue.constant("hello"))

        instr = UnaryOperation(dest=Temp(0), op=UnaryOp.NEG, operand=Var("x"))
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_top()

    def test_unaryop_not_non_bool(self):
        """Not of non-bool gives top."""
        analysis = ConstantPropagation()
        env = ConstEnv().set("x", ConstValue.constant(42))

        instr = UnaryOperation(dest=Temp(0), op=UnaryOp.NOT, operand=Var("x"))
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_top()

    def test_unaryop_bottom(self):
        """Unary op on bottom gives bottom."""
        analysis = ConstantPropagation()
        env = ConstEnv()  # x is bottom

        instr = UnaryOperation(dest=Temp(0), op=UnaryOp.NEG, operand=Var("x"))
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_bottom()

    def test_unaryop_top(self):
        """Unary op on top gives top."""
        analysis = ConstantPropagation()
        env = ConstEnv().set("x", ConstValue.top())

        instr = UnaryOperation(dest=Temp(0), op=UnaryOp.NEG, operand=Var("x"))
        result = analysis.transfer(env, instr)

        assert result.get("t0").is_top()

    def test_instruction_without_dest(self):
        """Instructions without dest don't change env."""
        analysis = ConstantPropagation()
        env = ConstEnv().set("x", ConstValue.constant(1))

        # Jump doesn't define a variable
        instr = Jump(target=Label("L1"))
        result = analysis.transfer(env, instr)

        assert result.get("x").get_constant() == 1

    def test_meet_empty_list(self):
        """Meeting empty list returns empty env."""
        analysis = ConstantPropagation()
        result = analysis.meet([])
        assert result.get("x").is_bottom()


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
        _result, changes = run_constant_propagation(cfg, fold=True)

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
        _result, changes = run_constant_propagation(cfg, fold=True)

        # The addition should have been folded
        assert changes >= 1

    def test_fold_unary_negation(self):
        """Fold ~5 to -5."""
        method = TACMethod(
            class_name="Test",
            method_name="fold_neg",
            params=[],
            instructions=[
                Copy(dest=Var("x"), source=Const(5, "Int")),
                UnaryOperation(dest=Temp(0), op=UnaryOp.NEG, operand=Var("x")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        _result, changes = run_constant_propagation(cfg, fold=True)

        assert changes >= 1

    def test_fold_unary_not(self):
        """Fold not true to false."""
        method = TACMethod(
            class_name="Test",
            method_name="fold_not",
            params=[],
            instructions=[
                Copy(dest=Var("b"), source=Const(True, "Bool")),
                UnaryOperation(dest=Temp(0), op=UnaryOp.NOT, operand=Var("b")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        _result, changes = run_constant_propagation(cfg, fold=True)

        assert changes >= 1

    def test_fold_copy(self):
        """Fold copy of known variable."""
        method = TACMethod(
            class_name="Test",
            method_name="fold_copy",
            params=[],
            instructions=[
                Copy(dest=Var("x"), source=Const(42, "Int")),
                Copy(dest=Var("y"), source=Var("x")),
                Return(Var("y")),
            ],
        )
        cfg = build_cfg(method)
        _result, changes = run_constant_propagation(cfg, fold=True)

        # The copy y = x should be folded to y = 42
        assert changes >= 1

    def test_partial_fold_binop(self):
        """Fold one operand but not both."""
        method = TACMethod(
            class_name="Test",
            method_name="partial",
            params=["p"],
            instructions=[
                Copy(dest=Var("x"), source=Const(5, "Int")),
                BinaryOp(dest=Temp(0), op=BinOp.ADD, left=Var("x"), right=Var("p")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        _result, changes = run_constant_propagation(cfg, params=["p"], fold=True)

        # x should be folded to 5 in the binop
        assert changes >= 1


class TestFoldHelpers:
    """Tests for folding helper functions."""

    def test_fold_operand_temp(self):
        """Fold temp with known constant."""
        env = ConstEnv().set("t0", ConstValue.constant(42))
        result = _fold_operand(Temp(0), env)
        assert isinstance(result, Const)
        assert result.value == 42

    def test_fold_operand_var(self):
        """Fold var with known constant."""
        env = ConstEnv().set("x", ConstValue.constant(10))
        result = _fold_operand(Var("x"), env)
        assert isinstance(result, Const)
        assert result.value == 10

    def test_fold_operand_unknown(self):
        """Unknown variable not folded."""
        env = ConstEnv().set("x", ConstValue.top())
        result = _fold_operand(Var("x"), env)
        assert isinstance(result, Var)

    def test_eval_const_binop_sub(self):
        """Subtraction."""
        assert _eval_const_binop(BinOp.SUB, 5, 3) == 2

    def test_eval_const_binop_mul(self):
        """Multiplication."""
        assert _eval_const_binop(BinOp.MUL, 2, 3) == 6

    def test_eval_const_binop_div(self):
        """Division."""
        assert _eval_const_binop(BinOp.DIV, 10, 2) == 5

    def test_eval_const_binop_div_zero(self):
        """Division by zero returns None."""
        assert _eval_const_binop(BinOp.DIV, 10, 0) is None

    def test_eval_const_binop_lt(self):
        """Less than."""
        assert _eval_const_binop(BinOp.LT, 3, 5) is True

    def test_eval_const_binop_le(self):
        """Less than or equal."""
        assert _eval_const_binop(BinOp.LE, 5, 5) is True

    def test_eval_const_binop_eq(self):
        """Equality."""
        assert _eval_const_binop(BinOp.EQ, 3, 3) is True

    def test_eval_const_binop_string_eq(self):
        """String equality."""
        assert _eval_const_binop(BinOp.EQ, "a", "a") is True

    def test_eval_const_binop_non_int_other_op(self):
        """Non-int with non-EQ op returns None."""
        assert _eval_const_binop(BinOp.ADD, "a", "b") is None

    def test_eval_const_unaryop_neg(self):
        """Negation."""
        assert _eval_const_unaryop(UnaryOp.NEG, 5) == -5

    def test_eval_const_unaryop_not(self):
        """Not."""
        assert _eval_const_unaryop(UnaryOp.NOT, True) is False

    def test_eval_const_unaryop_neg_non_int(self):
        """Negation of non-int returns None."""
        assert _eval_const_unaryop(UnaryOp.NEG, "hello") is None

    def test_eval_const_unaryop_not_non_bool(self):
        """Not of non-bool returns None."""
        assert _eval_const_unaryop(UnaryOp.NOT, 42) is None

    def test_type_of_bool(self):
        """Bool type."""
        assert _type_of(True) == "Bool"

    def test_type_of_int(self):
        """Int type."""
        assert _type_of(42) == "Int"

    def test_type_of_string(self):
        """String type."""
        assert _type_of("hello") == "String"
