"""
Tests for the data flow analysis framework.

These tests verify the core data flow abstractions work correctly
before testing specific analyses.
"""

import pytest
from pycoolc.optimization.dataflow import (
    ConstValue,
    ConstLattice,
    SetValue,
    Direction,
)


class TestConstValue:
    """Tests for the constant propagation lattice values."""

    def test_top(self):
        top = ConstValue.top()
        assert top.is_top()
        assert not top.is_bottom()
        assert not top.is_constant()
        assert str(top) == "⊤"

    def test_bottom(self):
        bottom = ConstValue.bottom()
        assert bottom.is_bottom()
        assert not bottom.is_top()
        assert not bottom.is_constant()
        assert str(bottom) == "⊥"

    def test_constant_int(self):
        c = ConstValue.constant(42)
        assert c.is_constant()
        assert not c.is_top()
        assert not c.is_bottom()
        assert c.get_constant() == 42
        assert str(c) == "42"

    def test_constant_bool(self):
        t = ConstValue.constant(True)
        f = ConstValue.constant(False)
        assert t.get_constant() is True
        assert f.get_constant() is False

    def test_constant_string(self):
        s = ConstValue.constant("hello")
        assert s.get_constant() == "hello"

    # Meet operation tests (from user's notes)
    
    def test_meet_bottom_with_anything(self):
        """lub(⊥, x) = x (Bottom is identity for meet)."""
        bottom = ConstValue.bottom()
        top = ConstValue.top()
        c = ConstValue.constant(42)
        
        assert bottom.meet(top) == top
        assert bottom.meet(c) == c
        assert bottom.meet(bottom) == bottom

    def test_meet_anything_with_bottom(self):
        """lub(x, ⊥) = x (Bottom is identity for meet)."""
        bottom = ConstValue.bottom()
        top = ConstValue.top()
        c = ConstValue.constant(42)
        
        assert top.meet(bottom) == top
        assert c.meet(bottom) == c

    def test_meet_top_absorbs(self):
        """lub(⊤, x) = ⊤ and lub(x, ⊤) = ⊤."""
        top = ConstValue.top()
        c = ConstValue.constant(42)
        
        assert top.meet(c) == top
        assert c.meet(top) == top
        assert top.meet(top) == top

    def test_meet_same_constant(self):
        """lub(c, c) = c."""
        c1 = ConstValue.constant(42)
        c2 = ConstValue.constant(42)
        
        result = c1.meet(c2)
        assert result.is_constant()
        assert result.get_constant() == 42

    def test_meet_different_constants(self):
        """lub(c1, c2) = ⊤ when c1 ≠ c2."""
        c1 = ConstValue.constant(1)
        c2 = ConstValue.constant(2)
        
        result = c1.meet(c2)
        assert result.is_top()

    def test_equality(self):
        assert ConstValue.top() == ConstValue.top()
        assert ConstValue.bottom() == ConstValue.bottom()
        assert ConstValue.constant(42) == ConstValue.constant(42)
        assert ConstValue.constant(1) != ConstValue.constant(2)
        assert ConstValue.top() != ConstValue.bottom()


class TestSetValue:
    """Tests for set-based lattice values."""

    def test_empty(self):
        s = SetValue.empty()
        assert len(s) == 0
        assert str(s) == "{}"

    def test_from_set(self):
        s = SetValue.from_set({"a", "b", "c"})
        assert len(s) == 3
        assert "a" in s
        assert "b" in s
        assert "c" in s

    def test_add(self):
        s = SetValue.empty()
        s2 = s.add("x")
        
        # Original unchanged (immutable)
        assert "x" not in s
        assert "x" in s2

    def test_remove(self):
        s = SetValue.from_set({"x", "y"})
        s2 = s.remove("x")
        
        assert "x" in s
        assert "x" not in s2
        assert "y" in s2

    def test_union(self):
        s1 = SetValue.from_set({"a", "b"})
        s2 = SetValue.from_set({"b", "c"})
        
        result = s1.union(s2)
        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_intersection(self):
        s1 = SetValue.from_set({"a", "b"})
        s2 = SetValue.from_set({"b", "c"})
        
        result = s1.intersection(s2)
        assert "a" not in result
        assert "b" in result
        assert "c" not in result

    def test_iteration(self):
        s = SetValue.from_set({"a", "b", "c"})
        elements = list(s)
        assert len(elements) == 3


class TestDirection:
    """Tests for analysis direction enum."""

    def test_forward(self):
        assert Direction.FORWARD != Direction.BACKWARD

    def test_backward(self):
        assert Direction.BACKWARD != Direction.FORWARD

