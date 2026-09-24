from __future__ import annotations
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from tcframe.runner.os_utils import run_solution

if TYPE_CHECKING:
    from tcframe.spec.base_problem import BaseProblemSpec
    from tcframe.spec.io_format import IOManipulator
    from tcframe.spec.constraint import Verifier
    from tcframe.spec.testcase import TestCase, TestSuite
    from tcframe.spec.config import GradingConfig, MultipleTestCasesConfig


@dataclass
class GenerationOptions:
    slug: str
    output_dir: str = 'tc'
    solution_command: str = './solution'
    seed: int = 0
    time_limit: Optional[int] = None
    memory_limit: Optional[int] = None
    has_output: bool = True                          # False → NoOutput, skip solution
    multi_tc_config: Optional['MultipleTestCasesConfig'] = None  # None → normal mode


class Generator:
    def __init__(
        self,
        problem_spec: 'BaseProblemSpec',
        io_manipulator: 'IOManipulator',
        verifier: 'Verifier',
        test_suite: 'TestSuite',
    ):
        self._spec = problem_spec
        self._io = io_manipulator
        self._verifier = verifier
        self._suite = test_suite

    def generate(self, options: GenerationOptions) -> None:
        out_dir = Path(options.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        if options.time_limit is not None:
            print(f"  time limit   : {options.time_limit}s")
        if options.memory_limit is not None:
            print(f"  memory limit : {options.memory_limit} MB")

        ok_count = fail_count = 0

        multi = options.multi_tc_config
        if multi and multi.counter_var:
            # MultipleTestCasesConfig mode: combine TCs per group
            ok, fail = self._generate_multi_tc(out_dir, options)
        else:
            ok, fail = self._generate_normal(out_dir, options)

        ok_count, fail_count = ok, fail
        print()
        print(f"{ok_count} test case(s) generated.", end='')
        if fail_count:
            print(f"  {fail_count} test case(s) FAILED.", end='')
        print()

    # ------------------------------------------------------------------
    # Normal (one file per TC) generation
    # ------------------------------------------------------------------

    def _generate_normal(self, out_dir: Path, options: GenerationOptions):
        ok = fail = 0
        for tc in self._suite.test_cases:
            if tc.is_sample:
                self._write_sample(tc, out_dir)
                print(f"  {tc.name}: OK")
                ok += 1
            else:
                if self._generate_official(tc, out_dir, options):
                    print(f"  {tc.name}: OK")
                    ok += 1
                else:
                    fail += 1
        return ok, fail

    # ------------------------------------------------------------------
    # MultipleTestCasesConfig mode: combine per group
    # ------------------------------------------------------------------

    def _generate_multi_tc(self, out_dir: Path, options: GenerationOptions):
        multi = options.multi_tc_config
        ok = fail = 0

        # Write sample TCs normally (they are separate)
        for tc in self._suite.test_cases:
            if tc.is_sample:
                self._write_sample(tc, out_dir)
                print(f"  {tc.name}: OK")
                ok += 1

        # Group official TCs by group_number
        groups: Dict[int, List] = {}
        for tc in self._suite.test_cases:
            if not tc.is_sample:
                groups.setdefault(tc.group_number, []).append(tc)

        for group_num in sorted(groups):
            tcs = groups[group_num]
            # Use group_num=0 (TestCases) → single combined file slug_1.in
            # group_num=N (TestGroupN) → slug_N.in
            file_idx = group_num if group_num > 0 else 1
            in_path = out_dir / f"{options.slug}_{file_idx}.in"
            out_path = out_dir / f"{options.slug}_{file_idx}.out"

            # Verify constraints and capture input for each TC
            combined_ok = True
            captured_inputs = []
            for tc in tcs:
                tc.apply()
                failures = self._verifier.verify(tc.subtask_ids if tc.subtask_ids else None)
                if failures:
                    print(f"  {tc.name}: FAILED")
                    for msg in failures:
                        print(f"    * Does not satisfy: {msg}")
                    combined_ok = False
                    fail += 1
                    break
                buf = StringIO()
                self._io.write_input(buf)
                captured_inputs.append(buf.getvalue())

            if not combined_ok:
                continue

            # Write combined input: count line + TC blocks
            count = len(tcs)
            object.__setattr__(self._spec, multi.counter_var, count)
            with open(in_path, 'w') as f:
                f.write(f"{count}\n")
                for block in captured_inputs:
                    f.write(block)

            if not options.has_output:
                for tc in tcs:
                    print(f"  {tc.name}: OK")
                    ok += 1
                continue

            ret, reason, _ = run_solution(
                options.solution_command,
                str(in_path),
                str(out_path),
                time_limit=options.time_limit,
                memory_limit=options.memory_limit,
            )
            if ret != 0:
                for tc in tcs:
                    print(f"  {tc.name}: FAILED ({reason})")
                    fail += 1
            else:
                for tc in tcs:
                    print(f"  {tc.name}: OK")
                    ok += 1

        return ok, fail

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_sample(self, tc, out_dir: Path) -> None:
        if tc.sample_input is not None:
            (out_dir / f"{tc.name}.in").write_text(tc.sample_input)
        if tc.sample_output is not None:
            (out_dir / f"{tc.name}.out").write_text(tc.sample_output)

    def _generate_official(self, tc, out_dir: Path, options: GenerationOptions) -> bool:
        in_path = out_dir / f"{tc.name}.in"
        out_path = out_dir / f"{tc.name}.out"

        tc.apply()

        failures = self._verifier.verify(tc.subtask_ids if tc.subtask_ids else None)
        if failures:
            print(f"  {tc.name}: FAILED")
            for msg in failures:
                print(f"    * Does not satisfy: {msg}")
            return False

        with open(in_path, 'w') as f:
            self._io.write_input(f)

        if not options.has_output:
            return True

        ret, reason, _ = run_solution(
            options.solution_command,
            str(in_path),
            str(out_path),
            time_limit=options.time_limit,
            memory_limit=options.memory_limit,
        )
        if ret != 0:
            print(f"  {tc.name}: FAILED ({reason})")
            return False

        return True
