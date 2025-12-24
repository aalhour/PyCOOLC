# PyCOOLC Intermediate Representation (IR)
#
# This package provides a Three-Address Code (TAC) intermediate representation
# for COOL programs, along with infrastructure for control flow analysis and
# SSA (Static Single Assignment) form.
#
# Architecture:
#   AST → IR (TAC) → Optimize → MIPS
#
# Why an IR?
# ----------
# 1. **Separation of concerns**: Optimizations work on a simple, uniform
#    representation rather than the complex AST or low-level MIPS.
#
# 2. **Machine independence**: The same optimizations apply regardless of
#    target architecture.
#
# 3. **Explicit control flow**: The IR makes jumps and labels explicit,
#    which is essential for data flow analysis.
#
# 4. **SSA enables clean analysis**: When each variable is assigned exactly
#    once, tracking definitions becomes trivial.

__all__ = ["cfg", "ssa", "tac", "translator"]
