"""
tcframe Python package.

    from tcframe import *

Exports everything a spec.py needs.
"""

from tcframe.spec.random import rnd
from tcframe.spec.io_format import LINE, LINES, GRID, EMPTY_LINE, SIZE
from tcframe.spec.constraint import CONS, Points
from tcframe.spec.testcase import CASE, SUBTASKS
from tcframe.spec.config import (
    TimeLimit, MemoryLimit,
    BatchEvaluator, InteractiveEvaluator, CustomScorer, NoOutput,
    Counter, OutputPrefix,
)
from tcframe.spec.base_problem import BaseProblemSpec
from tcframe.spec.base_test import BaseTestSpec
from tcframe.validator.core import valueOf, eachElementOf, elementsOf
from tcframe.core import tcframe

__all__ = [
    # RNG
    'rnd',
    # IO format DSL
    'LINE', 'LINES', 'GRID', 'EMPTY_LINE', 'SIZE',
    # Constraint DSL
    'CONS', 'Points',
    # Test case DSL
    'CASE', 'SUBTASKS',
    # Config DSL
    'TimeLimit', 'MemoryLimit',
    'BatchEvaluator', 'InteractiveEvaluator', 'CustomScorer', 'NoOutput',
    'Counter', 'OutputPrefix',
    # Validator helpers
    'valueOf', 'eachElementOf', 'elementsOf',
    # Base classes
    'BaseProblemSpec', 'BaseTestSpec',
    # Entry point
    'tcframe',
]
