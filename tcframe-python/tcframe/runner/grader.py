from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from tcframe.runner.verdict import Verdict, TestCaseVerdict, SubtaskVerdict, _fmt
from tcframe.runner.os_utils import run_solution

if TYPE_CHECKING:
    from tcframe.spec.testcase import TestSuite

MAIN_SUBTASK_ID = -1


@dataclass
class GradingOptions:
    slug: str
    output_dir: str = 'tc'
    solution_command: str = './solution'
    time_limit: Optional[int] = None
    memory_limit: Optional[int] = None
    subtask_points: Dict[int, float] = field(default_factory=dict)
    brief: bool = False


class Grader:
    def __init__(self, test_suite: 'TestSuite'):
        self._suite = test_suite

    def grade(self, options: GradingOptions) -> None:
        print(f"Grading '{options.slug}' with '{options.solution_command}'...")
        if options.time_limit is not None:
            print(f"  time limit   : {options.time_limit}s")
        if options.memory_limit is not None:
            print(f"  memory limit : {options.memory_limit} MB")
        print()

        out_dir = Path(options.output_dir)
        has_subtasks = any(tc.subtask_ids for tc in self._suite.test_cases if not tc.is_sample)

        verdicts_by_subtask: Dict[int, List[TestCaseVerdict]] = {}

        for tc in self._suite.test_cases:
            if tc.is_sample:
                continue

            in_path = out_dir / f"{tc.name}.in"
            expected_path = out_dir / f"{tc.name}.out"
            actual_path = out_dir / f"__tcframe_actual_{tc.name}.out"

            tc_verdict = self._grade_one(in_path, expected_path, actual_path, options)

            if not options.brief:
                print(f"  {tc.name}: {tc_verdict.verdict.code}")

            if actual_path.exists():
                actual_path.unlink()

            effective_ids = tc.subtask_ids if tc.subtask_ids else [MAIN_SUBTASK_ID]
            for sid in effective_ids:
                verdicts_by_subtask.setdefault(sid, []).append(tc_verdict)

        print()
        self._print_summary(verdicts_by_subtask, options, has_subtasks)

    def _grade_one(self, in_path, expected_path, actual_path, options) -> TestCaseVerdict:
        if not in_path.exists():
            return TestCaseVerdict(Verdict.err())

        ret, reason = run_solution(
            options.solution_command,
            str(in_path),
            str(actual_path),
            time_limit=options.time_limit,
            memory_limit=options.memory_limit,
        )

        if ret != 0:
            if 'time limit' in reason:
                return TestCaseVerdict(Verdict.tle())
            if 'memory limit' in reason:
                return TestCaseVerdict(Verdict.mle())
            return TestCaseVerdict(Verdict.rte())

        if not expected_path.exists():
            return TestCaseVerdict(Verdict.err())

        if _diff(str(actual_path), str(expected_path)):
            return TestCaseVerdict(Verdict.ac())
        return TestCaseVerdict(Verdict.wa())

    def _print_summary(
        self,
        verdicts_by_subtask: Dict[int, List[TestCaseVerdict]],
        options: GradingOptions,
        has_subtasks: bool,
    ) -> None:
        if not verdicts_by_subtask:
            print("No test cases graded.")
            return

        subtask_verdicts: Dict[int, SubtaskVerdict] = {}
        for sid, tcs in verdicts_by_subtask.items():
            pts = options.subtask_points.get(sid, 0.0)
            subtask_verdicts[sid] = _min_aggregate(tcs, pts)

        total_verdict = Verdict.ac()
        total_points = 0.0
        for sv in subtask_verdicts.values():
            if sv.verdict > total_verdict:
                total_verdict = sv.verdict
            total_points += sv.points

        if has_subtasks and options.subtask_points:
            for sid in sorted(subtask_verdicts):
                sv = subtask_verdicts[sid]
                print(f"  Subtask {sid}: {sv.verdict.name} [{_fmt(sv.points)}]")
            print()

        if options.subtask_points:
            print(f"Total verdict: {total_verdict.name} [{_fmt(total_points)}]")
        else:
            print(f"Total verdict: {total_verdict.name}")


def _min_aggregate(tcs: List[TestCaseVerdict], full_points: float) -> SubtaskVerdict:
    worst = Verdict.ac()
    points = full_points
    for tc in tcs:
        if tc.verdict > worst:
            worst = tc.verdict
        if tc.verdict != Verdict.ac():
            points = 0.0
    return SubtaskVerdict(worst, points)


def _diff(actual: str, expected: str) -> bool:
    """Compare files, ignoring trailing whitespace and trailing blank lines."""
    try:
        with open(actual) as af, open(expected) as ef:
            a = [l.rstrip() for l in af.readlines()]
            e = [l.rstrip() for l in ef.readlines()]
        while a and not a[-1]:
            a.pop()
        while e and not e[-1]:
            e.pop()
        return a == e
    except Exception:
        return False
