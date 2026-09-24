"""
Distinct Count — tcframe-python subtask + grading example.

Problem:
    Given N integers, count the number of distinct values.

Input:
    N
    A_1 A_2 ... A_N

Output:
    K   (number of distinct values)

Subtask 1 (30 pts): 1 <= N <= 1000,   1 <= A_i <= 1000
Subtask 2 (70 pts): 1 <= N <= 200000, 1 <= A_i <= 1e9

Setup:
    make                # builds solution_ac, solution_tle, solution_mle

Generate test cases:
    python3 spec.py

Grade with each solution:
    python3 spec.py grade --solution ./solution_ac   -> all AC
    python3 spec.py grade --solution ./solution_tle  -> subtask 2 TLE
    python3 spec.py grade --solution ./solution_mle  -> subtask 2 RTE (MLE)

Override limits from the command line:
    python3 spec.py grade --solution ./solution_tle --no-time-limit
    python3 spec.py grade --solution ./solution_mle --no-memory-limit
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tcframe import *


class ProblemSpec(BaseProblemSpec):
    N: int
    A: list
    K: int  # answer

    def InputFormat(self):
        LINE(self.N)
        LINE(self.A)

    def OutputFormat(self):
        LINE(self.K)

    def GradingConfig(self):
        TimeLimit(2)
        MemoryLimit(256)

    def Constraints(self):
        CONS(lambda: 1 <= self.N)

    def Subtask1(self):
        Points(30)
        CONS(lambda: self.N <= 1000)
        CONS(lambda: all(1 <= x <= 1000 for x in self.A))

    def Subtask2(self):
        Points(70)
        CONS(lambda: self.N <= 200000)
        CONS(lambda: all(1 <= x <= 10**9 for x in self.A))


class TestSpec(BaseTestSpec):

    def SampleTestCase1(self):
        SUBTASKS(1, 2)
        self.Input(["5", "3 1 4 1 5"])
        self.Output(["4"])

    def SampleTestCase2(self):
        SUBTASKS(1, 2)
        self.Input(["4", "7 7 7 7"])
        self.Output(["1"])

    def TestGroup1(self):
        SUBTASKS(1, 2)

        CASE(N=1, A=[1], K=1)
        CASE(N=5, A=[1, 1, 1, 1, 1], K=1)
        CASE(N=5, A=[1, 2, 3, 4, 5], K=5)

        for _ in range(7):
            n = rnd.nextInt(1, 1000)
            a = [rnd.nextInt(1, 1000) for _ in range(n)]
            CASE(N=n, A=a, K=len(set(a)))

    def TestGroup2(self):
        SUBTASKS(2)

        # max N, all same
        CASE(N=200000, A=[42] * 200000, K=1)
        # max N, all distinct
        vals = list(range(1, 200001))
        CASE(N=200000, A=vals, K=200000)

        for _ in range(8):
            n = rnd.nextInt(50000, 200000)
            a = [rnd.nextInt(1, 10**9) for _ in range(n)]
            CASE(N=n, A=a, K=len(set(a)))


tcframe.run(ProblemSpec, TestSpec)
