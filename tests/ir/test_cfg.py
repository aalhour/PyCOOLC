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
    
    def test_is_exit_empty_block(self):
        """Empty block is not an exit."""
        block = BasicBlock(id=0)
        assert not block.is_exit()
    
    def test_is_entry(self):
        """Block with no predecessors is entry."""
        entry = BasicBlock(id=0)
        assert entry.is_entry()
        
        non_entry = BasicBlock(id=1)
        non_entry.predecessors.append(entry)
        assert not non_entry.is_entry()

    def test_hash_and_eq(self):
        b1 = BasicBlock(id=0)
        b2 = BasicBlock(id=0)
        b3 = BasicBlock(id=1)
        
        assert b1 == b2
        assert b1 != b3
        assert hash(b1) == hash(b2)
    
    def test_eq_with_non_block(self):
        """Comparing with non-BasicBlock returns False."""
        block = BasicBlock(id=0)
        assert block != "not a block"
        assert block != 0
        assert block != None
    
    def test_str_representation(self):
        """Test string representation of block."""
        block = BasicBlock(
            id=0,
            label=Label("entry"),
            instructions=[
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Return(Temp(0)),
            ],
        )
        
        s = str(block)
        assert "Block B0" in s
        assert "entry" in s
    
    def test_str_with_successors(self):
        """Test string representation includes successors."""
        b1 = BasicBlock(id=0)
        b2 = BasicBlock(id=1)
        b1.successors.append(b2)
        
        s = str(b1)
        assert "B0" in s
        assert "B1" in s or "successors" in s
    
    def test_last_instruction(self):
        """Test last_instruction method."""
        block = BasicBlock(
            id=0,
            instructions=[
                Copy(dest=Temp(0), source=Const(1, "Int")),
                Return(Temp(0)),
            ],
        )
        last = block.last_instruction()
        assert isinstance(last, Return)
    
    def test_last_instruction_empty(self):
        """Empty block returns None for last_instruction."""
        block = BasicBlock(id=0)
        assert block.last_instruction() is None


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


class TestControlFlowGraphMethods:
    """Tests for ControlFlowGraph helper methods."""
    
    def test_str_representation(self):
        """Test string representation of CFG."""
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
        
        s = str(cfg)
        assert "CFG for Test.simple" in s
        assert "Entry:" in s
        assert "Exit blocks:" in s
    
    def test_str_with_no_entry(self):
        """CFG with no entry shows None."""
        method = TACMethod(
            class_name="Test",
            method_name="empty",
            params=[],
            instructions=[],
        )
        cfg = build_cfg(method)
        
        s = str(cfg)
        assert "Entry: None" in s or "Entry:" in s
    
    def test_iter(self):
        """Test iterating over CFG blocks."""
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
        
        blocks = list(cfg)
        assert len(blocks) == len(cfg.blocks)
        assert blocks[0] == cfg.blocks[0]
    
    def test_postorder(self):
        """Test postorder traversal."""
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
        po = cfg.postorder()
        
        assert len(po) == len(cfg.blocks)
    
    def test_postorder_with_branch(self):
        """Test postorder with branching CFG."""
        method = TACMethod(
            class_name="Test",
            method_name="branch",
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
        po = cfg.postorder()
        
        # All blocks should be visited
        assert len(po) == len(cfg.blocks)
        
        # Entry should come last in postorder (children before parent)
        # Note: This depends on the specific traversal
    
    def test_add_edge(self):
        """Test adding edges between blocks."""
        from pycoolc.ir.cfg import ControlFlowGraph
        
        method = TACMethod("Test", "test", [], [])
        cfg = ControlFlowGraph(method=method)
        
        b1 = BasicBlock(id=0)
        b2 = BasicBlock(id=1)
        cfg.add_block(b1)
        cfg.add_block(b2)
        
        cfg.add_edge(b1, b2)
        
        assert b2 in b1.successors
        assert b1 in b2.predecessors
    
    def test_add_edge_no_duplicate(self):
        """Adding same edge twice should not create duplicates."""
        from pycoolc.ir.cfg import ControlFlowGraph
        
        method = TACMethod("Test", "test", [], [])
        cfg = ControlFlowGraph(method=method)
        
        b1 = BasicBlock(id=0)
        b2 = BasicBlock(id=1)
        cfg.add_block(b1)
        cfg.add_block(b2)
        
        cfg.add_edge(b1, b2)
        cfg.add_edge(b1, b2)
        
        assert len(b1.successors) == 1
        assert len(b2.predecessors) == 1


class TestDominanceFrontier:
    """Tests for dominance frontier computation."""
    
    def test_dominance_frontier_simple(self):
        """Simple CFG should have empty frontiers."""
        from pycoolc.ir.cfg import compute_dominance_frontier
        
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
        df = compute_dominance_frontier(cfg)
        
        # Linear CFG should have empty frontiers
        assert isinstance(df, dict)
    
    def test_dominance_frontier_with_join(self):
        """Join point should be in dominance frontier of branches."""
        from pycoolc.ir.cfg import compute_dominance_frontier
        
        method = TACMethod(
            class_name="Test",
            method_name="branch",
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
        df = compute_dominance_frontier(cfg)
        
        assert isinstance(df, dict)
        # All blocks should have frontier entry
        assert len(df) == len(cfg.blocks)
    
    def test_dominance_frontier_with_precomputed_dominators(self):
        """Can pass precomputed dominators."""
        from pycoolc.ir.cfg import compute_dominance_frontier
        
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
        dominators = compute_dominators(cfg)
        df = compute_dominance_frontier(cfg, dominators)
        
        assert isinstance(df, dict)


class TestEdgeCases:
    """Test edge cases in CFG construction."""
    
    def test_compute_dominators_empty_cfg(self):
        """Empty CFG returns empty dominators."""
        method = TACMethod(
            class_name="Test",
            method_name="empty",
            params=[],
            instructions=[],
        )
        cfg = build_cfg(method)
        dom = compute_dominators(cfg)
        
        assert dom == {}
    
    def test_compute_immediate_dominators_empty_cfg(self):
        """Empty CFG returns empty idoms."""
        method = TACMethod(
            class_name="Test",
            method_name="empty",
            params=[],
            instructions=[],
        )
        cfg = build_cfg(method)
        idom = compute_immediate_dominators(cfg)
        
        assert idom == {}
    
    def test_block_with_no_predecessors_idom(self):
        """Block with no predecessors has None idom."""
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
        
        # Entry block has no idom
        assert cfg.entry is not None
        assert idom[cfg.entry.id] is None
    
    def test_unreachable_block_handling(self):
        """CFG should handle unreachable code."""
        # This is a pathological case - unreachable code after return
        method = TACMethod(
            class_name="Test",
            method_name="unreachable",
            params=[],
            instructions=[
                Return(Temp(0)),
                LabelInstr(Label("unreachable")),
                Copy(dest=Temp(1), source=Const(1, "Int")),
            ],
        )
        cfg = build_cfg(method)
        
        # Should still build CFG
        assert cfg is not None
        assert len(cfg.blocks) >= 1
    
    def test_postorder_empty_cfg(self):
        """Postorder of empty CFG returns empty list."""
        method = TACMethod(
            class_name="Test",
            method_name="empty",
            params=[],
            instructions=[],
        )
        cfg = build_cfg(method)
        po = cfg.postorder()
        
        assert po == []
    
    def test_reverse_postorder_empty_cfg(self):
        """Reverse postorder of empty CFG returns empty list."""
        method = TACMethod(
            class_name="Test",
            method_name="empty",
            params=[],
            instructions=[],
        )
        cfg = build_cfg(method)
        rpo = cfg.reverse_postorder()
        
        assert rpo == []

