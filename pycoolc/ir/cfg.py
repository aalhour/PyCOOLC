#!/usr/bin/env python3

"""
Control Flow Graph (CFG) for TAC Programs.

# What is a Control Flow Graph?

A CFG represents the possible paths of execution through a program.
Nodes are **basic blocks** (straight-line sequences of instructions),
and edges represent possible control flow between blocks.

# What is a Basic Block?

A basic block is a maximal sequence of instructions such that:
1. Control enters only at the first instruction (the "leader")
2. Control leaves only at the last instruction
3. All instructions execute sequentially (no jumps in the middle)

Leaders (first instructions of blocks) are:
- The first instruction of a method
- Any instruction that is a jump target (label)
- Any instruction immediately following a jump

# Why CFGs for Optimization?

1. **Local optimizations** work within a single basic block
2. **Global optimizations** use data flow information that propagates
   along CFG edges
3. **Dominance analysis** (for SSA) is defined on the CFG

# Example

Consider this TAC:

    t0 = 1
    t1 = 2
    if t0 < t1 goto L1
    t2 = t0 + t1
    goto L2
    L1:
    t2 = t0 - t1
    L2:
    return t2

This produces the following CFG:

    Block B0 (entry):
        t0 = 1
        t1 = 2
        if t0 < t1 goto L1
            │
        ┌───┴───┐
        ↓       ↓
    Block B1:  Block B2:
    t2 = t0+t1  L1:
    goto L2     t2 = t0-t1
        │           │
        └─────┬─────┘
              ↓
          Block B3:
          L2:
          return t2

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from pycoolc.ir.tac import (
    Instruction,
    Label,
    LabelInstr,
    Jump,
    CondJump,
    CondJumpNot,
    Return,
    TACMethod,
)


# =============================================================================
#                           BASIC BLOCK
# =============================================================================


@dataclass
class BasicBlock:
    """
    A basic block in the control flow graph.
    
    A basic block is a sequence of instructions with:
    - Single entry point (first instruction)
    - Single exit point (last instruction)
    - No jumps except possibly the last instruction
    
    Attributes:
        id: Unique identifier for this block
        label: Optional label at the start of this block
        instructions: The instructions in this block
        predecessors: Blocks that can jump to this block
        successors: Blocks this block can jump to
    """
    id: int
    label: Label | None = None
    instructions: list[Instruction] = field(default_factory=list)
    predecessors: list[BasicBlock] = field(default_factory=list)
    successors: list[BasicBlock] = field(default_factory=list)
    
    def __str__(self) -> str:
        lines = [f"Block B{self.id}:"]
        if self.label:
            lines.append(f"  (label: {self.label})")
        for instr in self.instructions:
            lines.append(f"    {instr}")
        if self.successors:
            succ_ids = [f"B{s.id}" for s in self.successors]
            lines.append(f"  → successors: {', '.join(succ_ids)}")
        return "\n".join(lines)
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BasicBlock):
            return False
        return self.id == other.id
    
    def is_entry(self) -> bool:
        """Is this the entry block (no predecessors)?"""
        return len(self.predecessors) == 0
    
    def is_exit(self) -> bool:
        """Is this an exit block (ends with return)?"""
        if not self.instructions:
            return False
        return isinstance(self.instructions[-1], Return)
    
    def last_instruction(self) -> Instruction | None:
        """Get the last instruction, if any."""
        return self.instructions[-1] if self.instructions else None


# =============================================================================
#                           CONTROL FLOW GRAPH
# =============================================================================


@dataclass
class ControlFlowGraph:
    """
    Control Flow Graph for a single method.
    
    The CFG represents all possible execution paths through the method.
    It's the foundation for data flow analysis and SSA construction.
    
    Attributes:
        method: The TAC method this CFG represents
        blocks: All basic blocks in the CFG
        entry: The entry block (where execution starts)
        exit_blocks: Blocks that end with return
        label_to_block: Map from labels to their blocks
    """
    method: TACMethod
    blocks: list[BasicBlock] = field(default_factory=list)
    entry: BasicBlock | None = None
    exit_blocks: list[BasicBlock] = field(default_factory=list)
    label_to_block: dict[str, BasicBlock] = field(default_factory=dict)
    
    def __str__(self) -> str:
        lines = [
            f"CFG for {self.method.class_name}.{self.method.method_name}:",
            f"  Entry: B{self.entry.id}" if self.entry else "  Entry: None",
            f"  Exit blocks: {[f'B{b.id}' for b in self.exit_blocks]}",
            "",
        ]
        for block in self.blocks:
            lines.append(str(block))
            lines.append("")
        return "\n".join(lines)
    
    def __iter__(self) -> Iterator[BasicBlock]:
        """Iterate over blocks in order."""
        return iter(self.blocks)
    
    def get_block_by_label(self, label: str) -> BasicBlock | None:
        """Find a block by its label."""
        return self.label_to_block.get(label)
    
    def add_block(self, block: BasicBlock) -> None:
        """Add a block to the CFG."""
        self.blocks.append(block)
        if block.label:
            self.label_to_block[block.label.name] = block
    
    def add_edge(self, from_block: BasicBlock, to_block: BasicBlock) -> None:
        """Add an edge between blocks."""
        if to_block not in from_block.successors:
            from_block.successors.append(to_block)
        if from_block not in to_block.predecessors:
            to_block.predecessors.append(from_block)
    
    def reverse_postorder(self) -> list[BasicBlock]:
        """
        Return blocks in reverse postorder (RPO).
        
        RPO is useful for forward data flow analysis because it visits
        predecessors before successors (except for back edges in loops).
        """
        visited: set[int] = set()
        postorder: list[BasicBlock] = []
        
        def dfs(block: BasicBlock) -> None:
            if block.id in visited:
                return
            visited.add(block.id)
            for succ in block.successors:
                dfs(succ)
            postorder.append(block)
        
        if self.entry:
            dfs(self.entry)
        
        return list(reversed(postorder))
    
    def postorder(self) -> list[BasicBlock]:
        """
        Return blocks in postorder.
        
        Postorder is useful for backward data flow analysis because it
        visits successors before predecessors.
        """
        visited: set[int] = set()
        postorder: list[BasicBlock] = []
        
        def dfs(block: BasicBlock) -> None:
            if block.id in visited:
                return
            visited.add(block.id)
            for succ in block.successors:
                dfs(succ)
            postorder.append(block)
        
        if self.entry:
            dfs(self.entry)
        
        return postorder


# =============================================================================
#                           CFG BUILDER
# =============================================================================


def build_cfg(method: TACMethod) -> ControlFlowGraph:
    """
    Build a control flow graph from a TAC method.
    
    Algorithm:
    1. Identify leaders (first instructions of basic blocks)
    2. Partition instructions into basic blocks
    3. Connect blocks with edges based on jumps
    
    Args:
        method: The TAC method to analyze
    
    Returns:
        A ControlFlowGraph representing the method's control flow
    """
    if not method.instructions:
        # Empty method
        cfg = ControlFlowGraph(method=method)
        return cfg
    
    # Step 1: Find leaders
    leaders = _find_leaders(method.instructions)
    
    # Step 2: Build basic blocks
    blocks = _build_blocks(method.instructions, leaders)
    
    # Step 3: Build CFG and connect edges
    cfg = ControlFlowGraph(method=method)
    
    for block in blocks:
        cfg.add_block(block)
    
    if blocks:
        cfg.entry = blocks[0]
    
    # Step 4: Add edges
    _connect_blocks(cfg, blocks)
    
    # Step 5: Identify exit blocks
    for block in blocks:
        if block.is_exit():
            cfg.exit_blocks.append(block)
    
    return cfg


def _find_leaders(instructions: list[Instruction]) -> set[int]:
    """
    Find the indices of leader instructions.
    
    Leaders are:
    1. The first instruction
    2. Any instruction that is a jump target (label)
    3. Any instruction immediately after a jump
    """
    leaders: set[int] = set()
    
    if not instructions:
        return leaders
    
    # Rule 1: First instruction is a leader
    leaders.add(0)
    
    # First pass: collect all label indices
    label_indices: dict[str, int] = {}
    for i, instr in enumerate(instructions):
        if isinstance(instr, LabelInstr):
            label_indices[instr.label.name] = i
    
    # Second pass: find leaders from jumps
    for i, instr in enumerate(instructions):
        # Rule 2: Jump targets are leaders
        if isinstance(instr, LabelInstr):
            leaders.add(i)
        
        # Rule 3: Instruction after a jump is a leader
        if instr.is_jump() and i + 1 < len(instructions):
            leaders.add(i + 1)
    
    return leaders


def _build_blocks(instructions: list[Instruction], leaders: set[int]) -> list[BasicBlock]:
    """
    Partition instructions into basic blocks based on leaders.
    """
    if not instructions:
        return []
    
    # Sort leader indices
    sorted_leaders = sorted(leaders)
    
    blocks: list[BasicBlock] = []
    block_id = 0
    
    for i, leader_idx in enumerate(sorted_leaders):
        # Find the end of this block
        if i + 1 < len(sorted_leaders):
            end_idx = sorted_leaders[i + 1]
        else:
            end_idx = len(instructions)
        
        # Extract instructions for this block
        block_instructions = instructions[leader_idx:end_idx]
        
        # Check if block starts with a label
        label = None
        if block_instructions and isinstance(block_instructions[0], LabelInstr):
            label = block_instructions[0].label
        
        block = BasicBlock(
            id=block_id,
            label=label,
            instructions=block_instructions,
        )
        blocks.append(block)
        block_id += 1
    
    return blocks


def _connect_blocks(cfg: ControlFlowGraph, blocks: list[BasicBlock]) -> None:
    """
    Add edges between basic blocks based on control flow.
    """
    for i, block in enumerate(blocks):
        last_instr = block.last_instruction()
        
        if last_instr is None:
            continue
        
        if isinstance(last_instr, Jump):
            # Unconditional jump: edge to target only
            target_label = last_instr.target.name
            target_block = cfg.get_block_by_label(target_label)
            if target_block:
                cfg.add_edge(block, target_block)
        
        elif isinstance(last_instr, (CondJump, CondJumpNot)):
            # Conditional jump: edges to target AND fall-through
            target_label = last_instr.target.name
            target_block = cfg.get_block_by_label(target_label)
            if target_block:
                cfg.add_edge(block, target_block)
            
            # Fall-through to next block
            if i + 1 < len(blocks):
                cfg.add_edge(block, blocks[i + 1])
        
        elif isinstance(last_instr, Return):
            # Return: no successors (exit block)
            pass
        
        else:
            # No explicit jump: fall through to next block
            if i + 1 < len(blocks):
                cfg.add_edge(block, blocks[i + 1])


# =============================================================================
#                           DOMINANCE ANALYSIS
# =============================================================================


def compute_dominators(cfg: ControlFlowGraph) -> dict[int, set[int]]:
    """
    Compute the dominator sets for all blocks in the CFG.
    
    A block D dominates block B if every path from the entry to B
    must go through D. Every block dominates itself.
    
    This is a forward data flow problem:
        dom(entry) = {entry}
        dom(B) = {B} ∪ ∩{dom(P) | P is a predecessor of B}
    
    Uses the iterative algorithm described in the Dragon Book.
    
    Returns:
        A dictionary mapping block IDs to their dominator sets
    """
    if not cfg.blocks or cfg.entry is None:
        return {}
    
    # Initialize: entry dominates only itself, others dominated by all
    all_block_ids = {b.id for b in cfg.blocks}
    dom: dict[int, set[int]] = {}
    
    dom[cfg.entry.id] = {cfg.entry.id}
    for block in cfg.blocks:
        if block.id != cfg.entry.id:
            dom[block.id] = set(all_block_ids)
    
    # Iterate until fixed point
    changed = True
    while changed:
        changed = False
        for block in cfg.blocks:
            if block.id == cfg.entry.id:
                continue
            
            if not block.predecessors:
                continue
            
            # New dom set = intersection of predecessors' dom sets + self
            new_dom = set(all_block_ids)
            for pred in block.predecessors:
                new_dom &= dom[pred.id]
            new_dom.add(block.id)
            
            if new_dom != dom[block.id]:
                dom[block.id] = new_dom
                changed = True
    
    return dom


def compute_immediate_dominators(
    cfg: ControlFlowGraph,
    dominators: dict[int, set[int]] | None = None,
) -> dict[int, int | None]:
    """
    Compute the immediate dominator for each block.
    
    The immediate dominator of B (idom(B)) is the unique block D such that:
    1. D dominates B
    2. D ≠ B
    3. Every other dominator of B also dominates D
    
    In other words, idom(B) is the closest dominator of B.
    
    Returns:
        A dictionary mapping block IDs to their immediate dominator's ID
        (or None for the entry block)
    """
    if dominators is None:
        dominators = compute_dominators(cfg)
    
    idom: dict[int, int | None] = {}
    
    for block in cfg.blocks:
        block_id = block.id
        
        # Entry has no immediate dominator
        if cfg.entry and block_id == cfg.entry.id:
            idom[block_id] = None
            continue
        
        # Candidates are dominators excluding self
        candidates = dominators[block_id] - {block_id}
        
        if not candidates:
            idom[block_id] = None
            continue
        
        # Find the immediate dominator: the one that's dominated by all others
        # (i.e., the one closest to the block)
        for candidate in candidates:
            is_immediate = True
            for other in candidates:
                if other != candidate and other not in dominators.get(candidate, set()):
                    # 'other' dominates 'candidate', so 'candidate' isn't immediate
                    pass
                elif other != candidate and candidate not in dominators.get(other, set()):
                    # 'candidate' doesn't dominate 'other', but 'other' is also a dominator
                    # This means 'candidate' is not dominated by 'other'
                    is_immediate = False
                    break
            
            # Actually, we need to find the candidate that is dominated by all others
            is_immediate = True
            for other in candidates:
                if other != candidate:
                    # Check if candidate is dominated by other
                    if candidate not in dominators.get(other, set()):
                        # Other doesn't dominate candidate
                        pass
                    else:
                        # Other dominates candidate, so candidate is not the closest
                        is_immediate = False
                        break
            
            if is_immediate:
                idom[block_id] = candidate
                break
        else:
            # Fallback: shouldn't happen with correct dominator sets
            idom[block_id] = None
    
    return idom


def compute_dominance_frontier(
    cfg: ControlFlowGraph,
    dominators: dict[int, set[int]] | None = None,
) -> dict[int, set[int]]:
    """
    Compute the dominance frontier for each block.
    
    The dominance frontier of block B is the set of blocks where B's
    dominance ends. Formally, DF(B) contains block X if:
    1. B dominates a predecessor of X
    2. B does not strictly dominate X
    
    The dominance frontier is crucial for SSA construction: φ-functions
    must be placed at the dominance frontier of variable definitions.
    
    Returns:
        A dictionary mapping block IDs to their dominance frontier sets
    """
    if dominators is None:
        dominators = compute_dominators(cfg)
    
    df: dict[int, set[int]] = {b.id: set() for b in cfg.blocks}
    
    for block in cfg.blocks:
        if len(block.predecessors) >= 2:
            # This is a join point (multiple predecessors)
            for pred in block.predecessors:
                runner = pred
                # Walk up the dominator tree from pred
                while runner.id not in (dominators.get(block.id, set()) - {block.id}):
                    df[runner.id].add(block.id)
                    # Move to immediate dominator
                    # For simplicity, we'll just check all dominators
                    found = False
                    for candidate_id in dominators.get(runner.id, set()):
                        if candidate_id != runner.id:
                            for b in cfg.blocks:
                                if b.id == candidate_id:
                                    runner = b
                                    found = True
                                    break
                        if found:
                            break
                    if not found:
                        break
    
    return df

