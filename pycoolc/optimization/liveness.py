#!/usr/bin/env python3

"""
Global Liveness Analysis.

# What is Liveness Analysis?

A variable is **live** at a program point if its value may be used in the
future. Liveness analysis computes which variables are live at each point.

This enables:
1. **Dead code elimination**: Remove assignments to dead variables
2. **Register allocation**: Live variables need registers
3. **Garbage collection**: Dead objects can be collected

# When is a Variable Live?

A variable x is **live** at statement s if:
1. There exists a statement s' that **uses** x
2. There is a path from s to s'
3. That path has no **definition** of x (no re-assignment)

# The Lattice

For liveness, the domain is sets of variables:
- Empty set: No variables live (at exit, before any uses)
- Union: Combine live sets at join points

This is a **may-analysis**: we want to know what *may* be live.

# Transfer Functions

For each statement, we define:
- **gen(s)**: Variables used by s (become live)
- **kill(s)**: Variables defined by s (become dead, unless also used)

The transfer function is:
    in[s] = gen(s) ∪ (out[s] - kill(s))

Or equivalently:
    in[s] = uses(s) ∪ (out[s] - defs(s))

# Direction

Liveness is a **backward** analysis:
- We start at exit points (where nothing is live)
- We propagate backwards to entry

At join points (multiple successors), we take the **union** of live sets.

# Example

```
    a = 1           # live-in: {} ∪ ({a,b} - {a}) = {b}
    b = 2           # live-in: {a} ∪ ({a,b} - {b}) = {a}
    c = a + b       # live-in: {a,b} ∪ ({c} - {c}) = {a,b}
    return c        # live-in: {c}, live-out: {}
```

Working backwards:
- After return c: live = {}
- At return c: live = {c}
- At c = a + b: live = (uses={a,b}) ∪ ({c} - {c}) = {a,b}
- At b = 2: live = {} ∪ ({a,b} - {b}) = {a}
- At a = 1: live = {} ∪ ({a} - {a}) = {}

# Live Ranges and Interference

Two variables **interfere** if their live ranges overlap, meaning they
cannot share a register. The **interference graph** has an edge between
variables that are simultaneously live.

"""

from __future__ import annotations

from dataclasses import dataclass, field

from pycoolc.ir.cfg import ControlFlowGraph, BasicBlock
from pycoolc.ir.tac import (
    Instruction,
    Operand,
    Temp,
    Var,
)
from pycoolc.optimization.dataflow import (
    DataFlowAnalysis,
    DataFlowResult,
    Direction,
    SetValue,
)


# =============================================================================
#                           LIVENESS ANALYSIS
# =============================================================================


class LivenessAnalysis(DataFlowAnalysis[SetValue[str]]):
    """
    Global liveness analysis.
    
    Computes which variables are live at each program point.
    This is a backward data flow analysis with set union as the meet.
    """
    
    @property
    def direction(self) -> Direction:
        return Direction.BACKWARD
    
    def initial_value(self) -> SetValue[str]:
        """Initial value: empty set (nothing live until proven otherwise)."""
        return SetValue.empty()
    
    def boundary_value(self) -> SetValue[str]:
        """
        Boundary value at exit: empty set.
        
        After returning from a method, no local variables are live.
        (Return value is handled specially.)
        """
        return SetValue.empty()
    
    def meet(self, values: list[SetValue[str]]) -> SetValue[str]:
        """
        Union of live variable sets.
        
        A variable is live if it's live on *any* path (may-analysis).
        """
        if not values:
            return SetValue.empty()
        result = values[0]
        for v in values[1:]:
            result = result.union(v)
        return result
    
    def transfer(self, live_out: SetValue[str], instruction: Instruction) -> SetValue[str]:
        """
        Backward transfer function:
        
        live_in = uses(instr) ∪ (live_out - defs(instr))
        
        In words: Variables used by this instruction are live before it,
        and variables live after it are still live before it (unless defined).
        """
        # Get variables defined and used by this instruction
        defs = self._get_var_names(instruction.defs())
        uses = self._get_var_names(instruction.uses())
        
        # live_in = uses ∪ (live_out - defs)
        live_in = live_out
        for d in defs:
            live_in = live_in.remove(d)
        for u in uses:
            live_in = live_in.add(u)
        
        return live_in
    
    def _get_var_names(self, operands: set[Operand]) -> set[str]:
        """Convert operands to variable name strings."""
        names: set[str] = set()
        for op in operands:
            match op:
                case Temp(index=idx):
                    names.add(f"t{idx}")
                case Var(name=name):
                    names.add(name)
        return names


# =============================================================================
#                           DEAD CODE IDENTIFICATION
# =============================================================================


@dataclass
class DeadCodeInfo:
    """Information about dead code in a method."""
    # Dead instructions: (block_id, instruction_index)
    dead_instructions: list[tuple[int, int]] = field(default_factory=list)
    
    # Dead variables (never live anywhere)
    dead_variables: set[str] = field(default_factory=set)
    
    def __str__(self) -> str:
        lines = ["Dead Code Analysis:"]
        if self.dead_instructions:
            lines.append(f"  Dead instructions: {len(self.dead_instructions)}")
            for block_id, idx in self.dead_instructions[:10]:
                lines.append(f"    B{block_id}[{idx}]")
            if len(self.dead_instructions) > 10:
                lines.append(f"    ... and {len(self.dead_instructions) - 10} more")
        else:
            lines.append("  No dead instructions found")
        
        if self.dead_variables:
            lines.append(f"  Dead variables: {self.dead_variables}")
        
        return "\n".join(lines)


def find_dead_code(
    cfg: ControlFlowGraph,
    liveness_result: DataFlowResult[SetValue[str]],
) -> DeadCodeInfo:
    """
    Identify dead code based on liveness analysis.
    
    An instruction is dead if:
    1. It defines a variable
    2. That variable is not live after the instruction
    3. The instruction has no side effects
    
    Args:
        cfg: The control flow graph
        liveness_result: Results from liveness analysis
    
    Returns:
        Information about dead code
    """
    from pycoolc.ir.tac import (
        Copy, BinaryOp, UnaryOperation, GetAttr,
        Call, Dispatch, StaticDispatch, SetAttr,
        Return, Jump, CondJump, CondJumpNot, LabelInstr, Param,
    )
    
    info = DeadCodeInfo()
    
    for block in cfg.blocks:
        for i, instr in enumerate(block.instructions):
            # Skip instructions with side effects
            if _has_side_effects(instr):
                continue
            
            # Get what this instruction defines
            defs = instr.defs()
            if not defs:
                continue
            
            # Check if any defined variable is live after this instruction
            live_out = liveness_result.instr_out.get(
                (block.id, i),
                SetValue.empty(),
            )
            
            def_names = {_operand_name(d) for d in defs}
            
            # If none of the defined variables are live, the instruction is dead
            if not any(name in live_out for name in def_names):
                info.dead_instructions.append((block.id, i))
                info.dead_variables.update(def_names)
    
    return info


def _has_side_effects(instr: Instruction) -> bool:
    """Check if an instruction has side effects (can't be removed)."""
    from pycoolc.ir.tac import (
        Call, Dispatch, StaticDispatch, SetAttr,
        Return, Jump, CondJump, CondJumpNot, LabelInstr, Param,
    )
    
    # These instructions have side effects
    side_effect_types = (
        Call, Dispatch, StaticDispatch,  # Function calls may have side effects
        SetAttr,  # Memory store
        Return, Jump, CondJump, CondJumpNot,  # Control flow
        LabelInstr,  # Labels are needed for jumps
        Param,  # Parameter setup
    )
    
    return isinstance(instr, side_effect_types)


def _operand_name(op: Operand) -> str:
    """Get the name of an operand."""
    match op:
        case Temp(index=idx):
            return f"t{idx}"
        case Var(name=name):
            return name
        case _:
            return str(op)


# =============================================================================
#                           DEAD CODE ELIMINATION
# =============================================================================


def eliminate_dead_code(
    cfg: ControlFlowGraph,
    dead_info: DeadCodeInfo,
) -> int:
    """
    Remove dead instructions from the CFG.
    
    Args:
        cfg: The control flow graph to modify
        dead_info: Information about dead code
    
    Returns:
        Number of instructions removed
    """
    if not dead_info.dead_instructions:
        return 0
    
    # Group dead instructions by block
    dead_by_block: dict[int, set[int]] = {}
    for block_id, instr_idx in dead_info.dead_instructions:
        if block_id not in dead_by_block:
            dead_by_block[block_id] = set()
        dead_by_block[block_id].add(instr_idx)
    
    # Remove dead instructions (in reverse order to preserve indices)
    removed = 0
    for block in cfg.blocks:
        if block.id not in dead_by_block:
            continue
        
        dead_indices = dead_by_block[block.id]
        new_instructions = []
        
        for i, instr in enumerate(block.instructions):
            if i not in dead_indices:
                new_instructions.append(instr)
            else:
                removed += 1
        
        block.instructions = new_instructions
    
    return removed


# =============================================================================
#                           CONVENIENCE FUNCTIONS
# =============================================================================


def run_liveness_analysis(cfg: ControlFlowGraph) -> DataFlowResult[SetValue[str]]:
    """
    Run liveness analysis on a CFG.
    
    Args:
        cfg: The control flow graph to analyze
    
    Returns:
        Analysis results with live variable sets at each point
    """
    analysis = LivenessAnalysis()
    return analysis.analyze(cfg)


def run_dead_code_elimination(cfg: ControlFlowGraph) -> int:
    """
    Run liveness analysis and eliminate dead code.
    
    This is a convenience function that runs the full DCE pipeline:
    1. Liveness analysis
    2. Identify dead code
    3. Remove dead instructions
    
    Args:
        cfg: The control flow graph to optimize
    
    Returns:
        Number of instructions removed
    """
    # Run liveness analysis
    liveness_result = run_liveness_analysis(cfg)
    
    # Find dead code
    dead_info = find_dead_code(cfg, liveness_result)
    
    # Eliminate dead code
    return eliminate_dead_code(cfg, dead_info)


# =============================================================================
#                           LIVE RANGE COMPUTATION
# =============================================================================


@dataclass
class LiveRange:
    """
    The live range of a variable.
    
    Represents all program points where the variable is live.
    Used for register allocation and interference graph construction.
    """
    variable: str
    # Set of (block_id, instruction_index) where the variable is live
    points: set[tuple[int, int]] = field(default_factory=set)
    
    def overlaps(self, other: LiveRange) -> bool:
        """Check if this live range overlaps with another."""
        return bool(self.points & other.points)


def compute_live_ranges(
    cfg: ControlFlowGraph,
    liveness_result: DataFlowResult[SetValue[str]],
) -> dict[str, LiveRange]:
    """
    Compute the live range for each variable.
    
    Args:
        cfg: The control flow graph
        liveness_result: Results from liveness analysis
    
    Returns:
        Dictionary mapping variable names to their live ranges
    """
    ranges: dict[str, LiveRange] = {}
    
    for block in cfg.blocks:
        for i in range(len(block.instructions)):
            # Variables live at this point
            live_in = liveness_result.instr_in.get((block.id, i), SetValue.empty())
            live_out = liveness_result.instr_out.get((block.id, i), SetValue.empty())
            
            # A variable is live at this point if it's in live_in OR live_out
            all_live = live_in.elements | live_out.elements
            
            for var in all_live:
                if var not in ranges:
                    ranges[var] = LiveRange(variable=var)
                ranges[var].points.add((block.id, i))
    
    return ranges


def build_interference_graph(
    live_ranges: dict[str, LiveRange],
) -> dict[str, set[str]]:
    """
    Build an interference graph from live ranges.
    
    Two variables interfere if their live ranges overlap, meaning they
    cannot share the same register.
    
    Args:
        live_ranges: Live ranges for each variable
    
    Returns:
        Adjacency list representation of the interference graph
    """
    graph: dict[str, set[str]] = {var: set() for var in live_ranges}
    
    variables = list(live_ranges.keys())
    for i, v1 in enumerate(variables):
        for v2 in variables[i + 1:]:
            if live_ranges[v1].overlaps(live_ranges[v2]):
                graph[v1].add(v2)
                graph[v2].add(v1)
    
    return graph

