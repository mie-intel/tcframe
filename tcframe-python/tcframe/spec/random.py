import random as _random


class Random:
    def __init__(self):
        self._rng = _random.Random(0)

    def setSeed(self, seed: int) -> None:
        self._rng.seed(seed)

    def nextInt(self, lo: int, hi: int) -> int:
        """Return a random integer in [lo, hi] inclusive. Works with Python big ints."""
        return self._rng.randint(lo, hi)

    def nextDouble(self, lo: float, hi: float) -> float:
        """Return a random float in [lo, hi]."""
        return self._rng.uniform(lo, hi)


rnd = Random()
