from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from tcframe.runner.verdict import Verdict, TestCaseVerdict, SubtaskVerdict, _fmt
from tcframe.runner.os_utils import run_solution, run_scorer, run_interactive
from tcframe.runner import colors

if TYPE_CHECKING:
    from tcframe.spec.testcase import TestSuite
    from tcframe.spec.config import MultipleTestCasesConfig

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
    scorer_command: Optional[str] = None         # None → diff; path → custom scorer
    communicator_command: Optional[str] = None   # None → batch; path → interactive
    has_output: bool = True                      # False → skip output comparison
    multi_tc_config: Optional['MultipleTestCasesConfig'] = None  # None → per-TC files


class Grader:
    def __init__(self, test_suite: 'TestSuite'):
        self._suite = test_suite

    def grade(self, options: GradingOptions) -> None:
        print(f"Grading {colors.bold(repr(options.slug))} "
              f"with {colors.bold(repr(options.solution_command))}...")
        if options.communicator_command:
            print(f"  mode         : interactive ({options.communicator_command})")
        elif options.scorer_command:
            print(f"  scorer       : {options.scorer_command}")
        if options.time_limit is not None:
            print(f"  time limit   : {options.time_limit}s")
        if options.memory_limit is not None:
            print(f"  memory limit : {options.memory_limit} MB")
        print()

        out_dir = Path(options.output_dir)
        has_subtasks = any(tc.subtask_ids for tc in self._suite.test_cases if not tc.is_sample)
        official_count = sum(1 for tc in self._suite.test_cases if not tc.is_sample)

        if options.multi_tc_config and options.multi_tc_config.counter_var:
            verdicts_by_subtask = self._grade_multi_tc(out_dir, options)
        else:
            verdicts_by_subtask = self._grade_normal(out_dir, options)

        print()
        self._print_summary(verdicts_by_subtask, options, has_subtasks, official_count)

    def _grade_normal(self, out_dir: Path, options: GradingOptions) -> Dict[int, List[TestCaseVerdict]]:
        verdicts_by_subtask: Dict[int, List[TestCaseVerdict]] = {}

        for tc in self._suite.test_cases:
            if tc.is_sample:
                continue

            in_path = out_dir / f"{tc.name}.in"
            expected_path = out_dir / f"{tc.name}.out"
            actual_path = out_dir / f"__tcframe_actual_{tc.name}.out"

            tc_verdict = self._grade_one(in_path, expected_path, actual_path, options)
            self._print_tc(tc.name, tc_verdict, options.brief)

            if actual_path.exists():
                actual_path.unlink()

            effective_ids = tc.subtask_ids if tc.subtask_ids else [MAIN_SUBTASK_ID]
            for sid in effective_ids:
                verdicts_by_subtask.setdefault(sid, []).append(tc_verdict)

        return verdicts_by_subtask

    def _grade_multi_tc(self, out_dir: Path, options: GradingOptions) -> Dict[int, List[TestCaseVerdict]]:
        verdicts_by_subtask: Dict[int, List[TestCaseVerdict]] = {}

        groups: Dict[int, List] = {}
        for tc in self._suite.test_cases:
            if not tc.is_sample:
                groups.setdefault(tc.group_number, []).append(tc)

        for group_num in sorted(groups):
            tcs = groups[group_num]
            file_idx = group_num if group_num > 0 else 1
            in_path = out_dir / f"{options.slug}_{file_idx}.in"
            expected_path = out_dir / f"{options.slug}_{file_idx}.out"
            actual_path = out_dir / f"__tcframe_actual_{options.slug}_{file_idx}.out"

            tc_verdict = self._grade_one(in_path, expected_path, actual_path, options)
            if actual_path.exists():
                actual_path.unlink()

            for tc in tcs:
                self._print_tc(tc.name, tc_verdict, options.brief)
                effective_ids = tc.subtask_ids if tc.subtask_ids else [MAIN_SUBTASK_ID]
                for sid in effective_ids:
                    verdicts_by_subtask.setdefault(sid, []).append(tc_verdict)

        return verdicts_by_subtask

    def _print_tc(self, name: str, tc_verdict: TestCaseVerdict, brief: bool) -> None:
        if brief:
            return
        code_str = colors.verdict(tc_verdict.verdict.code)
        suffix = ''
        if tc_verdict.verdict != Verdict.ac() and tc_verdict.extra:
            first_line = tc_verdict.extra.splitlines()[0] if tc_verdict.extra else ''
            if first_line:
                suffix = f' {colors.gray("—")} {first_line}'
        # Show partial score if scorer gave a fraction
        score_str = ''
        if tc_verdict.score < 1.0 and tc_verdict.verdict == Verdict.ac():
            score_str = f' [{_fmt(tc_verdict.score * 100)}%]'
        print(f"  {name}: {code_str}{score_str}{suffix}")

    def _grade_one(self, in_path, expected_path, actual_path, options) -> TestCaseVerdict:
        if not in_path.exists():
            return TestCaseVerdict(Verdict.err(), extra='input file not found')

        if options.communicator_command:
            ret, reason, stderr = run_interactive(
                options.communicator_command,
                options.solution_command,
                str(in_path),
                str(actual_path),
                time_limit=options.time_limit,
                memory_limit=options.memory_limit,
            )
        else:
            ret, reason, stderr = run_solution(
                options.solution_command,
                str(in_path),
                str(actual_path),
                time_limit=options.time_limit,
                memory_limit=options.memory_limit,
            )

        extra = stderr if stderr else None

        if ret != 0:
            if 'time limit' in reason:
                return TestCaseVerdict(Verdict.tle(), extra=extra)
            if 'memory limit' in reason:
                return TestCaseVerdict(Verdict.mle(), extra=extra)
            return TestCaseVerdict(Verdict.rte(), extra=extra)

        if not options.has_output:
            return TestCaseVerdict(Verdict.ac())

        if not expected_path.exists():
            return TestCaseVerdict(Verdict.err(), extra='expected output not found')

        if options.scorer_command:
            is_ac, score_frac, scorer_msg = run_scorer(
                options.scorer_command,
                str(in_path),
                str(expected_path),
                str(actual_path),
            )
            if is_ac:
                return TestCaseVerdict(Verdict.ac(), extra=scorer_msg or None,
                                       score=score_frac)
            return TestCaseVerdict(Verdict.wa(), extra=scorer_msg or None, score=0.0)
        else:
            if _diff(str(actual_path), str(expected_path)):
                return TestCaseVerdict(Verdict.ac())
            return TestCaseVerdict(Verdict.wa(), extra=extra)

    def _print_summary(
        self,
        verdicts_by_subtask: Dict[int, List[TestCaseVerdict]],
        options: GradingOptions,
        has_subtasks: bool,
        official_count: int,
    ) -> None:
        if not verdicts_by_subtask:
            print("No test cases graded.")
            return

        subtask_verdicts: Dict[int, SubtaskVerdict] = {}
        for sid, tcs in verdicts_by_subtask.items():
            if has_subtasks and options.subtask_points:
                pts = options.subtask_points.get(sid, 0.0)
                subtask_verdicts[sid] = _min_aggregate(tcs, pts)
            else:
                pts_each = 100.0 / official_count if official_count > 0 else 0.0
                subtask_verdicts[sid] = _sum_aggregate(tcs, pts_each)

        total_verdict = Verdict.ac()
        total_points = 0.0
        for sv in subtask_verdicts.values():
            if sv.verdict > total_verdict:
                total_verdict = sv.verdict
            total_points += sv.points

        if has_subtasks and options.subtask_points:
            for sid in sorted(subtask_verdicts):
                sv = subtask_verdicts[sid]
                v_str = colors.verdict(sv.verdict.code)
                print(f"  Subtask {sid}: {v_str} [{_fmt(sv.points)}]")
            print()

        v_str = colors.verdict(total_verdict.code)
        print(f"Total verdict: {v_str} [{_fmt(total_points)}]")


# ---------------------------------------------------------------------------
# Aggregators
# ---------------------------------------------------------------------------

def _min_aggregate(tcs: List[TestCaseVerdict], full_points: float) -> SubtaskVerdict:
    """MinAggregator: subtask passes only if ALL TCs pass (worst verdict wins)."""
    worst = Verdict.ac()
    min_score = 1.0
    for tc in tcs:
        if tc.verdict > worst:
            worst = tc.verdict
        if tc.score < min_score:
            min_score = tc.score
    points = full_points * min_score if worst == Verdict.ac() else 0.0
    return SubtaskVerdict(worst, points)


def _sum_aggregate(tcs: List[TestCaseVerdict], pts_each: float) -> SubtaskVerdict:
    """SumAggregator: each AC TC contributes pts_each * score; worst verdict reported."""
    worst = Verdict.ac()
    total = 0.0
    for tc in tcs:
        if tc.verdict > worst:
            worst = tc.verdict
        if tc.verdict == Verdict.ac():
            total += pts_each * tc.score
    return SubtaskVerdict(worst, total)


# ---------------------------------------------------------------------------
# Diff helper
# ---------------------------------------------------------------------------

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
