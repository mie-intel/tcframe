"""
Fluent constraint-checking helpers, mirroring C++ tcframe's validator/core.hpp.

Usage inside CONS():
    CONS(lambda: valueOf(N).isBetween(1, 1000))
    CONS(lambda: eachElementOf(A).isBetween(1, N))
    CONS(lambda: elementsOf(A).areAscending())
"""

from __future__ import annotations
from typing import Sequence


class _ScalarChecker:
    def __init__(self, val):
        self._val = val

    def isBetween(self, lo, hi) -> bool:
        return lo <= self._val <= hi

    def equals(self, expected) -> bool:
        return self._val == expected

    def isLessThan(self, bound) -> bool:
        return self._val < bound

    def isAtMost(self, bound) -> bool:
        return self._val <= bound

    def isGreaterThan(self, bound) -> bool:
        return self._val > bound

    def isAtLeast(self, bound) -> bool:
        return self._val >= bound


class _CollectionChecker:
    def __init__(self, items: Sequence):
        self._items = list(items)

    # element-wise range
    def isBetween(self, lo, hi) -> bool:
        return all(lo <= x <= hi for x in self._items)

    def isLessThan(self, bound) -> bool:
        return all(x < bound for x in self._items)

    def isAtMost(self, bound) -> bool:
        return all(x <= bound for x in self._items)

    def isGreaterThan(self, bound) -> bool:
        return all(x > bound for x in self._items)

    def isAtLeast(self, bound) -> bool:
        return all(x >= bound for x in self._items)

    # ordering
    def areAscending(self) -> bool:
        return all(self._items[i] < self._items[i + 1] for i in range(len(self._items) - 1))

    def areNonDescending(self) -> bool:
        return all(self._items[i] <= self._items[i + 1] for i in range(len(self._items) - 1))

    def areDescending(self) -> bool:
        return all(self._items[i] > self._items[i + 1] for i in range(len(self._items) - 1))

    def areNonAscending(self) -> bool:
        return all(self._items[i] >= self._items[i + 1] for i in range(len(self._items) - 1))

    # uniqueness
    def areUnique(self) -> bool:
        return len(set(self._items)) == len(self._items)

    def haveUniqueValues(self) -> bool:
        return self.areUnique()


def valueOf(val) -> _ScalarChecker:
    """Check a single scalar value."""
    return _ScalarChecker(val)


def eachElementOf(collection: Sequence) -> _CollectionChecker:
    """Check each element of a collection (range, ordering, uniqueness)."""
    return _CollectionChecker(collection)


def elementsOf(collection: Sequence) -> _CollectionChecker:
    """Alias for eachElementOf — check ordering / uniqueness across a collection."""
    return _CollectionChecker(collection)
