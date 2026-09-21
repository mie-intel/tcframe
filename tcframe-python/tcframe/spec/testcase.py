import threading
from typing import Callable, List, Optional

_ctx = threading.local()


class TestCase:
    def __init__(
        self,
        name: str,
        is_sample: bool = False,
        apply_fn: Optional[Callable[[], None]] = None,
        sample_input: Optional[str] = None,
        sample_output: Optional[str] = None,
    ):
        self.name = name
        self.is_sample = is_sample
        self._apply_fn = apply_fn
        self.sample_input = sample_input
        self.sample_output = sample_output

    def apply(self) -> None:
        if self._apply_fn:
            self._apply_fn()


class TestSuite:
    def __init__(self):
        self._cases: List[TestCase] = []

    def add(self, tc: TestCase) -> None:
        self._cases.append(tc)

    @property
    def test_cases(self) -> List[TestCase]:
        return self._cases


# ---------------------------------------------------------------------------
# Context helpers (set by BaseTestSpec._build_test_suite)
# ---------------------------------------------------------------------------

def _set_context(suite: Optional[TestSuite], spec: Optional[object]) -> None:
    _ctx.suite = suite
    _ctx.spec = spec


def _get_context():
    return getattr(_ctx, 'suite', None), getattr(_ctx, 'spec', None)


# ---------------------------------------------------------------------------
# Public DSL
# ---------------------------------------------------------------------------

def CASE(**kwargs) -> None:
    suite, spec = _get_context()
    if suite is None:
        raise RuntimeError("CASE() must be called inside TestCases() or TestGroupN()")

    _spec = spec  # capture for closure

    def apply():
        for name, value in kwargs.items():
            object.__setattr__(_spec, name, value)

    tc = TestCase(name="", is_sample=False, apply_fn=apply)
    suite.add(tc)
