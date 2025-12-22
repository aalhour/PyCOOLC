"""
Tests for Three-Address Code (TAC) representation.

These tests verify that TAC instructions correctly track their
definitions and uses, which is essential for data flow analysis.
"""

import pytest
from pycoolc.ir.tac import (
    # Operands
    Temp, Var, Const, Label,
    # Operators
    BinOp, UnaryOp,
    # Instructions
    BinaryOp, UnaryOperation, Copy,
    LabelInstr, Jump, CondJump, CondJumpNot,
    Param, Call, Return,
    New, Dispatch, StaticDispatch, IsVoid, GetAttr, SetAttr,
    Phi,
    # Program structures
    TACMethod, TACProgram, TempGenerator,
)


class TestOperands:
    """Tests for TAC operand types."""

    def test_temp_str(self):
        t = Temp(0)
        assert str(t) == "t0"
        
        t5 = Temp(5)
        assert str(t5) == "t5"

    def test_var_str(self):
        v = Var("x")
        assert str(v) == "x"
        
        self_var = Var("self")
        assert str(self_var) == "self"

    def test_const_int_str(self):
        c = Const(42, "Int")
        assert str(c) == "42"

    def test_const_bool_str(self):
        true_c = Const(True, "Bool")
        false_c = Const(False, "Bool")
        assert str(true_c) == "true"
        assert str(false_c) == "false"

    def test_const_string_str(self):
        c = Const("hello", "String")
        assert str(c) == '"hello"'
        
        # With escapes
        c2 = Const("line1\nline2", "String")
        assert "\\n" in str(c2)

    def test_label_str(self):
        lbl = Label("L0")
        assert str(lbl) == "L0"

    def test_operands_hashable(self):
        """Operands must be hashable for use in sets."""
        t = Temp(0)
        v = Var("x")
        c = Const(42, "Int")
        lbl = Label("L0")
        
        s = {t, v, c, lbl}
        assert len(s) == 4


class TestBinaryOpInstruction:
    """Tests for binary operation instructions."""

    def test_str(self):
        instr = BinaryOp(
            dest=Temp(0),
            op=BinOp.ADD,
            left=Var("a"),
            right=Var("b"),
        )
        assert str(instr) == "t0 = a + b"

    def test_defs(self):
        instr = BinaryOp(
            dest=Temp(0),
            op=BinOp.ADD,
            left=Var("a"),
            right=Var("b"),
        )
        assert instr.defs() == {Temp(0)}

    def test_uses_both_vars(self):
        instr = BinaryOp(
            dest=Temp(0),
            op=BinOp.ADD,
            left=Var("a"),
            right=Var("b"),
        )
        assert instr.uses() == {Var("a"), Var("b")}

    def test_uses_var_and_const(self):
        instr = BinaryOp(
            dest=Temp(0),
            op=BinOp.MUL,
            left=Var("x"),
            right=Const(2, "Int"),
        )
        # Constants don't count as uses
        assert instr.uses() == {Var("x")}

    def test_uses_both_consts(self):
        instr = BinaryOp(
            dest=Temp(0),
            op=BinOp.ADD,
            left=Const(1, "Int"),
            right=Const(2, "Int"),
        )
        assert instr.uses() == set()


class TestUnaryOpInstruction:
    """Tests for unary operation instructions."""

    def test_negation_str(self):
        instr = UnaryOperation(
            dest=Temp(0),
            op=UnaryOp.NEG,
            operand=Var("x"),
        )
        assert str(instr) == "t0 = ~ x"

    def test_not_str(self):
        instr = UnaryOperation(
            dest=Temp(0),
            op=UnaryOp.NOT,
            operand=Var("b"),
        )
        assert str(instr) == "t0 = not b"

    def test_defs(self):
        instr = UnaryOperation(
            dest=Temp(0),
            op=UnaryOp.NEG,
            operand=Var("x"),
        )
        assert instr.defs() == {Temp(0)}

    def test_uses(self):
        instr = UnaryOperation(
            dest=Temp(0),
            op=UnaryOp.NEG,
            operand=Var("x"),
        )
        assert instr.uses() == {Var("x")}


class TestCopyInstruction:
    """Tests for copy instructions."""

    def test_var_to_var(self):
        instr = Copy(dest=Var("y"), source=Var("x"))
        assert str(instr) == "y = x"
        assert instr.defs() == {Var("y")}
        assert instr.uses() == {Var("x")}

    def test_const_to_var(self):
        instr = Copy(dest=Var("x"), source=Const(42, "Int"))
        assert str(instr) == "x = 42"
        assert instr.defs() == {Var("x")}
        assert instr.uses() == set()

    def test_temp_to_temp(self):
        instr = Copy(dest=Temp(1), source=Temp(0))
        assert str(instr) == "t1 = t0"
        assert instr.defs() == {Temp(1)}
        assert instr.uses() == {Temp(0)}


class TestControlFlow:
    """Tests for control flow instructions."""

    def test_label(self):
        instr = LabelInstr(Label("loop_start"))
        assert str(instr) == "loop_start:"
        assert instr.is_label()
        assert not instr.is_jump()
        assert instr.defs() == set()
        assert instr.uses() == set()

    def test_jump(self):
        instr = Jump(Label("loop_start"))
        assert str(instr) == "goto loop_start"
        assert instr.is_jump()
        assert instr.jump_targets() == [Label("loop_start")]

    def test_cond_jump(self):
        instr = CondJump(condition=Var("cond"), target=Label("then"))
        assert str(instr) == "if cond goto then"
        assert instr.is_jump()
        assert instr.uses() == {Var("cond")}
        assert instr.jump_targets() == [Label("then")]

    def test_cond_jump_not(self):
        instr = CondJumpNot(condition=Var("cond"), target=Label("else"))
        assert str(instr) == "ifnot cond goto else"
        assert instr.is_jump()


class TestProcedureInstructions:
    """Tests for procedure-related instructions."""

    def test_param(self):
        instr = Param(Var("x"))
        assert str(instr) == "param x"
        assert instr.uses() == {Var("x")}

    def test_call_with_result(self):
        instr = Call(dest=Temp(0), target="foo", num_args=2)
        assert str(instr) == "t0 = call foo, 2"
        assert instr.defs() == {Temp(0)}

    def test_call_without_result(self):
        instr = Call(dest=None, target="print", num_args=1)
        assert str(instr) == "call print, 1"
        assert instr.defs() == set()

    def test_return_with_value(self):
        instr = Return(Temp(0))
        assert str(instr) == "return t0"
        assert instr.uses() == {Temp(0)}
        assert instr.is_jump()

    def test_return_void(self):
        instr = Return()
        assert str(instr) == "return"
        assert instr.uses() == set()


class TestCOOLSpecificInstructions:
    """Tests for COOL-specific instructions."""

    def test_new(self):
        instr = New(dest=Temp(0), type_name="Foo")
        assert str(instr) == "t0 = new Foo"
        assert instr.defs() == {Temp(0)}
        assert instr.uses() == set()

    def test_dispatch(self):
        instr = Dispatch(
            dest=Temp(0),
            obj=Var("self"),
            method="foo",
            num_args=2,
        )
        assert "self.foo" in str(instr)
        assert instr.defs() == {Temp(0)}
        assert instr.uses() == {Var("self")}

    def test_static_dispatch(self):
        instr = StaticDispatch(
            dest=Temp(0),
            obj=Var("self"),
            static_type="Parent",
            method="foo",
            num_args=1,
        )
        assert "@Parent" in str(instr)
        assert instr.defs() == {Temp(0)}

    def test_isvoid(self):
        instr = IsVoid(dest=Temp(0), operand=Var("x"))
        assert str(instr) == "t0 = isvoid x"
        assert instr.defs() == {Temp(0)}
        assert instr.uses() == {Var("x")}

    def test_get_attr(self):
        instr = GetAttr(dest=Temp(0), obj=Var("self"), attr="x")
        assert str(instr) == "t0 = self.x"
        assert instr.defs() == {Temp(0)}
        assert instr.uses() == {Var("self")}

    def test_set_attr(self):
        instr = SetAttr(obj=Var("self"), attr="x", value=Temp(0))
        assert str(instr) == "self.x = t0"
        assert instr.defs() == set()  # Modifies memory, not a register
        assert instr.uses() == {Var("self"), Temp(0)}


class TestPhiFunction:
    """Tests for SSA φ-functions."""

    def test_phi_str(self):
        instr = Phi(
            dest=Var("x3"),
            sources=[
                (Var("x1"), Label("then")),
                (Var("x2"), Label("else")),
            ],
        )
        assert "φ" in str(instr) or "phi" in str(instr).lower()
        assert "x1" in str(instr)
        assert "x2" in str(instr)

    def test_phi_defs(self):
        instr = Phi(
            dest=Var("x3"),
            sources=[
                (Var("x1"), Label("L1")),
                (Var("x2"), Label("L2")),
            ],
        )
        assert instr.defs() == {Var("x3")}

    def test_phi_uses(self):
        instr = Phi(
            dest=Var("x3"),
            sources=[
                (Var("x1"), Label("L1")),
                (Var("x2"), Label("L2")),
            ],
        )
        assert instr.uses() == {Var("x1"), Var("x2")}


class TestTACMethod:
    """Tests for TAC method representation."""

    def test_empty_method(self):
        method = TACMethod(
            class_name="Main",
            method_name="main",
            params=[],
        )
        assert "Main.main" in str(method)

    def test_method_with_instructions(self):
        method = TACMethod(
            class_name="Main",
            method_name="main",
            params=["x", "y"],
            instructions=[
                Copy(dest=Temp(0), source=Var("x")),
                BinaryOp(dest=Temp(1), op=BinOp.ADD, left=Temp(0), right=Var("y")),
                Return(Temp(1)),
            ],
        )
        output = str(method)
        assert "x, y" in output
        assert "t0 = x" in output
        assert "return t1" in output

    def test_iterate_instructions(self):
        method = TACMethod(
            class_name="Main",
            method_name="main",
            params=[],
            instructions=[
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Return(Temp(0)),
            ],
        )
        instrs = list(method)
        assert len(instrs) == 2


class TestTempGenerator:
    """Tests for temporary/label generation."""

    def test_new_temp(self):
        gen = TempGenerator()
        t0 = gen.new_temp()
        t1 = gen.new_temp()
        t2 = gen.new_temp()
        
        assert t0.index == 0
        assert t1.index == 1
        assert t2.index == 2

    def test_new_label(self):
        from pycoolc.ir.tac import LabelGenerator
        gen = LabelGenerator()
        l0 = gen.new_label("if")
        l1 = gen.new_label("if")
        
        assert l0.name == "if_0"
        assert l1.name == "if_1"

    def test_reset(self):
        gen = TempGenerator()
        gen.new_temp()
        gen.new_temp()
        gen.reset()
        
        t = gen.new_temp()
        assert t.index == 0
    
    def test_label_generator_reset(self):
        from pycoolc.ir.tac import LabelGenerator
        gen = LabelGenerator()
        gen.new_label()
        gen.new_label()
        gen.reset()
        
        lbl = gen.new_label("test")
        assert lbl.name == "test_0"
    
    def test_label_generator_default_prefix(self):
        from pycoolc.ir.tac import LabelGenerator
        gen = LabelGenerator()
        lbl = gen.next()
        
        assert lbl.name == "L_0"


class TestTACProgram:
    """Tests for TACProgram."""
    
    def test_str_empty(self):
        from pycoolc.ir.tac import TACProgram
        prog = TACProgram()
        s = str(prog)
        
        assert "TAC Program" in s
    
    def test_str_with_constants(self):
        from pycoolc.ir.tac import TACProgram
        prog = TACProgram(
            string_constants={"hello": "str_0", "world\n": "str_1"}
        )
        s = str(prog)
        
        assert "String Constants:" in s
        assert "str_0" in s
        assert "hello" in s
    
    def test_str_with_methods(self):
        from pycoolc.ir.tac import TACProgram
        prog = TACProgram(
            methods=[
                TACMethod(
                    class_name="Main",
                    method_name="main",
                    params=[],
                    instructions=[Return(Const(0, "Int"))],
                )
            ]
        )
        s = str(prog)
        
        assert "Main.main" in s
    
    def test_get_method_found(self):
        from pycoolc.ir.tac import TACProgram
        method = TACMethod(
            class_name="Main",
            method_name="main",
            params=[],
            instructions=[],
        )
        prog = TACProgram(methods=[method])
        
        found = prog.get_method("Main", "main")
        assert found is method
    
    def test_get_method_not_found(self):
        from pycoolc.ir.tac import TACProgram
        prog = TACProgram()
        
        found = prog.get_method("Main", "main")
        assert found is None


class TestComment:
    """Tests for Comment instruction."""
    
    def test_str(self):
        from pycoolc.ir.tac import Comment
        c = Comment("This is a comment")
        assert str(c) == "# This is a comment"
    
    def test_defs_empty(self):
        from pycoolc.ir.tac import Comment
        c = Comment("Test")
        assert c.defs() == set()
    
    def test_uses_empty(self):
        from pycoolc.ir.tac import Comment
        c = Comment("Test")
        assert c.uses() == set()


class TestInstructionMethods:
    """Tests for Instruction base class methods."""
    
    def test_is_jump_default_false(self):
        # Regular instruction should return False
        instr = Copy(dest=Temp(0), source=Const(1, "Int"))
        assert not instr.is_jump()
    
    def test_is_label_default_false(self):
        # Regular instruction should return False
        instr = Copy(dest=Temp(0), source=Const(1, "Int"))
        assert not instr.is_label()
    
    def test_jump_targets_default_empty(self):
        # Regular instruction has no jump targets
        instr = Copy(dest=Temp(0), source=Const(1, "Int"))
        assert instr.jump_targets() == []
    
    def test_jump_is_jump_true(self):
        # Jump instruction should return True for is_jump
        instr = Jump(target=Label("L0"))
        assert instr.is_jump()
    
    def test_jump_targets_returns_target(self):
        # Jump instruction returns its target
        instr = Jump(target=Label("L0"))
        targets = instr.jump_targets()
        assert Label("L0") in targets
    
    def test_label_instr_is_label_true(self):
        # LabelInstr should return True for is_label
        instr = LabelInstr(Label("L0"))
        assert instr.is_label()


class TestAdditionalInstructions:
    """Additional tests for instruction coverage."""
    
    def test_dispatch_with_none_dest(self):
        instr = Dispatch(
            dest=None,
            obj=Var("self"),
            method="foo",
            num_args=0,
        )
        s = str(instr)
        assert "self.foo" in s
        assert instr.defs() == set()
    
    def test_static_dispatch_with_none_dest(self):
        instr = StaticDispatch(
            dest=None,
            obj=Var("self"),
            static_type="IO",
            method="out_string",
            num_args=1,
        )
        s = str(instr)
        assert "self@IO.out_string" in s
        assert instr.defs() == set()
    
    def test_call_with_none_dest(self):
        instr = Call(
            dest=None,
            target="func",
            num_args=2,
        )
        s = str(instr)
        assert "call func" in s
        assert instr.defs() == set()
    
    def test_dispatch_uses(self):
        instr = Dispatch(
            dest=Temp(0),
            obj=Var("obj"),
            method="foo",
            num_args=1,
        )
        uses = instr.uses()
        assert Var("obj") in uses
    
    def test_static_dispatch_uses(self):
        instr = StaticDispatch(
            dest=Temp(0),
            obj=Var("obj"),
            static_type="Base",
            method="foo",
            num_args=1,
        )
        uses = instr.uses()
        assert Var("obj") in uses
    
    def test_get_attr_uses(self):
        instr = GetAttr(
            dest=Temp(0),
            obj=Var("self"),
            attr="x",
        )
        uses = instr.uses()
        assert Var("self") in uses
    
    def test_set_attr_uses(self):
        instr = SetAttr(
            obj=Var("self"),
            attr="x",
            value=Temp(0),
        )
        uses = instr.uses()
        assert Var("self") in uses
        assert Temp(0) in uses
    
    def test_cond_jump_not_is_jump(self):
        instr = CondJumpNot(
            condition=Var("cond"),
            target=Label("L0"),
        )
        assert instr.is_jump()
        assert Label("L0") in instr.jump_targets()

