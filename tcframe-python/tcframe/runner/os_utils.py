import os
import shlex
import subprocess
import sys
from typing import Optional

# Signals that typically indicate memory exhaustion under RLIMIT_AS
_MLE_SIGNALS = frozenset((6, 7, 11))           # SIGABRT, SIGBUS, SIGSEGV
# Shell-wrapped signal exit codes (128 + signal) for the same signals
_MLE_SHELL_EXIT_CODES = frozenset((134, 135, 139))


def _make_memory_preexec(limit_mb: int):
    """Return a preexec_fn that sets RLIMIT_AS to limit_mb MB (Linux only)."""
    try:
        import resource
        limit_bytes = limit_mb * 1024 * 1024
        def preexec():
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        return preexec
    except ImportError:
        return None


def run_solution(
    command: str,
    in_path: str,
    out_path: str,
    time_limit: Optional[int] = None,
    memory_limit: Optional[int] = None,
) -> tuple[int, str, str]:
    """
    Run solution: stdin=in_path, stdout=out_path.
    Returns (exit_code, verdict_hint, stderr_text).
    verdict_hint is '' on success or a human-readable reason on failure.
    """
    preexec_fn = None
    if memory_limit is not None and sys.platform != 'win32':
        preexec_fn = _make_memory_preexec(memory_limit)

    try:
        with open(in_path, 'r') as stdin_f, open(out_path, 'w') as stdout_f:
            result = subprocess.run(
                command,
                stdin=stdin_f,
                stdout=stdout_f,
                stderr=subprocess.PIPE,
                shell=True,
                timeout=time_limit,
                preexec_fn=preexec_fn,
            )

        stderr_text = result.stderr.decode(errors='replace').strip()
        rc = result.returncode
        if rc == 0:
            return 0, '', stderr_text
        if rc < 0:
            sig = -rc
            if sig in _MLE_SIGNALS:
                return rc, 'memory limit exceeded', stderr_text
            return rc, f'killed by signal {sig}', stderr_text
        if memory_limit is not None and rc in _MLE_SHELL_EXIT_CODES:
            return rc, 'memory limit exceeded', stderr_text
        return rc, f'exit code {rc}', stderr_text

    except subprocess.TimeoutExpired:
        return -1, f'time limit exceeded ({time_limit}s)', ''
    except MemoryError:
        return -1, 'memory limit exceeded', ''
    except FileNotFoundError:
        return -1, 'solution not found', ''
    except Exception as exc:
        return -1, str(exc), ''


def run_scorer(
    scorer_command: str,
    in_path: str,
    expected_path: str,
    actual_path: str,
) -> tuple[bool, str]:
    """
    Run custom scorer: scorer <in> <expected> <actual>.
    Scorer exit 0 = AC, non-0 = WA.
    Returns (is_ac, scorer_message).
    scorer_message is the scorer's stdout/stderr output.
    """
    try:
        result = subprocess.run(
            f'{scorer_command} {shlex.quote(in_path)} '
            f'{shlex.quote(expected_path)} {shlex.quote(actual_path)}',
            capture_output=True,
            shell=True,
            timeout=30,
        )
        msg = (result.stdout + result.stderr).decode(errors='replace').strip()
        return result.returncode == 0, msg
    except subprocess.TimeoutExpired:
        return False, 'scorer timed out'
    except Exception as exc:
        return False, str(exc)


def run_interactive(
    communicator_command: str,
    solution_command: str,
    in_path: str,
    out_path: str,
    time_limit: Optional[int] = None,
    memory_limit: Optional[int] = None,
) -> tuple[int, str, str]:
    """
    Run an interactive problem.

    Communicator convention (same as C++ tcframe):
      - communicator stdin  = problem input file
      - communicator stdout = final output/verdict (written to out_path)
      - communicator talks to solution via fd3 (read from sol) and fd4 (write to sol)
      - solution uses its own stdin/stdout for the dialogue

    Returns (exit_code, verdict_hint, communicator_stderr).
    """
    if sys.platform == 'win32':
        return -1, 'interactive mode not supported on Windows', ''

    # comm_to_sol: communicator fd4 → solution stdin
    comm_to_sol_r, comm_to_sol_w = os.pipe()
    # sol_to_comm: solution stdout → communicator fd3
    sol_to_comm_r, sol_to_comm_w = os.pipe()

    sol_args = shlex.split(solution_command)
    comm_args = shlex.split(communicator_command)

    preexec_fn = None
    if memory_limit is not None:
        preexec_fn = _make_memory_preexec(memory_limit)

    try:
        solution = subprocess.Popen(
            sol_args,
            stdin=comm_to_sol_r,
            stdout=sol_to_comm_w,
            stderr=subprocess.PIPE,
            preexec_fn=preexec_fn,
        )
        # Close parent's copies of the solution ends
        os.close(comm_to_sol_r)
        os.close(sol_to_comm_w)

        _sol_to_comm_r = sol_to_comm_r
        _comm_to_sol_w = comm_to_sol_w

        def setup_comm_fds():
            # Remap: fd3 = read from solution, fd4 = write to solution
            os.dup2(_sol_to_comm_r, 3)
            os.dup2(_comm_to_sol_w, 4)
            if _sol_to_comm_r != 3:
                os.close(_sol_to_comm_r)
            if _comm_to_sol_w != 4:
                os.close(_comm_to_sol_w)

        with open(in_path, 'r') as in_f, open(out_path, 'w') as out_f:
            communicator = subprocess.Popen(
                comm_args,
                stdin=in_f,
                stdout=out_f,
                stderr=subprocess.PIPE,
                preexec_fn=setup_comm_fds,
                pass_fds=(sol_to_comm_r, comm_to_sol_w),
            )

        # Close the fds in the parent now that they're in the communicator child
        os.close(sol_to_comm_r)
        os.close(comm_to_sol_w)

        timeout = time_limit
        try:
            communicator.wait(timeout=timeout)
            solution.wait(timeout=max(timeout or 5, 5))
        except subprocess.TimeoutExpired:
            communicator.kill()
            solution.kill()
            communicator.wait()
            solution.wait()
            return -1, f'time limit exceeded ({time_limit}s)', ''

        sol_rc = solution.returncode
        sol_stderr = solution.stderr.read().decode(errors='replace').strip()
        comm_rc = communicator.returncode
        comm_stderr = communicator.stderr.read().decode(errors='replace').strip()

        if sol_rc != 0:
            if sol_rc < 0 and -sol_rc in _MLE_SIGNALS:
                return sol_rc, 'memory limit exceeded', comm_stderr
            if memory_limit is not None and sol_rc in _MLE_SHELL_EXIT_CODES:
                return sol_rc, 'memory limit exceeded', comm_stderr
            return sol_rc, f'solution exit code {sol_rc}', comm_stderr

        if comm_rc != 0:
            return comm_rc, f'communicator exit code {comm_rc}', comm_stderr

        return 0, '', comm_stderr

    except Exception as exc:
        # Clean up dangling fds on error
        for fd in (comm_to_sol_r, comm_to_sol_w, sol_to_comm_r, sol_to_comm_w):
            try:
                os.close(fd)
            except OSError:
                pass
        return -1, str(exc), ''
