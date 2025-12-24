#!/usr/bin/env python3

"""
Static Single Assignment (SSA) Form Construction.

# What is SSA Form?

SSA (Static Single Assignment) is an IR property where each variable is
assigned exactly once. This makes data flow analysis trivial because
definitions are unique.

Consider this code:
    x = 1
    x = 2
    y = x

In SSA form, we rename variables to make each assignment unique:
    x1 = 1
    x2 = 2
    y1 = x2

# The φ-Function Problem

At join points in the control flow (after if-else, loop headers),
different paths may have different versions of a variable:

    if (cond)
        x1 = 1
    else
        x2 = 2

    # Which x do we use here? x1 or x2?

SSA introduces φ (phi) functions to solve this:

    if (cond)
        x1 = 1
    else
        x2 = 2
    x3 = φ(x1, x2)  # Selects x1 or x2 based on which branch was taken

# SSA Construction Algorithm

We implement the standard algorithm from Cytron et al. (1991):

1. **Compute Dominance Frontiers**
   The dominance frontier of block B is the set of blocks where B's
   dominance ends - where we need φ-functions.

2. **Insert φ-Functions**
   For each variable v with multiple assignments, insert φ-functions
   at the dominance frontier of each definition's block.

3. **Rename Variables**
   Walk the dominator tree, renaming variables to their SSA versions.

# Why SSA for Optimization?

1. **Use-def chains are trivial**: Each use has exactly one definition.
2. **Dead code is obvious**: If a definition has no uses, it's dead.
3. **Constant propagation is simple**: Replace uses with the constant.
4. **Copy propagation is simple**: Replace uses with the source.

# References

- Cytron et al., "Efficiently Computing Static Single Assignment Form
  and the Control Dependence Graph", ACM TOPLAS 1991.
- Cooper & Torczon, "Engineering a Compiler", Chapter 9.

"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from pycoolc.ir.cfg import (
    BasicBlock,
    ControlFlowGraph,
    build_cfg,
    compute_dominators,
    compute_immediate_dominators,
)
from pycoolc.ir.tac import (
    Instruction,
    Label,
    LabelInstr,
    Phi,
    TACMethod,
    Var,
)


@dataclass
class SSABuilder:
    """
    Converts a TACMethod to SSA form.

    This implements the standard SSA construction algorithm:
    1. Build CFG
    2. Compute dominance frontiers
    3. Insert φ-functions
    4. Rename variables

    Usage:
        builder = SSABuilder()
        ssa_method = builder.convert_to_ssa(method)
    """

    def convert_to_ssa(self, method: TACMethod) -> TACMethod:
        """Convert a method to SSA form."""
        # Build CFG
        cfg = build_cfg(method)

        if not cfg.blocks:
            return method

        # Compute dominance information
        dominators = compute_dominators(cfg)
        idoms = compute_immediate_dominators(cfg, dominators)

        # Build dominator tree
        dom_tree = self._build_dominator_tree(cfg, idoms)

        # Compute dominance frontiers
        frontiers = self._compute_dominance_frontiers(cfg, idoms)

        # Find all variables that need φ-functions
        var_defs = self._find_variable_definitions(cfg)

        # Insert φ-functions
        phi_locations = self._compute_phi_locations(cfg, var_defs, frontiers)
        self._insert_phi_functions(cfg, phi_locations)

        # Rename variables
        self._rename_variables(cfg, dom_tree, var_defs)

        # Collect instructions back into a list
        new_instructions = self._collect_instructions(cfg)

        return TACMethod(
            class_name=method.class_name,
            method_name=method.method_name,
            params=method.params,
            instructions=new_instructions,
        )

    def _build_dominator_tree(
        self,
        cfg: ControlFlowGraph,
        idoms: dict[str, str],
    ) -> dict[str, list[str]]:
        """
        Build the dominator tree from immediate dominators.

        Returns a dict mapping each block to its children in the dom tree.
        """
        tree: dict[str, list[str]] = defaultdict(list)

        for block_id, idom_id in idoms.items():
            if idom_id is not None and idom_id != block_id:
                tree[idom_id].append(block_id)

        return dict(tree)

    def _compute_dominance_frontiers(
        self,
        cfg: ControlFlowGraph,
        idoms: dict[str, str],
    ) -> dict[str, set[str]]:
        """
        Compute dominance frontiers for each block.

        The dominance frontier of B is the set of blocks X such that:
        - B dominates a predecessor of X, but
        - B does not strictly dominate X

        This is where we need φ-functions for definitions in B.
        """
        frontiers: dict[str, set[str]] = {b.id: set() for b in cfg.blocks}

        for block in cfg.blocks:
            if len(block.predecessors) < 2:
                continue

            for pred in block.predecessors:
                runner = pred.id

                # Walk up the dominator tree until we find block's idom
                while runner != idoms.get(block.id):
                    frontiers[runner].add(block.id)
                    runner = idoms.get(runner)
                    if runner is None:
                        break

        return frontiers

    def _find_variable_definitions(
        self,
        cfg: ControlFlowGraph,
    ) -> dict[str, set[str]]:
        """
        Find all blocks that define each variable.

        Returns: var_name -> set of block IDs that assign to var
        """
        var_defs: dict[str, set[str]] = defaultdict(set)

        for block in cfg.blocks:
            for instr in block.instructions:
                for defined in instr.defs():
                    if isinstance(defined, Var):
                        var_defs[defined.name].add(block.id)

        return dict(var_defs)

    def _compute_phi_locations(
        self,
        cfg: ControlFlowGraph,
        var_defs: dict[str, set[str]],
        frontiers: dict[str, set[str]],
    ) -> dict[str, set[str]]:
        """
        Compute where to insert φ-functions for each variable.

        Uses the iterated dominance frontier algorithm.

        Returns: var_name -> set of block IDs needing φ for that var
        """
        phi_locs: dict[str, set[str]] = defaultdict(set)

        for var, def_blocks in var_defs.items():
            # Worklist algorithm for iterated dominance frontier
            worklist = list(def_blocks)
            processed = set()

            while worklist:
                block_id = worklist.pop()

                for frontier_block in frontiers.get(block_id, set()):
                    if frontier_block not in phi_locs[var]:
                        phi_locs[var].add(frontier_block)

                        # The φ-function itself is a definition
                        if frontier_block not in processed:
                            worklist.append(frontier_block)
                            processed.add(frontier_block)

        return dict(phi_locs)

    def _insert_phi_functions(
        self,
        cfg: ControlFlowGraph,
        phi_locations: dict[str, set[str]],
    ) -> None:
        """
        Insert φ-functions at the computed locations.

        Modifies the CFG in place.
        """
        block_map = {b.id: b for b in cfg.blocks}

        for var, block_ids in phi_locations.items():
            for block_id in block_ids:
                block = block_map[block_id]

                # Create φ-function with placeholder sources
                # Will be filled in during renaming
                phi = Phi(
                    dest=Var(var),
                    sources=[(Var(var), Label(pred.id)) for pred in block.predecessors],
                )

                # Insert at the beginning (after any labels)
                insert_idx = 0
                while insert_idx < len(block.instructions):
                    if not block.instructions[insert_idx].is_label():
                        break
                    insert_idx += 1

                block.instructions.insert(insert_idx, phi)

    def _rename_variables(
        self,
        cfg: ControlFlowGraph,
        dom_tree: dict[str, list[str]],
        var_defs: dict[str, set[str]],
    ) -> None:
        """
        Rename variables to SSA form.

        Uses a stack-based algorithm walking the dominator tree.
        """
        # Counter for each variable
        counters: dict[str, int] = defaultdict(int)

        # Stack of definitions for each variable
        stacks: dict[str, list[int]] = defaultdict(list)

        # Initialize stacks for all variables
        for var in var_defs:
            stacks[var] = [0]
            counters[var] = 1

        block_map = {b.id: b for b in cfg.blocks}
        entry_id = cfg.blocks[0].id if cfg.blocks else None

        if entry_id:
            self._rename_block(entry_id, block_map, dom_tree, counters, stacks)

    def _rename_block(
        self,
        block_id: str,
        block_map: dict[str, BasicBlock],
        dom_tree: dict[str, list[str]],
        counters: dict[str, int],
        stacks: dict[str, list[int]],
    ) -> None:
        """Rename variables in a block and its dominated children."""
        block = block_map[block_id]
        pushed: list[str] = []  # Variables we pushed onto stacks

        for _i, instr in enumerate(block.instructions):
            # Rename uses first (before processing defs)
            if not isinstance(instr, Phi):
                self._rename_uses(instr, stacks)

            # Rename definitions
            for defined in instr.defs():
                if isinstance(defined, Var):
                    var_name = defined.name
                    new_version = counters[var_name]
                    counters[var_name] += 1
                    stacks[var_name].append(new_version)
                    pushed.append(var_name)

                    # Update the instruction's destination
                    self._rename_def(instr, var_name, new_version)

        # Update φ-functions in successor blocks
        for succ in block.successors:
            for instr in succ.instructions:
                if isinstance(instr, Phi):
                    self._rename_phi_source(instr, block_id, stacks)

        # Recursively process dominated children
        for child_id in dom_tree.get(block_id, []):
            self._rename_block(child_id, block_map, dom_tree, counters, stacks)

        # Pop our definitions from the stacks
        for var_name in pushed:
            stacks[var_name].pop()

    def _rename_uses(
        self,
        instr: Instruction,
        stacks: dict[str, list[int]],
    ) -> None:
        """Rename variable uses in an instruction to their current SSA version."""
        # This is a simplified version - in practice we'd need to modify
        # the instruction's operands in place
        pass  # TODO: Implement proper use renaming

    def _rename_def(
        self,
        instr: Instruction,
        var_name: str,
        new_version: int,
    ) -> None:
        """Rename a definition to its new SSA version."""
        # Create new versioned name
        new_name = f"{var_name}_{new_version}"

        # Update the instruction's destination
        if hasattr(instr, "dest") and isinstance(instr.dest, Var):
            if instr.dest.name == var_name:
                instr.dest = Var(new_name)

    def _rename_phi_source(
        self,
        phi: Phi,
        pred_block_id: str,
        stacks: dict[str, list[int]],
    ) -> None:
        """Update a φ-function's source for a specific predecessor."""
        var_name = phi.dest.name.split("_")[0]  # Original variable name

        if stacks.get(var_name):
            current_version = stacks[var_name][-1]
            new_name = f"{var_name}_{current_version}"

            # Update the source for this predecessor
            new_sources = []
            for val, label in phi.sources:
                if label.name == pred_block_id:
                    new_sources.append((Var(new_name), label))
                else:
                    new_sources.append((val, label))
            phi.sources = new_sources

    def _collect_instructions(self, cfg: ControlFlowGraph) -> list[Instruction]:
        """Collect instructions from CFG blocks in order."""
        instructions: list[Instruction] = []

        # Use reverse postorder to get a reasonable ordering
        order = cfg.reverse_postorder()

        for block in order:
            # Add a label for the block
            instructions.append(LabelInstr(Label(block.id)))

            # Add the block's instructions
            for instr in block.instructions:
                if not instr.is_label():  # Skip labels we already added
                    instructions.append(instr)

        return instructions


def convert_to_ssa(method: TACMethod) -> TACMethod:
    """Convenience function to convert a method to SSA form."""
    builder = SSABuilder()
    return builder.convert_to_ssa(method)
