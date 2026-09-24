from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Verdict:
    code: str
    name: str
    priority: int

    def __gt__(self, other: 'Verdict') -> bool:
        return self.priority > other.priority

    def __ge__(self, other: 'Verdict') -> bool:
        return self.priority >= other.priority

    @classmethod
    def ac(cls) -> 'Verdict':
        return cls('AC', 'Accepted', 0)

    @classmethod
    def wa(cls) -> 'Verdict':
        return cls('WA', 'Wrong Answer', 2)

    @classmethod
    def rte(cls) -> 'Verdict':
        return cls('RTE', 'Runtime Error', 3)

    @classmethod
    def tle(cls) -> 'Verdict':
        return cls('TLE', 'Time Limit Exceeded', 4)

    @classmethod
    def err(cls) -> 'Verdict':
        return cls('ERR', 'Internal Error', 99)


@dataclass
class TestCaseVerdict:
    verdict: Verdict
    points: Optional[float] = None

    def to_string(self) -> str:
        if self.points is not None:
            return f"{self.verdict.name} [{_fmt(self.points)}]"
        return self.verdict.name


@dataclass
class SubtaskVerdict:
    verdict: Verdict
    points: float

    def to_string(self) -> str:
        return f"{self.verdict.name} [{_fmt(self.points)}]"


def _fmt(p: float) -> str:
    return f"{p:.2f}".rstrip('0').rstrip('.')
