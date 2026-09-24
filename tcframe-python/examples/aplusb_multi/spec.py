"""
A+B problem with MultipleTestCasesConfig.

Input format:
  T
  A B       (T times)

Output format:
  Case #i: A+B     (T times)
"""
import sys
sys.path.insert(0, '../..')

from tcframe import *


class ProblemSpec(BaseProblemSpec):
    T: int
    A: int
    B: int
    ANS: int

    def InputFormat(self):
        LINE(self.A, self.B)

    def OutputFormat(self):
        LINE(self.ANS)

    def MultipleTestCasesConfig(self):
        Counter(self.T)
        OutputPrefix("Case #%d: ")

    def GradingConfig(self):
        TimeLimit(1)
        MemoryLimit(64)

    def Constraints(self):
        CONS(lambda: valueOf(self.A).isBetween(-10**9, 10**9))
        CONS(lambda: valueOf(self.B).isBetween(-10**9, 10**9))


class TestSpec(BaseTestSpec):
    def SampleTestCase1(self):
        self.Input(["3", "1 2", "-3 5", "100 200"])
        self.Output(["Case #1: 3", "Case #2: 2", "Case #3: 300"])

    def TestCases(self):
        CASE(A=1, B=1)
        CASE(A=0, B=0)
        CASE(A=-10**9, B=10**9)
        CASE(A=10**9, B=10**9)
        CASE(A=rnd.nextInt(-10**9, 10**9), B=rnd.nextInt(-10**9, 10**9))


if __name__ == '__main__':
    tcframe.run(ProblemSpec, TestSpec)
