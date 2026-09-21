"""
Basic tests for tcframe-python MVP.

Run with:
    cd tcframe-python
    python -m pytest tests/ -v
"""

import io
import sys
import os

# Allow running from repo root without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tcframe import *
from tcframe.spec.io_format import IOFormat, IOManipulator, VarRef
from tcframe.spec.constraint import ConstraintSuite, Verifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_spec():
    """Return a fresh A+B ProblemSpec instance."""
    class ProblemSpec(BaseProblemSpec):
        A: int
        B: int
        result: int

        def InputFormat(self):
            LINE(self.A, self.B)

        def OutputFormat(self):
            LINE(self.result)

        def Constraints(self):
            CONS(lambda: 1 <= self.A <= 1000)
            CONS(lambda: 1 <= self.B <= 1000)

    return ProblemSpec()


# ---------------------------------------------------------------------------
# VarRef
# ---------------------------------------------------------------------------

def test_varref_get_set():
    spec = _make_spec()
    spec.A = 42
    ref = VarRef(spec, 'A', int)
    assert ref.get() == 42
    ref.set(99)
    assert spec.A == 99


# ---------------------------------------------------------------------------
# IO format — recording + writing
# ---------------------------------------------------------------------------

def test_line_write_scalars():
    spec = _make_spec()
    io = spec._build_io_format()
    spec.A = 3
    spec.B = 7
    buf = io.StringIO() if False else __import__('io').StringIO()
    io.write_input(buf)
    assert buf.getvalue() == '3 7\n'


def test_output_format_write():
    spec = _make_spec()
    io_m = spec._build_io_format()
    spec.result = 10
    buf = __import__('io').StringIO()
    io_m.write_output(buf)
    assert buf.getvalue() == '10\n'


# ---------------------------------------------------------------------------
# LINES + SIZE
# ---------------------------------------------------------------------------

def test_lines_write():
    class Spec(BaseProblemSpec):
        N: int
        vec: list

        def InputFormat(self):
            LINE(self.N)
            LINES(self.vec) % SIZE(self.N)

        def Constraints(self):
            pass

    spec = Spec()
    io_m = spec._build_io_format()
    spec.N = 3
    spec.vec = [10, 20, 30]
    buf = __import__('io').StringIO()
    io_m.write_input(buf)
    assert buf.getvalue() == '3\n10\n20\n30\n'


# ---------------------------------------------------------------------------
# GRID + SIZE
# ---------------------------------------------------------------------------

def test_grid_write():
    class Spec(BaseProblemSpec):
        R: int
        C: int
        grid: list

        def InputFormat(self):
            LINE(self.R, self.C)
            GRID(self.grid) % SIZE(self.R, self.C)

        def Constraints(self):
            pass

    spec = Spec()
    io_m = spec._build_io_format()
    spec.R = 2
    spec.C = 3
    spec.grid = [[1, 2, 3], [4, 5, 6]]
    buf = __import__('io').StringIO()
    io_m.write_input(buf)
    assert buf.getvalue() == '2 3\n1 2 3\n4 5 6\n'


# ---------------------------------------------------------------------------
# Constraints / Verifier
# ---------------------------------------------------------------------------

def test_constraints_pass():
    spec = _make_spec()
    spec.A = 500
    spec.B = 1000
    _, verifier = spec._build_constraint_suite()
    assert verifier.verify() == []


def test_constraints_fail_A():
    spec = _make_spec()
    spec.A = 0   # violates 1 <= A <= 1000
    spec.B = 1
    _, verifier = spec._build_constraint_suite()
    failures = verifier.verify()
    assert len(failures) == 1
    assert 'self.A' in failures[0]


def test_constraints_fail_both():
    spec = _make_spec()
    spec.A = 0
    spec.B = 9999
    _, verifier = spec._build_constraint_suite()
    assert len(verifier.verify()) == 2


# ---------------------------------------------------------------------------
# CASE + TestSuite
# ---------------------------------------------------------------------------

def test_case_assigns_variables():
    spec = _make_spec()

    class TestSpec(BaseTestSpec):
        def TestCases(self):
            CASE(A=3, B=7)
            CASE(A=100, B=200)

    ts = TestSpec()
    suite = ts._build_test_suite('prob', spec)

    assert len(suite.test_cases) == 2

    suite.test_cases[0].apply()
    assert spec.A == 3
    assert spec.B == 7

    suite.test_cases[1].apply()
    assert spec.A == 100
    assert spec.B == 200


def test_sample_test_case():
    spec = _make_spec()

    class TestSpec(BaseTestSpec):
        def SampleTestCase1(self):
            self.Input(["2 8"])
            self.Output(["10"])

        def TestCases(self):
            CASE(A=1, B=1)

    ts = TestSpec()
    suite = ts._build_test_suite('prob', spec)
    cases = suite.test_cases
    assert cases[0].is_sample
    assert cases[0].sample_input == '2 8\n'
    assert cases[0].sample_output == '10\n'
    assert not cases[1].is_sample


# ---------------------------------------------------------------------------
# Big integers
# ---------------------------------------------------------------------------

def test_big_int_in_case():
    spec = _make_spec()

    big = 10 ** 500

    class TestSpec(BaseTestSpec):
        def TestCases(self):
            CASE(A=big, B=big)

    ts = TestSpec()
    suite = ts._build_test_suite('prob', spec)
    suite.test_cases[0].apply()
    assert spec.A == big
    assert spec.B == big


# ---------------------------------------------------------------------------
# Test case naming
# ---------------------------------------------------------------------------

def test_test_case_names():
    spec = _make_spec()

    class TestSpec(BaseTestSpec):
        def SampleTestCase1(self):
            self.Input(["1 1"])
            self.Output(["2"])

        def TestCases(self):
            CASE(A=1, B=1)
            CASE(A=2, B=2)

    ts = TestSpec()
    suite = ts._build_test_suite('myprob', spec)
    names = [tc.name for tc in suite.test_cases]
    assert names == ['myprob_sample_1', 'myprob_1', 'myprob_2']


# ---------------------------------------------------------------------------
# rnd
# ---------------------------------------------------------------------------

def test_rnd_reproducible():
    rnd.setSeed(42)
    a = rnd.nextInt(1, 100)
    rnd.setSeed(42)
    b = rnd.nextInt(1, 100)
    assert a == b


def test_rnd_big_int():
    rnd.setSeed(0)
    v = rnd.nextInt(0, 10 ** 100)
    assert 0 <= v <= 10 ** 100
