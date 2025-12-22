#!/usr/bin/env python3

"""
Global Constant Propagation Analysis.

# What is Constant Propagation?

Constant propagation determines which variables have constant values at
each point in the program. This enables:

1. **Constant folding**: Replace `x + y` with `6` if x=2 and y=4
2. **Dead code elimination**: Remove `if false then ...`
3. **Better code generation**: Use immediate values instead of loads

# The Lattice

For each variable, we track a value from the constant lattice:

    ⊥ (Bottom) — Unreachable; no value flows here
         |
    Constants — Known constant values (1, 2, "hello", true, ...)
         |
    ⊤ (Top) — Unknown; multiple possible values

The ordering is: ⊥ < C < ⊤

# Transfer Functions

For each statement type, we define how it affects variable values:

1. **x = c** (constant assignment):
   C(x) = c

2. **x = y op z** (operation with constants):
   If C(y) and C(z) are both constants, evaluate and set C(x) = result
   Otherwise, C(x) = ⊤

3. **x = f(...)** (function call):
   C(x) = ⊤ (we can't know what the function returns)

4. **y = ...** (assignment to other variable):
   C(x) = C(x) unchanged (if x ≠ y)

# Meet at Join Points

When control flow merges, we compute the meet of incoming values:

    meet(⊥, v) = v
    meet(v, ⊥) = v
    meet(c, c) = c  (same constant)
    meet(c1, c2) = ⊤  (different constants)
    meet(⊤, v) = ⊤

# Algorithm

This is a forward data flow analysis:

1. Initialize: All variables are ⊥ at entry
2. At entry point: Parameters and self are ⊤ (unknown)
3. Iterate until fixed point:
   - For each block B:
     - in[B] = meet of out[predecessors]
     - out[B] = apply transfer functions to in[B]

# Example

```
    a = 2           # C(a) = 2
    b = 3           # C(b) = 3
    if cond:
        c = a + b   # C(c) = 5
    else:
        c = a * b   # C(c) = 6
    # At join: C(c) = ⊤ (meet of 5 and 6)
    d = a + 1       # C(d) = 3 (a is still 2)
```

"""

from __future__ import annotations

from dataclasses import dataclass, field

from pycoolc.ir.cfg import ControlFlowGraph, BasicBlock
from pycoolc.ir.tac import (
    Instruction,
    Operand,
    Temp,
    Var,
    Const,
    BinaryOp,
    UnaryOperation,
    Copy,
    BinOp,
    UnaryOp,
    Call,
    Dispatch,
    StaticDispatch,
    New,
    IsVoid,
    GetAttr,
    Phi,
)
from pycoolc.optimization.dataflow import (
    DataFlowAnalysis,
    DataFlowResult,
    Direction,
    ConstValue,
)


# =============================================================================
#                           CONSTANT ENVIRONMENT
# =============================================================================


@dataclass(frozen=False)
class ConstEnv:
    """
    Environment mapping variables to their constant values.
    
    This is the data flow value for constant propagation.
    Each variable maps to a ConstValue (⊤, ⊥, or a constant).
    """
    values: dict[str, ConstValue] = field(default_factory=dict)
    
    def get(self, var: str) -> ConstValue:
        """Get the value for a variable (default: ⊥)."""
        return self.values.get(var, ConstValue.bottom())
    
    def set(self, var: str, value: ConstValue) -> ConstEnv:
        """Return a new environment with the variable set."""
        new_values = dict(self.values)
        new_values[var] = value
        return ConstEnv(new_values)
    
    def meet(self, other: ConstEnv) -> ConstEnv:
        """Meet two environments (merge at join points)."""
        all_vars = set(self.values.keys()) | set(other.values.keys())
        new_values = {}
        for var in all_vars:
            v1 = self.get(var)
            v2 = other.get(var)
            new_values[var] = v1.meet(v2)
        return ConstEnv(new_values)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConstEnv):
            return False
        # Compare all variables in either environment
        all_vars = set(self.values.keys()) | set(other.values.keys())
        for var in all_vars:
            if self.get(var) != other.get(var):
                return False
        return True
    
    def __hash__(self) -> int:
        return hash(frozenset(self.values.items()))
    
    def __str__(self) -> str:
        if not self.values:
            return "{}"
        items = [f"{k}: {v}" for k, v in sorted(self.values.items())]
        return "{\n  " + ",\n  ".join(items) + "\n}"
    
    def copy(self) -> ConstEnv:
        """Create a copy of this environment."""
        return ConstEnv(dict(self.values))


# =============================================================================
#                           CONSTANT PROPAGATION ANALYSIS
# =============================================================================


class ConstantPropagation(DataFlowAnalysis[ConstEnv]):
    """
    Global constant propagation analysis.
    
    Computes which variables have constant values at each program point.
    """
    
    def __init__(self, params: list[str] | None = None) -> None:
        """
        Initialize the analysis.
        
        Args:
            params: Method parameters (these start as ⊤, not ⊥)
        """
        self.params = params or []
    
    @property
    def direction(self) -> Direction:
        return Direction.FORWARD
    
    def initial_value(self) -> ConstEnv:
        """Initial value: empty environment (all variables are ⊥)."""
        return ConstEnv()
    
    def boundary_value(self) -> ConstEnv:
        """
        Boundary value at entry: parameters and 'self' are ⊤.
        
        We don't know what values are passed to the method.
        """
        env = ConstEnv()
        # 'self' is always available but unknown
        env = env.set("self", ConstValue.top())
        # Parameters are unknown
        for param in self.params:
            env = env.set(param, ConstValue.top())
        return env
    
    def meet(self, values: list[ConstEnv]) -> ConstEnv:
        """Meet of multiple environments."""
        if not values:
            return ConstEnv()
        result = values[0].copy()
        for env in values[1:]:
            result = result.meet(env)
        return result
    
    def transfer(self, env: ConstEnv, instruction: Instruction) -> ConstEnv:
        """
        Transfer function: how does an instruction affect the environment?
        """
        match instruction:
            case Copy(dest=dest, source=source):
                value = self._eval_operand(source, env)
                return env.set(self._operand_name(dest), value)
            
            case BinaryOp(dest=dest, op=op, left=left, right=right):
                left_val = self._eval_operand(left, env)
                right_val = self._eval_operand(right, env)
                result = self._eval_binop(op, left_val, right_val)
                return env.set(self._operand_name(dest), result)
            
            case UnaryOperation(dest=dest, op=op, operand=operand):
                val = self._eval_operand(operand, env)
                result = self._eval_unaryop(op, val)
                return env.set(self._operand_name(dest), result)
            
            case Call(dest=dest) if dest is not None:
                # Function calls return unknown values
                return env.set(self._operand_name(dest), ConstValue.top())
            
            case Dispatch(dest=dest) | StaticDispatch(dest=dest) if dest is not None:
                # Method calls return unknown values
                return env.set(self._operand_name(dest), ConstValue.top())
            
            case New(dest=dest):
                # New objects are not constants
                return env.set(self._operand_name(dest), ConstValue.top())
            
            case IsVoid(dest=dest, operand=operand):
                # isvoid result depends on whether operand is known void
                # For simplicity, treat as unknown
                return env.set(self._operand_name(dest), ConstValue.top())
            
            case GetAttr(dest=dest):
                # Attribute loads are unknown
                return env.set(self._operand_name(dest), ConstValue.top())
            
            case Phi(dest=dest, sources=sources):
                # Meet all source values
                values = [self._eval_operand(val, env) for val, _ in sources]
                if not values:
                    result = ConstValue.bottom()
                else:
                    result = values[0]
                    for v in values[1:]:
                        result = result.meet(v)
                return env.set(self._operand_name(dest), result)
            
            case _:
                # Instructions that don't define variables
                return env
    
    def _operand_name(self, op: Operand) -> str:
        """Get the name of an operand for the environment."""
        match op:
            case Temp(index=idx):
                return f"t{idx}"
            case Var(name=name):
                return name
            case _:
                return str(op)
    
    def _eval_operand(self, op: Operand, env: ConstEnv) -> ConstValue:
        """Evaluate an operand to a constant value."""
        match op:
            case Const(value=val):
                return ConstValue.constant(val)
            case Temp() | Var():
                return env.get(self._operand_name(op))
            case _:
                return ConstValue.top()
    
    def _eval_binop(
        self,
        op: BinOp,
        left: ConstValue,
        right: ConstValue,
    ) -> ConstValue:
        """Evaluate a binary operation on constant values."""
        # If either is bottom, result is bottom (unreachable)
        if left.is_bottom() or right.is_bottom():
            return ConstValue.bottom()
        
        # If either is top, result is top (unknown)
        if left.is_top() or right.is_top():
            return ConstValue.top()
        
        # Both are constants - evaluate
        lval = left.get_constant()
        rval = right.get_constant()
        
        if not isinstance(lval, int) or not isinstance(rval, int):
            # Non-integer operations are complex
            if op == BinOp.EQ:
                return ConstValue.constant(lval == rval)
            return ConstValue.top()
        
        try:
            match op:
                case BinOp.ADD:
                    return ConstValue.constant(lval + rval)
                case BinOp.SUB:
                    return ConstValue.constant(lval - rval)
                case BinOp.MUL:
                    return ConstValue.constant(lval * rval)
                case BinOp.DIV:
                    if rval == 0:
                        return ConstValue.top()  # Division by zero
                    return ConstValue.constant(lval // rval)
                case BinOp.LT:
                    return ConstValue.constant(lval < rval)
                case BinOp.LE:
                    return ConstValue.constant(lval <= rval)
                case BinOp.EQ:
                    return ConstValue.constant(lval == rval)
                case _:
                    return ConstValue.top()
        except Exception:
            return ConstValue.top()
    
    def _eval_unaryop(self, op: UnaryOp, val: ConstValue) -> ConstValue:
        """Evaluate a unary operation on a constant value."""
        if val.is_bottom():
            return ConstValue.bottom()
        if val.is_top():
            return ConstValue.top()
        
        cval = val.get_constant()
        
        match op:
            case UnaryOp.NEG:
                if isinstance(cval, int):
                    return ConstValue.constant(-cval)
            case UnaryOp.NOT:
                if isinstance(cval, bool):
                    return ConstValue.constant(not cval)
        
        return ConstValue.top()


# =============================================================================
#                           CONSTANT FOLDING TRANSFORMATION
# =============================================================================


def fold_constants(
    cfg: ControlFlowGraph,
    analysis_result: DataFlowResult[ConstEnv],
) -> int:
    """
    Apply constant folding to the CFG using analysis results.
    
    Replaces:
    1. Variables with known constant values
    2. Operations on constants with their results
    
    Returns the number of instructions modified.
    """
    changes = 0
    
    for block in cfg.blocks:
        new_instructions = []
        
        for i, instr in enumerate(block.instructions):
            env = analysis_result.instr_in.get((block.id, i), ConstEnv())
            folded = _fold_instruction(instr, env)
            new_instructions.append(folded)
            if folded is not instr:
                changes += 1
        
        block.instructions = new_instructions
    
    return changes


def _fold_instruction(instr: Instruction, env: ConstEnv) -> Instruction:
    """Fold constants in a single instruction."""
    match instr:
        case BinaryOp(dest=dest, op=op, left=left, right=right):
            # Try to fold operands
            new_left = _fold_operand(left, env)
            new_right = _fold_operand(right, env)
            
            # If both are now constants, evaluate
            if isinstance(new_left, Const) and isinstance(new_right, Const):
                result = _eval_const_binop(op, new_left.value, new_right.value)
                if result is not None:
                    return Copy(dest=dest, source=Const(result, _type_of(result)))
            
            # Return with folded operands
            if new_left is not left or new_right is not right:
                return BinaryOp(dest=dest, op=op, left=new_left, right=new_right)
        
        case UnaryOperation(dest=dest, op=op, operand=operand):
            new_operand = _fold_operand(operand, env)
            
            if isinstance(new_operand, Const):
                result = _eval_const_unaryop(op, new_operand.value)
                if result is not None:
                    return Copy(dest=dest, source=Const(result, _type_of(result)))
            
            if new_operand is not operand:
                return UnaryOperation(dest=dest, op=op, operand=new_operand)
        
        case Copy(dest=dest, source=source):
            new_source = _fold_operand(source, env)
            if new_source is not source:
                return Copy(dest=dest, source=new_source)
    
    return instr


def _fold_operand(op: Operand, env: ConstEnv) -> Operand:
    """Replace a variable with its constant value if known."""
    match op:
        case Temp(index=idx):
            val = env.get(f"t{idx}")
            if val.is_constant():
                cval = val.get_constant()
                if cval is not None:
                    return Const(cval, _type_of(cval))
        case Var(name=name):
            val = env.get(name)
            if val.is_constant():
                cval = val.get_constant()
                if cval is not None:
                    return Const(cval, _type_of(cval))
    return op


def _eval_const_binop(op: BinOp, left: int | bool | str, right: int | bool | str):
    """Evaluate a binary operation on constant values."""
    if not isinstance(left, int) or not isinstance(right, int):
        if op == BinOp.EQ:
            return left == right
        return None
    
    try:
        match op:
            case BinOp.ADD:
                return left + right
            case BinOp.SUB:
                return left - right
            case BinOp.MUL:
                return left * right
            case BinOp.DIV:
                return left // right if right != 0 else None
            case BinOp.LT:
                return left < right
            case BinOp.LE:
                return left <= right
            case BinOp.EQ:
                return left == right
    except Exception:
        return None
    return None


def _eval_const_unaryop(op: UnaryOp, val: int | bool | str):
    """Evaluate a unary operation on a constant value."""
    match op:
        case UnaryOp.NEG:
            if isinstance(val, int):
                return -val
        case UnaryOp.NOT:
            if isinstance(val, bool):
                return not val
    return None


def _type_of(val: int | bool | str) -> str:
    """Get the COOL type of a Python value."""
    if isinstance(val, bool):
        return "Bool"
    elif isinstance(val, int):
        return "Int"
    else:
        return "String"


# =============================================================================
#                           CONVENIENCE FUNCTION
# =============================================================================


def run_constant_propagation(
    cfg: ControlFlowGraph,
    params: list[str] | None = None,
    fold: bool = True,
) -> tuple[DataFlowResult[ConstEnv], int]:
    """
    Run constant propagation on a CFG.
    
    Args:
        cfg: The control flow graph to analyze
        params: Method parameters (start as unknown)
        fold: Whether to apply constant folding transformations
    
    Returns:
        Tuple of (analysis results, number of folded instructions)
    """
    analysis = ConstantPropagation(params=params)
    result = analysis.analyze(cfg)
    
    changes = 0
    if fold:
        changes = fold_constants(cfg, result)
    
    return result, changes

