"""DEMO ONLY: a deliberately broken engine used to show the tests catching bugs.

The real engine in game/game_engine.py is never modified. This subclass is only
loaded when the environment variable GAMETESTPRO_DEMO_BUG=1 is set
(see tests/conftest.py and scripts/demo_bug.py).
"""

from game.game_engine import GameEngine


class BuggyGameEngine(GameEngine):
    # BUG 1: score can be changed even when the game is not running / has ended
    def _require_running(self):
        pass

    # BUG 2: negative scores are accepted (only the type check is kept)
    def _validate_points(self, points):
        if isinstance(points, bool) or not isinstance(points, int):
            super()._validate_points(points)
