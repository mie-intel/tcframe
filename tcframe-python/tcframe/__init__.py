"""
tcframe Python package.

    from tcframe import *

Exports everything a spec.py needs.
"""

from tcframe.spec.random import rnd
from tcframe.spec.io_format import LINE, LINES, GRID, EMPTY_LINE, SIZE
from tcframe.spec.constraint import CONS
from tcframe.spec.testcase import CASE, SUBTASKS
from tcframe.spec.config import TimeLimit, MemoryLimit
from tcframe.spec.base_problem import BaseProblemSpec
from tcframe.spec.base_test import BaseTestSpec
from tcframe.core import tcframe

__all__ = [
    'rnd',
    'LINE', 'LINES', 'GRID', 'EMPTY_LINE', 'SIZE',
    'CONS',
    'CASE', 'SUBTASKS',
    'TimeLimit', 'MemoryLimit',
    'BaseProblemSpec',
    'BaseTestSpec',
    'tcframe',
]
