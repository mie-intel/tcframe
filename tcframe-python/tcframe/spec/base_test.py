"""
BaseTestSpec — base class for all test specifications.

Users subclass this and implement SampleTestCaseN(), TestCases(), and/or
TestGroupN() methods.  self.Input([...]) / self.Output([...]) set the raw
strings for sample test cases.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from tcframe.spec.testcase import TestCase, TestSuite, _set_context

if TYPE_CHECKING:
    from tcframe.spec.base_problem import BaseProblemSpec


class BaseTestSpec:
    def __init__(self):
        self._current_sample: Optional[TestCase] = None

    # ------------------------------------------------------------------
    # Sample test case I/O helpers
    # ------------------------------------------------------------------

    def Input(self, lines: list) -> None:
        if self._current_sample is None:
            raise RuntimeError("Input() must be called inside SampleTestCaseN()")
        self._current_sample.sample_input = '\n'.join(str(l) for l in lines) + '\n'

    def Output(self, lines: list) -> None:
        if self._current_sample is None:
            raise RuntimeError("Output() must be called inside SampleTestCaseN()")
        self._current_sample.sample_output = '\n'.join(str(l) for l in lines) + '\n'

    # ------------------------------------------------------------------
    # Build the TestSuite (called by core.py)
    # ------------------------------------------------------------------

    def _build_test_suite(self, slug: str, problem_spec: 'BaseProblemSpec') -> TestSuite:
        suite = TestSuite()
        _set_context(suite, problem_spec)

        # --- Sample test cases ---
        for i in range(1, 26):
            method = getattr(type(self), f'SampleTestCase{i}', None)
            if method is None:
                break
            tc = TestCase(name=f'{slug}_sample_{i}', is_sample=True)
            self._current_sample = tc
            try:
                method(self)
            except NotImplementedError:
                self._current_sample = None
                break
            self._current_sample = None
            suite.add(tc)

        # --- Official test cases: TestCases() first, then TestGroupN() ---
        try:
            self.TestCases()
        except NotImplementedError:
            for i in range(1, 26):
                method = getattr(type(self), f'TestGroup{i}', None)
                if method is None:
                    break
                try:
                    method(self)
                except NotImplementedError:
                    break

        # Assign sequential names to unnamed official test cases
        idx = 1
        for tc in suite.test_cases:
            if not tc.is_sample and not tc.name:
                tc.name = f'{slug}_{idx}'
                idx += 1

        _set_context(None, None)
        return suite

    # ------------------------------------------------------------------
    # Stubs — user overrides these; not implemented = stop iteration
    # ------------------------------------------------------------------

    def TestCases(self): raise NotImplementedError
    def TestGroup1(self): raise NotImplementedError
    def TestGroup2(self): raise NotImplementedError
    def TestGroup3(self): raise NotImplementedError
    def TestGroup4(self): raise NotImplementedError
    def TestGroup5(self): raise NotImplementedError
    def TestGroup6(self): raise NotImplementedError
    def TestGroup7(self): raise NotImplementedError
    def TestGroup8(self): raise NotImplementedError
    def TestGroup9(self): raise NotImplementedError
    def TestGroup10(self): raise NotImplementedError
    def TestGroup11(self): raise NotImplementedError
    def TestGroup12(self): raise NotImplementedError
    def TestGroup13(self): raise NotImplementedError
    def TestGroup14(self): raise NotImplementedError
    def TestGroup15(self): raise NotImplementedError
    def TestGroup16(self): raise NotImplementedError
    def TestGroup17(self): raise NotImplementedError
    def TestGroup18(self): raise NotImplementedError
    def TestGroup19(self): raise NotImplementedError
    def TestGroup20(self): raise NotImplementedError
    def TestGroup21(self): raise NotImplementedError
    def TestGroup22(self): raise NotImplementedError
    def TestGroup23(self): raise NotImplementedError
    def TestGroup24(self): raise NotImplementedError
    def TestGroup25(self): raise NotImplementedError

    def SampleTestCase1(self): raise NotImplementedError
    def SampleTestCase2(self): raise NotImplementedError
    def SampleTestCase3(self): raise NotImplementedError
    def SampleTestCase4(self): raise NotImplementedError
    def SampleTestCase5(self): raise NotImplementedError
    def SampleTestCase6(self): raise NotImplementedError
    def SampleTestCase7(self): raise NotImplementedError
    def SampleTestCase8(self): raise NotImplementedError
    def SampleTestCase9(self): raise NotImplementedError
    def SampleTestCase10(self): raise NotImplementedError
    def SampleTestCase11(self): raise NotImplementedError
    def SampleTestCase12(self): raise NotImplementedError
    def SampleTestCase13(self): raise NotImplementedError
    def SampleTestCase14(self): raise NotImplementedError
    def SampleTestCase15(self): raise NotImplementedError
    def SampleTestCase16(self): raise NotImplementedError
    def SampleTestCase17(self): raise NotImplementedError
    def SampleTestCase18(self): raise NotImplementedError
    def SampleTestCase19(self): raise NotImplementedError
    def SampleTestCase20(self): raise NotImplementedError
    def SampleTestCase21(self): raise NotImplementedError
    def SampleTestCase22(self): raise NotImplementedError
    def SampleTestCase23(self): raise NotImplementedError
    def SampleTestCase24(self): raise NotImplementedError
    def SampleTestCase25(self): raise NotImplementedError
