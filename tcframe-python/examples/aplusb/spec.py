"""
A+B Problem — tcframe-python end-to-end example.

Run:
    cd examples/aplusb
    python3 spec.py

Or with a custom solution path:
    python3 spec.py  (defaults to ./solution)

Generates test cases in tc/ directory.
"""

import sys
import os

# When running without pip install, find the package from the repo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tcframe import *


class ProblemSpec(BaseProblemSpec):
    A: int
    B: int
    result: int

    def InputFormat(self):
        LINE(self.A, self.B)

    def OutputFormat(self):
        LINE(self.result)

    def Constraints(self):
        CONS(lambda: 1 <= self.A <= 10**18)
        CONS(lambda: 1 <= self.B <= 10**18)


class TestSpec(BaseTestSpec):

    def SampleTestCase1(self):
        self.Input(["2 8"])
        self.Output(["10"])

    def SampleTestCase2(self):
        self.Input(["1000000000000000000 1"])
        self.Output(["1000000000000000001"])

    def TestCases(self):
        # Edge cases
        CASE(A=1, B=1)
        CASE(A=1, B=10**18)
        CASE(A=10**18, B=10**18)

        # Random small
        for _ in range(3):
            CASE(A=rnd.nextInt(1, 1000), B=rnd.nextInt(1, 1000))

        # Random large
        for _ in range(3):
            CASE(A=rnd.nextInt(1, 10**18), B=rnd.nextInt(1, 10**18))

        # Python big int — works natively, no overflow
        CASE(A=10**18, B=10**18 - 1)


tcframe.run(ProblemSpec, TestSpec)
