import inspect
import threading
from typing import Callable, Dict, List, Optional

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
        # 0 = global (Constraints()), 1..25 = subtask N (SubtaskN())
        self._groups: Dict[int, List[Constraint]] = {0: []}

    def add(self, c: Constraint) -> None:
        subtask_id = getattr(_ctx, 'current_subtask_id', 0)
        if subtask_id not in self._groups:
            self._groups[subtask_id] = []
        self._groups[subtask_id].append(c)

    def global_constraints(self) -> List[Constraint]:
        return self._groups.get(0, [])

    def subtask_constraints(self, subtask_id: int) -> List[Constraint]:
        return self._groups.get(subtask_id, [])

    def has_subtasks(self) -> bool:
        return any(k != 0 for k in self._groups)


class Verifier:
    def __init__(self, suite: ConstraintSuite):
        self._suite = suite

    def verify(self, subtask_ids: Optional[List[int]] = None) -> List[str]:
        """Return failure descriptions. Empty = all pass."""
        failures = []
        for c in self._suite.global_constraints():
            if not c.check():
                failures.append(c.description)
        if subtask_ids:
            for sid in subtask_ids:
                for c in self._suite.subtask_constraints(sid):
                    if not c.check():
                        failures.append(f"[subtask {sid}] {c.description}")
        return failures


# ---------------------------------------------------------------------------
# Context helpers
# ---------------------------------------------------------------------------

def _set_suite(suite: Optional[ConstraintSuite]) -> None:
    _ctx.suite = suite


def _get_suite() -> Optional[ConstraintSuite]:
    return getattr(_ctx, 'suite', None)


def _set_current_subtask(subtask_id: int) -> None:
    _ctx.current_subtask_id = subtask_id


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
        raise RuntimeError("CONS() must be called inside Constraints() or SubtaskN()")
    suite.add(Constraint(predicate, _extract_desc(predicate)))
