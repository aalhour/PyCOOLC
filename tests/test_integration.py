"""
Integration tests for PyCOOLC.

These tests verify that all example programs in the examples/ directory
can be successfully parsed and (where applicable) semantically analyzed.
"""

from pathlib import Path

import pytest

import pycoolc.ast as AST
from pycoolc.parser import make_parser
from pycoolc.semanalyser import make_semantic_analyser

# Find all .cl files in the examples directory
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
EXAMPLE_FILES = sorted(EXAMPLES_DIR.glob("*.cl"))

# Example files that are complete, self-contained programs
# They have a Main class with main method and don't depend on other files
COMPLETE_PROGRAMS = {
    "hello_world.cl",
    "arith.cl",
    "book_list.cl",
    "cells.cl",
    "complex.cl",
    "cool.cl",
    "graph.cl",
    "hairyscary.cl",
    "io.cl",
    "life.cl",
    "new_complex.cl",
    "palindrome.cl",
    "primes.cl",
    "sort_list.cl",
}

# Library files (no Main class) - valid COOL but not standalone programs
LIBRARY_FILES = {
    "atoi.cl",  # A2I class for ASCII/integer conversion
    "list.cl",  # List implementation
}

# Programs that depend on external files or have complex scoping patterns
# These require multi-file compilation which is not yet supported
MULTI_FILE_PROGRAMS = {
    "atoi_test.cl",  # Depends on atoi.cl for A2I class
    "lam.cl",  # Complex scoping patterns
}


@pytest.fixture(scope="module")
def parser():
    """Create a parser once for all tests in this module."""
    return make_parser()


@pytest.fixture(scope="module")
def analyzer():
    """Create a semantic analyzer once for all tests in this module."""
    return make_semantic_analyser()


class TestExampleProgramsParse:
    """Verify all example programs parse without syntax errors."""

    @pytest.mark.parametrize("example_file", EXAMPLE_FILES, ids=lambda f: f.name)
    def test_example_parses(self, parser, example_file):
        source = example_file.read_text(encoding="utf-8")
        result = parser.parse(source)
        assert result is not None, f"Parser returned None for {example_file.name}"
        assert isinstance(result, AST.Program), f"Expected Program AST for {example_file.name}"
        assert len(result.classes) > 0, f"No classes found in {example_file.name}"


class TestExampleProgramsAnalyze:
    """Verify complete example programs pass semantic analysis."""

    @pytest.mark.parametrize(
        "example_file",
        [f for f in EXAMPLE_FILES if f.name in COMPLETE_PROGRAMS],
        ids=lambda f: f.name,
    )
    def test_example_analyzes(self, parser, analyzer, example_file):
        source = example_file.read_text(encoding="utf-8")
        ast = parser.parse(source)
        # Should not raise any errors
        result = analyzer.transform(ast)
        assert isinstance(result, AST.Program)


class TestLibraryFilesParseButNotAnalyze:
    """Library files parse but lack Main class, so semantic analysis fails."""

    @pytest.mark.parametrize(
        "example_file", [f for f in EXAMPLE_FILES if f.name in LIBRARY_FILES], ids=lambda f: f.name
    )
    def test_library_parses(self, parser, example_file):
        source = example_file.read_text(encoding="utf-8")
        result = parser.parse(source)
        assert isinstance(result, AST.Program)
