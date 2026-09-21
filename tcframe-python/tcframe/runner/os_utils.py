import subprocess


def run_solution(command: str, in_path: str, out_path: str) -> int:
    """
    Run solution binary with stdin from in_path, stdout to out_path.
    Returns the process exit code. Cross-platform (no ulimit).
    """
    try:
        with open(in_path, 'r') as stdin_f, open(out_path, 'w') as stdout_f:
            result = subprocess.run(
                command,
                stdin=stdin_f,
                stdout=stdout_f,
                stderr=subprocess.PIPE,
                shell=True,
            )
        return result.returncode
    except FileNotFoundError:
        return -1
    except Exception as exc:
        print(f"  [error] running solution: {exc}")
        return -1
