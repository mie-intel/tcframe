"""ANSI color helpers for terminal output. Falls back to plain text when not a TTY."""

import sys


def _c(code: str, text: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f'\033[{code}m{text}\033[0m'


def green(t: str) -> str:   return _c('32', t)
def red(t: str) -> str:     return _c('31', t)
def yellow(t: str) -> str:  return _c('33', t)
def cyan(t: str) -> str:    return _c('36', t)
def gray(t: str) -> str:    return _c('90', t)
def bold(t: str) -> str:    return _c('1',  t)


# Map verdict code → color function
_VERDICT_COLOR = {
    'AC':  green,
    'WA':  red,
    'RTE': red,
    'TLE': yellow,
    'MLE': yellow,
    'ERR': gray,
}


def verdict(code: str) -> str:
    """Return verdict code colored for the terminal."""
    fn = _VERDICT_COLOR.get(code, lambda t: t)
    return fn(code)


def ok(text: str = 'OK') -> str:
    return green(text)


def failed(text: str = 'FAILED') -> str:
    return red(text)
