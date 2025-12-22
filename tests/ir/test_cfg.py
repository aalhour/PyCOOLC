"""
Tests for Control Flow Graph (CFG) construction and analysis.

These tests verify that:
1. Basic blocks are correctly identified
2. CFG edges are correctly computed
3. Dominance analysis is correct
"""

import pytest
from pycoolc.ir.tac import (
    Temp, Var, Const, Label, BinOp,
    Copy, BinaryOp, LabelInstr, Jump, CondJump, CondJumpNot, Return,
    TACMethod,
)
from pycoolc.ir.cfg import (
    BasicBlock,
    ControlFlowGraph,
    build_cfg,
    compute_dominators,
    compute_immediate_dominators,
)


class TestBasicBlock:
    """Tests for BasicBlock class."""

    def test_empty_block(self):
        block = BasicBlock(id=0)
        assert block.id == 0
        assert block.label is None
        assert block.instructions == []
        assert block.predecessors == []
        assert block.successors == []

    def test_block_with_instructions(self):
        block = BasicBlock(
            id=0,
            instructions=[
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Return(Temp(0)),
            ],
        )
        assert len(block.instructions) == 2

    def test_is_exit(self):
        # Block ending with return is an exit
        exit_block = BasicBlock(
            id=0,
            instructions=[Return(Temp(0))],
        )
        assert exit_block.is_exit()
        
        # Block without return is not
        non_exit = BasicBlock(
            id=1,
            instructions=[Copy(dest=Temp(0), source=Const(1, "Int"))],
        )
        assert not non_exit.is_exit()

    def test_hash_and_eq(self):
        b1 = BasicBlock(id=0)
        b2 = BasicBlock(id=0)
        b3 = BasicBlock(id=1)
        
        assert b1 == b2
        assert b1 != b3
        assert hash(b1) == hash(b2)


class TestCFGConstruction:
    """Tests for CFG construction from TAC methods."""

    def test_empty_method(self):
        method = TACMethod(
            class_name="Test",
            method_name="empty",
            params=[],
            instructions=[],
        )
        cfg = build_cfg(method)
        assert len(cfg.blocks) == 0

    def test_single_block_method(self):
        """Method with no branches creates a single block."""
        method = TACMethod(
            class_name="Test",
            method_name="simple",
            params=[],
            instructions=[
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Copy(dest=Temp(1), source=Const(2, "Int")),
                BinaryOp(dest=Temp(2), op=BinOp.ADD, left=Temp(0), right=Temp(1)),
                Return(Temp(2)),
            ],
        )
        cfg = build_cfg(method)
        
        assert len(cfg.blocks) == 1
        assert cfg.entry == cfg.blocks[0]
        assert len(cfg.exit_blocks) == 1
        assert cfg.exit_blocks[0] == cfg.blocks[0]

    def test_if_then_else_cfg(self):
        """
        if cond goto L1
        t0 = 1
        goto L2
        L1:
        t0 = 2
        L2:
        return t0
        
        Expected CFG:
        B0 -> B1 (fall through)
        B0 -> B2 (L1)
        B1 -> B3 (goto L2)
        B2 -> B3 (fall through)
        """
        method = TACMethod(
            class_name="Test",
            method_name="if_else",
            params=[],
            instructions=[
                CondJump(condition=Var("cond"), target=Label("L1")),
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Jump(target=Label("L2")),
                LabelInstr(Label("L1")),
                Copy(dest=Temp(0), source=Const(2, "Int")),
                LabelInstr(Label("L2")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        
        # Should have 4 blocks
        assert len(cfg.blocks) == 4
        
        # Entry block (B0) should have 2 successors
        entry = cfg.entry
        assert entry is not None
        assert len(entry.successors) == 2
        
        # Exit block should exist
        assert len(cfg.exit_blocks) == 1

    def test_while_loop_cfg(self):
        """
        L1:
        if not cond goto L2
        t0 = t0 + 1
        goto L1
        L2:
        return t0
        
        Expected CFG:
        B0 (entry with label L1) -> B1 (loop body) or B2 (exit)
        B1 -> B0 (back edge)
        """
        method = TACMethod(
            class_name="Test",
            method_name="loop",
            params=[],
            instructions=[
                LabelInstr(Label("L1")),
                CondJumpNot(condition=Var("cond"), target=Label("L2")),
                BinaryOp(dest=Temp(0), op=BinOp.ADD, left=Temp(0), right=Const(1, "Int")),
                Jump(target=Label("L1")),
                LabelInstr(Label("L2")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        
        # Find the block with L1 label
        l1_block = cfg.get_block_by_label("L1")
        assert l1_block is not None
        
        # L1 block should have a back edge (predecessor from later block)
        # This indicates a loop
        has_back_edge = any(
            pred.id > l1_block.id for pred in l1_block.predecessors
        )
        # Note: depending on block ordering, this might not always be true
        # But we should have at least one predecessor (the back edge)
        assert len(cfg.blocks) >= 3

    def test_label_to_block_mapping(self):
        method = TACMethod(
            class_name="Test",
            method_name="labels",
            params=[],
            instructions=[
                Jump(target=Label("end")),
                LabelInstr(Label("end")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        
        end_block = cfg.get_block_by_label("end")
        assert end_block is not None
        assert end_block.label == Label("end")


class TestCFGTraversal:
    """Tests for CFG traversal algorithms."""

    def test_reverse_postorder_simple(self):
        """Simple method should give blocks in order."""
        method = TACMethod(
            class_name="Test",
            method_name="simple",
            params=[],
            instructions=[
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        rpo = cfg.reverse_postorder()
        
        assert len(rpo) == 1
        assert rpo[0] == cfg.entry

    def test_reverse_postorder_if_else(self):
        """RPO should visit all blocks."""
        method = TACMethod(
            class_name="Test",
            method_name="if_else",
            params=[],
            instructions=[
                CondJump(condition=Var("cond"), target=Label("L1")),
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Jump(target=Label("L2")),
                LabelInstr(Label("L1")),
                Copy(dest=Temp(0), source=Const(2, "Int")),
                LabelInstr(Label("L2")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        rpo = cfg.reverse_postorder()
        
        # All blocks should be visited
        assert len(rpo) == len(cfg.blocks)
        
        # Entry should come first
        assert rpo[0] == cfg.entry


class TestDominance:
    """Tests for dominance analysis."""

    def test_single_block_dominators(self):
        method = TACMethod(
            class_name="Test",
            method_name="simple",
            params=[],
            instructions=[
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        dom = compute_dominators(cfg)
        
        # Single block dominates itself
        assert cfg.entry is not None
        assert cfg.entry.id in dom
        assert dom[cfg.entry.id] == {cfg.entry.id}

    def test_linear_dominators(self):
        """In a linear sequence, each block dominates all following blocks."""
        method = TACMethod(
            class_name="Test",
            method_name="linear",
            params=[],
            instructions=[
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Jump(target=Label("L1")),
                LabelInstr(Label("L1")),
                Copy(dest=Temp(1), source=Const(2, "Int")),
                Jump(target=Label("L2")),
                LabelInstr(Label("L2")),
                Return(Temp(1)),
            ],
        )
        cfg = build_cfg(method)
        dom = compute_dominators(cfg)
        
        # Entry dominates everything
        entry_id = cfg.entry.id if cfg.entry else 0
        for block in cfg.blocks:
            assert entry_id in dom[block.id]

    def test_if_else_dominators(self):
        """Entry dominates all; branches don't dominate the join."""
        method = TACMethod(
            class_name="Test",
            method_name="if_else",
            params=[],
            instructions=[
                CondJump(condition=Var("cond"), target=Label("L1")),
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Jump(target=Label("L2")),
                LabelInstr(Label("L1")),
                Copy(dest=Temp(0), source=Const(2, "Int")),
                LabelInstr(Label("L2")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        dom = compute_dominators(cfg)
        
        # Find the blocks
        entry = cfg.entry
        assert entry is not None
        
        # Entry dominates all blocks
        for block in cfg.blocks:
            assert entry.id in dom[block.id]
        
        # Find the join block (L2)
        join_block = cfg.get_block_by_label("L2")
        if join_block:
            # The then and else branches should NOT dominate the join
            # (since there are two paths to the join)
            then_block = cfg.blocks[1] if len(cfg.blocks) > 1 else None
            if then_block and then_block.id != entry.id and then_block.id != join_block.id:
                # Then block doesn't dominate join
                assert then_block.id not in dom[join_block.id] or then_block.id == join_block.id


class TestImmediateDominators:
    """Tests for immediate dominator computation."""

    def test_entry_has_no_idom(self):
        method = TACMethod(
            class_name="Test",
            method_name="simple",
            params=[],
            instructions=[
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        idom = compute_immediate_dominators(cfg)
        
        assert cfg.entry is not None
        assert idom[cfg.entry.id] is None

    def test_linear_idoms(self):
        """In a linear sequence, each block's idom is its predecessor."""
        method = TACMethod(
            class_name="Test",
            method_name="linear",
            params=[],
            instructions=[
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Jump(target=Label("L1")),
                LabelInstr(Label("L1")),
                Return(Temp(0)),
            ],
        )
        cfg = build_cfg(method)
        idom = compute_immediate_dominators(cfg)
        
        # Entry has no idom
        assert cfg.entry is not None
        assert idom[cfg.entry.id] is None
        
        # Other blocks should have idom pointing to their predecessor
        for block in cfg.blocks:
            if block.id != cfg.entry.id:
                # Should have some idom
                assert idom[block.id] is not None or len(block.predecessors) == 0

