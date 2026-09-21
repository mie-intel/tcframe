import inspect
import threading
from typing import Callable, List, Optional

_ctx = threading.local()


class Constraint:
    def __init__(self, predicate: Callable[[], bool], description: str):
        self._pred = predicate
        self._desc = description

    def check(self) -> bool:
        return bool(self._pred())

    @property
    def description(self) -> str:
        return self._desc


class ConstraintSuite:
    def __init__(self):
        self._constraints: List[Constraint] = []

    def add(self, c: Constraint) -> None:
        self._constraints.append(c)

    @property
    def constraints(self) -> List[Constraint]:
        return self._constraints


class Verifier:
    def __init__(self, suite: ConstraintSuite):
        self._suite = suite

    def verify(self) -> List[str]:
        """Return list of failure descriptions (empty = all pass)."""
        return [c.description for c in self._suite.constraints if not c.check()]


# ---------------------------------------------------------------------------
# Context helpers
# ---------------------------------------------------------------------------

def _set_suite(suite: Optional[ConstraintSuite]) -> None:
    _ctx.suite = suite


def _get_suite() -> Optional[ConstraintSuite]:
    return getattr(_ctx, 'suite', None)


# ---------------------------------------------------------------------------
# Public DSL
# ---------------------------------------------------------------------------

def _extract_desc(pred: Callable) -> str:
    try:
        src_lines = inspect.getsource(pred).strip().splitlines()
        src = ' '.join(l.strip() for l in src_lines)
        idx = src.find('lambda:')
        if idx >= 0:
            body = src[idx + 7:].strip()
            # Trim trailing unmatched ')' that belong to CONS(...)
            depth = 0
            end = len(body)
            for i, ch in enumerate(body):
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    if depth == 0:
                        end = i
                        break
                    depth -= 1
            return body[:end].strip()
        return src
    except Exception:
        return repr(pred)


def CONS(predicate: Callable[[], bool]) -> None:
    suite = _get_suite()
    if suite is None:
        raise RuntimeError("CONS() must be called inside Constraints()")
    suite.add(Constraint(predicate, _extract_desc(predicate)))
