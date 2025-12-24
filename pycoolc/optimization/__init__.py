# PyCOOLC Optimization Module
#
# This package provides optimization passes that work on the IR (TAC/CFG).
#
# Architecture:
#   AST → IR → [Optimize] → MIPS
#
# The optimization phase applies a series of transformations to improve
# the generated code. Each optimization is a "pass" that reads and
# potentially modifies the IR.
#
# Key Concepts:
#
# 1. **Data Flow Analysis**: A framework for computing information about
#    values at each program point. Examples include constant propagation
#    and liveness analysis.
#
# 2. **Local vs Global**: Local optimizations work within a single basic
#    block. Global optimizations use information from the entire CFG.
#
# 3. **Forward vs Backward**: Forward analysis propagates information from
#    entry to exit. Backward analysis propagates from exit to entry.
#
# 4. **Lattice Theory**: Data flow values form a lattice with meet/join
#    operations. Fixed-point iteration converges because lattices are finite.

__all__ = ["constant_prop", "dataflow", "dce", "liveness"]
