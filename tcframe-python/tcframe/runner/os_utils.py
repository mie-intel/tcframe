import os
import shlex
import shutil
import subprocess
import sys
from typing import Optional, Union

_IS_WINDOWS = sys.platform == 'win32'

# Signals that typically indicate memory exhaustion under RLIMIT_AS
_MLE_SIGNALS = frozenset((6, 7, 11))           # SIGABRT, SIGBUS, SIGSEGV
# Shell-wrapped signal exit codes (128 + signal) for the same signals
_MLE_SHELL_EXIT_CODES = frozenset((134, 135, 139))

# Shell exit codes meaning the command itself could not be run
# (only relevant when a command needs a shell, see _needs_shell)
_SHELL_NOT_FOUND = 127           # POSIX sh: command not found
_SHELL_NOT_EXECUTABLE = 126      # POSIX sh: found but not executable
_CMD_NOT_FOUND = 9009            # Windows cmd.exe: command not recognized

# Characters that require a real shell to interpret the command
_SHELL_METACHARS = frozenset('|&;<>$`')


# ----------------------------------------------------------------------
# Command resolution (same behavior on Windows, Linux and macOS)
# ----------------------------------------------------------------------

class CommandError(Exception):
    """Raised when a command's executable cannot be found or run."""


def _needs_shell(command: str) -> bool:
    return any(c in _SHELL_METACHARS for c in command)


def _split_command(command: str) -> list[str]:
    """Split a command line into argv, keeping Windows backslash paths intact."""
    if _IS_WINDOWS:
        parts = shlex.split(command, posix=False)
        return [p[1:-1] if len(p) >= 2 and p[0] == p[-1] and p[0] in '"\'' else p
                for p in parts]
    return shlex.split(command)


def _is_path(prog: str) -> bool:
    return '/' in prog or os.sep in prog or bool(os.altsep and os.altsep in prog)


def _executable_candidates(prog: str) -> list[str]:
    """Paths to try for a program path; on Windows './solution' also matches solution.exe."""
    candidates = [prog]
    if _IS_WINDOWS and not os.path.splitext(prog)[1]:
        exts = os.environ.get('PATHEXT', '.COM;.EXE;.BAT;.CMD').split(os.pathsep)
        candidates += [prog + ext.lower() for ext in exts if ext]
    return candidates


def resolve_command(command: str, what: str = 'solution') -> Union[list[str], str]:
    """
    Resolve `command` into something subprocess can run without a shell.

    Returns an argv list whose first element is an absolute executable path,
    or the original string if the command needs a shell (pipes, redirects...).
    Raises CommandError with a human-readable message if the executable is missing.
    """
    try:
        parts = _split_command(command)
    except ValueError as exc:
        raise CommandError(f"cannot parse {what} command {command!r}: {exc}")
    if not parts:
        raise CommandError(f"{what} command is empty")

    resolved = _resolve_executable(parts[0], what)
    if _needs_shell(command):
        # Swap in the resolved path so every shell (sh, cmd.exe) runs the same program
        return f'{_quote_arg(resolved)} {_strip_first_token(command)}'.rstrip()
    return [resolved] + parts[1:]


def _quote_arg(arg: str) -> str:
    return subprocess.list2cmdline([arg]) if _IS_WINDOWS else shlex.quote(arg)


def _strip_first_token(command: str) -> str:
    """Return `command` without its leading (possibly quoted) program token."""
    s = command.lstrip()
    if s[:1] in ('"', "'"):
        end = s.find(s[0], 1)
        return s[end + 1:].lstrip() if end != -1 else ''
    parts = s.split(None, 1)
    return parts[1] if len(parts) > 1 else ''


def _resolve_executable(prog: str, what: str) -> str:
    if not _is_path(prog):
        found = shutil.which(prog)
        if found:
            return found
        msg = f"{what} command '{prog}' was not found on PATH."
        if any(os.path.isfile(c) for c in _executable_candidates(prog)):
            msg += f"\n    A file named '{prog}' exists here; use './{prog}' to run it."
        raise CommandError(msg)

    for path in _executable_candidates(prog):
        if os.path.isfile(path):
            if not _IS_WINDOWS and not os.access(path, os.X_OK):
                raise CommandError(f"{what} '{path}' exists but is not executable.\n"
                                   f"    Try: chmod +x {path}")
            return os.path.abspath(path)

    raise CommandError(_not_found_message(prog, what))


def _not_found_message(prog: str, what: str) -> str:
    msg = (f"{what} '{prog}' not found.\n"
           f"    looked for : {os.path.abspath(prog)}")
    if _IS_WINDOWS and not os.path.splitext(prog)[1]:
        msg += " (also tried .exe, .bat, .cmd, ...)"
    msg += f"\n    cwd        : {os.getcwd()}"

    stem = os.path.splitext(prog)[0]
    if not _IS_WINDOWS and os.path.isfile(stem + '.exe'):
        msg += (f"\n    '{stem}.exe' exists, but that is a Windows binary; "
                f"recompile it on this machine.")

    for src_ext in ('.cpp', '.cc', '.c'):
        if os.path.isfile(stem + src_ext):
            msg += (f"\n    Found '{stem + src_ext}'; compile it first, e.g.:"
                    f"\n        g++ -std=c++17 -O2 -o {stem} {stem + src_ext}")
            break
    else:
        msg += f"\n    Compile your {what} first, or pass --{what} <command>."
    return msg


def check_command(command: str, what: str = 'solution') -> Optional[str]:
    """Return None if `command` can be run, else a human-readable error message."""
    try:
        resolve_command(command, what)
        return None
    except CommandError as exc:
        return str(exc)


def _describe_exit(rc: int, stderr_text: str, via_shell: bool) -> str:
    if via_shell:
        if rc == _SHELL_NOT_FOUND:
            return 'exit code 127: command not found'
        if rc == _SHELL_NOT_EXECUTABLE:
            return 'exit code 126: command not executable'
        if _IS_WINDOWS and (rc == _CMD_NOT_FOUND
                            or 'is not recognized as an internal' in stderr_text):
            return f'exit code {rc}: command not found'
    return f'exit code {rc}'


def _signal_name(sig: int) -> str:
    try:
        import signal
        return f'{sig} ({signal.Signals(sig).name})'
    except (ValueError, AttributeError):
        return str(sig)


def _describe_os_error(exc: OSError, what: str) -> tuple[str, str]:
    """Map an OSError raised when starting a process to (verdict_hint, detail)."""
    if isinstance(exc, FileNotFoundError):
        return f'{what} not found', str(exc)
    if isinstance(exc, PermissionError):
        return f'{what} not executable', str(exc)
    # ENOEXEC on POSIX / WinError 193 on Windows: wrong binary format
    return (f'cannot execute {what}',
            f"{exc}\nThe binary may have been compiled for another OS or architecture.")


def _make_memory_preexec(limit_mb: int):
    """Return a preexec_fn that sets RLIMIT_AS to limit_mb MB (POSIX only)."""
    try:
        import resource
        limit_bytes = limit_mb * 1024 * 1024
        def preexec():
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        return preexec
    except ImportError:
        return None


# ----------------------------------------------------------------------
# Runners
# ----------------------------------------------------------------------

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
    if memory_limit is not None and not _IS_WINDOWS:
        preexec_fn = _make_memory_preexec(memory_limit)

    try:
        args = resolve_command(command, 'solution')
    except CommandError as exc:
        return -1, 'solution not found', str(exc)
    via_shell = isinstance(args, str)

    try:
        with open(in_path, 'r') as stdin_f, open(out_path, 'w') as stdout_f:
            result = subprocess.run(
                args,
                stdin=stdin_f,
                stdout=stdout_f,
                stderr=subprocess.PIPE,
                shell=via_shell,
                timeout=time_limit,
                preexec_fn=preexec_fn,
            )

        stderr_text = result.stderr.decode(errors='replace').strip()
        rc = result.returncode
        if rc == 0:
            return 0, '', stderr_text
        if rc < 0:
            sig = -rc
            if memory_limit is not None and sig in _MLE_SIGNALS:
                return rc, 'memory limit exceeded', stderr_text
            return rc, f'killed by signal {_signal_name(sig)}', stderr_text
        if memory_limit is not None and via_shell and rc in _MLE_SHELL_EXIT_CODES:
            return rc, 'memory limit exceeded', stderr_text
        return rc, _describe_exit(rc, stderr_text, via_shell), stderr_text

    except subprocess.TimeoutExpired:
        return -1, f'time limit exceeded ({time_limit}s)', ''
    except MemoryError:
        return -1, 'memory limit exceeded', ''
    except OSError as exc:
        reason, detail = _describe_os_error(exc, 'solution')
        return -1, reason, detail
    except Exception as exc:
        return -1, str(exc), ''

def run_scorer(
    scorer_command: str,
    in_path: str,
    expected_path: str,
    actual_path: str,
) -> tuple[bool, float, str]:
    """
    Run custom scorer: scorer <in> <expected> <actual>.

    Scorer stdout protocol (first line):
      AC           → accepted, full score (1.0)
      AC 0.7       → accepted, partial score 0.7 (0.0–1.0)
      WA           → wrong answer, score 0.0
      WA <msg>     → wrong answer with message
      (exit 0)     → AC if no verdict line; (exit non-0) → WA

    Returns (is_ac, score_fraction, message).
    score_fraction is in [0.0, 1.0]; 1.0 for full AC, 0.0 for WA.
    """
    try:
        args = resolve_command(scorer_command, 'scorer')
    except CommandError as exc:
        return False, 0.0, str(exc)
    file_args = [in_path, expected_path, actual_path]
    if isinstance(args, str):
        quote = subprocess.list2cmdline if _IS_WINDOWS else shlex.join
        args = f'{args} {quote(file_args)}'
    else:
        args = args + file_args

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            shell=isinstance(args, str),
            timeout=30,
        )
        raw = (result.stdout + result.stderr).decode(errors='replace').strip()
        lines = raw.splitlines()
        first = lines[0].strip() if lines else ''
        rest = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''
        message = rest or first

        parts = first.split()
        verdict_code = parts[0].upper() if parts else ''

        score = 1.0
        if len(parts) >= 2:
            try:
                score = max(0.0, min(1.0, float(parts[1])))
            except ValueError:
                pass

        # Determine AC/WA
        if verdict_code == 'AC':
            return True, score, rest
        if verdict_code == 'WA':
            return False, 0.0, message
        # No explicit verdict: use exit code
        if result.returncode == 0:
            return True, 1.0, message
        return False, 0.0, message

    except subprocess.TimeoutExpired:
        return False, 0.0, 'scorer timed out'
    except Exception as exc:
        return False, 0.0, str(exc)


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
    if _IS_WINDOWS:
        return -1, 'interactive mode not supported on Windows', ''

    try:
        sol_args = resolve_command(solution_command, 'solution')
        comm_args = resolve_command(communicator_command, 'communicator')
    except CommandError as exc:
        return -1, 'command not found', str(exc)
    if isinstance(sol_args, str):
        sol_args = ['/bin/sh', '-c', sol_args]
    if isinstance(comm_args, str):
        comm_args = ['/bin/sh', '-c', comm_args]

    # comm_to_sol: communicator fd4 → solution stdin
    comm_to_sol_r, comm_to_sol_w = os.pipe()
    # sol_to_comm: solution stdout → communicator fd3
    sol_to_comm_r, sol_to_comm_w = os.pipe()


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
