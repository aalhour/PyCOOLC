#!/usr/bin/env python3

"""
Generic Data Flow Analysis Framework.

# What is Data Flow Analysis?

Data Flow Analysis (DFA) computes information about the possible states
of a program at each point in the control flow. It answers questions like:

- "What values might variable X have at this point?" (Reaching Definitions)
- "Is variable X used after this point?" (Liveness)
- "Is expression X always the same at this point?" (Available Expressions)

# The Data Flow Framework

All data flow problems share a common structure:

1. **Domain (D)**: The set of possible values (e.g., sets of definitions)
2. **Direction**: Forward (entry → exit) or backward (exit → entry)
3. **Transfer function**: How values change across an instruction
4. **Meet operation**: How to combine values from multiple paths
5. **Initial values**: Starting values for entry (forward) or exit (backward)

# The Lattice

Data flow values form a **lattice** with:

- **Top (⊤)**: The "most general" value (we know nothing)
- **Bottom (⊥)**: The "most specific" value (unreachable)
- **Meet (⊓)**: Combines values at join points
- **Ordering (≤)**: Bottom ≤ everything ≤ Top

For constant propagation:
    ⊥ < any_constant < ⊤

For sets (e.g., liveness):
    {} (empty) is bottom
    meet is union or intersection depending on the problem

# Fixed-Point Iteration

We iterate until no values change:

```
initialize all data flow values
repeat:
    for each block B:
        compute in[B] from predecessors (forward) or successors (backward)
        compute out[B] by applying transfer functions
until no changes
```

This converges because:
1. Lattices are finite (or have finite height)
2. Transfer functions are monotonic
3. Meet is also monotonic

# Forward vs Backward Analysis

**Forward** (e.g., Reaching Definitions, Constant Propagation):
    in[B] = meet { out[P] | P is predecessor of B }
    out[B] = transfer(in[B], instructions in B)

**Backward** (e.g., Liveness):
    out[B] = meet { in[S] | S is successor of B }
    in[B] = transfer(out[B], instructions in B, backwards)

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Generic, TypeVar

from pycoolc.ir.cfg import ControlFlowGraph, BasicBlock
from pycoolc.ir.tac import Instruction


# =============================================================================
#                           LATTICE ABSTRACTION
# =============================================================================


# Type variable for lattice elements
T = TypeVar("T")


class LatticeValue(ABC, Generic[T]):
    """
    Abstract base class for lattice values.
    
    A lattice must provide:
    - Top (⊤): least informative value
    - Bottom (⊥): most informative value
    - Meet (⊓): combine values at join points
    - Ordering (≤): partial order on values
    """
    
    @abstractmethod
    def meet(self, other: LatticeValue[T]) -> LatticeValue[T]:
        """
        Meet operation: combine with another value.
        
        The meet is the greatest lower bound in the lattice.
        """
        pass
    
    @abstractmethod
    def is_top(self) -> bool:
        """Is this the top element?"""
        pass
    
    @abstractmethod
    def is_bottom(self) -> bool:
        """Is this the bottom element?"""
        pass
    
    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Equality for fixed-point detection."""
        pass
    
    @abstractmethod
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        pass


# =============================================================================
#                           CONSTANT PROPAGATION LATTICE
# =============================================================================


class ConstLattice(Enum):
    """
    The lattice for constant propagation.
    
    Values:
    - TOP (⊤): Unknown value (haven't analyzed yet, or multiple values)
    - BOTTOM (⊥): Unreachable (no definitions reach this point)
    - CONST: A known constant value
    
    Ordering: BOTTOM < CONST < TOP
    
    Meet operation:
    - meet(⊥, x) = x
    - meet(x, ⊥) = x
    - meet(⊤, x) = ⊤
    - meet(x, ⊤) = ⊤
    - meet(c1, c2) = c1 if c1 == c2 else ⊤
    """
    TOP = auto()
    BOTTOM = auto()


@dataclass(frozen=True)
class ConstValue:
    """
    A value in the constant propagation lattice.
    
    Can be:
    - ConstLattice.TOP: Multiple possible values
    - ConstLattice.BOTTOM: No value (unreachable)
    - An actual constant (int, bool, str)
    """
    value: ConstLattice | int | bool | str
    
    @staticmethod
    def top() -> ConstValue:
        return ConstValue(ConstLattice.TOP)
    
    @staticmethod
    def bottom() -> ConstValue:
        return ConstValue(ConstLattice.BOTTOM)
    
    @staticmethod
    def constant(val: int | bool | str) -> ConstValue:
        return ConstValue(val)
    
    def is_top(self) -> bool:
        return self.value == ConstLattice.TOP
    
    def is_bottom(self) -> bool:
        return self.value == ConstLattice.BOTTOM
    
    def is_constant(self) -> bool:
        return not isinstance(self.value, ConstLattice)
    
    def get_constant(self) -> int | bool | str | None:
        if self.is_constant():
            return self.value  # type: ignore
        return None
    
    def meet(self, other: ConstValue) -> ConstValue:
        """
        Meet operation for constant propagation.
        
        This implements the lattice meet as described in the module docstring.
        """
        # Bottom is identity for meet
        if self.is_bottom():
            return other
        if other.is_bottom():
            return self
        
        # Top absorbs everything
        if self.is_top() or other.is_top():
            return ConstValue.top()
        
        # Both are constants
        if self.value == other.value:
            return self
        else:
            # Different constants → Top
            return ConstValue.top()
    
    def __str__(self) -> str:
        if self.is_top():
            return "⊤"
        elif self.is_bottom():
            return "⊥"
        else:
            return str(self.value)


# =============================================================================
#                           DATA FLOW ANALYSIS
# =============================================================================


class Direction(Enum):
    """Direction of data flow analysis."""
    FORWARD = auto()
    BACKWARD = auto()


@dataclass
class DataFlowResult(Generic[T]):
    """
    Results of a data flow analysis.
    
    Stores the computed values at entry (in) and exit (out) of each block.
    """
    # Values at block entry: block_id → value
    block_in: dict[int, T] = field(default_factory=dict)
    
    # Values at block exit: block_id → value
    block_out: dict[int, T] = field(default_factory=dict)
    
    # Values before each instruction: (block_id, instr_index) → value
    instr_in: dict[tuple[int, int], T] = field(default_factory=dict)
    
    # Values after each instruction: (block_id, instr_index) → value
    instr_out: dict[tuple[int, int], T] = field(default_factory=dict)


class DataFlowAnalysis(ABC, Generic[T]):
    """
    Abstract base class for data flow analyses.
    
    Subclasses implement specific analyses by defining:
    - direction: Forward or backward
    - initial_value: Starting value for boundary blocks
    - meet: How to combine values from multiple paths
    - transfer: How values change across an instruction
    """
    
    @property
    @abstractmethod
    def direction(self) -> Direction:
        """Direction of analysis (forward or backward)."""
        pass
    
    @abstractmethod
    def initial_value(self) -> T:
        """Initial value for entry (forward) or exit (backward) blocks."""
        pass
    
    @abstractmethod
    def boundary_value(self) -> T:
        """Value for boundary condition (entry for forward, exit for backward)."""
        pass
    
    @abstractmethod
    def meet(self, values: list[T]) -> T:
        """
        Combine values from multiple control flow paths.
        
        For forward analysis: combines values from predecessors
        For backward analysis: combines values from successors
        """
        pass
    
    @abstractmethod
    def transfer(self, value: T, instruction: Instruction) -> T:
        """
        Compute the output value after an instruction.
        
        For forward analysis: input flows in, output flows out
        For backward analysis: output flows in, input flows out
        """
        pass
    
    def analyze(self, cfg: ControlFlowGraph) -> DataFlowResult[T]:
        """
        Run the data flow analysis on a CFG.
        
        Uses the worklist algorithm for efficiency.
        """
        if not cfg.blocks:
            return DataFlowResult()
        
        result = DataFlowResult[T]()
        
        # Initialize all blocks
        for block in cfg.blocks:
            result.block_in[block.id] = self.initial_value()
            result.block_out[block.id] = self.initial_value()
        
        # Set boundary condition
        if self.direction == Direction.FORWARD and cfg.entry:
            result.block_in[cfg.entry.id] = self.boundary_value()
        elif self.direction == Direction.BACKWARD:
            for exit_block in cfg.exit_blocks:
                result.block_out[exit_block.id] = self.boundary_value()
        
        # Worklist algorithm
        if self.direction == Direction.FORWARD:
            worklist = list(cfg.reverse_postorder())
        else:
            worklist = list(cfg.postorder())
        
        iterations = 0
        max_iterations = len(cfg.blocks) * 100  # Safety limit
        
        while worklist and iterations < max_iterations:
            iterations += 1
            block = worklist.pop(0)
            
            if self.direction == Direction.FORWARD:
                changed = self._analyze_block_forward(block, result)
            else:
                changed = self._analyze_block_backward(block, result)
            
            if changed:
                # Add affected blocks back to worklist
                if self.direction == Direction.FORWARD:
                    for succ in block.successors:
                        if succ not in worklist:
                            worklist.append(succ)
                else:
                    for pred in block.predecessors:
                        if pred not in worklist:
                            worklist.append(pred)
        
        return result
    
    def _analyze_block_forward(
        self,
        block: BasicBlock,
        result: DataFlowResult[T],
    ) -> bool:
        """Analyze a block in forward direction. Returns True if changed."""
        # Compute in[B] from predecessors
        if block.predecessors:
            pred_outs = [result.block_out[p.id] for p in block.predecessors]
            new_in = self.meet(pred_outs)
        else:
            new_in = result.block_in[block.id]
        
        # Apply transfer functions through the block
        current = new_in
        for i, instr in enumerate(block.instructions):
            result.instr_in[(block.id, i)] = current
            current = self.transfer(current, instr)
            result.instr_out[(block.id, i)] = current
        
        new_out = current
        
        # Check for changes
        old_in = result.block_in[block.id]
        old_out = result.block_out[block.id]
        
        changed = (new_in != old_in) or (new_out != old_out)
        
        result.block_in[block.id] = new_in
        result.block_out[block.id] = new_out
        
        return changed
    
    def _analyze_block_backward(
        self,
        block: BasicBlock,
        result: DataFlowResult[T],
    ) -> bool:
        """Analyze a block in backward direction. Returns True if changed."""
        # Compute out[B] from successors
        if block.successors:
            succ_ins = [result.block_in[s.id] for s in block.successors]
            new_out = self.meet(succ_ins)
        else:
            new_out = result.block_out[block.id]
        
        # Apply transfer functions backwards through the block
        current = new_out
        for i in range(len(block.instructions) - 1, -1, -1):
            instr = block.instructions[i]
            result.instr_out[(block.id, i)] = current
            current = self.transfer(current, instr)
            result.instr_in[(block.id, i)] = current
        
        new_in = current
        
        # Check for changes
        old_in = result.block_in[block.id]
        old_out = result.block_out[block.id]
        
        changed = (new_in != old_in) or (new_out != old_out)
        
        result.block_in[block.id] = new_in
        result.block_out[block.id] = new_out
        
        return changed


# =============================================================================
#                           SET-BASED ANALYSES
# =============================================================================


@dataclass(frozen=True)
class SetValue(Generic[T]):
    """
    A set-based lattice value.
    
    Used for analyses like liveness where the domain is sets of variables.
    """
    elements: frozenset[T]
    
    @staticmethod
    def empty() -> SetValue[T]:
        return SetValue(frozenset())
    
    @staticmethod
    def from_set(s: set[T]) -> SetValue[T]:
        return SetValue(frozenset(s))
    
    def union(self, other: SetValue[T]) -> SetValue[T]:
        """Union of sets (used as meet for may-analyses like liveness)."""
        return SetValue(self.elements | other.elements)
    
    def intersection(self, other: SetValue[T]) -> SetValue[T]:
        """Intersection of sets (used as meet for must-analyses)."""
        return SetValue(self.elements & other.elements)
    
    def add(self, element: T) -> SetValue[T]:
        """Add an element to the set."""
        return SetValue(self.elements | {element})
    
    def remove(self, element: T) -> SetValue[T]:
        """Remove an element from the set."""
        return SetValue(self.elements - {element})
    
    def __contains__(self, item: T) -> bool:
        return item in self.elements
    
    def __len__(self) -> int:
        return len(self.elements)
    
    def __iter__(self):
        return iter(self.elements)
    
    def __str__(self) -> str:
        if not self.elements:
            return "{}"
        return "{" + ", ".join(str(e) for e in sorted(self.elements, key=str)) + "}"

